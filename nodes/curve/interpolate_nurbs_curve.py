
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.curve.nurbs import SvNurbsCurve, SvNativeNurbsCurve, SvGeomdlCurve
from sverchok.utils.math import supported_metrics
from sverchok.dependencies import geomdl

class SvExInterpolateNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Curve interpolation
    Tooltip: Interpolating NURBS Curve
    """
    bl_idname = 'SvExInterpolateNurbsCurveNode'
    bl_label = 'Interpolating NURBS Curve'
    bl_icon = 'CURVE_NCURVE'

    degree : IntProperty(
            name = "Degree",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            default = False,
            update = updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics,
        update=updateNode)

    def get_implementations(self, context):
        items = []
        i = 0
        if geomdl is not None:
            item = (SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation",i)
            i += 1
            items.append(item)
        item = (SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", i)
        items.append(item)
        return items

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')
        if self.nurbs_implementation == SvNurbsCurve.GEOMDL:
            layout.prop(self, 'centripetal', toggle=True)
        else:
            layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Knots")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        degree_s = self.inputs['Degree'].sv_get()

        curves_out = []
        points_out = []
        knots_out = []
        for vertices, degree in zip_long_repeat(vertices_s, degree_s):
            if isinstance(degree, (tuple, list)):
                degree = degree[0]

            vertices = np.array(vertices)
            if self.nurbs_implementation == SvNurbsCurve.GEOMDL:
                nurbs_class = SvGeomdlCurve
                metric = 'CENTRIPETAL' if self.centripetal else 'DISTANCE'
            else:
                nurbs_class = SvNativeNurbsCurve
                metric = self.metric

            curve = nurbs_class.interpolate(degree, vertices, metric=metric)

            points_out.append(curve.get_control_points().tolist())
            knots_out.append(curve.get_knotvector().tolist())

            curves_out.append(curve)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['Knots'].sv_set(knots_out)

def register():
    bpy.utils.register_class(SvExInterpolateNurbsCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExInterpolateNurbsCurveNode)

