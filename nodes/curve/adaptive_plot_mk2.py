from sys import implementation
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.adaptive_curve import populate_curve, populate_curve_old, MinMaxPerSegment, TotalCount

LEGACY_IMPLEMENTATION = '1'
NEW_IMPLEMENTATION = '2'

class SvAdaptivePlotCurveMk2Node(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Adaptive Plot Curve
    Tooltip: Adaptive Plot Curve
    """
    bl_idname = 'SvAdaptivePlotCurveMk2Node'
    bl_label = 'Adaptive Plot Curve'
    bl_icon = 'CURVE_NCURVE'

    def update_sockets(self, context):
        self.inputs['Seed'].hide_safe = not self.random
        self.inputs['Resolution'].hide_safe = (self.implementation == LEGACY_IMPLEMENTATION) or not (self.by_length or self.by_curvature)

        self.inputs['Count'].hide_safe = not (self.implementation == LEGACY_IMPLEMENTATION and self.gen_mode == 'TOTAL' or self.implementation == NEW_IMPLEMENTATION)
        self.inputs['MinPpe'].hide_safe = not (self.implementation == LEGACY_IMPLEMENTATION and self.gen_mode != 'TOTAL')
        self.inputs['MaxPpe'].hide_safe = not (self.implementation == LEGACY_IMPLEMENTATION and self.gen_mode != 'TOTAL')
        self.inputs['Segments'].hide_safe = not (self.implementation == LEGACY_IMPLEMENTATION)
        updateNode(self, context)

    implementations = [
        (LEGACY_IMPLEMENTATION, "Legacy implementation", "Legacy algorithm", 0),
        (NEW_IMPLEMENTATION, "Default implementation", "New (default) algorithm", 1)
    ]

    implementation : EnumProperty(
            name = "Implementation",
            items = implementations,
            default = NEW_IMPLEMENTATION,
            update = update_sockets)

    modes = [
            ('TOTAL', "Total count", "Specify total number of points to generate", 0),
            ('SEGMENT', "Per segment", "Specify minimum and maximum number of points per segment", 1)
        ]

    gen_mode : EnumProperty(
            name = "Points count",
            items = modes,
            default = 'TOTAL',
            update = update_sockets)

    sample_size : IntProperty(
            name = "Segments",
            description = "Number of initial subdivisions",
            default = 50,
            min = 3,
            update = updateNode)

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
            description = "Total number of points",
            min = 2, default = 50,
            update = updateNode)

    resolution : IntProperty(
            name = "Resolution",
            description = "Length and curvature calculation resolution",
            min = 3, default = 100,
            update = updateNode)

    random : BoolProperty(
            name = "Random",
            description = "Distribute points randomly",
            default = False,
            update = update_sockets)

    seed : IntProperty(
            name = "Seed",
            description = "Random Seed value",
            default = 0,
            update = updateNode)

    by_curvature : BoolProperty(
            name = "By Curvature",
            description = "Use curve curvature value to distribute additional points on the curve: places with greater curvature value will receive more points",
            default = True,
            update = update_sockets)

    by_length : BoolProperty(
            name = "By Length",
            description = "Use segment lengths to distribute additional points on the curve: segments with greater length will receive more points",
            default = False,
            update = update_sockets)

    curvature_clip : FloatProperty(
            name = "Curvature Clip",
            min = 0.0,
            default = 100.0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        row = layout.row(align=True)
        row.prop(self, 'by_curvature', toggle=True)
        row.prop(self, 'by_length', toggle=True)
        layout.prop(self, 'random')
        if self.implementation == LEGACY_IMPLEMENTATION:
            layout.prop(self, 'gen_mode')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'curvature_clip')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "Segments").prop_name = 'sample_size'
        self.inputs.new('SvStringsSocket', "MinPpe").prop_name = 'min_ppe'
        self.inputs.new('SvStringsSocket', "MaxPpe").prop_name = 'max_ppe'
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
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
        count_s = self.inputs['Count'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()
        samples_s = self.inputs['Segments'].sv_get()
        min_ppe_s = self.inputs['MinPpe'].sv_get()
        max_ppe_s = self.inputs['MaxPpe'].sv_get()

        verts_out = []
        edges_out = []
        ts_out = []
        inputs = zip_long_repeat(curve_s, count_s, resolution_s, seed_s, samples_s, min_ppe_s, max_ppe_s)
        for params in inputs:
            for curve, count, resolution, seed, samples, min_ppe, max_ppe in zip_long_repeat(*params):
                if not self.random:
                    seed = None
                if self.implementation == NEW_IMPLEMENTATION:
                    new_t = populate_curve(curve, count,
                                resolution = resolution,
                                by_length = self.by_length,
                                by_curvature = self.by_curvature,
                                curvature_clip = self.curvature_clip,
                                random = self.random,
                                seed = seed)
                else:
                    if self.gen_mode == 'SEGMENT':
                        controller = MinMaxPerSegment(min_ppe, max_ppe)
                    else:
                        controller = TotalCount(count)
                    new_t = populate_curve_old(curve, samples+1,
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
    bpy.utils.register_class(SvAdaptivePlotCurveMk2Node)

def unregister():
    bpy.utils.unregister_class(SvAdaptivePlotCurveMk2Node)

