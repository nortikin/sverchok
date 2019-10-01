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

from itertools import product

import bpy
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect


class SvBBoxNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    '''Bounding box'''
    bl_idname = 'SvBBoxNodeMk2'
    bl_label = 'Bounding box'
    bl_icon = 'NONE'
    sv_icon = 'SV_BOUNDING_BOX'

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices')

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvVerticesSocket', 'Mean')
        son('SvMatrixSocket', 'Center')
        son('SvStringsSocket', 'Min X')
        son('SvStringsSocket', 'Min Y')
        son('SvStringsSocket', 'Min Z')
        son('SvStringsSocket', 'Max X')
        son('SvStringsSocket', 'Max Y')
        son('SvStringsSocket', 'Max Z')
        son('SvStringsSocket', 'Size X')
        son('SvStringsSocket', 'Size Y')
        son('SvStringsSocket', 'Size Z')

    def process(self):
        if not self.inputs['Vertices'].is_linked:
            return
        if not any(s.is_linked for s in self.outputs):
            return
        has_mat_out = bool(self.outputs['Center'].is_linked)
        has_mean = bool(self.outputs['Mean'].is_linked)
        has_vert_out = bool(self.outputs['Vertices'].is_linked)
        has_min_x_out = bool(self.outputs['Min X'].is_linked)
        has_min_y_out = bool(self.outputs['Min Y'].is_linked)
        has_min_z_out = bool(self.outputs['Min Z'].is_linked)
        has_max_x_out = bool(self.outputs['Max X'].is_linked)
        has_max_y_out = bool(self.outputs['Max Y'].is_linked)
        has_max_z_out = bool(self.outputs['Max Z'].is_linked)
        has_size_x_out = bool(self.outputs['Size X'].is_linked)
        has_size_y_out = bool(self.outputs['Size Y'].is_linked)
        has_size_z_out = bool(self.outputs['Size Z'].is_linked)
        vert = self.inputs['Vertices'].sv_get(deepcopy=False)
        vert = dataCorrect(vert, nominal_dept=2)
        has_limits = any(s.is_linked for s in self.outputs[4:])
        if vert:
            verts_out = []
            edges_out = []
            edges = [
                (0, 1), (1, 3), (3, 2), (2, 0),  # bottom edges
                (4, 5), (5, 7), (7, 6), (6, 4),  # top edges
                (0, 4), (1, 5), (2, 6), (3, 7)  # sides
            ]
            mat_out = []
            mean_out = []
            min_vals = [[],[],[]]
            max_vals = [[],[],[]]
            size_vals = [[],[],[]]

            for v in vert:
                if has_mat_out or has_vert_out or has_limits:
                    maxmin = list(zip(map(max, *v), map(min, *v)))
                    print(maxmin)
                    out = list(product(*reversed(maxmin)))
                    verts_out.append([l[::-1] for l in out[::-1]])
                edges_out.append(edges)
                if has_mat_out:
                    center = [(u+v)*.5 for u, v in maxmin]
                    mat = Matrix.Translation(center)
                    scale = [(u-v) for u, v in maxmin]
                    for i, s in enumerate(scale):
                        mat[i][i] = s
                    mat_out.append(mat)
                if has_mean:
                    avr = list(map(sum, zip(*v)))
                    avr = [n/len(v) for n in avr]
                    mean_out.append([avr])
                if has_limits:
                    # min_vals[0].append([maxmin[0][1]])
                    # min_vals[1].append([maxmin[1][1]])
                    # min_vals[2].append([maxmin[2][1]])
                    # max_vals[0].append([maxmin[0][0]])
                    # max_vals[1].append([maxmin[1][0]])
                    # max_vals[2].append([maxmin[2][0]])
                    for i in range(3):
                        min_vals[i].append([maxmin[i][1]])
                        max_vals[i].append([maxmin[i][0]])
                        size_vals[i].append([maxmin[i][0]-maxmin[i][1]])

            if has_vert_out:
                self.outputs['Vertices'].sv_set(verts_out)

            if self.outputs['Edges'].is_linked:
                self.outputs['Edges'].sv_set(edges_out)

            if has_mean:
                self.outputs['Mean'].sv_set(mean_out)

            if self.outputs['Center'].is_linked:
                self.outputs['Center'].sv_set(mat_out)

            if has_min_x_out:
                self.outputs['Min X'].sv_set(min_vals[0])
            if has_min_y_out:
                self.outputs['Min Y'].sv_set(min_vals[1])
            if has_min_z_out:
                self.outputs['Min Z'].sv_set(min_vals[2])
            if has_max_x_out:
                self.outputs['Max X'].sv_set(max_vals[0])
            if has_max_y_out:
                self.outputs['Max Y'].sv_set(max_vals[1])
            if has_max_z_out:
                self.outputs['Max Z'].sv_set(max_vals[2])
            if has_size_x_out:
                self.outputs['Size X'].sv_set(size_vals[0])
            if has_size_y_out:
                self.outputs['Size Y'].sv_set(size_vals[1])
            if has_size_z_out:
                self.outputs['Size Z'].sv_set(size_vals[2])


def register():
    bpy.utils.register_class(SvBBoxNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvBBoxNodeMk2)
