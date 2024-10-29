import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.adaptive_curve import populate_curve

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
        self.inputs['Resolution'].hide_safe = not (self.by_length or self.by_curvature)
        updateNode(self, context)

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

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'by_curvature', toggle=True)
        row.prop(self, 'by_length', toggle=True)
        layout.prop(self, 'random')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
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

        verts_out = []
        edges_out = []
        ts_out = []
        inputs = zip_long_repeat(curve_s, count_s, resolution_s, seed_s)
        for curves, count_i, resolution_i, seed_i in inputs:
            objects = zip_long_repeat(curves, count_i, resolution_i, seed_i)
            for curve, count, resolution, seed in objects:
                if not self.random:
                    seed = None
                new_t = populate_curve(curve, count,
                            resolution = resolution,
                            by_length = self.by_length,
                            by_curvature = self.by_curvature,
                            random = self.random,
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

