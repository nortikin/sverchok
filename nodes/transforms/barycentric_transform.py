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


def matrix_def(tri0, tri1, tri2):
    '''Creation of Transform matrix from triangle'''
    tri_normal = cross(tri1 - tri0, tri2 - tri0)
    magnitude = norm(tri_normal)
    tri_area = 0.5 * magnitude
    tri3 = tri0 + (tri_normal / magnitude)* sqrt(tri_area)

    transform_matrix = zeros([3, 3], dtype=float32)
    transform_matrix[0, :] = tri0 - tri3
    transform_matrix[1, :] = tri1 - tri3
    transform_matrix[2, :] = tri2 - tri3

    return transform_matrix, tri3

def compute_barycentric_transform_np(params, result, out_numpy):
    '''NumPy Implementation of a barycentric transform'''
    verts = array(params[0])
    egde_pol = params[1]
    tri_s = array(params[2])
    tri_d = array(params[3])

    transform_matrix_s, tri3_s = matrix_def(tri_s[0, :], tri_s[1, :], tri_s[2, :])
    transform_matrix_d, tri3_d = matrix_def(tri_d[0, :], tri_d[1, :], tri_d[2, :])

    barycentric_co = dot(inv(transform_matrix_s).T, (verts - tri3_s).T)
    cartesian = dot(barycentric_co.T, transform_matrix_d) + tri3_d
    result.append(cartesian if out_numpy else cartesian.tolist())


def compute_barycentric_transform_mu(params, result, out_numpy):
    '''Port to MathUtils barycentric transform function'''
    edge_pol = params[1]
    tri_s = [V(v) for v in params[2]]
    tri_d = [V(v) for v in params[3]]
    sub_result = []
    for vert in params[0]:
        point = V(vert)
        transformed_vert = barycentric_transform(point, tri_s[0], tri_s[1], tri_s[2], tri_d[0], tri_d[1], tri_d[2])
        sub_result.append(list(transformed_vert))
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

    compute_distances = {
        "NumPy": compute_barycentric_transform_np,
        "MathUtils": compute_barycentric_transform_mu}

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
        return list_match_func[self.list_match]([s.sv_get(default=[[]]) for s in self.inputs])

    def process(self):
        '''main node function called every update'''
        outputs = self.outputs
        inputs = self.inputs
        if not (outputs[0].is_linked and all(s.is_linked for s in inputs[:1] + inputs[2:])):
            return

        result = [[], []]
        group = self.get_data()
        func = self.compute_distances[self.implementation]
        out_numpy = self.output_numpy
        edg_pol_data = inputs[1].is_linked and outputs[1].is_linked
        
        for params in zip(*group):
            func(params, result[0], out_numpy)
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
