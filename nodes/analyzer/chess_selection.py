# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

from sverchok.node_tree import SverchCustomTreeNode


def get_selection(verts, faces):
    """
    Returns face mask like chess board.
    :param verts: list of vertices
    :param faces: list of faces
    :return: list of bool per given face
    """
    bm = bmesh_from_pydata(verts, faces=faces)
    mark_faces(bm)
    out_mask = [face.select for face in bm.faces]
    bm.free()
    return out_mask


def mark_faces(bm):
    # https://en.wikipedia.org/wiki/Depth-first_search
    used = set()
    for face in bm.faces:
        if face in used:
            continue
        stack = [(face, 'add')]
        while stack:
            next_face, type_face = stack.pop()
            if next_face in used:
                continue
            used.add(next_face)
            if type_face == 'add':
                next_face.select = True
            for edge in next_face.edges:
                for twin_face in edge.link_faces:
                    if twin_face in used:
                        continue
                    stack.append((twin_face, 'sub' if type_face == 'add' else 'add'))


class SvChessSelection(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: returns selection like chess board
    Tooltip: can be used with 3d objects like torus and other primitives

    Topology of input mesh should be in an appropriate view for getting expecting result
    """
    bl_idname = 'SvChessSelection'
    bl_label = 'Chess selection'
    bl_icon = 'TEXTURE'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvStringsSocket', "Face mask")

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        out = []
        for v, f in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get()):
            out.append(get_selection(v, f))
        self.outputs['Face mask'].sv_set(out)


def register():
    bpy.utils.register_class(SvChessSelection)


def unregister():
    bpy.utils.unregister_class(SvChessSelection)
