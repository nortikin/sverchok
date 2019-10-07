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
from sverchok.data_structure import updateNode, match_long_repeat, get_edge_list
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


class SvPathLengthNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Path / Edges length
    Tooltip: Measures the length of a path or the length of its segments
    '''
    bl_idname = 'SvPathLengthNode'
    bl_label = 'Path Length'
    sv_icon = 'SV_PATH_LENGTH'

    output_numpy = BoolProperty(
        name='Output NumPy', description='output NumPy arrays',
        default=False, update=updateNode)

    segment = BoolProperty(
        name='Segment', description='Get segments length or the sum of them',
        default=True, update=updateNode)

    def draw_buttons(self, context, layout):
        '''draw buttons on the Node'''
        layout.prop(self, "segment", toggle=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, "output_numpy", toggle=False)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', "Vertices")
        sinw('StringsSocket', "Edges")

        sonw('StringsSocket', "Length")

    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs

        vertices = si['Vertices'].sv_get()

        if si['Edges'].is_linked:
            edges_in = si['Edges'].sv_get()
        else:
            edges_in = edges_aux(vertices)

        return match_long_repeat([vertices, edges_in])


    def process(self):
        '''main node function called every update'''
        si = self.inputs
        so = self.outputs
        if not (so['Length'].is_linked):
            return

        result = []
        gates = []
        gates.append(self.output_numpy)
        gates.append(self.segment)
        meshes = self.get_data()

        result = edges_length(meshes, gates, result)

        so['Length'].sv_set(result)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvPathLengthNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvPathLengthNode)
