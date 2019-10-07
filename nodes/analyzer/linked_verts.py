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
from bpy.props import IntProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat


def all_connexions(edges, item_n, distance, connexions_dict, distance_max):
    '''iterative calculation of connexions'''
    connexions_list = []
    edges_out = []
    for e in edges:
        edge_in = True
        for s in e:
            if s in item_n:
                connexions_list += e
                edge_in = False
                break
        if edge_in:
            edges_out.append(e)
    connexions_list_clean = list(set(connexions_list) - set(item_n))
    connexions_dict[distance_max - distance + 1] = connexions_list_clean

    if distance > 1:
        connexions_list_clean = all_connexions(edges_out, connexions_list_clean, distance - 1, connexions_dict, distance_max)

    return connexions_list_clean


def calc_connexions(meshes, gates, result):
    '''calculate connexions by creating sets'''

    for vertices, edges, item_n, distance in zip(*meshes):
        if gates[3]:
            item_n = [i for i, m in enumerate(item_n) if m]
            print(item_n)
        connexions_dict = {}
        connexions_dict[0] = item_n
        d_max = max(distance)
        _ = all_connexions(edges, item_n, d_max, connexions_dict, d_max)

        out_index = []
        for d in distance:
            if d in connexions_dict:
                out_index += connexions_dict[d]

        out_index = list(set(out_index))

        result[0].append(out_index)

        if gates[1]:
            connected_v = []
            for i in out_index:
                connected_v.append(vertices[i])
            result[1].append(connected_v)

        if gates[2]:
            mask = [True if i in out_index else False for i in range(len(vertices))]
            result[2].append(mask)

    return result


class SvLinkedVertsNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Measure deformation
    Tooltip: Deformation between to states, edge elong a area variation
    '''
    bl_idname = 'SvLinkedVertsNode'
    bl_label = 'Linked Verts'
    bl_icon = 'MOD_SIMPLEDEFORM'

    selection_type_Items = [
        ("Index", "Index", "Input selected Indexes",       0),
        ("Mask",  "Mask",  "Input selection though mask",  1)]

    item = IntProperty(
        name='Selection', description='Selected Items (Index or Mask)',
        default=0, update=updateNode)
    distance = IntProperty(
        name='distance', description='Include subject vertex',
        default=1, min=0, update=updateNode)
    selection_type = EnumProperty(
        name='Selection Mode', description='Input selection type',
        items=selection_type_Items,
        default="Index", update=updateNode)

    def draw_buttons(self, context, layout):
        '''draw buttons on the Node'''
        layout.prop(self, "selection_type", expand=False)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', "Verts")
        sinw('StringsSocket', "Edges")
        sinw('StringsSocket', "Item").prop_name = 'item'
        sinw('StringsSocket', "Distance").prop_name = 'distance'

        sonw('StringsSocket', "Verts Id")
        sonw('VerticesSocket', "Verts")
        sonw('StringsSocket', "Mask")

    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        vertices_s = si['Verts'].sv_get(default=[[]])
        edges_in = si['Edges'].sv_get(default=[[]])
        item_n = si['Item'].sv_get(default=[[]])
        distance = si['Distance'].sv_get(default=[[]])

        return match_long_repeat([vertices_s, edges_in, item_n, distance])

    def ready(self):
        '''check if there are the needed links'''
        si = self.inputs
        so = self.outputs
        ready = any(s.is_linked for s in so)
        ready = ready and si[1].is_linked
        return ready

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        si = self.inputs
        if not self.ready():
            return

        result = [[], [], [], []]
        gates = []
        gates.append(so['Verts Id'].is_linked)
        gates.append(so['Verts'].is_linked)
        gates.append(so['Mask'].is_linked)
        gates.append(self.selection_type == "Mask")

        meshes = self.get_data()

        result = calc_connexions(meshes, gates, result)

        if gates[0]:
            so['Verts Id'].sv_set(result[0])
        if gates[1]:
            so['Verts'].sv_set(result[1])
        if gates[2]:
            so['Mask'].sv_set(result[2])


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvLinkedVertsNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvLinkedVertsNode)
