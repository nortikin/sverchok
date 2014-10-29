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
from bpy.props import EnumProperty, StringProperty
import mathutils
from mathutils import Vector

from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import SvSetSocketAnyType, SvGetSocketAnyType


# documentation/blender_python_api_2_70_release/mathutils.kdtree.html
class SvKDTreeNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvKDTreeNode'
    bl_label = 'Kdtree search'
    bl_icon = 'OUTLINER_OB_EMPTY'

    current_mode = StringProperty(default="FIND")

    def mode_change(self, context):

        # just because click doesn't mean we need to change mode
        mode = self.mode
        if mode == self.current_mode:
            return

        inputs = self.inputs
        outputs = self.outputs

        socket_map = {
            'Verts': 'VerticesSocket',
            'Check Verts': 'VerticesSocket',
            'n nearest': 'StringsSocket',
            'radius': 'StringsSocket',
            'proxima .co': 'VerticesSocket',
            'proxima .idx': 'StringsSocket',
            'proxima dist': 'StringsSocket',
            'n proxima .co': 'VerticesSocket',
            'n proxima .idx': 'StringsSocket',
            'n proxima dist': 'StringsSocket',
            'grouped .co': 'VerticesSocket',
            'grouped .idx': 'StringsSocket',
            'grouped dist': 'StringsSocket'
        }

        standard_inputs = ['Verts', 'Check Verts']

        while len(inputs) > 2:
            inputs.remove(inputs[-1])
        while len(outputs) > 0:
            outputs.remove(outputs[-1])

        if mode == 'FIND':
            self.current_mode = mode
            outs = ['proxima .co', 'proxima .idx', 'proxima dist']
            for socket_name in outs:
                socket_type = socket_map[socket_name]
                outputs.new(socket_type, socket_name, socket_name)

        elif mode == 'FIND_N':
            self.current_mode = mode
            socket_name = 'n nearest'
            socket_type = socket_map[socket_name]
            inputs.new(socket_type, socket_name, socket_name)

            outs = ['n proxima .co', 'n proxima .idx', 'n proxima dist']
            for socket_name in outs:
                socket_type = socket_map[socket_name]
                outputs.new(socket_type, socket_name, socket_name)

        elif mode == 'FIND_RANGE':
            self.current_mode = mode
            socket_name = 'radius'
            socket_type = socket_map[socket_name]
            inputs.new(socket_type, socket_name, socket_name)

            outs = ['grouped .co', 'grouped .idx', 'grouped dist']
            for socket_name in outs:
                socket_type = socket_map[socket_name]
                outputs.new(socket_type, socket_name, socket_name)

        else:
            return

    modes = [
        ("FIND", " 1 ", "Find nearest", 1),
        ("FIND_N", " n ", "Find n nearest", 2),
        ("FIND_RANGE", "radius", "Find within Distance", 3)
    ]

    mode = EnumProperty(items=modes,
                        default='FIND',
                        update=mode_change)

    def draw_buttons(self, context, layout):
        layout.label("Search mode:")
        layout.prop(self, "mode", expand=True)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Verts', 'Verts')
        self.inputs.new('VerticesSocket', 'Check Verts', 'Check Verts')

        defaults = ['proxima .co', 'proxima .idx', 'proxima dist']
        pVerts, pIdxs, pDists = defaults
        self.outputs.new('VerticesSocket', pVerts, pVerts)
        self.outputs.new('StringsSocket', pIdxs, pIdxs)
        self.outputs.new('StringsSocket', pDists, pDists)

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        if not ('Verts' in inputs and inputs['Verts'].links):
            return

        try:
            verts = SvGetSocketAnyType(self, inputs['Verts'])[0]
        except IndexError:
            return

        '''
        - assumptions:
            : MainVerts are potentially different on each update
            : not nested input ([vlist1],[vlist2],...)

        with small vert lists I don't imagine this will be very noticeable,
        '''

        # make kdtree
        # documentation/blender_python_api_2_70_release/mathutils.kdtree.html
        size = len(verts)
        kd = mathutils.kdtree.KDTree(size)

        for i, vtx in enumerate(verts):
            kd.insert(Vector(vtx), i)
        kd.balance()

        reset_outs = {
            'FIND': ['proxima .co', 'proxima .idx', 'proxima dist'],
            'FIND_N': ['n proxima .co', 'n proxima .idx', 'n proxima dist'],
            'FIND_RANGE': ['grouped .co', 'grouped .idx', 'grouped dist']
            #'EDGES': [Edges]
        }

        # set sockets to [] and return early, somehow this has been triggered
        # early.
        if not ('Check Verts' in inputs and inputs['Check Verts']):
            try:
                for socket in reset_outs[self.mode]:
                    SvSetSocketAnyType(self, socket, [])
            except KeyError:
                pass
            return

        # before continuing check at least that there is one output.
        try:
            some_output = any([outputs[i].links for i in range(3)])
        except (IndexError, KeyError) as e:
            return

        if self.mode == 'FIND':
            ''' [Verts.co,..] =>
                [Verts.idx,.] =>
                [Verts.dist,.] =>
            => [Main Verts]
            => [cVert,..]
            '''
            try:
                cVerts = SvGetSocketAnyType(self, inputs['Check Verts'])[0]
            except (IndexError, KeyError) as e:
                return

            verts_co_list = []
            verts_idx_list = []
            verts_dist_list = []
            add_verts_coords = verts_co_list.append
            add_verts_idxs = verts_idx_list.append
            add_verts_dists = verts_dist_list.append

            for i, vtx in enumerate(cVerts):
                co, index, dist = kd.find(vtx)
                add_verts_coords(co.to_tuple())
                add_verts_idxs(index)
                add_verts_dists(dist)

            SvSetSocketAnyType(self, 'proxima .co', verts_co_list)
            SvSetSocketAnyType(self, 'proxima .idx', verts_idx_list)
            SvSetSocketAnyType(self, 'proxima dist', verts_dist_list)

        elif self.mode == 'FIND_N':
            ''' [[Verts.co,..n],..c] => from MainVerts closest to v.co
                [[Verts.idx,..n],.c] => from MainVerts closest to v.co
                [[Verts.dist,.n],.c] => from MainVerts closest to v.co
            => [Main Verts]
            => [cVert,..]
            => [n, max n nearest
            '''
            try:
                cVerts = SvGetSocketAnyType(self, inputs['Check Verts'])[0]
                n = SvGetSocketAnyType(self, inputs['n nearest'])[0][0]
            except (IndexError, KeyError) as e:
                return

            if n < 1:
                return

            n_proxima_co = []
            n_proxima_idx = []
            n_proxima_dist = []
            add_co_proximas = n_proxima_co.append
            add_idx_proximas = n_proxima_idx.append
            add_dist_proximas = n_proxima_dist.append

            for i, vtx in enumerate(cVerts):
                co_list = []
                idx_list = []
                dist_list = []
                n_list = kd.find_n(vtx, n)
                for co, index, dist in n_list:
                    co_list.append(co.to_tuple())
                    idx_list.append(index)
                    dist_list.append(dist)
                add_co_proximas(co_list)
                add_idx_proximas(idx_list)
                add_dist_proximas(dist_list)

            SvSetSocketAnyType(self, 'n proxima .co', n_proxima_co)
            SvSetSocketAnyType(self, 'n proxima .idx', n_proxima_idx)
            SvSetSocketAnyType(self, 'n proxima dist', n_proxima_dist)

        elif self.mode == 'FIND_RANGE':
            ''' [grouped [.co for p in MainVerts in r of v in cVert]] =>
                [grouped [.idx for p in MainVerts in r of v in cVert]] =>
                [grouped [.dist for p in MainVerts in r of v in cVert]] =>
            => [Main Verts]
            => [cVert,..]
            => n
            '''
            try:
                cVerts = SvGetSocketAnyType(self, inputs['Check Verts'])[0]
                r = SvGetSocketAnyType(self, inputs['radius'])[0][0]
            except (IndexError, KeyError) as e:
                return

            # for i, vtx in enumerate(verts):
            #     num_edges = 0
            #     for (co, index, dist) in kd.find_range(vtx, mdist):
            #         if i == index or (num_edges > 2):
            #             continue
            #         e.append([i, index])
            #         num_edges += 1
            if r < 0:
                return

            grouped_co = []
            grouped_idx = []
            grouped_dist = []
            add_co = grouped_co.append
            add_idx = grouped_idx.append
            add_dist = grouped_dist.append

            for i, vtx in enumerate(cVerts):
                co_list = []
                idx_list = []
                dist_list = []
                n_list = kd.find_range(vtx, r)
                for co, index, dist in n_list:
                    co_list.append(co.to_tuple())
                    idx_list.append(index)
                    dist_list.append(dist)
                add_co(co_list)
                add_idx(idx_list)
                add_dist(dist_list)

            SvSetSocketAnyType(self, 'grouped .co', grouped_co)
            SvSetSocketAnyType(self, 'grouped .idx', grouped_idx)
            SvSetSocketAnyType(self, 'grouped dist', grouped_dist)
            pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvKDTreeNode)


def unregister():
    bpy.utils.unregister_class(SvKDTreeNode)
