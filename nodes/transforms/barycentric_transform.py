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

from numpy import cross, sqrt, zeros, float32, array, dot
from numpy.linalg import norm, inv
from mathutils import Vector as V
from mathutils.geometry import  barycentric_transform

import bpy
from bpy.props import BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes


def matrix_def(triangle):
    '''Creation of Transform matrix from triangle'''
    tri0, tri1, tri2 = triangle[0, :], triangle[1, :], triangle[2, :]
    tri_normal = cross(tri1 - tri0, tri2 - tri0)
    magnitude = norm(tri_normal)
    tri_area = 0.5 * magnitude
    tri3 = tri0 + (tri_normal / magnitude)* sqrt(tri_area)

    transform_matrix = zeros([3, 3], dtype=float32)
    transform_matrix[0, :] = tri0 - tri3
    transform_matrix[1, :] = tri1 - tri3
    transform_matrix[2, :] = tri2 - tri3

    return transform_matrix, tri3

def prepare_source_data(tri_src):
    '''Create the inverted Transformation Matrix and 4th point of the tetrahedron'''
    inverted_matrix_s = []
    tri3_src = []
    for tri in tri_src:
        np_tri = array(tri)
        matrix_trasform_s, tri3 = matrix_def(np_tri)
        tri3_src.append(tri3)
        inverted_matrix_s.append(inv(matrix_trasform_s).T)

    return inverted_matrix_s, tri3_src


def prepare_dest_data(tri_dest):
    '''Create Transformation Matrix and 4th point of the tetrahedron'''
    tri3_dest = []
    matrix_transform_d = []
    for tri in tri_dest:
        np_tri = array(tri)
        matrix_trasform, tri3 = matrix_def(np_tri)
        matrix_transform_d.append(matrix_trasform)
        tri3_dest.append(tri3)

    return matrix_transform_d, tri3_dest

def compute_barycentric_transform_np(params, matched_index, result, out_numpy, edg_pol_data):
    '''NumPy Implementation of a barycentric transform'''
    verts, egde_pol, tri_src, tri_dest = params
    np_verts = [array(v) for v in verts]
    inverted_matrix_s, tri3_src = prepare_source_data(tri_src)
    matrix_transform_d, tri3_dest = prepare_dest_data(tri_dest)


    for v_id, edge_id, tri_src_id, tri_dest_id in zip(*matched_index):
    
        barycentric_co = dot(inverted_matrix_s[tri_src_id], (np_verts[v_id] - tri3_src[tri_src_id]).T)       
        cartesian_co = dot(barycentric_co.T, matrix_transform_d[tri_dest_id]) + tri3_dest[tri_dest_id]
        
        result[0].append(cartesian_co if out_numpy else cartesian_co.tolist())
        if edg_pol_data:
            result[1].append(egde_pol[edge_id])


def compute_barycentric_transform_mu(params, result):
    '''Port to MathUtils barycentric transform function'''

    tri_src = [V(v) for v in params[2]]
    tri_dest = [V(v) for v in params[3]]
    sub_result = []
    for vert in params[0]:
        point = V(vert)
        new_vert = barycentric_transform(point, tri_src[0], tri_src[1], tri_src[2], tri_dest[0], tri_dest[1], tri_dest[2])
        sub_result.append(list(new_vert))
    result.append(sub_result)


class SvBarycentricTransformNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Adaptive Triangles
    Tooltip: Adaptive Triangles. Barycentric transformation between triangles.
    '''
    bl_idname = 'SvBarycentricTransformNode'
    bl_label = 'Barycentric Transform'
    bl_icon = 'MESH_DATA'

    implentation_modes = [
        ("NumPy", "NumPy", "Faster to transform heavy meshes", 0),
        ("MathUtils", "MathUtils", "Faster to transform light meshes", 1)]

    output_numpy = BoolProperty(
        name='Output NumPy', description='Output NumPy arrays',
        default=False, update=updateNode)

    implementation = EnumProperty(
        name='Implementation', items=implentation_modes,
        description='Choose calculation method',
        default="NumPy", update=updateNode)

    list_match = EnumProperty(
        name="List Match",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', 'Vertices')
        sinw('StringsSocket', 'Edg_Pol')
        sinw('VerticesSocket', 'Verts Tri Source')
        sinw('VerticesSocket', 'Verts Tri Target')

        sonw('VerticesSocket', 'Vertices')
        sonw('StringsSocket', 'Edg_Pol')

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "implementation", expand=True)
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)
        layout.prop(self, "list_match", text="Match Length List", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def get_data(self):
        '''get all data from sockets'''
        return [s.sv_get(default=[[]]) for s in self.inputs]


    def process(self):
        '''main node function called every update'''
        outputs = self.outputs
        inputs = self.inputs
        if not (outputs[0].is_linked and all(s.is_linked for s in inputs[:1] + inputs[2:])):
            return

        result = [[], []]
        out_numpy = self.output_numpy
        edg_pol_data = inputs[1].is_linked and outputs[1].is_linked
        params = self.get_data()

        if self.implementation == 'NumPy':

            matched_indexes = list_match_func[self.list_match]([list(range(len(p))) for p in params])

            compute_barycentric_transform_np(params, matched_indexes, result, out_numpy, edg_pol_data)

        else:

            group = list_match_func[self.list_match](params)

            for params in zip(*group):
                compute_barycentric_transform_mu(params, result[0])
                if edg_pol_data:
                    result[1].append(params[1])

        outputs[0].sv_set(result[0])
        if edg_pol_data:
            outputs[1].sv_set(result[1])



def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvBarycentricTransformNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvBarycentricTransformNode)
