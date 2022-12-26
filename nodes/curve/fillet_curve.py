# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.fillet import (
        SMOOTH_POSITION, SMOOTH_TANGENT, SMOOTH_ARC, SMOOTH_BIARC, SMOOTH_QUAD, SMOOTH_NORMAL, SMOOTH_CURVATURE,
        SMOOTH_G2,
        fillet_polyline_from_curve, fillet_nurbs_curve
    )
from sverchok.utils.handle_blender_data import keep_enum_reference

class SvFilletCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Fillet Curve Bevel
    Tooltip: Smooth a NURBS curve (or polyline) by adding fillets or bevels in it's fracture points.
    """
    bl_idname = 'SvFilletCurveNode'
    bl_label = 'Fillet Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FILLET_POLYLINE'

    radius : FloatProperty(
        name = "Radius",
        min = 0.0,
        default = 0.2,
        update = updateNode)

    cut_offset : FloatProperty(
        name = "Cut Offset",
        default = 0.05,
        min = 0.0,
        update = updateNode)

    bulge_factor : FloatProperty(
        name = "Bulge Factor",
        default = 0.5,
        min = 0.0,
        update = updateNode)

    concat : BoolProperty(
        name = "Concatenate",
        default = True,
        update = updateNode)

    scale_to_unit : BoolProperty(
        name = "Even domains",
        description = "Give each segment and each arc equal T parameter domain of [0; 1]",
        default = False,
        update = updateNode)

    @keep_enum_reference
    def get_smooth_modes(self, context):
        items = []
        items.append((SMOOTH_POSITION, "0 - Position", "Connect segments with straight line segment", 0))
        items.append((SMOOTH_TANGENT, "1 - Tangency", "Connect segments such that their tangents are smoothly joined", 1))
        if not self.is_polyline:
            items.append((SMOOTH_BIARC, "1 - Bi Arc", "Connect segments with Bi Arc, such that tangents are smoothly joined", 2))
            #items.append((SMOOTH_NORMAL, "2 - Normals", "Connect segments such that their normals (second derivatives) are smoothly joined", 3))
            #items.append((SMOOTH_CURVATURE, "3 - Curvature", "Connect segments such that their curvatures (third derivatives) are smoothly joined", 4))
            #items.append((SMOOTH_G2, "G2 - Curvature", "Connect curves such that their tangents, normals and curvatures are continuosly joined", 6))
        else:
            items.append((SMOOTH_ARC, "1 - Circular Arc", "Connect segments with circular arcs", 5))
        return items

    def update_sockets(self, context):
        self.inputs['Radius'].hide_safe = not self.is_polyline
        self.inputs['CutOffset'].hide_safe = self.is_polyline
        self.inputs['BulgeFactor'].hide_safe = self.is_polyline or self.smooth_mode != SMOOTH_TANGENT
        self.outputs['Centers'].hide_safe = not (self.is_polyline and self.smooth_mode == SMOOTH_ARC)
        self.outputs['Radius'].hide_safe = not (self.is_polyline and self.smooth_mode == SMOOTH_ARC)
        updateNode(self, context)

    smooth_mode : EnumProperty(
        name = "Continuity",
        description = "How smooth should be the curve at points where original curve is replaced with fillet arcs; bigger value give more smooth touching",
        items = get_smooth_modes,
        update = update_sockets)

    is_polyline : BoolProperty(
        name = "Polylines only",
        description = "If checked, the node will work with polylines only, but `Circular Arc' option will be available",
        default = False,
        update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'is_polyline')
        layout.label(text="Continuity")
        layout.prop(self, 'smooth_mode', text='')
        layout.prop(self, "concat")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.concat:
            layout.prop(self, "scale_to_unit")

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "CutOffset").prop_name = 'cut_offset'
        self.inputs.new('SvStringsSocket', "BulgeFactor").prop_name = 'bulge_factor'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvMatrixSocket', "Centers")
        self.outputs.new('SvStringsSocket', "Radius")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        cut_offset_s = self.inputs['CutOffset'].sv_get()
        bulge_factor_s = self.inputs['BulgeFactor'].sv_get()

        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        nested_output = input_level > 1

        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        if self.is_polyline:
            radius_s = ensure_nesting_level(radius_s, 3)
        else:
            radius_s = ensure_nesting_level(radius_s, 2)
        cut_offset_s = ensure_nesting_level(cut_offset_s, 2)
        bulge_factor_s = ensure_nesting_level(bulge_factor_s, 2)

        curves_out = []
        centers_out = []
        radius_out = []
        for params in zip_long_repeat(curves_s, radius_s, cut_offset_s, bulge_factor_s):
            new_curves = []
            new_centers = []
            new_radiuses = []
            for curve, radiuses, cut_offset, bulge_factor in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("One of curves is not a NURBS")
                if self.is_polyline:
                    curve, centers, radiuses = fillet_polyline_from_curve(curve, radiuses,
                                smooth = self.smooth_mode,
                                concat = self.concat,
                                scale_to_unit = self.scale_to_unit)
                    new_centers.append(centers)
                    new_curves.append(curve)
                    new_radiuses.append(radiuses)
                else:
                    curve = fillet_nurbs_curve(curve,
                                smooth = self.smooth_mode,
                                cut_offset = cut_offset,
                                bulge_factor = bulge_factor)
                    new_curves.append(curve)
            if nested_output:
                curves_out.append(new_curves)
                centers_out.append(new_centers)
                radius_out.append(new_radiuses)
            else:
                curves_out.extend(new_curves)
                centers_out.extend(new_centers)
                radius_out.extend(new_radiuses)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Centers'].sv_set(centers_out)
        self.outputs['Radius'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvFilletCurveNode)

def unregister():
    bpy.utils.unregister_class(SvFilletCurveNode)

