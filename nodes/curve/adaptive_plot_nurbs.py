import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve

class SvAdaptivePlotNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Adaptive Plot NURBS Curve
    Tooltip: Adaptive Plot NURBS Curve
    """
    bl_idname = 'SvAdaptivePlotNurbsCurveNode'
    bl_label = 'Adaptive Plot NURBS Curve'
    bl_icon = 'CURVE_NCURVE'

    init_cuts : IntProperty(
            name = "Init Cuts",
            description = "Number of segments to subdivide the curve into, on each recursion step",
            default = 2,
            min = 2,
            update = updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            description = "Maximum permissible distance between the curve and it's plot",
            min = 1e-12,
            default = 1e-4,
            precision = 8,
            update = updateNode)

    join : BoolProperty(
            name = "Join",
            description = "Output single list of vertices / edges for all input curves",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "InitCuts").prop_name = 'init_cuts'
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "T")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        init_cuts_s = self.inputs['InitCuts'].sv_get()
        tolerance_s = self.inputs['Tolerance'].sv_get()

        curve_s = ensure_nesting_level(curve_s, 2, data_types = (SvCurve,))
        init_cuts_s = ensure_nesting_level(init_cuts_s, 2)
        tolerance_s = ensure_nesting_level(tolerance_s, 2)

        need_verts = self.outputs['Vertices'].is_linked

        verts_out = []
        edges_out = []
        ts_out = []

        for params in zip_long_repeat(curve_s, init_cuts_s, tolerance_s):
            new_verts = []
            new_edges = []
            new_ts = []
            for curve, init_cuts, tolerance in zip_long_repeat(*params):
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("Curve is not NURBS")
                ts = curve.calc_linear_segment_knots(splits = init_cuts, tolerance = tolerance)
                new_ts.append(ts.tolist())
                if need_verts:
                    verts = curve.evaluate_array(ts)
                    new_verts.append(verts.tolist())
                n = len(ts)
                edges = [(i, i+1) for i in range(n-1)]
                new_edges.append(edges)

            if self.join:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                ts_out.extend(new_ts)
            else:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                ts_out.append(new_ts)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['T'].sv_set(ts_out)

def register():
    bpy.utils.register_class(SvAdaptivePlotNurbsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvAdaptivePlotNurbsCurveNode)

