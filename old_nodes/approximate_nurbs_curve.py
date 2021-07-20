
import bpy
from bpy.props import BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.curve.nurbs import SvGeomdlCurve
from sverchok.dependencies import geomdl
from sverchok.utils.dummy_nodes import add_dummy

if geomdl is None:
    add_dummy('SvExApproxNurbsCurveNode', "Approximate NURBS Curve", 'geomdl')
else:
    from geomdl import fitting
    
    class SvExApproxNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: NURBS Curve
        Tooltip: Approximate NURBS Curve
        """
        bl_idname = 'SvExApproxNurbsCurveNode'
        bl_label = 'Approximate NURBS Curve'
        bl_icon = 'CURVE_NCURVE'

        replacement_nodes = [('SvApproxNurbsCurveMk2Node', None, None)]

        degree : IntProperty(
                name = "Degree",
                min = 2, max = 6,
                default = 3,
                update = updateNode)

        centripetal : BoolProperty(
                name = "Centripetal",
                default = False,
                update = updateNode)

        def update_sockets(self, context):
            self.inputs['PointsCnt'].hide_safe = not self.has_points_cnt
            updateNode(self, context)

        has_points_cnt : BoolProperty(
                name = "Specify points count",
                default = False,
                update = update_sockets)

        points_cnt : IntProperty(
                name = "Points count",
                min = 3, default = 5,
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'centripetal', toggle=True)
            layout.prop(self, 'has_points_cnt', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
            self.inputs.new('SvStringsSocket', "PointsCnt").prop_name = 'points_cnt'
            self.outputs.new('SvCurveSocket', "Curve")
            self.outputs.new('SvVerticesSocket', "ControlPoints")
            self.outputs.new('SvStringsSocket', "Knots")
            self.update_sockets(context)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            degree_s = self.inputs['Degree'].sv_get()
            points_cnt_s = self.inputs['PointsCnt'].sv_get()

            input_level = get_data_nesting_level(vertices_s)
            vertices_s = ensure_nesting_level(vertices_s, 4)
            degree_s = ensure_nesting_level(degree_s, 2)
            points_cnt_s = ensure_nesting_level(points_cnt_s, 2)

            nested_output = input_level > 3

            curves_out = []
            points_out = []
            knots_out = []
            for params in zip_long_repeat(vertices_s, degree_s, points_cnt_s):
                new_curves = []
                new_points = []
                new_knots = []
                for vertices, degree, points_cnt in zip_long_repeat(*params):

                    kwargs = dict(centripetal = self.centripetal)
                    if self.has_points_cnt:
                        kwargs['ctrlpts_size'] = points_cnt

                    curve = fitting.approximate_curve(vertices, degree, **kwargs)

                    new_points.append(curve.ctrlpts)
                    new_knots.append(curve.knotvector)

                    curve = SvGeomdlCurve(curve)
                    new_curves.append(curve)

                if nested_output:
                    curves_out.append(new_curves)
                    points_out.append(new_points)
                    knots_out.append(new_knots)
                else:
                    curves_out.extend(new_curves)
                    points_out.extend(new_points)
                    knots_out.extend(new_knots)

            self.outputs['Curve'].sv_set(curves_out)
            self.outputs['ControlPoints'].sv_set(points_out)
            self.outputs['Knots'].sv_set(knots_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExApproxNurbsCurveNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExApproxNurbsCurveNode)

