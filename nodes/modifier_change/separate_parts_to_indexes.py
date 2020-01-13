# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle

import bpy
import bmesh

from sverchok.node_tree import SverchCustomTreeNode


def mark_mesh(verts, edges=None, faces=None):
    if edges is None and faces is None:
        raise ValueError("Edges or Faces should be given")

    bm = bmesh.new()
    ind_v = bm.verts.layers.int.new('SV index')
    ind_e = bm.edges.layers.int.new('SV index')
    ind_f = bm.faces.layers.int.new('SV index')
    bm_verts = [bm.verts.new(co) for co in verts]
    bm_edges = [bm.edges.new((bm_verts[i1], bm_verts[i2])) for i1, i2 in edges] if edges else None
    bm_faces = [bm.faces.new([bm_verts[i] for i in face]) for face in faces] if faces else None
    if bm_edges:
        mark_edges(bm_edges, ind_e)
    if bm_faces:
        mark_faces(bm_faces, ind_f)
    mark_verts(bm_verts, ind_v, True if edges else False, ind_e, True if faces else False, ind_f)
    v_out = [vert[ind_v] for vert in bm_verts]
    e_out = [edge[ind_e] for edge in bm_edges] if edges else []
    f_out = [face[ind_f] for face in bm_faces] if faces else []
    return v_out, e_out, f_out


def mark_edges(bm_edges, layer):
    used = set()
    current_i = 0
    for edge in bm_edges:
        if edge in used:
            continue
        stack = {edge, }
        while stack:
            e = stack.pop()
            used.add(e)
            e[layer] = current_i
            for v in e.verts:
                for next_e in v.link_edges:
                    if next_e not in used:
                        stack.add(next_e)

        current_i += 1


def mark_faces(bm_faces, layer):
    used = set()
    current_i = 0
    for face in bm_faces:
        if face in used:
            continue
        stack = {face, }
        while stack:
            f = stack.pop()
            used.add(f)
            f[layer] = current_i
            for edge in f.edges:
                for next_f in edge.link_faces:
                    if next_f not in used:
                        stack.add(next_f)

        current_i += 1


def mark_verts(bm_verts, v_layer, by_edges=False, e_layer=None, by_faces=False, f_layer=None):
    if not ((by_edges and e_layer) or (by_faces and f_layer)):
        raise ValueError("Pick edges or faces for filling index values of vertices")
    if by_edges and e_layer:
        for vert in bm_verts:
            for edge in vert.link_edges:
                vert[v_layer] = edge[e_layer]
                break
    elif by_faces and f_layer:
        for vert in bm_verts:
            for face in vert.link_faces:
                vert[v_layer] = face[f_layer]
                break


class SvSeparatePartsToIndexes(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: separate

    ...
    ...
    """
    bl_idname = 'SvSeparatePartsToIndexes'
    bl_label = 'Separate Parts To Indexes'
    bl_icon = 'MOD_BOOLEAN'
    sv_icon = 'SV_SEPARATE_LOOSE_PARTS'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', "Vert index")
        self.outputs.new('SvStringsSocket', 'Edge index')
        self.outputs.new('SvStringsSocket', "Face index")

    def process(self):
        if not (self.inputs['Verts'].is_linked and (self.inputs['Edges'].is_linked or self.inputs['Faces'].is_linked)):
            return

        out = []
        for v, e, f in zip(*[sock.sv_get(deepcopy=False) if sock.is_linked else cycle([None]) for sock in self.inputs]):
            out.append(mark_mesh(v, e, f))
        [sock.sv_set(data) for sock, data in zip(self.outputs, zip(*out))]


def register():
    bpy.utils.register_class(SvSeparatePartsToIndexes)


def unregister():
    bpy.utils.unregister_class(SvSeparatePartsToIndexes)
