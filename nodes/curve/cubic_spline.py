
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.curve import SvExSplineCurve

class SvExCubicSplineNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Cubic Spline
    Tooltip: Generate cubic interpolation curve
    """
    bl_idname = 'SvExCubicSplineNode'
    bl_label = 'Cubic Spline'
    bl_icon = 'CON_SPLINEIK'

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

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_cyclic", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvExCurveSocket', "Curve")

    def build_spline(self, path):
        spline = CubicSpline(path, metric = self.metric, is_cyclic = self.is_cyclic)
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
    bpy.utils.register_class(SvExCubicSplineNode)

def unregister():
    bpy.utils.unregister_class(SvExCubicSplineNode)

