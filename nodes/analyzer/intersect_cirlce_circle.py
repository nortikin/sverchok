# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
from bpy.props import FloatProperty, FloatVectorProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from mathutils import Vector as V
from mathutils.geometry import intersect_sphere_sphere_2d, normal, barycentric_transform


def compute_intersect_circle_circle(params, result, gates):
    '''Compute two circles intersection(s)
    Result has to be [[],[],[]] to host the solutions
    Gates are as follow:
    0: Is there a intersection?
    1: First Intersecction
    2: Second intersection
    3: The working plane is defined by its normal (True) or by a third point (False)'''
    center_a, radius_a, center_b, radius_b, plane_pt, plane_normal = params
    local_result = []
    sphere_loc_a = V(center_a)
    sphere_loc_b = V(center_b)
    if gates[3]:
        norm = V(plane_normal).normalized()
    else:
        v_in_plane = V(plane_pt)
        norm = normal([sphere_loc_a, sphere_loc_b, v_in_plane])
    if norm.length == 0:
        if gates[3]:
            print("Circle Intersection Error: the Normal can't be (0,0,0)")
        else:
            print("Circle Intersection Error: the point in plane is aligned with origins")

    is_2d = norm.x == 0 and norm.y == 0

    if is_2d and False:
        z_coord = sphere_loc_a.z
        inter_p = intersect_sphere_sphere_2d(sphere_loc_a.to_2d(), radius_a, sphere_loc_b.to_2d(), radius_b)
        if inter_p[0]:
            intersect = True
            vec1 = list(inter_p[1]) + [z_coord]
            vec0 = list(inter_p[0]) + [z_coord]
            local_result = [intersect, vec0, vec1]

    else:
        dist = (sphere_loc_a - sphere_loc_b).length
        new_a = V([0, 0, 0])
        new_b = V([dist, 0, 0])
        inter_p = intersect_sphere_sphere_2d(new_a.to_2d(), radius_a, new_b.to_2d(), radius_b)
        if inter_p[0]:
            intersect_num = True
            trird_point = sphere_loc_a + norm
            new_c = V([0, 0, 1])
            vec0 = barycentric_transform(inter_p[0].to_3d(), new_a, new_b, new_c, sphere_loc_a, sphere_loc_b, trird_point)
            vec1 = barycentric_transform(inter_p[1].to_3d(), new_a, new_b, new_c, sphere_loc_a, sphere_loc_b, trird_point)
            local_result = [intersect_num, list(vec0), list(vec1)]

    if not local_result:
        direc = (sphere_loc_b - sphere_loc_a).normalized()
        intersect_num = False
        vec0 = sphere_loc_a + direc * radius_a
        vec1 = sphere_loc_b - direc * radius_b
        local_result = [intersect_num, list(vec0), list(vec1)]

    for i, res in enumerate(result):
        if gates[i]:
            res.append(local_result[i])


class SvIntersectCircleCircleNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Intersect Circle Circle
    Tooltip: Intersect between to co-planar Circles.
    '''
    bl_idname = 'SvIntersectCircleCircleNode'
    bl_label = 'Circle Intersection'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CIRCLE_INTERSECTION'

    radius_A: FloatProperty(
        name="Radius", description='intersection tolerance',
        default=1, min=0.0,
        update=updateNode)

    sphere_center_A: FloatVectorProperty(
        name='Center', description='Origin of circle A',
        size=3, default=(0, 0, 0),
        update=updateNode)

    radius_B: FloatProperty(
        name="Radius", description='intersection tolerance',
        default=1, min=0.0,
        update=updateNode)

    sphere_center_B: FloatVectorProperty(
        name='Center', description='Origin of circle B',
        size=3, default=(1, 0, 0),
        update=updateNode)

    v_in_plane: FloatVectorProperty(
        name='Pt. in plane', description='Point on the plane',
        size=3, default=(0, 0, 0),
        update=updateNode)

    plane_normal: FloatVectorProperty(
        name='Normal', description='Normal of the plane',
        size=3, default=(0, 0, 1),
        update=updateNode)

    modes = [
        ("Point", "Pt in plane", "point on intersection plane", 0),
        ("Normal", "Normal", "Normal of intersection plane", 1)
        ]

    def change_mode(self, context):
        si = self.inputs
        if self.define_plane == 'Normal':
            si['Pt. in plane'].hide_safe = True
            if si['Normal'].hide_safe:
                si['Normal'].hide_safe = False
        else:
            si['Normal'].hide_safe = True
            if si['Pt. in plane'].hide_safe:
                si['Pt. in plane'].hide_safe = False
        updateNode(self, context)


    define_plane: EnumProperty(
        name='Plane defined by', description='How to define intersection plane',
        items=modes, default='Point',
        update=change_mode)

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level (Level 1)",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level (Level 2)",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'define_plane', expand=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, 'define_plane', expand=False)
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('SvVerticesSocket', 'Center A').prop_name = 'sphere_center_A'
        sinw('SvStringsSocket', 'Radius A').prop_name = 'radius_A'
        sinw('SvVerticesSocket', 'Center B').prop_name = 'sphere_center_B'
        sinw('SvStringsSocket', 'Radius B').prop_name = 'radius_B'
        sinw('SvVerticesSocket', 'Pt. in plane').prop_name = 'v_in_plane'
        sinw('SvVerticesSocket', 'Normal').prop_name = 'plane_normal'
        self.inputs['Normal'].hide_safe = True
        sonw('SvStringsSocket', 'Intersect Num')
        sonw('SvVerticesSocket', 'Intersection A')
        sonw('SvVerticesSocket', 'Intersection B')


    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        return list_match_func[self.list_match_global]([s.sv_get(default=[[]]) for s in si])

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        if not any(s.is_linked for s in so):
            return

        result = [[], [], []]
        gates = []
        gates.append(so['Intersect Num'].is_linked)
        gates.append(so['Intersection A'].is_linked)
        gates.append(so['Intersection B'].is_linked)
        gates.append(self.define_plane == 'Normal')

        group = self.get_data()

        for subgroup in zip(*group):
            subgroup = list_match_func[self.list_match_local](subgroup)
            subresult = [[], [], []]
            for param in zip(*subgroup):
                compute_intersect_circle_circle(param, subresult, gates)
            for i, res in enumerate(result):
                if gates[i]:
                    res.append(subresult[i])

        for i, res in enumerate(result):
            if gates[i]:
                so[i].sv_set(res)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvIntersectCircleCircleNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvIntersectCircleCircleNode)
