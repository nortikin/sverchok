import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.adaptive_curve import populate_curve, MinMaxPerSegment, TotalCount

class SvAdaptivePlotCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Adaptive Plot Curve
    Tooltip: Adaptive Plot Curve
    """
    bl_idname = 'SvAdaptivePlotCurveNode'
    bl_label = 'Adaptive Plot Curve'
    bl_icon = 'CURVE_NCURVE'

    sample_size : IntProperty(
            name = "Segments",
            default = 50,
            min = 3,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['Seed'].hide_safe = not self.random
        self.inputs['Count'].hide_safe = self.gen_mode != 'TOTAL'
        self.inputs['MinPpe'].hide_safe = self.gen_mode == 'TOTAL'
        self.inputs['MaxPpe'].hide_safe = self.gen_mode == 'TOTAL'
        updateNode(self, context)

    modes = [
            ('TOTAL', "Total count", "Specify total number of points to generate", 0),
            ('SEGMENT', "Per segment", "Specify minimum and maximum number of points per segment", 1)
        ]

    gen_mode : EnumProperty(
            name = "Points count",
            items = modes,
            default = 'TOTAL',
            update = update_sockets)

    min_ppe : IntProperty(
            name = "Min per segment",
            description = "Minimum number of new points per regular sampling interval",
            min = 0, default = 0,
            update = updateNode)

    max_ppe : IntProperty(
            name = "Max per segment",
            description = "Minimum number of new points per regular sampling interval",
            min = 1, default = 5,
            update = updateNode)

    count : IntProperty(
            name = "Count",
            description = "Total number of points; NOTE: with Random mode enabled, actual number of generated points can be smaller than specified here",
            min = 2, default = 50,
            update = updateNode)

    random : BoolProperty(
            name = "Random",
            description = "Distribute points randomly; NOTE: in this mode, if Total Count is specified, actual number of generated points can be less than specified",
            default = False,
            update = update_sockets)

    seed : IntProperty(
            name = "Seed",
            description = "Random Seed value",
            default = 0,
            update = updateNode)

    by_curvature : BoolProperty(
            name = "By Curvature",
            default = True,
            update = updateNode)

    by_length : BoolProperty(
            name = "By Length",
            default = False,
            update = updateNode)

    curvature_clip : FloatProperty(
            name = "Clip Curvature",
            description = "Do not consider curvature values bigger than specified one; set to 0 to consider all curvature values",
            default = 100,
            min = 0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'by_curvature', toggle=True)
        row.prop(self, 'by_length', toggle=True)
        layout.prop(self, 'gen_mode')
        layout.prop(self, 'random', toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.by_curvature:
            layout.prop(self, 'curvature_clip')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Segments").prop_name = 'sample_size'
        self.inputs.new('SvStringsSocket', "MinPpe").prop_name = 'min_ppe'
        self.inputs.new('SvStringsSocket', "MaxPpe").prop_name = 'max_ppe'
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "Seed").prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "T")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        curve_s = ensure_nesting_level(curve_s, 2, data_types = (SvCurve,))
        samples_s = self.inputs['Segments'].sv_get()
        count_s = self.inputs['Count'].sv_get()
        min_ppe_s = self.inputs['MinPpe'].sv_get()
        max_ppe_s = self.inputs['MaxPpe'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()

        verts_out = []
        edges_out = []
        ts_out = []
        inputs = zip_long_repeat(curve_s, samples_s, min_ppe_s, max_ppe_s, count_s, seed_s)
        for curves, samples_i, min_ppe_i, max_ppe_i, count_i, seed_i in inputs:
            objects = zip_long_repeat(curves, samples_i, min_ppe_i, max_ppe_i, count_i, seed_i)
            for curve, samples, min_ppe, max_ppe, count, seed in objects:
                if not self.random:
                    seed = None
                if self.gen_mode == 'SEGMENT':
                    controller = MinMaxPerSegment(min_ppe, max_ppe)
                else:
                    controller = TotalCount(count)
                new_t = populate_curve(curve, samples+1,
                            by_length = self.by_length,
                            by_curvature = self.by_curvature,
                            population_controller = controller,
                            curvature_clip = self.curvature_clip,
                            seed = seed)
                n = len(new_t)
                ts_out.append(new_t.tolist())
                new_verts = curve.evaluate_array(new_t).tolist()
                verts_out.append(new_verts)
                new_edges = [(i,i+1) for i in range(n-1)]
                edges_out.append(new_edges)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['T'].sv_set(ts_out)

def register():
    bpy.utils.register_class(SvAdaptivePlotCurveNode)

def unregister():
    bpy.utils.unregister_class(SvAdaptivePlotCurveNode)

