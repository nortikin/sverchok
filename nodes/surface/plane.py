
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level
from sverchok.utils.surface import SvExPlane

class SvExPlaneSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Plane
    Tooltip: Generate planar surface
    """
    bl_idname = 'SvExPlaneSurfaceNode'
    bl_label = 'Plane (Surface)'
    bl_icon = 'MESH_PLANE'

    modes = [
        ('3PT', "Three points", "Three points", 0),
        ('NORM', "Point and normal", "Point and normal", 1)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Point2'].hide_safe = self.mode != '3PT'
        self.inputs['Point3'].hide_safe = self.mode != '3PT'
        self.inputs['Normal'].hide_safe = self.mode != 'NORM'

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = '3PT',
        update = update_sockets)

    u_min : FloatProperty(
        name = "U Min",
        default = 0.0,
        update = updateNode)


    u_max : FloatProperty(
        name = "U Max",
        default = 1.0,
        update = updateNode)

    v_min : FloatProperty(
        name = "V Min",
        default = 0.0,
        update = updateNode)


    v_max : FloatProperty(
        name = "V Max",
        default = 1.0,
        update = updateNode)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Point1")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Point2")
        p.use_prop = True
        p.prop = (1.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Point3")
        p.use_prop = True
        p.prop = (0.0, 1.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Normal")
        p.use_prop = True
        p.prop = (0.0, 0.0, 1.0)
        self.inputs.new('SvStringsSocket', "UMin").prop_name = 'u_min'
        self.inputs.new('SvStringsSocket', "UMax").prop_name = 'u_max'
        self.inputs.new('SvStringsSocket', "VMin").prop_name = 'v_min'
        self.inputs.new('SvStringsSocket', "VMax").prop_name = 'v_max'
        self.outputs.new('SvExSurfaceSocket', "Surface")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point1_s = self.inputs['Point1'].sv_get()
        point2_s = self.inputs['Point2'].sv_get()
        point3_s = self.inputs['Point3'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()
        u_min_s = self.inputs['UMin'].sv_get()
        u_max_s = self.inputs['UMax'].sv_get()
        v_min_s = self.inputs['VMin'].sv_get()
        v_max_s = self.inputs['VMax'].sv_get()

        surfaces_out = []
        inputs = zip_long_repeat(point1_s, point2_s, point3_s, normal_s, u_min_s, u_max_s, v_min_s, v_max_s)
        for point1, point2, point3, normal, u_min, u_max, v_min, v_max in inputs:
            if isinstance(u_min, (list, tuple)):
                u_min = u_min[0]
            if isinstance(u_max, (list, tuple)):
                u_max = u_max[0]
            if isinstance(v_min, (list, tuple)):
                v_min = v_min[0]
            if isinstance(v_max, (list, tuple)):
                v_max = v_max[0]
            if get_data_nesting_level(normal) == 2:
                normal = normal[0]

            point1 = np.array(point1)
            if self.mode == '3PT':
                point2 = np.array(point2)
                point3 = np.array(point3)
                vec1 = point2 - point1
                vec2 = point3 - point1
            else:
                vec1 = np.array( Vector(normal).orthogonal() )
                vec2 = np.cross(np.array(normal), vec1)
                v1n = np.linalg.norm(vec1)
                v2n = np.linalg.norm(vec2)
                vec1, vec2 = vec1 / v1n, vec2 / v2n

            plane = SvExPlane(point1, vec1, vec2)
            plane.u_bounds = (u_min, u_max)
            plane.v_bounds = (v_min, v_max)
            surfaces_out.append(plane)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvExPlaneSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExPlaneSurfaceNode)

