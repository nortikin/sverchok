# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import chain, cycle

import bpy
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def unwrap_mesh(verts, faces):
    bm = bmesh.new()
    bm_verts = [bm.verts.new(co) for co in verts]
    bm_faces = [bm.faces.new([bm_verts[i] for i in face]) for face in faces]

    # todo pre unwrap ???

    f_act = bm_faces[0]
    uv_act = bm.loops.layers.uv.new('node')

    for loop in (loop for face in bm_faces for loop in face.loops):
        loop[uv_act].uv = loop.vert.co.to_2d()

    if f_act is None:
        # todo note useful for the node
        print("No active face")
        return
    elif len(f_act.verts) != 4:
        print("Active face must be a quad")
        return

    # todo add selection
    # faces = [f for f in bm.faces if f.select and len(f.verts) == 4]
    faces = [f for f in bm.faces if len(f.verts) == 4]

    # -------------------------------------------
    # Calculate average length per loop if needed

    # if EXTEND_MODE == 'LENGTH_AVERAGE':
    #     bm.edges.index_update()
    #     edge_lengths = [None] * len(bm.edges)
    #
    #     for f in faces:
    #         # we know its a quad
    #         l_quad = f.loops[:]
    #         l_pair_a = (l_quad[0], l_quad[2])
    #         l_pair_b = (l_quad[1], l_quad[3])
    #
    #         for l_pair in (l_pair_a, l_pair_b):
    #             if edge_lengths[l_pair[0].edge.index] is None:
    #
    #                 edge_length_store = [-1.0]
    #                 edge_length_accum = 0.0
    #                 edge_length_total = 0
    #
    #                 for l in l_pair:
    #                     if edge_lengths[l.edge.index] is None:
    #                         for e in walk_edgeloop(l):
    #                             if edge_lengths[e.index] is None:
    #                                 edge_lengths[e.index] = edge_length_store
    #                                 edge_length_accum += e.calc_length()
    #                                 edge_length_total += 1
    #
    #                 edge_length_store[0] = edge_length_accum / edge_length_total

    # done with average length
    # ------------------------

    walk_face_init(bm, faces, f_act)
    for f_triple in walk_face(f_act):
        apply_uv(*f_triple, uv_act)

    bm.verts.index_update()
    v_indexes = iter(range(100000000000))
    return [loop[uv_act].uv.to_3d()[:] for face in bm.faces for loop in face.loops], [[next(v_indexes) for _ in face.verts] for face in bm.faces]


def walk_face_init(bm, faces, f_act):
    # our own local walker
    # first tag all faces True (so we dont uvmap them)
    for f in bm.faces:
        f.tag = True
    # then tag faces arg False
    for f in faces:
        f.tag = False
    # tag the active face True since we begin there
    f_act.tag = True


def walk_face(f):
    # all faces in this list must be tagged
    f.tag = True
    faces_a = [f]
    faces_b = []

    while faces_a:
        for f in faces_a:
            for l in f.loops:
                l_edge = l.edge
                if (l_edge.is_manifold is True) and (l_edge.seam is False):
                    l_other = l.link_loop_radial_next
                    f_other = l_other.face
                    if not f_other.tag:
                        yield (f, l, f_other)
                        f_other.tag = True
                        faces_b.append(f_other)
        # swap
        faces_a, faces_b = faces_b, faces_a
        faces_b.clear()


def walk_edgeloop(l):
    """
    Could make this a generic function
    """
    e_first = l.edge
    e = None
    while True:
        e = l.edge
        yield e

        # don't step past non-manifold edges
        if e.is_manifold:
            # welk around the quad and then onto the next face
            l = l.link_loop_radial_next
            if len(l.face.verts) == 4:
                l = l.link_loop_next.link_loop_next
                if l.edge is e_first:
                    break
            else:
                break
        else:
            break


def extrapolate_uv(fac,
                   l_a_outer, l_a_inner,
                   l_b_outer, l_b_inner):
    l_b_inner[:] = l_a_inner
    l_b_outer[:] = l_a_inner + ((l_a_inner - l_a_outer) * fac)


def apply_uv(f_prev, l_prev, f_next, uv_act):
    l_a = [None, None, None, None]
    l_b = [None, None, None, None]

    l_a[0] = l_prev
    l_a[1] = l_a[0].link_loop_next
    l_a[2] = l_a[1].link_loop_next
    l_a[3] = l_a[2].link_loop_next

    #  l_b
    #  +-----------+
    #  |(3)        |(2)
    #  |           |
    #  |l_next(0)  |(1)
    #  +-----------+
    #        ^
    #  l_a   |
    #  +-----------+
    #  |l_prev(0)  |(1)
    #  |    (f)    |
    #  |(3)        |(2)
    #  +-----------+
    #  copy from this face to the one above.

    # get the other loops
    l_next = l_prev.link_loop_radial_next
    if l_next.vert != l_prev.vert:
        l_b[1] = l_next
        l_b[0] = l_b[1].link_loop_next
        l_b[3] = l_b[0].link_loop_next
        l_b[2] = l_b[3].link_loop_next
    else:
        l_b[0] = l_next
        l_b[1] = l_b[0].link_loop_next
        l_b[2] = l_b[1].link_loop_next
        l_b[3] = l_b[2].link_loop_next

    l_a_uv = [l[uv_act].uv for l in l_a]
    l_b_uv = [l[uv_act].uv for l in l_b]

    # if EXTEND_MODE == 'LENGTH_AVERAGE':
    #     fac = edge_lengths[l_b[2].edge.index][0] / edge_lengths[l_a[1].edge.index][0]
    # elif EXTEND_MODE == 'LENGTH':
    #     a0, b0, c0 = l_a[3].vert.co, l_a[0].vert.co, l_b[3].vert.co
    #     a1, b1, c1 = l_a[2].vert.co, l_a[1].vert.co, l_b[2].vert.co
    #
    #     d1 = (a0 - b0).length + (a1 - b1).length
    #     d2 = (b0 - c0).length + (b1 - c1).length
    #     try:
    #         fac = d2 / d1
    #     except ZeroDivisionError:
    #         fac = 1.0
    # else:
    fac = 1.0

    extrapolate_uv(fac,
                   l_a_uv[3], l_a_uv[0],
                   l_b_uv[3], l_b_uv[0])

    extrapolate_uv(fac,
                   l_a_uv[2], l_a_uv[1],
                   l_b_uv[2], l_b_uv[1])


class SvFollowActiveQuad(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    ...
    """
    bl_idname = 'SvFollowActiveQuad'
    bl_label = 'Follow active quad'
    bl_icon = 'MOD_BOOLEAN'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return

        out = []
        for v, f in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get()):
            out.append(unwrap_mesh(v, f))

        verts_out, faces_out = zip(*out)
        self.outputs['Verts'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvFollowActiveQuad)


def unregister():
    bpy.utils.unregister_class(SvFollowActiveQuad)
