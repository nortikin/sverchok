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
import numpy as np
import bpy
from bpy.props import BoolVectorProperty, EnumProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

from sverchok.data_structure import dataCorrect, updateNode

EDGES = [
    (0, 1), (1, 3), (3, 2), (2, 0),  # bottom edges
    (4, 5), (5, 7), (7, 6), (6, 4),  # top edges
    (0, 4), (1, 5), (2, 6), (3, 7)  # sides
]
def generate_matrix(maxmin, dims, to_2d):
    center = [(u+v)*.5 for u, v in maxmin[:dims]]
    scale = [(u-v) for u, v in maxmin[:dims]]
    if to_2d:
        center += [0]
        scale += [1]
    mat = Matrix.Translation(center)
    for i, sca in enumerate(scale):
        mat[i][i] = sca
    return mat

def generate_mean_np(verts, dims, to_2d):
    avr = (np.sum(verts[:, :dims], axis=0)/len(verts)).tolist()
    if to_2d:
        avr += [0]
    return [avr]

def generate_mean(verts, dims, to_2d):
    avr = list(map(sum, zip(*verts)))
    avr = [n/len(verts) for n in avr[:dims]]
    if to_2d:
        avr += [0]
    return [avr]

def bounding_box(verts,
                 box_dimensions='2D',
                 output_verts=True,
                 output_mat=True,
                 output_mean=True,
                 output_limits=True):
    '''
    verts expects a list of level 3 [[[0,0,0],[1,1,1]..],[]]
    returns per sublist:
        verts_out: vertices of the bounding box
        edges_out: edges of the bounding box
        mean_out: mean of all vertcies
        mat_out: Matrix that would transform a box of 1 unit into the bbox
        *min_vals, Min X, Y and Z of the bounding box
        *max_vals, Max X, Y and Z of the bounding box
        *size_vals Size X, Y and Z of the bounding box
    '''
    verts_out = []
    edges_out = []
    edges = EDGES

    mat_out = []
    mean_out = []
    min_vals = [[], [], []]
    max_vals = [[], [], []]
    size_vals = [[], [], []]
    to_2d = box_dimensions == '2D'
    dims = int(box_dimensions[0])
    calc_maxmin = output_mat or output_verts or output_limits

    for vec in verts:
        if calc_maxmin:
            if isinstance(vec, np.ndarray):
                np_vec = vec
            else:
                np_vec = np.array(vec)
            bbox_max = np.amax(np_vec, axis=0)
            bbox_min = np.amin(np_vec, axis=0)
            maxmin = np.concatenate([bbox_max, bbox_min]).reshape(2,3).T.tolist()

        if output_verts:
            out = list(product(*reversed(maxmin)))
            v_out = [l[::-1] for l in out[::-1]]
            if to_2d:
                verts_out.append([[v[0], v[1], 0] for v in v_out[:4]])
                edges = edges[:4]
            else:
                verts_out.append(v_out)
            edges_out.append(edges)

        if output_mat:
            mat_out.append(generate_matrix(maxmin, dims, to_2d))

        if output_mean:
            if calc_maxmin:
                mean_out.append(generate_mean_np(np_vec, dims, to_2d))
            else:
                if isinstance(vec, np.ndarray):
                    mean_out.append(generate_mean_np(vec, dims, to_2d))
                else:
                    mean_out.append(generate_mean(vec, dims, to_2d))

        if output_limits:
            for i in range(dims):
                min_vals[i].append([maxmin[i][1]])
                max_vals[i].append([maxmin[i][0]])
                size_vals[i].append([maxmin[i][0] - maxmin[i][1]])

    return (verts_out,
            edges_out,
            mean_out,
            mat_out,
            *min_vals,
            *max_vals,
            *size_vals)


class SvBBoxNodeMk3(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    """
    Triggers: Bbox 2D or 3D
    Tooltip: Get vertices bounding box (vertices, sizes, center)
    """
    bl_idname = 'SvBBoxNodeMk3'
    bl_label = 'Bounding box'
    bl_icon = 'SHADING_BBOX'
    sv_icon = 'SV_BOUNDING_BOX'

    def update_sockets(self, context):
        bools = [self.min_list, self.max_list, self.size_list]
        dims = int(self.box_dimensions[0])
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
        name='Max', description="Show Maximum values sockets", size=3, update=update_sockets)
    size_list: BoolVectorProperty(
        name='Size', description="Show Size values sockets", size=3, update=update_sockets)
    implentation_modes = [
        ("2D", "2D", "Outputs Rectangle over XY plane", 0),
        ("3D", "3D", "Outputs standard bounding box", 1)]
    box_dimensions: EnumProperty(
        name='Implementation', items=implentation_modes,
        description='Choose calculation method',
        default="3D", update=update_sockets)



    def draw_buttons(self, context, layout):
        layout .prop(self, 'box_dimensions', expand=True)
        col = layout.column(align=True)
        titles = ["Min", "Max", "Size"]
        prop = ['min_list', 'max_list', 'size_list']
        dims = int(self.box_dimensions[0])
        for i in range(3):
            row = col.row(align=True)
            row.label(text=titles[i])
            row2 = row.row(align=True)
            for j in range(dims):
                row2 .prop(self, prop[i], index=j, text='XYZ'[j], toggle=True)

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices').is_mandatory = True

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvVerticesSocket', 'Mean')
        son('SvMatrixSocket', 'Center')
        titles = ['Min', 'Max', 'Size']
        for j in range(3):
            for i in range(3):
                son('SvStringsSocket', titles[j] + ' ' + 'XYZ'[i])

        self.update_sockets(context)

    def migrate_from(self, old_node):
        self.box_dimensions = old_node.dimensions

    def process_data(self, params):

        verts = params[0]

        output_mat = self.outputs['Center'].is_linked
        output_mean = self.outputs['Mean'].is_linked
        output_verts = self.outputs['Vertices'].is_linked
        output_limits = any(s.is_linked for s in self.outputs[4:])
        return bounding_box(verts,
                            box_dimensions=self.box_dimensions,
                            output_verts=output_verts,
                            output_mat=output_mat,
                            output_mean=output_mean,
                            output_limits=output_limits)



def register():
    bpy.utils.register_class(SvBBoxNodeMk3)


def unregister():
    bpy.utils.unregister_class(SvBBoxNodeMk3)
