# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import List, Dict

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last, fixed_iter


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


class SvSplitMeshElements(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers:

    todo
    """
    bl_idname = 'SvSplitMeshElements'
    bl_label = 'Split mesh elements'
    bl_icon = 'MOD_EDGESPLIT'

    select_mode_items = [(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]

    mask_mode = bpy.props.EnumProperty(items=select_mode_items, update=updateNode)
    split_type = bpy.props.EnumProperty(items=[(i, i, '') for i in ['verts', 'edges']], update=updateNode)

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

        obj_n = max(map(len, (vertices, edges, faces, mask)))

        out = []
        for v, e, f, m in zip(fixed_iter(vertices, obj_n), fixed_iter(edges, obj_n, None),
                              fixed_iter(faces, obj_n, None), fixed_iter(mask, obj_n, None)):
            if self.split_type == 'verts':
                out.append(split_by_vertices(v, e, f, m))

        v, e, f = zip(*out) if out else ([], [], [])
        self.outputs['Vertices'].sv_set(v)
        self.outputs['Edges'].sv_set(e)
        self.outputs['Faces'].sv_set(f)


register, unregister = bpy.utils.register_classes_factory([SvSplitMeshElements])
