
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, describe_data_shape
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve import SvSplineCurve

class SvCubicSplineNode(bpy.types.Node, SverchCustomTreeNode):
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

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics + xyz_metrics,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_cyclic", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvCurveSocket', "Curve")

    def build_spline(self, path):
        spline = CubicSpline(path, metric = self.metric, is_cyclic = self.is_cyclic)
        return spline

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        level = get_data_nesting_level(vertices_s)
        if level < 2 or level > 4:
            raise TypeError(f"Required nesting level is 2 to 4, provided data nesting level is {level}")
        if level == 2:
            vertices_s = [vertices_s]
            level = 3
        if level == 3:
            vertices_s = [vertices_s]

        out_curves = []
        for vertices_group in vertices_s:
            new_curves = []
            for vertices in vertices_group:
                spline = self.build_spline(vertices)
                curve = SvSplineCurve(spline)
                new_curves.append(curve)
            if level == 4:
                out_curves.append(new_curves)
            else:
                out_curves.extend(new_curves)

        self.outputs['Curve'].sv_set(out_curves)

def register():
    bpy.utils.register_class(SvCubicSplineNode)

def unregister():
    bpy.utils.unregister_class(SvCubicSplineNode)

