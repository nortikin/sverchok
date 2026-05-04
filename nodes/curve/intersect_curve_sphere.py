# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, IntProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import get_data_nesting_level, updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve.core import UnsupportedCurveTypeException, SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.manifolds import intersect_curve_sphere, intersect_nurbs_curve_sphere


class SvCrossCurveSphereNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Intersect Curve with Sphere
    Tooltip: Intersect Curve with Sphere
    """
    bl_idname = 'SvCrossCurveSphereNode'
    bl_label = 'Intersect Curve with Sphere'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CROSS_CURVE_PLANE'
    sv_dependencies = {'scipy'}

    directions = [
            ('1', 'Forward by T', "From smaller to bigger values of curve T parameter", 0),
            ('-1', 'Backward by T', "From bigger to smaller values of curve T parameter", 1)
        ]
    
    radius : FloatProperty(
        name = "Radius",
        description = "Sphere radius",
        min = 0.0,
        default = 1.0,
        update = updateNode)

    init_samples : IntProperty(
        name = "Init Resolution",
        description = "A number of segments to subdivide the curve in",
        default = 50,
        min = 2,
        update = updateNode)

    accuracy : IntProperty(
        name = "Accuracy",
        description = "Accuracy level - number of exact digits after decimal points.",
        default = 4,
        min = 1,
        update = updateNode)

    use_nurbs : BoolProperty(
        name = "Use NURBS algorithm",
        description = "Use special algorithm for NURBS curves",
        default = True,
        update = updateNode)

    direction : EnumProperty(
        name = "Direction",
        default = '1',
        items = directions,
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['MaxResults'].hide_safe = not self.use_max_results
        updateNode(self, context)

    use_max_results : BoolProperty(
        name = "Set max. results",
        description = "Define maximum number of results",
        default = False,
        update = update_sockets)

    max_results : IntProperty(
        name = "Max Results",
        default = 1,
        min = 1,
        update = updateNode)

    max_subdivisions : IntProperty(
        name = "Max Subdivisions",
        default = 3,
        min = 1,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'use_nurbs')
        if not self.use_nurbs:
            layout.prop(self, 'init_samples')
        layout.prop(self, 'use_max_results')
        layout.prop(self, 'direction', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')
        layout.prop(self, 'max_subdivisions')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_proerty = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "MaxResults").prop_name = 'max_results'
        self.outputs.new('SvVerticesSocket', "Point")
        self.outputs.new('SvStringsSocket', "T")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        center_s = self.inputs['Center'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        max_results_s = self.inputs['MaxResults'].sv_get()

        input_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        flat_output = input_level < 2
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        center_s = ensure_nesting_level(center_s, 3)
        radius_s = ensure_nesting_level(radius_s, 2)
        max_results_s = ensure_nesting_level(max_results_s, 2)

        tolerance = 10**(-self.accuracy)

        t_out = []
        points_out = []

        for params in zip_long_repeat(curves_s, center_s, radius_s, max_results_s):
            new_ts = []
            new_points = []
            for curve, center, radius, max_results in zip_long_repeat(*params):
                if not self.use_max_results:
                    max_results = None

                if self.use_nurbs:
                    nurbs_curve = SvNurbsCurve.to_nurbs(curve)
                    if nurbs_curve is None:
                        raise UnsupportedCurveTypeException("Curve is not a NURBS")
                    ts = intersect_nurbs_curve_sphere(nurbs_curve, center, radius,
                                                      max_results = max_results,
                                                      direction = int(self.direction),
                                                      tolerance = tolerance,
                                                      max_subdivisions = self.max_subdivisions,
                                                      logger = self.sv_logger)
                else:
                    ts = intersect_curve_sphere(curve, center, radius,
                                                init_samples = self.init_samples,
                                                max_results = max_results,
                                                direction = int(self.direction),
                                                tolerance = tolerance,
                                                max_subdivisions = self.max_subdivisions,
                                                logger = self.sv_logger)
                if len(ts) > 0:
                    points = curve.evaluate_array(ts).tolist()
                else:
                    points = []
                ts = ts.tolist()
                new_ts.append(ts)
                new_points.append(points)
            if flat_output:
                t_out.extend(new_ts)
                points_out.extend(new_points)
            else:
                t_out.append(new_ts)
                points_out.append(new_points)

        self.outputs['Point'].sv_set(points_out)
        self.outputs['T'].sv_set(t_out)

def register():
    bpy.utils.register_class(SvCrossCurveSphereNode)

def unregister():
    bpy.utils.unregister_class(SvCrossCurveSphereNode)

