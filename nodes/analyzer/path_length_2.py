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
    np_edges = np.add.outer(np.arange(v_len_max - 1), [0, 1])

    return [np_edges]

def edges_length(meshes, need_total=False, need_cumsum=False, need_cumsum1=False, as_numpy=False):
    '''calculate edges length '''

    lengths_out = []
    cumsum_out = []
    cumsum_1_out = []
    total_lengths_out = []

    for vertices, edges in zip(*meshes):
        np_verts = np.array(vertices)
        if type(edges[0]) in (list, tuple):
            np_edges = np.array(edges)
        else:
            np_edges = edges[:len(vertices)-1, :]

        vect = np_verts[np_edges[:, 0], :] - np_verts[np_edges[:, 1], :]
        lengths = np.linalg.norm(vect, axis=1)

        if need_cumsum or need_cumsum1 or need_total:
            total_length = np.sum(lengths)[np.newaxis]
        else:
            total_length = None

        if need_cumsum or need_cumsum1:
            cumsum = np.cumsum(np.insert(lengths, 0, 0))
        else:
            cumsum = None

        if need_cumsum1 and total_length is not None and cumsum is not None:
            cumsum_1 = cumsum / total_length
        else:
            cumsum_1 = None

        if not as_numpy:
            lengths = lengths.tolist()
            if cumsum is not None:
                cumsum = cumsum.tolist()
            if cumsum_1 is not None:
                cumsum_1 = cumsum_1.tolist()
            if total_length is not None:
                total_length = total_length.tolist()

        total_lengths_out.append(total_length)
        lengths_out.append(lengths)
        cumsum_out.append(cumsum)
        cumsum_1_out.append(cumsum_1)

    return lengths_out, cumsum_out, cumsum_1_out, total_lengths_out

class SvPathLengthMk2Node(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Path / Edges length
    Tooltip: Measures the length of a path or the length of its segments
    '''
    bl_idname = 'SvPathLengthMk2Node'
    bl_label = 'Path Length'
    sv_icon = 'SV_PATH_LENGTH'

    output_numpy : BoolProperty(
        name='Output NumPy', description='output NumPy arrays',
        default=False, update=updateNode)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "output_numpy", toggle=False)

    def sv_init(self, context):
        '''create sockets'''
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")

        self.outputs.new('SvStringsSocket', "SegmentLength")
        self.outputs.new('SvStringsSocket', "TotalLength")
        self.outputs.new('SvStringsSocket', "CumulativeSum")
        self.outputs.new('SvStringsSocket', "CumulativeSum1")

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
        if not any(socket.is_linked for socket in self.outputs):
            return

        meshes = self.get_data()

        lengths_out, cumsum_out, cumsum_1_out, total_lengths_out = edges_length(meshes,
                        need_total = self.outputs['TotalLength'].is_linked,
                        need_cumsum = self.outputs['CumulativeSum'].is_linked,
                        need_cumsum1 = self.outputs['CumulativeSum1'].is_linked,
                        as_numpy=self.output_numpy)

        self.outputs['SegmentLength'].sv_set(lengths_out)
        self.outputs['TotalLength'].sv_set(total_lengths_out)
        self.outputs['CumulativeSum'].sv_set(cumsum_out)
        self.outputs['CumulativeSum1'].sv_set(cumsum_1_out)

    def migrate_links_from(self, old_node, operator):
        if old_node.bl_idname != 'SvPathLengthNode':
            return
        tree = self.id_data

        old_in_links = [link for link in tree.links if link.to_node == old_node]
        old_out_links = [link for link in tree.links if link.from_node == old_node]

        for old_link in old_in_links:
            new_target_socket_name = operator.get_new_input_name(old_link.to_socket.name)
            if new_target_socket_name in self.inputs:
                new_target_socket = self.inputs[new_target_socket_name]
                new_link = tree.links.new(old_link.from_socket, new_target_socket)
            else:
                self.debug("New node %s has no input named %s, skipping", self.name, new_target_socket_name)
            tree.links.remove(old_link)

        for old_link in old_out_links:
            if old_node.segment:
                new_source_socket_name = 'SegmentLength'
            else:
                new_source_socket_name = 'TotalLength'

            # We have to remove old link before creating new one
            # Blender would not allow two links pointing to the same target socket
            old_target_socket = old_link.to_socket
            tree.links.remove(old_link)
            if new_source_socket_name in self.outputs:
                new_source_socket = self.outputs[new_source_socket_name]
                new_link = tree.links.new(new_source_socket, old_target_socket)
            else:
                self.debug("New node %s has no output named %s, skipping", self.name, new_source_socket_name)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvPathLengthMk2Node)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvPathLengthMk2Node)

