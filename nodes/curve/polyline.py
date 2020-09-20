
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.curve.primitives import SvLine
from sverchok.utils.curve import SvSplineCurve

class SvPolylineNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Polyline
    Tooltip: Generate segments of straight lines to connect several points
    """
    bl_idname = 'SvExPolylineNode'
    bl_label = 'Polyline'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POLYLINE'

    is_cyclic : BoolProperty(name = "Cyclic",
        description = "Whether the polyline is cyclic",
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

    concat : BoolProperty(
        name = "Concatenate",
        description = "If checked, output single curve which goes through all points; otherwise, output a separate curve for each edge",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_cyclic", toggle=True)
        layout.prop(self, "concat", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvCurveSocket', "Curve")

    def make_edges(self, vertices, is_cyclic):
        curves = []
        for v1, v2 in zip(vertices[:-1], vertices[1:]):
            line = SvLine.from_two_points(v1, v2)
            curves.append(line)
        if is_cyclic:
            line = SvLine.from_two_points(vertices[-1], vertices[0])
            curves.append(line)
        return curves

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])

        out_curves = []
        for vertices in vertices_s:
            if self.concat:
                spline = LinearSpline(vertices, metric = self.metric, is_cyclic = self.is_cyclic)
                curve = SvSplineCurve(spline)
                out_curves.append(curve)
            else:
                curves = self.make_edges(vertices, is_cyclic = self.is_cyclic)
                out_curves.append(curves)

        self.outputs['Curve'].sv_set(out_curves)

def register():
    bpy.utils.register_class(SvPolylineNode)

def unregister():
    bpy.utils.unregister_class(SvPolylineNode)

