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

from itertools import chain
import bpy
from bpy.props import BoolProperty, EnumProperty, BoolVectorProperty
from mathutils import Vector
import numpy as np

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.modules.matrix_utils import matrix_apply_np

socket_names = ['Vertices', 'Edges', 'Polygons']

def mesh_join_np(verts, edges, pols, out_np_pols):
    '''
    joins many meshes
    verts and edges have to be list of numpy arrays [(n,3), (n,3),...] and [(n,2), (n,2), ...]
    pols should be a numpy array only if you want to get a numpy array with polygons, otherways inputting a regular list will be faster
    out_np_pols is a boolean to indicate if you want output numpy arrays in the faces'''


    accum_vert_lens = np.add.accumulate([len(v) for v in chain([[]], verts)])

    v_out = np.concatenate(verts)

    # just checking the first object to detect presence of edges and Polygons
    # this would fail if the first object does not have edges/pols and there
    # are edges/pols in the next objects but I guess is enough
    are_some_edges = len(edges[0]) > 0
    are_some_pols = len(pols[0]) > 0

    if are_some_edges:
        e_out = np.concatenate([edg + l for edg, l in zip(edges, accum_vert_lens)])
    else:
        e_out = np.array([])

    if are_some_pols:
        if out_np_pols:
            is_array_of_lists = pols[0].dtype == object
            if is_array_of_lists:
                p_out = [np.array(p) + l  for pol, l in zip(pols, accum_vert_lens) for p in pol]

            else:
                p_out = np.concatenate([pol + l for pol, l in zip(pols, accum_vert_lens)])
        else:
            p_out = [[v + l for v in p]  for pol, l in zip(pols, accum_vert_lens) for p in pol]
    else:
        p_out = np.array([])

    return v_out, e_out, p_out

def apply_matrix_to_vectors(vertices, matrices, out_verts):
    max_v = len(vertices) - 1
    for i, mat in enumerate(matrices):
        vert_id = min(i, max_v)
        out_verts.append([(mat @ Vector(v))[:] for v in vertices[vert_id]])

def apply_matrix_to_vectors_np(vertices, matrices, out_verts):
    r_vertices = [np.array(v) for v in vertices]
    max_v = len(vertices) - 1
    for i, mat in enumerate(matrices):
        vert_id = min(i, max_v)
        out_verts.append(matrix_apply_np(r_vertices[vert_id], mat))

def apply_and_join_numpy(vertices, edges, faces, matrices, do_join, out_np):
    out_verts = []
    output_numpy_verts, output_numpy_edges, output_numpy_pols = out_np
    n = len(matrices)
    apply_matrix_to_vectors_np(vertices, matrices, out_verts)

    if do_join:
        #prepare data for joining
        out_edges = ([np.array(e) for e in edges] * n)[:n]
        if output_numpy_pols:
            out_faces = ([np.array(f) for f in faces] * n)[:n]
        else:
            out_faces = (faces * n)[:n]

        out_verts, out_edges, out_faces = mesh_join_np(out_verts, out_edges, out_faces, output_numpy_pols)

        out_verts, out_faces = [out_verts], [out_faces]

        if output_numpy_edges:
            out_edges = [out_edges]
        else:
            out_edges = [out_edges.tolist()]
    else:
        out_edges = (edges * n)[:n]
        out_faces = (faces * n)[:n]

    if not output_numpy_verts:
        out_verts = [v.tolist() for v in out_verts]

    return out_verts, out_edges, out_faces

def apply_and_join_python(vertices, edges, faces, matrices, do_join):
    n = len(matrices)
    out_verts = []
    if isinstance(vertices[0], np.ndarray):
        py_verts = [v.tolist() for v in vertices]
    else:
        py_verts = vertices
    apply_matrix_to_vectors(py_verts, matrices, out_verts)

    if do_join:
        out_edges = (edges * n)[:n]
        out_faces = (faces * n)[:n]
        out_verts, out_edges, out_faces = mesh_join(out_verts, out_edges, out_faces)
        out_verts, out_edges, out_faces = [out_verts], [out_edges], [out_faces]
    else:
        out_edges = (edges * n)[:n]
        out_faces = (faces * n)[:n]
    return out_verts, out_edges, out_faces

class SvMatrixApplyJoinNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mat * Mesh (& Join)
    Tooltip: Multiply vectors on matrices with several objects in output, processes edges & faces too. It can also join the output meshes in to a single one
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
            row = layout.row()
            for i in range(3):
                row.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

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

        if self.implementation == 'NumPy':
            out_verts, out_edges, out_faces = apply_and_join_numpy(vertices, edges, faces, matrices, self.do_join, self.out_np)

        else:
            out_verts, out_edges, out_faces = apply_and_join_python(vertices, edges, faces, matrices, self.do_join)

        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)
        self.outputs['Vertices'].sv_set(out_verts)


def register():
    bpy.utils.register_class(SvMatrixApplyJoinNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixApplyJoinNode)
