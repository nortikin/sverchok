
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.surface.algorithms import SvInterpolatingSurface
from sverchok.utils.curve import SvSplineCurve, make_euclidian_ts
from sverchok.dependencies import geomdl, scipy
from sverchok.utils.curve.nurbs import SvGeomdlCurve
from sverchok.utils.curve.rbf import SvRbfCurve
from sverchok.utils.math import rbf_functions

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
        if geomdl is not None:
            modes.append(('BSPLINE', "B-Spline", "B-Spline interpolation", 2))
        if scipy is not None:
            modes.append(('RBF', "RBF", "RBF interpolation", 3))
        return modes

    @throttled
    def update_sockets(self, context):
        self.inputs['Degree'].hide_safe = self.interp_mode != 'BSPLINE'
        self.inputs['Smooth'].hide_safe = self.interp_mode != 'RBF'
        self.inputs['Epsilon'].hide_safe = self.interp_mode != 'RBF'

    interp_mode : EnumProperty(
        name = "Interpolation mode",
        items = get_interp_modes,
        update = update_sockets)

    is_cyclic : BoolProperty(
        name = "Cyclic",
        default = False,
        update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            default = False,
            update = updateNode)

    degree : IntProperty(
            name = "Degree",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    function : EnumProperty(
            name = "Function",
            items = rbf_functions,
            default = 'multiquadric',
            update = updateNode)

    smooth : FloatProperty(
            name = "Smooth",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    epsilon : FloatProperty(
            name = "Epsilon",
            default = 1.0,
            min = 0.0,
            update = updateNode)
        
    def get_u_spline_constructor(self, degree, smooth, epsilon):
        if self.interp_mode == 'LIN':
            def make(vertices):
                spline = LinearSpline(vertices, metric='DISTANCE', is_cyclic=self.is_cyclic)
                return SvSplineCurve(spline)
            return make
        elif self.interp_mode == 'CUBIC':
            def make(vertices):
                spline = CubicSpline(vertices, metric='DISTANCE', is_cyclic=self.is_cyclic)
                return SvSplineCurve(spline)
            return make
        elif geomdl is not None and self.interp_mode == 'BSPLINE':
            from geomdl import fitting
            def make(vertices):
                curve = fitting.interpolate_curve(vertices, degree, centripetal=self.centripetal)
                return SvGeomdlCurve(curve)
            return make
        elif scipy is not None and self.interp_mode == 'RBF':
            from scipy.interpolate import Rbf
            def make(vertices):
                vertices = np.array(vertices)
                ts = make_euclidian_ts(vertices)
                rbf = Rbf(ts, vertices,
                            function=self.function,
                            smooth=smooth,
                            epsilon=epsilon, mode='N-D')
                return SvRbfCurve(rbf, (0.0, 1.0))
            return make
        else:
            raise Exception("Unsupported spline type: " + self.interp_mode)

    def draw_buttons(self, context, layout):
        layout.label(text='Interpolation mode:')
        layout.prop(self, 'interp_mode', text='')
        if self.interp_mode in {'LIN', 'CUBIC'}:
            layout.prop(self, 'is_cyclic', toggle=True)
        if self.interp_mode == 'BSPLINE':
            layout.prop(self, 'centripetal', toggle=True)
        if self.interp_mode == 'RBF':
            layout.prop(self, 'function')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curves")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
        self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curves'].sv_get()
        if 'Degree' in self.inputs:
            degree_s = self.inputs['Degree'].sv_get()
        else:
            degree_s = [[3]]
        if 'Epsilon' in self.inputs:
            epsilon_s = self.inputs['Epsilon'].sv_get()
        else:
            epsilon_s = [[1.0]]
        if 'Smooth' in self.inputs:
            smooth_s = self.inputs['Smooth'].sv_get()
        else:
            smooth_s = [[0.0]]

        if not isinstance(curves_s[0], (list, tuple)):
            curves_s = [curves_s]

        surfaces_out = []
        for curves, degree, epsilon, smooth in zip_long_repeat(curves_s, degree_s, epsilon_s, smooth_s):
            if isinstance(degree, (list, tuple)):
                degree = degree[0]
            if isinstance(epsilon, (list, int)):
                epsilon = epsilon[0]
            if isinstance(smooth, (list, int)):
                smooth = smooth[0]

            u_spline_constructor = self.get_u_spline_constructor(degree, smooth, epsilon)
            v_bounds = (0.0, 1.0)
            u_bounds = (0.0, 1.0)
            surface = SvInterpolatingSurface(u_bounds, v_bounds, u_spline_constructor, curves)
            surfaces_out.append(surface)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvInterpolatingSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvInterpolatingSurfaceNode)

