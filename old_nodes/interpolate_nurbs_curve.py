
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.curve.nurbs import SvNurbsCurve, SvNativeNurbsCurve, SvGeomdlCurve
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.math import supported_metrics
from sverchok.dependencies import geomdl

class SvExInterpolateNurbsCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve interpolation
    Tooltip: Interpolate NURBS Curve
    """
    bl_idname = 'SvExInterpolateNurbsCurveNode'
    bl_label = 'Interpolate NURBS Curve'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_INTERPOLATE_CURVE'
    
    replacement_nodes = [('SvExInterpolateNurbsCurveNodeMK2', None, None)]

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

    cyclic : BoolProperty(
            name = "Cyclic",
            default = False,
            update = updateNode)

    implementations = []
    if geomdl is not None:
        implementations.append((SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    implementations.append((SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", 1))

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items=implementations,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')
        if self.nurbs_implementation == SvNurbsCurve.GEOMDL:
            layout.prop(self, 'centripetal', toggle=True)
        else:
            layout.prop(self, 'cyclic')
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
                implementation = SvNurbsCurve.GEOMDL
                metric = 'CENTRIPETAL' if self.centripetal else 'DISTANCE'
            else:
                implementation = SvNurbsCurve.NATIVE
                metric = self.metric

            curve = SvNurbsMaths.interpolate_curve(implementation, degree, vertices, metric=metric, cyclic=self.cyclic, logger=self.sv_logger)

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

