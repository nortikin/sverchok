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
from bpy.props import BoolVectorProperty, EnumProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode


class SvBBoxNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    '''Bounding box'''
    bl_idname = 'SvBBoxNodeMk2'
    bl_label = 'Bounding box'
    bl_icon = 'NONE'
    sv_icon = 'SV_BOUNDING_BOX'
    def update_sockets(self, context):
        bools = [self.min_list, self.max_list, self.size_list]
        dims = int(self.dimensions[0])
        for i in range(3):
            for j in range(3):
                out_index = 4 + j + 3*i
                hidden = self.outputs[out_index].hide_safe
                if bools[i][j] and j < dims:
                    if hidden:
                        self.outputs[out_index].hide_safe = False
                else:
                    self.outputs[out_index].hide_safe = True

            updateNode(self, context)

    min_list: BoolVectorProperty(
        name='Min', description="Show Minimum values sockets", size=3, update=update_sockets)
    max_list: BoolVectorProperty(
        name='Max', description="Show Maximun values sockets", size=3, update=update_sockets)
    size_list: BoolVectorProperty(
        name='Size', description="Show Size values sockets", size=3, update=update_sockets)
    implentation_modes = [
        ("2D", "2D", "Outputs Rectangle over XY plane", 0),
        ("3D", "3D", "Outputs standard bounding box", 1)]
    dimensions: EnumProperty(
        name='Implementation', items=implentation_modes,
        description='Choose calculation method',
        default="3D", update=update_sockets)



    def draw_buttons(self, context, layout):
        layout .prop(self, 'dimensions', expand=True)
        col = layout.column(align=True)
        titles = ["Min", "Max", "Size"]
        prop = ['min_list', 'max_list', 'size_list']
        dims = int(self.dimensions[0])
        for i in range(3):
            row = col.row(align=True)
            row.label(text=titles[i])
            row2 = row.row(align=True)
            for j in range(dims):
                row2 .prop(self, prop[i], index=j, text='XYZ'[j], toggle=True)

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices')

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvVerticesSocket', 'Mean')
        son('SvMatrixSocket', 'Center')
        titles = ['Min', 'Max', 'Size']
        for j in range(3):
            for i in range(3):
                son('SvStringsSocket', titles[j] + ' ' + 'XYZ'[i])

        self.update_sockets(context)

    def generate_matrix(self, maxmin, dims, to_2d):
        center = [(u+v)*.5 for u, v in maxmin[:dims]]
        scale = [(u-v) for u, v in maxmin[:dims]]
        if to_2d:
            center += [0]
            scale += [1]
        mat = Matrix.Translation(center)
        for i, sca in enumerate(scale):
            mat[i][i] = sca
        return mat

    def generate_mean(self, verts, dims, to_2d):
        avr = list(map(sum, zip(*verts)))
        avr = [n/len(verts) for n in avr[:dims]]
        if to_2d:
            avr += [0]
        return [avr]

    def process(self):
        if not self.inputs['Vertices'].is_linked:
            return
        if not any(s.is_linked for s in self.outputs):
            return
        has_mat_out = bool(self.outputs['Center'].is_linked)
        has_mean = bool(self.outputs['Mean'].is_linked)
        has_vert_out = bool(self.outputs['Vertices'].is_linked)

        verts = self.inputs['Vertices'].sv_get(deepcopy=False)
        verts = dataCorrect(verts, nominal_dept=2)
        has_limits = any(s.is_linked for s in self.outputs[4:])
        if verts:
            verts_out = []
            edges_out = []
            edges = [
                (0, 1), (1, 3), (3, 2), (2, 0),  # bottom edges
                (4, 5), (5, 7), (7, 6), (6, 4),  # top edges
                (0, 4), (1, 5), (2, 6), (3, 7)  # sides
            ]

            mat_out = []
            mean_out = []
            min_vals = [[], [], []]
            max_vals = [[], [], []]
            size_vals = [[], [], []]
            to_2d = self.dimensions == '2D'
            dims = int(self.dimensions[0])

            for vec in verts:
                if has_mat_out or has_vert_out or has_limits:
                    maxmin = list(zip(map(max, *vec), map(min, *vec)))
                if has_vert_out:
                    out = list(product(*reversed(maxmin)))
                    v_out = [l[::-1] for l in out[::-1]]
                    if to_2d:
                        verts_out.append([[v[0], v[1], 0] for v in v_out[:4]])
                        edges = edges[:4]
                    else:
                        verts_out.append(v_out)
                    edges_out.append(edges)

                if has_mat_out:
                    mat_out.append(self.generate_matrix(maxmin, dims, to_2d))

                if has_mean:
                    mean_out.append(self.generate_mean(v, dims, to_2d))

                if has_limits:
                    for i in range(dims):
                        min_vals[i].append([maxmin[i][1]])
                        max_vals[i].append([maxmin[i][0]])
                        size_vals[i].append([maxmin[i][0] - maxmin[i][1]])

            if has_vert_out:
                self.outputs['Vertices'].sv_set(verts_out)

            if self.outputs['Edges'].is_linked:
                self.outputs['Edges'].sv_set(edges_out)

            if has_mean:
                self.outputs['Mean'].sv_set(mean_out)

            if self.outputs['Center'].is_linked:
                self.outputs['Center'].sv_set(mat_out)

            vals = [min_vals, max_vals, size_vals]
            for j in range(3):
                for i, socket in enumerate(self.outputs[4+3*j:7+3*j]):
                    if socket.is_linked:
                        socket.sv_set(vals[j][i])


def register():
    bpy.utils.register_class(SvBBoxNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvBBoxNodeMk2)
