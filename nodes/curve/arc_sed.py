
import numpy as np
from math import pi

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.geom import circle_by_start_end_tangent
from sverchok.utils.curve import SvCircle

class SvArcSedCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Arc Start, End, Tangent
    Tooltip: Generate an arc from Start point, End point and Tangent vector
    """
    bl_idname = 'SvArcSedCurveNode'
    bl_label = 'Arc SED'
    bl_icon = 'SPHERECURVE'

    join : BoolProperty(
            name = "Join",
            description = "Output single flat list of curves",
            default = True,
            update = updateNode)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Start")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "End")
        p.use_prop = True
        p.prop = (1.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Tangent")
        p.use_prop = True
        p.prop = (0.0, 1.0, 0.0)
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

        start_s = self.inputs['Start'].sv_get()
        end_s = self.inputs['End'].sv_get()
        tangent_s = self.inputs['Tangent'].sv_get()

        start_s = ensure_nesting_level(start_s, 3)
        end_s = ensure_nesting_level(end_s, 3)
        tangent_s = ensure_nesting_level(tangent_s, 3)

        arcs_out = []
        circles_out = []
        centers_out = []
        radius_out = []
        angle_out = []
        for starts, ends, tangents in zip_long_repeat(start_s, end_s, tangent_s):
            arcs_new = []
            circles_new = []
            centers_new = []
            radius_new = []
            angle_new = []
            for start, end, tangent in zip_long_repeat(starts, ends, tangents):
                circle_data = circle_by_start_end_tangent(start, end, tangent)
                if circle_data is None:
                    raise Exception("Can't build a circle")
                matrix = circle_data.get_matrix()
                circle = SvCircle(matrix, circle_data.radius)
                arc = SvCircle(matrix, circle_data.radius)
                arc.u_bounds = (0.0, circle_data.arc_angle)
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
    bpy.utils.register_class(SvArcSedCurveNode)

def unregister():
    bpy.utils.unregister_class(SvArcSedCurveNode)

