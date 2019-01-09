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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
import numpy as np


def edges_aux(vertices):
    '''create auxiliary edges array '''
    v_len = [len(v) for v in vertices]
    v_len_max = max(v_len)
    np_in = np.arange(v_len_max - 1)
    np_edges = np.array([np_in, np_in + 1]).T

    return [np_edges]


def edges_length(meshes, gates, result):
    '''calculate edges length '''

    for vertices, edges in zip(*meshes):
        np_verts = np.array(vertices)
        print(np_verts.shape)
        if type(edges[0]) in (list, tuple):
            np_edges = np.array(edges)
        else:
            np_edges = edges[:len(vertices)-1, :]

        vect = np_verts[np_edges[:, 0], :] - np_verts[np_edges[:, 1], :]
        length = np.linalg.norm(vect, axis=1)
        if not gates[1]:
            length = np.sum(length)[np.newaxis]

        result.append(length if gates[0] else length.tolist())

    return result


class SvLengthNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Path / Edges length
    Tooltip: Deformation between to states, edge elong a area variation
    '''
    bl_idname = 'SvLengthNode'
    bl_label = 'Length'
    bl_icon = 'MOD_SIMPLEDEFORM'

    output_numpy = BoolProperty(
        name='Output NumPy', description='output NumPy arrays',
        default=False, update=updateNode)

    sum_lengths = BoolProperty(
        name='by Edge', description='individual lengths or the sum of them',
        default=True, update=updateNode)

    def draw_buttons(self, context, layout):
        '''draw buttons on the Node'''
        layout.prop(self, "sum_lengths", toggle=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, "output_numpy", toggle=False)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', "Verts")
        sinw('StringsSocket', "Edges")

        sonw('StringsSocket', "Length")

    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        vertices = si['Verts'].sv_get(default=[[]])
        edges_in = si['Edges'].sv_get(default=[[]])
        if len(edges_in[0]) < 1:
            edges_in = edges_aux(vertices)

        return match_long_repeat([vertices, edges_in])

    def process(self):
        '''main node function called every update'''
        si = self.inputs
        so = self.outputs
        if not (so[0].is_linked and si[0].is_linked):
            return

        result = []
        gates = []
        gates.append(self.output_numpy)
        gates.append(self.sum_lengths)
        meshes = self.get_data()

        result = edges_length(meshes, gates, result)

        so['Length'].sv_set(result)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvLengthNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvLengthNode)
