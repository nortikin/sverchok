
import numpy as np
from math import pi

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.geom import circle_by_three_points
from sverchok.utils.curve import SvCircle

class SvArc3ptCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Arc 3pt
    Tooltip: Generate an arc via three points
    """
    bl_idname = 'SvArc3ptCurveNode'
    bl_label = 'Arc 3pt (Curve)'
    bl_icon = 'SPHERECURVE'

    join : BoolProperty(
            name = "Join",
            description = "Output single flat list of curves",
            default = True,
            update = updateNode)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Point1")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Point2")
        p.use_prop = True
        p.default_property = (1.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Point3")
        p.use_prop = True
        p.default_property = (0.0, 1.0, 0.0)
        self.outputs.new('SvCurveSocket', "Arc")
        self.outputs.new('SvCurveSocket', "Circle")
        self.outputs.new('SvMatrixSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")
        self.outputs.new('SvStringsSocket', "Angle")

    def draw_buttons(self, context, layout):
        layout.prop(self, "join")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point1_s = self.inputs['Point1'].sv_get()
        point2_s = self.inputs['Point2'].sv_get()
        point3_s = self.inputs['Point3'].sv_get()

        point1_s = ensure_nesting_level(point1_s, 3)
        point2_s = ensure_nesting_level(point2_s, 3)
        point3_s = ensure_nesting_level(point3_s, 3)

        arcs_out = []
        circles_out = []
        centers_out = []
        radius_out = []
        angle_out = []
        for point1s, point2s, point3s in zip_long_repeat(point1_s, point2_s, point3_s):
            arcs_new = []
            circles_new = []
            centers_new = []
            radius_new = []
            angle_new = []
            for point1, point2, point3 in zip_long_repeat(point1s, point2s, point3s):
                circle_data = circle_by_three_points(point1, point2, point3)
                if circle_data is None:
                    raise Exception("Can't build a circle by these points: {}, {}, {}".format(point1, point2, point3))
                matrix = circle_data.get_matrix()
                circle = SvCircle(matrix, circle_data.radius)
#                 arc = SvCircle(radius=circle_data.radius,
#                                 center=np.array(circle_data.center),
#                                 normal=np.array(circle_data.normal),
#                                 vectorx = np.array(circle_data.point1) - np.array(circle_data.center))
                #arc.u_bounds = (0.0, circle_data.arc_angle)
                arc = SvCircle.from_equation(circle_data)
                arcs_new.append(arc)
                circles_new.append(circle)
                centers_new.append(matrix)
                radius_new.append(circle_data.radius)
                angle_new.append(circle_data.arc_angle)

            if self.join:
                arcs_out.extend(arcs_new)
                circles_out.extend(circles_new)
                centers_out.extend(centers_new)
                radius_out.extend(radius_new)
                angle_out.extend(angle_new)
            else:
                arcs_out.append(arcs_new)
                circles_out.append(circles_new)
                centers_out.append(centers_new)
                radius_out.append(radius_new)
                angle_out.append(angle_new)

        self.outputs['Arc'].sv_set(arcs_out)
        self.outputs['Circle'].sv_set(circles_out)
        self.outputs['Center'].sv_set(centers_out)
        self.outputs['Radius'].sv_set(radius_out)
        self.outputs['Angle'].sv_set(angle_out)

def register():
    bpy.utils.register_class(SvArc3ptCurveNode)

def unregister():
    bpy.utils.unregister_class(SvArc3ptCurveNode)

