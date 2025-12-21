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
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.nurbs_solver import adjust_nurbs_surface_for_curves, adjust_nurbs_surface_for_points

class SvAdjustNurbsSurfaceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Adjust NURBS Surfrace
    Tooltip: Adjust NURBS surface to pass through specified point or curve
    """
    bl_idname = 'SvAdjustNurbsSurfaceNode'
    bl_label = 'Adjust NURBS Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MOVE_CURVE_POINT'

    modes = [
            ('CURVE', "Iso U/V Curve", "Adjust surface to pass trough curve", 0),
            ('POINT', "Point", "Adjust surface to pass trhough point", 1)
        ]

    directions = [
            ('U', "U", "U direction", 0),
            ('V', "V", "V direction", 1)
        ]

    def update_sockets(self, context):
        self.inputs['UVPoint'].hide_safe = self.mode != 'POINT'
        self.inputs['Point'].hide_safe = self.mode != 'POINT'
        self.inputs['Parameter'].hide_safe = self.mode != 'CURVE'
        self.inputs['Curve'].hide_safe = self.mode != 'CURVE'
        updateNode(self, context)

    mode : EnumProperty(
            name = "Mode",
            items = modes,
            default = 'CURVE',
            update = update_sockets)

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
        self.inputs.new('SvVerticesSocket', "UVPoint")
        self.inputs.new('SvVerticesSocket', "Point")
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text='Mode:')
        layout.prop(self, 'mode', text='')
        if self.mode == 'CURVE':
            layout.prop(self, 'direction', expand=True)
            layout.prop(self, 'preserve_tangents')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        p_value_s = self.inputs['Parameter'].sv_get()

        input_level = get_data_nesting_level(surface_s, data_types=(SvSurface,))
        flat_output = input_level < 2

        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))

        if self.mode == 'POINT':
            uv_point_s = self.inputs['UVPoint'].sv_get()
            point_s = self.inputs['Point'].sv_get()
            uv_point_s = ensure_nesting_level(uv_point_s, 4)
            point_s = ensure_nesting_level(point_s, 4)
            curve_s = [[[None]]]
            p_value_s = [[[None]]]
        else:
            curve_s = self.inputs['Curve'].sv_get()
            curve_s = ensure_nesting_level(curve_s, 3, data_types=(SvCurve,))
            p_value_s = ensure_nesting_level(p_value_s, 3)
            uv_point_s = [[[[None]]]]
            point_s = [[[[None]]]]

        surface_out = []
        for params in zip_long_repeat(surface_s, curve_s, p_value_s, uv_point_s, point_s):
            new_surfaces = []
            for surface, curves, p_values, uv_points, points in zip_long_repeat(*params):
                surface = SvNurbsSurface.get(surface)
                if surface is None:
                    raise UnsupportedSurfaceTypeException("One of surfaces is not NURBS")
                if self.mode == 'CURVE':
                    curves = [SvNurbsCurve.to_nurbs(c) for c in curves]
                    if any(c is None for c in curves):
                        raise UnsupportedCurveTypeException("One of target curves is not NURBS")

                    targets = list(zip_long_repeat(p_values, curves))
                    surface = adjust_nurbs_surface_for_curves(surface, self.direction, targets,
                                                preserve_tangents = self.preserve_tangents,
                                                logger = self.sv_logger)
                else:
                    targets = [(uv[0], uv[1], pt) for uv, pt in zip_long_repeat(uv_points, points)]
                    surface = adjust_nurbs_surface_for_points(surface, targets)

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

