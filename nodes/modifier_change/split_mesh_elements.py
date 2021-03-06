# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import List, Dict, Tuple

import bpy
from bmesh.ops import split_edges

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last, fixed_iter
from sverchok.utils.sv_bmesh_utils import empty_bmesh, add_mesh_to_bmesh, pydata_from_bmesh
from sverchok.utils.handling_nodes import vectorize


# my guess is that any of such functions should not modifier input data
def split_mesh_elements_node(*,
                             vertices=None,
                             edges=None,
                             faces=None,
                             mask=None,
                             mask_mode='VERTS',
                             split_type='VERTS'):

    out = {'vertices': [], 'edges': [], 'faces': []}

    if not vertices:
        return out

    edges = edges or []
    faces = faces or []
    mask = mask or []

    if split_type == 'VERTS':
        result = split_by_vertices(vertices, edges, faces, mask)
    elif split_type == 'EDGES':
        result = split_by_edges(vertices, edges, faces, mask)
    else:
        raise TypeError(f'Unknown "split_typ" mode = {split_type}')

    for k, r in zip(out, result):
        out[k] = r

    return out


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
    return out_verts, [], out_faces


def split_by_edges(verts, edges=None, faces=None, selected_edges: List[bool] = None):
    with empty_bmesh() as bm:
        add_mesh_to_bmesh(bm, verts, edges, faces, 'old_i')
        split_edges(bm, edges=[e for e, b in zip(bm.edges, selected_edges) if b])
        v, e, f = pydata_from_bmesh(bm)
        return v, e, f


class SvSplitMeshElements(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers:

    todo
    """
    bl_idname = 'SvSplitMeshElements'
    bl_label = 'Split mesh elements'
    bl_icon = 'MOD_EDGESPLIT'

    select_mode_items = [(n.upper(), n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]

    mask_mode = bpy.props.EnumProperty(items=select_mode_items, update=updateNode)
    split_type = bpy.props.EnumProperty(items=[(i.upper(), i, '') for i in ['verts', 'edges']], update=updateNode)

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
        self.inputs.new('SvStringsSocket', 'Mask').custom_draw = 'draw_mask_socket'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        vertices = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[])
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])
        mask = self.inputs['Mask'].sv_get(deepcopy=False, default=[])

        result = vectorize(split_mesh_elements_node)(vertices=vertices, edges=edges, faces=faces, mask=mask,
                                                     mask_mode=[self.mask_mode], split_type=[self.split_type])

        self.outputs['Vertices'].sv_set(result['vertices'])
        self.outputs['Edges'].sv_set(result['edges'])
        self.outputs['Faces'].sv_set(result['faces'])


register, unregister = bpy.utils.register_classes_factory([SvSplitMeshElements])
