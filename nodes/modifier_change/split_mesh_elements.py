# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import List, Dict

import bpy
from bmesh.ops import split_edges

from sverchok.nodes.list_masks.mask_convert import mask_converter_node
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fixed_iter
from sverchok.utils.sv_bmesh_utils import empty_bmesh, add_mesh_to_bmesh, pydata_from_bmesh


# my guess is that any of such functions should not modifier input data
def split_mesh_elements_node(vertices=None,
                             edges=None,
                             faces=None,
                             face_data=None,
                             mask=None,
                             mask_mode='BY_VERTEX',
                             split_type='VERTS'):

    if not vertices:
        return [], [], [], []

    edges = edges or []
    faces = faces or []
    face_data = list(fixed_iter(face_data, len(faces))) if face_data else None
    mask = mask or []

    if split_type == 'VERTS':
        vs, es, fs, fds = split_by_vertices(vertices, edges, faces, mask)
    elif split_type == 'EDGES':

        if mask_mode != 'BY_EDGE':
            _, mask, _ = mask_converter_node(
                vertices, edges, faces,
                vertices_mask=mask if mask_mode == 'BY_VERTEX' else None,
                faces_mask=mask if mask_mode == 'BY_FACE' else None,
                mode=mask_mode)

        vs, es, fs, fds = split_by_edges(vertices, edges, faces, face_data, mask)
    else:
        raise TypeError(f'Unknown "split_typ" mode = {split_type}')

    return vs, es, fs, fds


def split_by_vertices(verts, edges=None, faces=None, selected_verts: List[bool] = None):
    edges = edges or []
    faces = faces or []
    selected_verts = selected_verts or [True] * len(verts)

    out_verts = []
    out_faces = []
    old_new_verts: Dict[int, int] = dict()
    for face in faces:
        new_face = []
        for i in face:
            if selected_verts[i]:
                out_verts.append(verts[i])
                new_face.append(len(out_verts) - 1)
            else:
                if i in old_new_verts:
                    new_face.append(old_new_verts[i])
                else:
                    out_verts.append(verts[i])
                    old_new_verts[i] = len(out_verts) - 1
                    new_face.append(len(out_verts) - 1)
        out_faces.append(new_face)
    return out_verts, [], out_faces, []


def split_by_edges(verts, edges=None, faces=None, face_data=None, selected_edges: List[bool] = None):
    with empty_bmesh() as bm:
        add_mesh_to_bmesh(bm, verts, edges, faces, 'initial_index')
        split_edges(bm, edges=[e for e, b in zip(bm.edges, selected_edges) if b])
        if face_data:
            v, e, f, fd = pydata_from_bmesh(bm, face_data=face_data)
        else:
            v, e, f = pydata_from_bmesh(bm)
            fd = []
        return v, e, f, fd


class SvSplitMeshElements(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers:

    todo
    """
    bl_idname = 'SvSplitMeshElements'
    bl_label = 'Split mesh elements'
    bl_icon = 'MOD_EDGESPLIT'

    select_mode_items = [(n.upper(), n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('By_Vertex', 'By_Edge', 'By_Face'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]

    mask_mode: bpy.props.EnumProperty(items=select_mode_items, update=updateNode)
    split_type: bpy.props.EnumProperty(items=[(i.upper(), i, '') for i in ['verts', 'edges']], update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'split_type', expand=True)

    def draw_mask_socket(self, socket, context, layout):
        row = layout.row()
        text = f'. {socket.objects_number}' if socket.objects_number else ""
        row.label(text=f'{socket.label or socket.name}{text}')
        row.prop(self, 'mask_mode', expand=True, icon_only=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Face_data')
        self.inputs.new('SvStringsSocket', 'Mask').custom_draw = 'draw_mask_socket'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Face_data')

    @property
    def sv_internal_links(self):
        return [
            (self.inputs[0], self.outputs[0]),
            (self.inputs[1], self.outputs[1]),
            (self.inputs[2], self.outputs[2]),
            (self.inputs[3], self.outputs[3]),
        ]

    def process(self):
        vertices = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[])
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])
        face_data = self.inputs['Face_data'].sv_get(deepcopy=False, default=[])
        mask = self.inputs['Mask'].sv_get(deepcopy=False, default=[])

        out = []
        data = [vertices, edges, faces, face_data, mask]
        obj_n = max(map(len, data))
        iter_data = zip(*[fixed_iter(d, obj_n, None) for d in data])
        for v, e, f, fd, m in iter_data:
            out.append(split_mesh_elements_node(v, e, f, fd, m, self.mask_mode, self.split_type))

        vs, es, fs, fds = list(zip(*out)) if out else ([], [], [], [])
        self.outputs['Vertices'].sv_set(vs)
        self.outputs['Edges'].sv_set(es)
        self.outputs['Faces'].sv_set(fs)
        self.outputs['Face_data'].sv_set(fds)


register, unregister = bpy.utils.register_classes_factory([SvSplitMeshElements])
