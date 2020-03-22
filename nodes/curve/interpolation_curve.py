
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.geom import LinearSpline, CubicSpline

from sverchok.utils.curve import SvExSplineCurve

class SvExSplineCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Interpolation Curve / Spline
    Tooltip: Interpolation Curve
    """
    bl_idname = 'SvExSplineCurveNode'
    bl_label = 'Interpolation Curve'
    bl_icon = 'CURVE_NCURVE'

    is_cyclic : BoolProperty(name = "Cyclic",
        description = "Whether the spline is cyclic",
        default = False,
        update=updateNode)

    metrics = [
        ('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
        ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
        ('POINTS', 'Points', "Points based", 2),
        ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=metrics,
        update=updateNode)

    modes = [
        ('SPL', 'Cubic', "Cubic Spline", 0),
        ('LIN', 'Linear', "Linear Interpolation", 1)]

    spline_mode: EnumProperty(name='Interpolation mode',
        default="SPL", items=modes,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "spline_mode", expand=True)
        layout.prop(self, "is_cyclic", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'

    def build_spline(self, path):
        metric = self.metric
        if self.spline_mode == 'LIN':
            spline = LinearSpline(path, metric = metric, is_cyclic = self.is_cyclic)
        else:  # SPL
            spline = CubicSpline(path, metric = metric, is_cyclic = self.is_cyclic)
        return spline

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])

        out_curves = []
        for vertices in vertices_s:
            spline = self.build_spline(vertices)
            curve = SvExSplineCurve(spline)
            out_curves.append(curve)

        self.outputs['Curve'].sv_set(out_curves)

def register():
    bpy.utils.register_class(SvExSplineCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExSplineCurveNode)

