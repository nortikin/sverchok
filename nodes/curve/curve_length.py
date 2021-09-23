import numpy as np

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve.algorithms import SvCurveLengthSolver
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import SvNurbsCurveLengthSolver

class SvCurveLengthNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve Length
    Tooltip: Calculate length of the curve or it's segment
    """
    bl_idname = 'SvExCurveLengthNode'
    bl_label = 'Curve Length'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_LENGTH'

    resolution : IntProperty(
        name = 'Resolution',
        min = 1,
        default = 50,
        update = updateNode)

    t_min : FloatProperty(
        name = "T Min",
        default = 0.0,
        update = updateNode)

    t_max : FloatProperty(
        name = "T Max",
        default = 1.0,
        update = updateNode)

    modes = [
        ('ABS', "Absolute", "Use absolute values of T", 0),
        ('REL', "Relative", "Use relative values of T", 1)
    ]

    mode : EnumProperty(
        name = "T Mode",
        default = 'ABS',
        items = modes,
        update = updateNode)

    specify_accuracy : BoolProperty(
        name = "Specify accuracy",
        default = False,
        update = updateNode)

    accuracy : IntProperty(
        name = "Accuracy",
        default = 3,
        min = 0,
        update = updateNode)

    use_nurbs : BoolProperty(
        name = "NURBS",
        description = "Use special algorithm for NURBS curves",
        default = False,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "TMin").prop_name = 't_min'
        self.inputs.new('SvStringsSocket', "TMax").prop_name = 't_max'
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.outputs.new('SvStringsSocket', "Length")

    def draw_buttons(self, context, layout):
        layout.label(text='T mode:')
        layout.prop(self, 'mode', expand=True)
        layout.prop(self, 'specify_accuracy')
        if self.specify_accuracy:
            layout.prop(self, 'accuracy')
        #layout.prop(self, 'use_nurbs')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves = self.inputs['Curve'].sv_get()
        t_min_s = self.inputs['TMin'].sv_get()
        t_max_s = self.inputs['TMax'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()

        t_min_s = ensure_nesting_level(t_min_s, 2)
        t_max_s = ensure_nesting_level(t_max_s, 2)
        resolution_s = ensure_nesting_level(resolution_s, 2)

        if self.specify_accuracy:
            tolerance = 10 ** (-self.accuracy)
        else:
            tolerance = None

        length_out = []
        for curve, t_mins, t_maxs, resolutions in zip_long_repeat(curves, t_min_s, t_max_s, resolution_s):
            for t_min, t_max, resolution in zip_long_repeat(t_mins, t_maxs, resolutions):
                if self.mode == 'REL':
                    curve_t_min, curve_t_max = curve.get_u_bounds()
                    curve_t_range = curve_t_max - curve_t_min
                    t_min = t_min * curve_t_range + curve_t_min
                    t_max = t_max * curve_t_range + curve_t_min

                if t_min >= t_max:
                    length = 0.0
                else:
                    # "resolution" is for whole range of curve;
                    # take only part of it which corresponds to t_min...t_max segment.
                    curve_t_min, curve_t_max = curve.get_u_bounds()
                    resolution = int(resolution * (t_max - t_min) / (curve_t_max - curve_t_min))
                    if resolution < 1:
                        resolution = 1
                    if self.use_nurbs:
                        solver = SvNurbsCurveLengthSolver(curve)
                    else:
                        solver = SvCurveLengthSolver(curve)
                    solver.prepare('SPL', resolution, tolerance=tolerance)
                    length = solver.calc_length(t_min, t_max)

                length_out.append([length])

        self.outputs['Length'].sv_set(length_out)

def register():
    bpy.utils.register_class(SvCurveLengthNode)

def unregister():
    bpy.utils.unregister_class(SvCurveLengthNode)

