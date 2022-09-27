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
from bpy.props import BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fixed_iter


def mask_converter_node(vertices=None,
                        edges=None,
                        faces=None,
                        vertices_mask=None,
                        edges_mask=None,
                        faces_mask=None,
                        mode='BY_VERTEX',
                        include_partial=False):
    vertices = vertices or []
    edges = edges or []
    faces = faces or []

    if mode == 'BY_VERTEX':
        len_verts = len(vertices)
        len_edges_verts = (max(i for e in edges for i in e) + 1) if edges else 0
        len_faces_verts = (max(i for f in faces for i in f) + 1) if faces else 0
        len_verts = max(len_verts, len_edges_verts, len_faces_verts)

        vertices_mask = list(fixed_iter(vertices_mask, len_verts))
        out_edges_mask, out_faces_mask = by_vertex(vertices_mask, edges, faces, include_partial)
        out_verts_mask = vertices_mask
    elif mode == 'BY_EDGE':
        edges_mask = list(fixed_iter(edges_mask, len(edges)))
        out_verts_mask, out_faces_mask = by_edge(edges_mask, vertices, edges, faces, include_partial)
        out_edges_mask = edges_mask
    elif mode == 'BY_FACE':
        faces_mask = list(fixed_iter(faces_mask, len(faces)))
        out_verts_mask, out_edges_mask = by_face(faces_mask, vertices, edges, faces, include_partial)
        out_faces_mask = faces_mask
    else:
        raise ValueError("Unknown mode: " + mode)

    return out_verts_mask, out_edges_mask, out_faces_mask


def by_vertex(verts_mask, edges, faces, include_partial):
    indicies = set(i for (i, m) in enumerate(verts_mask) if m)
    if include_partial:
        edges_mask = [any(v in indicies for v in edge) for edge in edges]
        faces_mask = [any(v in indicies for v in face) for face in faces]
    else:
        edges_mask = [all(v in indicies for v in edge) for edge in edges]
        faces_mask = [all(v in indicies for v in face) for face in faces]

    return edges_mask, faces_mask


def by_edge(edge_mask, verts, edges, faces, include_partial):
    indicies = set()
    for m, (u,v) in zip(edge_mask, edges):
        if m:
            indicies.add(u)
            indicies.add(v)

    verts_mask = [i in indicies for i in range(len(verts))]
    if include_partial:
        faces_mask = [any(v in indicies for v in face) for face in faces]
    else:
        faces_mask = [all(v in indicies for v in face) for face in faces]

    return verts_mask, faces_mask


def by_face(faces_mask, verts, edges, faces, include_partial):
    indicies = set()
    for m, face in zip(faces_mask, faces):
        if m:
            indicies.update(set(face))
    verts_mask = [i in indicies for i in range(len(verts))]

    if include_partial:
        edges_mask = [any(v in indicies for v in edge) for edge in edges]
    else:
        selected_edges = set()
        for is_selected_face, face in zip(faces_mask, faces):
            if is_selected_face:
                for face_edge in walk_face(face):
                    selected_edges.add(face_edge)
        edges_mask = [tuple(sorted(edge)) in selected_edges for edge in edges]

    return verts_mask, edges_mask


def walk_face(face, from_edge=None, return_sorted=True):
    # yields all edges in a face
    # face direction has matter
    # from_edge should be not sorted
    first_indexes = list(range(len(face)))
    second_indexes = list(range(1, len(face))) + [0]
    if from_edge:
        start_index = face.index(from_edge[0])
        first_indexes = first_indexes[start_index:] + first_indexes[:start_index]
        second_indexes = second_indexes[start_index:] + second_indexes[:start_index]
    for i1, i2 in zip(first_indexes, second_indexes):
        if return_sorted:
            yield tuple(sorted([face[i1], face[i2]]))
        else:
            yield face[i1], face[i2]


class SvMaskConvertNode(SverchCustomTreeNode, bpy.types.Node):
    '''Convert selected elements to:
vertex -> edges and faces indexes
edges -> vertex and faces indexes
faces -> vertex and edges indexes'''
    bl_idname = 'SvMaskConvertNode'
    bl_label = 'Mask Converter'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MASK_CONVERTER'

    modes = [
            ('BY_VERTEX', "Vertices", "Get edges and faces masks by vertex mask", 0),
            ('BY_EDGE', "Edges", "Get vertex and faces masks by edges mask", 1),
            ('BY_FACE', "Faces", "Get vertex and edge masks by faces mask", 2)
        ]

    def update_mode(self, context):
        self.inputs['Vertices'].hide_safe = (self.mode == 'BY_VERTEX')

        self.inputs['VerticesMask'].hide_safe = (self.mode != 'BY_VERTEX')
        self.inputs['EdgesMask'].hide_safe = (self.mode != 'BY_EDGE')
        self.inputs['FacesMask'].hide_safe = (self.mode != 'BY_FACE')

        self.outputs['VerticesMask'].hide_safe = (self.mode == 'BY_VERTEX')
        self.outputs['EdgesMask'].hide_safe = (self.mode == 'BY_EDGE')
        self.outputs['FacesMask'].hide_safe = (self.mode == 'BY_FACE')

        updateNode(self, context)

    mode: EnumProperty(name="Mode", items=modes, update=update_mode)

    include_partial: BoolProperty(name="Include partial selection",
            description="Include partially selected edges/faces",
            default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.label(text="From:")
        row = col.row(align=True)
        row.prop(self, 'mode', expand=True)
        col.prop(self, 'include_partial', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")

        self.inputs.new('SvStringsSocket', "VerticesMask")
        self.inputs.new('SvStringsSocket', "EdgesMask")
        self.inputs.new('SvStringsSocket', "FacesMask")

        self.outputs.new('SvStringsSocket', 'VerticesMask')
        self.outputs.new('SvStringsSocket', 'EdgesMask')
        self.outputs.new('SvStringsSocket', 'FacesMask')

        self.update_mode(context)

    def process(self):

        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(deepcopy=False, default=[[]])
        edges_s = self.inputs['Edges'].sv_get(deepcopy=False, default=[[]])
        faces_s = self.inputs['Faces'].sv_get(deepcopy=False, default=[[]])

        verts_mask_s = self.inputs['VerticesMask'].sv_get(deepcopy=False, default=[[True]])
        edge_mask_s = self.inputs['EdgesMask'].sv_get(deepcopy=False, default=[[True]])
        face_mask_s = self.inputs['FacesMask'].sv_get(deepcopy=False, default=[[True]])

        out = []
        data = [vertices_s, edges_s, faces_s, verts_mask_s, edge_mask_s, face_mask_s]
        obj_n = max(map(len, data))
        iter_data = zip(*[fixed_iter(d, obj_n, None) for d in data])
        for v, e, f, vm, em, fm in iter_data:
            out.append(mask_converter_node(v, e, f, vm, em, fm, self.mode, self.include_partial))

        vm, em, fm = list(zip(*out))
        self.outputs['VerticesMask'].sv_set(vm)
        self.outputs['EdgesMask'].sv_set(em)
        self.outputs['FacesMask'].sv_set(fm)


def register():
    bpy.utils.register_class(SvMaskConvertNode)


def unregister():
    bpy.utils.unregister_class(SvMaskConvertNode)
