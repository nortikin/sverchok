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
from mathutils.geometry import intersect_plane_plane


def compute_intersect_plane_plane(params, result, gates):

    plane_co_a, plane_norm_a, plane_co_b, plane_norm_b = params
    
    local_result = []
    plane_co_a_V = V(plane_co_a)
    plane_norm_a_V = V(plane_norm_a)
    plane_co_b_V = V(plane_co_b)
    plane_norm_b_V = V(plane_norm_b)

    inter_p = intersect_plane_plane(plane_co_a_V, plane_norm_a_V, plane_co_b_V, plane_norm_b_V)

    if inter_p[0]:
        intersect = True
        line_origin = list(inter_p[0])
        line_direction = list(inter_p[1])
    else:
        print("Plane Intersection Warning:  Planes are parallel")
        intersect = False
        line_origin = list(plane_co_a_V)
        line_direction = list(plane_norm_a_V)
        
    local_result =[intersect, line_origin, line_direction]

    for i, r in enumerate(result):
        if gates[i]:
            r.append(local_result[i])


class SvIntersectPlanePlaneNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Line from Intersection
    Tooltip: Intersect two planes and get the resulting line.
    '''
    bl_idname = 'SvIntersectPlanePlaneNode'
    bl_label = 'Plane Intersection'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_PLANE_INTERSECTION_ICON'

    plane_loc_a = FloatVectorProperty(
        name="Location A", description='First Plane point',
        size=3, default=(0, 0, 0),
        update=updateNode)

    plane_normal_a = FloatVectorProperty(
        name='Normal A', description='First Plane Normal',
        size=3, default=(0, 0, 1),
        update=updateNode)

    plane_loc_b = FloatVectorProperty(
        name="Location B", description='Second Plane point',
        size=3, default=(0, 0, 0),
        update=updateNode)

    plane_normal_b = FloatVectorProperty(
        name='Normal B', description='Second Plane Normal',
        size=3, default=(0, 1, 0),
        update=updateNode)

    list_match_global = EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level (Level 1)",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match_local = EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level (Level 2)",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', 'Location A').prop_name = 'plane_loc_a'
        sinw('VerticesSocket', 'Normal A').prop_name = 'plane_normal_a'
        sinw('VerticesSocket', 'Location B').prop_name = 'plane_loc_b'
        sinw('VerticesSocket', 'Normal B').prop_name = 'plane_normal_b'

        sonw('StringsSocket', 'Intersect')
        sonw('VerticesSocket', 'Origin')
        sonw('VerticesSocket', 'Direction')

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        return list_match_func[self.list_match_global]([s.sv_get(default=[[]]) for s in si])
        

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        si = self.inputs
        if not (any(s.is_linked for s in so)):
            return

        result = [[] for socket in so]
        gates = [socket.is_linked for socket in so]

        group = self.get_data()

        for subgroup in zip(*group):
            subgroup = list_match_func[self.list_match_local](subgroup)
            subresult = [[], [], []]
            for p in zip(*subgroup):
                compute_intersect_plane_plane(p, subresult, gates)
            for i, r in enumerate(result):
                if gates[i]:
                    r.append(subresult[i])

        for i, r in enumerate(result):
            if gates[i]:
                so[i].sv_set(result[i])


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvIntersectPlanePlaneNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvIntersectPlanePlaneNode)
