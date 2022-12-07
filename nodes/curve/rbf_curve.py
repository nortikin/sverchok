
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import make_euclidean_ts
from sverchok.utils.curve.rbf import SvRbfCurve
from sverchok.dependencies import scipy
from sverchok.utils.math import rbf_functions

if scipy is not None:
    from scipy.interpolate import Rbf


class SvExRbfCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Minimal RBF Curve
    Tooltip: Generate interpolating or approximating curve by RBF method
    """
    bl_idname = 'SvExRbfCurveNode'
    bl_label = 'RBF Curve'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_INTERP_CURVE'
    sv_dependencies = {'scipy'}

    function : EnumProperty(
            name = "Function",
            items = rbf_functions,
            default = 'multiquadric',
            update = updateNode)

    smooth : FloatProperty(
            name = "Smooth",
            description = "Smoothness parameter of used RBF function. If this is zero, then the curve will go through all provided points; otherwise, it will be only an approximating curve",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    epsilon : FloatProperty(
            name = "Epsilon",
            description = "Epsilon parameter of used RBF function; it affects the shape of generated curve",
            default = 1.0,
            min = 0.0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "function")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
        self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        vertices_s = ensure_nesting_level(vertices_s, 3)
        epsilon_s = self.inputs['Epsilon'].sv_get()
        smooth_s = self.inputs['Smooth'].sv_get()

        curves_out = []
        for vertices, epsilon, smooth in zip_long_repeat(vertices_s, epsilon_s, smooth_s):
            if isinstance(epsilon, (list, int)):
                epsilon = epsilon[0]
            if isinstance(smooth, (list, int)):
                smooth = smooth[0]

            vertices = np.array(vertices)
            ts = make_euclidean_ts(vertices)
            rbf = Rbf(ts, vertices,
                        function=self.function,
                        smooth=smooth,
                        epsilon=epsilon, mode='N-D')
            curve = SvRbfCurve(rbf, (0.0, 1.0))
            curves_out.append(curve)

        self.outputs['Curve'].sv_set(curves_out)


def register():
    bpy.utils.register_class(SvExRbfCurveNode)


def unregister():
    bpy.utils.unregister_class(SvExRbfCurveNode)
