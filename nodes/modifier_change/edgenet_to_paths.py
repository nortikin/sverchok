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

from typing import NamedTuple
import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

class Limit(NamedTuple):
    v_index: int
    edge_side: int
    edge_index: int

class EdgesNet(NamedTuple):
    starts: list
    ends: list
    indexes: list

    def pop(self, idx):
        self.starts.pop(idx)
        self.ends.pop(idx)
        self.indexes.pop(idx)


def find_limits(verts_in, edges_in):
    v_count = [[0, 0, 0] for i in range(len(verts_in))]
    limits = []

    for i, e in enumerate(edges_in):
        v_count[e[0]][0] += 1
        v_count[e[0]][1] = 0
        v_count[e[0]][2] = i
        v_count[e[1]][0] += 1
        v_count[e[1]][1] = 1
        v_count[e[1]][2] = i
    for i, v in enumerate(v_count):
        if v[0] == 1:
            limits.append(Limit(i, v[1], v[2]))
    return limits


def edgenet_to_paths(verts_in, edges_in, close_loops):

    # prepare data and arrays
    verts_out_s = [[]]
    edges_out_s = [[]]
    index_vs_s = [[]]
    index_eds_s = [[]]
    closed = []
    edges_len = len(edges_in)
    edges_index = [j for j in range(edges_len)]
    edges0 = [j[0] for j in edges_in]
    edges1 = [j[1] for j in edges_in]
    edges_net = EdgesNet(edges0, edges1, edges_index)

    # start point
    limiting = False

    limits = find_limits(verts_in, edges_in)
    limiting = len(limits) > 0
    if limiting:
        v_index = limits[0].v_index
        ed_index = limits[0].edge_index
        or_side = limits[0].edge_side
        limits.pop(0)
    else:
        v_index = edges_in[0][0]
        ed_index = 0
        or_side = 0  # direction of the edge

    edge_start = edges_in[ed_index]
    verts_out_s[0].append(verts_in[v_index])
    index_vs_s[0].append(edge_start[or_side])

    edges_net.pop(ed_index)
    for j in range(edges_len):
        edges_out = edges_out_s[-1]
        verts_out = verts_out_s[-1]
        index_vs = index_vs_s[-1]
        index_eds = index_eds_s[-1]

        index_eds.append(ed_index)
        actual_edge = edges_in[ed_index]

        if or_side == 1:
            actual_edge = [actual_edge[1], actual_edge[0]]

        index_vs.append(actual_edge[1])
        verts_out.append(verts_in[actual_edge[1]])
        len_v = len(verts_out)
        edges_out.append([len_v-2, len_v-1])
        # find next edge
        ed_index_old = ed_index
        v_index = actual_edge[1]

        try:
            k = edges_net.starts.index(v_index)
            ed_index = edges_net.indexes[k]
            or_side = 0
            edges_net.pop(k)

        except ValueError:
            try:
                k = edges_net.ends.index(v_index)
                ed_index = edges_net.indexes[k]
                or_side = 1
                edges_net.pop(k)

            except ValueError:
                if close_loops and verts_out[0] == verts_out[-1]:
                    verts_out.pop(-1)
                    edges_out[-1][1] = 0
                    closed.append(True)
                else:
                    closed.append(False)
                for i, lim in enumerate(limits):
                    if lim[0] == v_index:
                        limits.pop(i)
                        break

        # if not found take next point or next limit
        if ed_index == ed_index_old and len(edges_net.starts) > 0:
            edges_out_s.append([])
            verts_out_s.append([])
            index_vs_s.append([])
            index_eds_s.append([])
            if limits:
                lim = limits[0]
                ed_index = lim.edge_index
                or_side = lim.edge_side
                v_index = lim.v_index
                try:
                    actual_index = edges_net.starts.index(v_index)
                except ValueError:
                    actual_index = edges_net.ends.index(v_index)

                edges_net.pop(actual_index)
                limits.pop(0)
            else:
                ed_index = edges_net.indexes[0]
                or_side = 0
                edges_net.pop(0)

            edge_start = edges_in[ed_index]
            verts_out_s[-1].append(verts_in[edge_start[or_side]])
            index_vs_s[-1].append(edge_start[or_side])

    return verts_out_s, edges_out_s, index_vs_s, index_eds_s, closed

class SvEdgenetToPathsNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Mesh to polylines
    Tooltip: Sort Vertices and split different paths
    '''
    bl_idname = 'SvEdgenetToPathsNode'
    bl_label = 'Edgenet to Paths'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SEPARATE_LOOSE_PARTS'

    join: bpy.props.BoolProperty(
        name="Join",
        description="If checked, generate one flat list of paths for all input meshes; otherwise, generate separate list of loose parts for each input mesh",
        default=True,
        update=updateNode)
    def update_sockets(self, context):
        self.outputs['Cyclic'].hide_safe = not self.cycle
        updateNode(self, context)
    cycle: bpy.props.BoolProperty(
        name="Close Loops",
        description="When checked if the first and last vertices are identical they will merge; otherwise, this wont be checked",
        default=True,
        update=update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'cycle')
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'join')
        layout.prop(self, 'cycle')
    def rclick_menu(self, context, layout):
        self.draw_buttons_ext(context, layout)
    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Vert Indexes')
        self.outputs.new('SvStringsSocket', 'Edge Indexes')
        self.outputs.new('SvStringsSocket', 'Cyclic')


    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        verts = self.inputs[0].sv_get(deepcopy=False)
        edges = self.inputs[1].sv_get(deepcopy=False)
        verts_out = []
        edge_out = []
        v_index_out = []
        e_index_out = []
        cyclic_out = []
        if self.join:
            new_verts = verts_out.extend
            new_edges = edge_out.extend
            new_v_index = v_index_out.extend
            new_e_index = e_index_out.extend
            new_cyclic = cyclic_out.extend
        else:
            new_verts = verts_out.append
            new_edges = edge_out.append
            new_v_index = v_index_out.append
            new_e_index = e_index_out.append
            new_cyclic = cyclic_out.append

        for vecs, edgs in zip_long_repeat(verts, edges):
            verts, edges, v_index, ed_index, cyclic = edgenet_to_paths(vecs, edgs, self.cycle)
            new_verts(verts)
            new_edges(edges)
            new_v_index(v_index)
            new_e_index(ed_index)
            new_cyclic(cyclic)

        self.outputs[0].sv_set(verts_out)
        self.outputs[1].sv_set(edge_out)
        self.outputs['Vert Indexes'].sv_set(v_index_out)
        self.outputs['Edge Indexes'].sv_set(e_index_out)
        self.outputs['Cyclic'].sv_set([cyclic_out] if self.join else cyclic_out)


def register():
    bpy.utils.register_class(SvEdgenetToPathsNode)


def unregister():
    bpy.utils.unregister_class(SvEdgenetToPathsNode)
