# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from hmac import new
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface import SvSurface, UnsupportedSurfaceTypeException
from sverchok.utils.surface.nurbs import SvNurbsSurface, adjust_nurbs_surface_for_curves

class SvAdjustNurbsSurfaceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Adjust NURBS Surfrace
    Tooltip: Adjust NURBS surface to pass through specified curve
    """
    bl_idname = 'SvAdjustNurbsSurfaceNode'
    bl_label = 'Adjust NURBS Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MOVE_CURVE_POINT'

    directions = [
            ('U', "U", "U direction", 0),
            ('V', "V", "V direction", 1)
        ]

    direction : EnumProperty(
            name = "Parameter",
            items = directions,
            default = 'U',
            update = updateNode)

    p_value : FloatProperty(
            name = "Parameter",
            default = 0.5,
            update = updateNode)

    preserve_tangents : BoolProperty(
            name = "Preserve tangents",
            description = "Preserve surface tangents along second direction",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Parameter").prop_name = 'p_value'
        self.outputs.new('SvSurfaceSocket', "Surface")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'direction', expand=True)
        layout.prop(self, 'preserve_tangents')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        curve_s = self.inputs['Curve'].sv_get()
        p_value_s = self.inputs['Parameter'].sv_get()

        input_level = get_data_nesting_level(surface_s, data_types=(SvSurface,))
        flat_output = input_level < 2

        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        curve_s = ensure_nesting_level(curve_s, 3, data_types=(SvCurve,))
        p_value_s = ensure_nesting_level(p_value_s, 3)

        surface_out = []
        for params in zip_long_repeat(surface_s, curve_s, p_value_s):
            new_surfaces = []
            for surface, curves, p_values in zip_long_repeat(*params):
                surface = SvNurbsSurface.get(surface)
                if surface is None:
                    raise UnsupportedSurfaceTypeException("One of surfaces is not NURBS")
                curves = [SvNurbsCurve.to_nurbs(c) for c in curves]
                if any(c is None for c in curves):
                    raise UnsupportedCurveTypeException("One of curves is not NURBS")

                targets = list(zip_long_repeat(p_values, curves))
                surface = adjust_nurbs_surface_for_curves(surface, self.direction, targets,
                                               preserve_tangents = self.preserve_tangents,
                                               logger = self.sv_logger)
                new_surfaces.append(surface)
            if flat_output:
                surface_out.extend(new_surfaces)
            else:
                surface_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvAdjustNurbsSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvAdjustNurbsSurfaceNode)

