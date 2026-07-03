import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_to_first, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve.algorithms import SvCurveLengthSolver
from sverchok.utils.curve import SvCurve

class SvCurveRangeNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Domain / Range
    Tooltip: Output minimum and maximum values of T parameter allowed by the curve
    """
    bl_idname = 'SvExCurveRangeNodeMK2'
    bl_label = 'Curve Domain'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_DOMAIN'

    resolution : IntProperty(
        name = 'Resolution',
        min = 1,
        default = 50,
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

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "curves")
        self.inputs.new('SvStringsSocket', "resolution").prop_name = 'resolution'
        self.inputs["curves"].label = "Curves"
        self.inputs["resolution"].label = "Resolution"

        self.outputs.new('SvStringsSocket', "tmin")
        self.outputs.new('SvStringsSocket', "tmax")
        self.outputs.new('SvStringsSocket', "range")
        self.outputs.new('SvStringsSocket', "lengths")

        self.outputs['tmin'].label = "TMin"
        self.outputs['tmax'].label = "TMax"
        self.outputs['range'].label = "Range"
        self.outputs['lengths'].label = "Lengths"

    def draw_buttons(self, context, layout):
        col = layout.box().column(align=True)
        col.prop(self, 'specify_accuracy', )
        col1 = col.row(heading='Accuracy:')
        if self.specify_accuracy==False:
            col1.enabled = False
        col1.prop(self, 'accuracy', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['curves'].sv_get()
        resolution_s = self.inputs['resolution'].sv_get()
        resolution_s = ensure_nesting_level(resolution_s, 2)
        t_min_out = []
        t_max_out = []
        range_out = []
        lengths_out = []

        if isinstance(curve_s[0], SvCurve):
            curve_s = [curve_s]

        if self.specify_accuracy:
            tolerance = 10 ** (-self.accuracy)
        else:
            tolerance = None

        for curves, resolutions in zip_to_first(curve_s, resolution_s):
            t_min_new = []
            t_max_new = []
            range_new = []
            lengths_new = []
            for curve, resolution in zip_to_first(curves, resolutions):
                t_min, t_max = curve.get_u_bounds()
                t_range = t_max - t_min
                t_min_new.append(t_min)
                t_max_new.append(t_max)
                range_new.append(t_range)

                if resolution < 1:
                        resolution = 1
                solver = SvCurveLengthSolver(curve)
                solver.prepare('SPL', resolution, tolerance=tolerance)
                length = solver.calc_length(t_min, t_max)
                lengths_new.append(length)
                pass
            t_min_out.append(t_min_new)
            t_max_out.append(t_max_new)
            range_out.append(range_new)
            lengths_out.append(lengths_new)

        self.outputs['tmin'].sv_set(t_min_out)
        self.outputs['tmax'].sv_set(t_max_out)
        self.outputs['range'].sv_set(range_out)
        self.outputs['lengths'].sv_set(lengths_out)
        return

classes = [SvCurveRangeNodeMK2,]
register, unregister = bpy.utils.register_classes_factory(classes)

