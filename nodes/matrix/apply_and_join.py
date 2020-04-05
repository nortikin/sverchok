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
from bpy.props import BoolProperty, EnumProperty, BoolVectorProperty
from mathutils import Vector
import numpy as np

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.modules.matrix_utils import matrix_apply_np


socket_names = ['Vertices', 'Edges', 'Polygons']

def mesh_join_np(verts, edges, pols, out_np):

    lens = [0]
    for v in verts:
        lens.append(lens[-1] + v.shape[0])

    v_out = np.concatenate(verts)
    e_out, p_out = np.array([]), np.array([])

    if len(edges[0]) > 0:
        e_out = np.concatenate([edg + l for edg, l in zip(edges, lens)])

    if len(pols[0]) > 0 and out_np[2]:

        if pols[0].dtype == object:
            p_out = [np.array(p) + l  for pol, l in zip(pols, lens) for p in pol]

        else:
            p_out = np.concatenate([pol + l for pol, l in zip(pols, lens)])
    else:
        p_out = [[v + l for v in p]  for pol, l in zip(pols, lens) for p in pol]

    return v_out, e_out, p_out

def apply_matrix_to_vectors(vertices, matrices, out_verts):
    max_v = len(vertices) - 1
    for i, m in enumerate(matrices):
        vert_id = min(i, max_v)
        out_verts.append([(m @ Vector(v))[:] for v in vertices[vert_id]])

def apply_matrix_to_vectors_np(vertices, matrices,out_verts):
    r_vertices = [np.array(v) for v in vertices]
    max_v = len(vertices) - 1
    for i, m in enumerate(matrices):
        vert_id = min(i, max_v)
        out_verts.append(matrix_apply_np(r_vertices[vert_id], m))


class SvMatrixApplyJoinNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mat * Mesh (& Join)
    Tooltip: Multiply vectors on matrices with several objects in output,
    and process edges & faces too. It can also join the output meshes in to a
    single one.
    """

    bl_idname = 'SvMatrixApplyJoinNode'
    bl_label = 'Matrix Apply'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_APPLY_JOIN'

    do_join: BoolProperty(name='Join', default=True, update=updateNode)

    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    implementation: EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method (See Documentation)',
        default="Python", update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)
    out_np: BoolVectorProperty(
        name="Ouput Numpy",
        description="Output NumPy arrays",
        default=(False, False, False),
        size=3, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvMatrixSocket', "Matrices")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "do_join")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "do_join")
        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)
        if self.implementation == 'NumPy':
            layout.label(text="Ouput Numpy:")
            r = layout.row()
            for i in range(3):
                r.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

    def rclick_menu(self, context, layout):
        layout.prop(self, "do_join")
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == 'NumPy':
            layout.label(text="Ouput Numpy:")

            for i in range(3):
                layout.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

    def process(self):
        if not (self.inputs['Matrices'].is_linked and any(s.is_linked for s in self.outputs)):
            return
        vertices = self.inputs['Vertices'].sv_get(deepcopy=False)

        edges = self.inputs['Edges'].sv_get(default=[[]], deepcopy=False)
        faces = self.inputs['Faces'].sv_get(default=[[]], deepcopy=False)
        matrices = self.inputs['Matrices'].sv_get(deepcopy=False)

        out_verts = []
        n = len(matrices)

        if self.implementation == 'NumPy':

            apply_matrix_to_vectors_np(vertices, matrices, out_verts)

            if self.do_join:
                #prepare data for joining
                out_edges = ([np.array(e) for e in edges] * n)[:n]
                if self.out_np[2]:
                    out_faces = ([np.array(f) for f in faces] * n)[:n]
                else:
                    out_faces = (faces * n)[:n]

                out_verts, out_edges, out_faces = mesh_join_np(out_verts, out_edges, out_faces, self.out_np)

                out_verts, out_faces = [out_verts], [out_faces]

                if self.out_np[1]:
                    out_edges = [out_edges]
                else:
                    out_edges = [out_edges.tolist()]
            else:
                out_edges = (edges * n)[:n]
                out_faces = (faces * n)[:n]

            if not self.out_np[0]:
                out_verts = [v.tolist() for v in out_verts]

        else:
            if isinstance(vertices[0], np.ndarray):
                py_verts = [v.tolist() for v in vertices]
            else:
                py_verts = vertices
            apply_matrix_to_vectors(py_verts, matrices, out_verts)

            if self.do_join:
                out_edges = (edges * n)[:n]
                out_faces = (faces * n)[:n]
                out_verts, out_edges, out_faces = mesh_join(out_verts, out_edges, out_faces)
                out_verts, out_edges, out_faces = [out_verts], [out_edges], [out_faces]
            else:
                out_edges = (edges * n)[:n]
                out_faces = (faces * n)[:n]



        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)
        self.outputs['Vertices'].sv_set(out_verts)


def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)
