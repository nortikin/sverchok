
from math import pi

from mathutils import Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvSplineCurve
from sverchok.utils.curve.algorithms import concatenate_curves

class SvKinkyCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Kinked Curve
    Tooltip: Construct an interpolated curve through a set of points with a kink angle threshold
    """
    bl_idname = 'SvKinkyCurveNode'
    bl_label = 'Kinked Curve'
    bl_icon = 'CON_SPLINEIK'
    sv_icon = 'SV_KINKY_CURVE'

    is_cyclic : BoolProperty(name = "Cyclic",
        description = "Whether the curve is cyclic",
        default = False,
        update=updateNode)

    metrics = [
        ('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
        ('DISTANCE', 'Euclidean', "Euclidean distance metric", 1),
        ('POINTS', 'Points', "Points based", 2),
        ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=metrics,
        update=updateNode)

    threshold : FloatProperty(
        name = "Angle threshold",
        description = "Kink angle threshold (in radians)",
        min = 0,
        default = pi/3,
        update=updateNode)

    concat : BoolProperty(
            name = "Concatenate",
            description = "Concatenate arc segments into single curve",
            default = True,
            update = updateNode)

    make_nurbs : BoolProperty(
        name = "NURBS output",
        description = "Generate a NURBS curve",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "concat", toggle=True)
        layout.prop(self, "is_cyclic", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'make_nurbs', toggle=True)
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "AngneThreshold").prop_name = 'threshold'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        threshold_s = self.inputs['AngneThreshold'].sv_get()

        verts_s = ensure_nesting_level(verts_s, 4)
        threshold_s = ensure_nesting_level(threshold_s, 2)

        curve_out = []
        for verts_i, threshold_i in zip_long_repeat(verts_s, threshold_s):
            for verts, threshold in zip_long_repeat(verts_i, threshold_i):
                verts = [Vector(v) for v in verts]

                if self.is_cyclic:
                    verts.append(verts[0])

                segments = [[verts[0]]]
                for v1, v2, v3 in zip(verts, verts[1:], verts[2:]):
                    dv1 = v2 - v1
                    dv2 = v2 - v3
                    angle = dv1.angle(dv2)
                    if angle < threshold:
                        segments[-1].append(v2)
                        segment = [v2]
                        segments.append(segment)
                    else:
                        segments[-1].append(v2)
                if not self.is_cyclic:
                    segments[-1].append(verts[-1])

                if self.is_cyclic:
                    v1, v2, v3 = verts[-2], verts[0], verts[1]
                    dv1 = v2 - v1
                    dv2 = v2 - v3
                    angle = dv1.angle(dv2)
                    if angle < threshold:
                        segments[-1].append(verts[-1])
                    else:
                        first_segment = segments[0]
                        segments = segments[1:]
                        if segments:
                            segments[-1].extend(first_segment)
                        else:
                            segments = [first_segment]

                if len(segments)==1:
                    # if len(segments)==1 then result curve is monosegment and smooth and is_cyclic has to be as is params 
                    new_curves = [SvSplineCurve.from_points(segment, metric=self.metric, is_cyclic=self.is_cyclic ) for segment in segments]
                elif len(segments)>1:
                    # if len(segments)>1 then result curve is multisegment and not smooth and is_cyclic has to be False
                    new_curves = [SvSplineCurve.from_points(segment, metric=self.metric, is_cyclic=False)           for segment in segments]
                else:
                    raise Exception("Count of segments has to be not 0")

                if self.make_nurbs:
                    if self.concat:
                        new_curves = [curve.to_nurbs().elevate_degree(target=3) for curve in new_curves]
                    else:
                        new_curves = [curve.to_nurbs() for curve in new_curves]
                if self.concat:
                    new_curves = [concatenate_curves(new_curves)]
                curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvKinkyCurveNode)

def unregister():
    bpy.utils.unregister_class(SvKinkyCurveNode)

