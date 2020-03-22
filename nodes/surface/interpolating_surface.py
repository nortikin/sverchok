
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.surface import SvExInterpolatingSurface
from sverchok.utils.curve import SvExSplineCurve, make_euclidian_ts

class SvInterpolatingSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Interpolating surface from curves
    Tooltip: Generate interpolating surface across several curves
    """
    bl_idname = 'SvInterpolatingSurfaceNode'
    bl_label = 'Surface from Curves'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_FROM_CURVES'

    def get_interp_modes(self, context):
        modes = [
            ('LIN', "Linear", "Linear interpolation", 0),
            ('CUBIC', "Cubic", "Cubic interpolation", 1)
        ]
        return modes

    interp_mode : EnumProperty(
        name = "Interpolation mode",
        items = get_interp_modes,
        update = updateNode)

    is_cyclic : BoolProperty(
        name = "Cyclic",
        default = False,
        update = updateNode)

    def get_u_spline_constructor(self):
        if self.interp_mode == 'LIN':
            def make(vertices):
                spline = LinearSpline(vertices, metric='DISTANCE', is_cyclic=self.is_cyclic)
                return SvExSplineCurve(spline)
            return make
        elif self.interp_mode == 'CUBIC':
            def make(vertices):
                spline = CubicSpline(vertices, metric='DISTANCE', is_cyclic=self.is_cyclic)
                return SvExSplineCurve(spline)
            return make
        else:
            raise Exception("Unsupported spline type: " + self.interp_mode)

    def draw_buttons(self, context, layout):
        layout.label(text='Interpolation mode:')
        layout.prop(self, 'interp_mode', text='')
        layout.prop(self, 'is_cyclic', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Curves").display_shape = 'DIAMOND'
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curves'].sv_get()

        if not isinstance(curves_s[0], (list, tuple)):
            curves_s = [curves_s]

        surfaces_out = []
        for curves in curves_s:

            u_spline_constructor = self.get_u_spline_constructor(degree)
            v_bounds = (0.0, 1.0)
            u_bounds = (0.0, 1.0)
            surface = SvExInterpolatingSurface(u_bounds, v_bounds, u_spline_constructor, curves)
            surfaces_out.append(surface)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvInterpolatingSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvInterpolatingSurfaceNode)

