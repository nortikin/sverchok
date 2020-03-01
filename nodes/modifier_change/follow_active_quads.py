# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle, chain
from collections import namedtuple

import bpy
import bmesh
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


Modes = namedtuple('Modes', ['even', 'length', 'average'])
MODE = Modes('Even', 'Length', 'Average')


def unwrap_mesh(verts, faces, active_indexes, uv_verts=None, uv_faces=None, face_mask=None, mode=MODE.even):
    """
    Unwrap mesh similar to Blender operator: follow active quad
    :param verts: list of tuple(float, float, float)
    :param faces: list of list of int
    :param active_indexes: list of indexes, arbitrary number
    :param uv_verts: list of tuple(float, float, float), only XY ate taken in account
    :param uv_faces: list of list of int, in the same order as faces input
    :param face_mask: list of bool, for selecting unwrapping faces
    :param mode: 'even', 'length' or 'average'
    :return: list of tuple(float, float, float), list of list of int (faces indexes)
    """
    bm = bmesh.new()
    # create layer for marking unwrapped faces for protection from re unwrapping, should be done before mesh generation
    used_layer = bm.faces.layers.int.new('uv done')
    bm_verts = [bm.verts.new(co) for co in verts]
    bm_faces = [bm.faces.new([bm_verts[i] for i in face]) for face in faces]

    # get active faces
    f_acts = []
    for ai in active_indexes:
        if ai < len(faces) and len(bm_faces[ai].verts) == 4 and (True if face_mask is None else face_mask[ai]):
            f_acts.append(bm_faces[ai])
    if not f_acts:
        raise LookupError("Given indexes point to faces which are not quads"
                          " or does not mark by mask if face mask was given.")

    # create and apply given UC coordinates to bmesh
    uv_act = bm.loops.layers.uv.new('node')
    if uv_verts and uv_faces:
        for face, uv_face in zip(bm_faces, uv_faces):
            for loop, uv_i in zip(face.loops, uv_face):
                loop[uv_act].uv = uv_verts[uv_i][:2]

    # unwrap active face if they does not have UV map
    for fa in f_acts:
        if all([loop[uv_act].uv == Vector((0, 0)) for loop in fa.loops]):
            for loop, co in zip(fa.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uv_act].uv = co

    # Select faces
    faces = [f for i, f in enumerate(bm_faces) if len(f.verts) == 4 and (True if face_mask is None else face_mask[i])]

    # prepare help data
    if mode == MODE.average:
        edge_lengths = calc_average_length(bm, faces)
    else:
        edge_lengths = None

    # process
    for fa in f_acts:
        if fa[used_layer] == 0:
            walk_face_init(bm, faces, fa)
            for f_triple in walk_face(fa, used_layer):
                apply_uv(*f_triple, uv_act, mode, edge_lengths)

    # prepare output
    bm.verts.index_update()
    v_indexes = iter(range(100000000000))
    uv_vert_out = (loop[uv_act].uv.to_3d()[:] for face in bm.faces for loop in face.loops)
    uv_face_out = ([next(v_indexes) for _ in face.verts] for face in bm.faces)
    return list(uv_vert_out), list(uv_face_out)


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


def walk_face(f, used_layer):
    # all faces in this list must be tagged
    f.tag = True
    faces_a = [f]
    faces_b = []

    while faces_a:
        for f in faces_a:
            f[used_layer] = 1
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


def apply_uv(f_prev, l_prev, f_next, uv_act, mode, edge_lengths=None):
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

    if mode == MODE.average:
        fac = edge_lengths[l_b[2].edge.index][0] / edge_lengths[l_a[1].edge.index][0]
    elif mode == MODE.length:
        a0, b0, c0 = l_a[3].vert.co, l_a[0].vert.co, l_b[3].vert.co
        a1, b1, c1 = l_a[2].vert.co, l_a[1].vert.co, l_b[2].vert.co

        d1 = (a0 - b0).length + (a1 - b1).length
        d2 = (b0 - c0).length + (b1 - c1).length
        try:
            fac = d2 / d1
        except ZeroDivisionError:
            fac = 1.0
    else:
        fac = 1.0

    extrapolate_uv(fac,
                   l_a_uv[3], l_a_uv[0],
                   l_b_uv[3], l_b_uv[0])

    extrapolate_uv(fac,
                   l_a_uv[2], l_a_uv[1],
                   l_b_uv[2], l_b_uv[1])


def calc_average_length(bm, faces):
    # Calculate average length per loop

    bm.edges.index_update()
    edge_lengths = [None] * len(bm.edges)

    for f in faces:
        # we know its a quad
        l_quad = f.loops[:]
        l_pair_a = (l_quad[0], l_quad[2])
        l_pair_b = (l_quad[1], l_quad[3])

        for l_pair in (l_pair_a, l_pair_b):
            if edge_lengths[l_pair[0].edge.index] is None:

                edge_length_store = [-1.0]
                edge_length_accum = 0.0
                edge_length_total = 0

                for l in l_pair:
                    if edge_lengths[l.edge.index] is None:
                        for e in walk_edgeloop(l):
                            if edge_lengths[e.index] is None:
                                edge_lengths[e.index] = edge_length_store
                                edge_length_accum += e.calc_length()
                                edge_length_total += 1

                edge_length_store[0] = edge_length_accum / edge_length_total

    return edge_lengths


class SvFollowActiveQuads(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: UV unwrapping

    As blender unwrapping function
    Can unwrap mesh  with separate parts at once
    """
    bl_idname = 'SvFollowActiveQuads'
    bl_label = 'Follow active quads'
    bl_icon = 'MOD_UVPROJECT'

    edge_length_mode: bpy.props.EnumProperty(items=[(i, i, '') for i in MODE], update=updateNode)
    active_index: bpy.props.IntProperty(name='Index active quad', min=0, update=updateNode)
    unwrap_all: bpy.props.BoolProperty(name='All', update=updateNode, description="Unwrap all disjoint parts")

    def draw_buttons(self, context, layout):
        layout.label(text='Edge length mode:')
        layout.prop(self, 'edge_length_mode', expand=True)

    def draw_socket(self, socket, context, layout):
        if socket.is_linked:
            layout.label(text=socket.name)
        else:
            row = layout.row(align=True)
            row.enabled = False if self.unwrap_all else True
            row.prop(self, 'active_index')
            row = layout.row(align=True)
            row.ui_units_x = 1.2
            row.prop(self, 'unwrap_all', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvVerticesSocket', 'UV verts')
        self.inputs.new('SvStringsSocket', "UV faces")
        self.inputs.new('SvStringsSocket', "Active quad index").custom_draw = 'draw_socket'
        self.inputs.new('SvStringsSocket', "Face mask")
        self.outputs.new('SvVerticesSocket', 'UV verts')
        self.outputs.new('SvStringsSocket', "UV faces")

    def process(self):
        if not all([sock.is_linked for sock in list(self.inputs)[:2]]):
            return

        in1 = [sock.sv_get(deepcopy=False) for sock in [self.inputs[n] for n in ('Verts', 'Faces')]]

        in2 = [chain(sock.sv_get(deepcopy=False), cycle([sock.sv_get(deepcopy=False)[-1]])) if sock.is_linked else
               cycle([None]) for sock in [self.inputs[n] for n in ('UV verts', 'UV faces', 'Face mask')]]

        in3 = [chain(sock.sv_get(deepcopy=False), cycle([sock.sv_get(deepcopy=False)[-1]])) if sock.is_linked else
               cycle([[self.active_index]]) for sock in [self.inputs[n] for n in ('Active quad index',)]]

        set_all = bool(not self.inputs['Active quad index'].is_linked and self.unwrap_all)
        out = [unwrap_mesh(v, f, range(len(f)) if set_all else i, uv_v, uv_f, m, self.edge_length_mode)
               for v, f, uv_v, uv_f, m, i in zip(*chain(in1, in2, in3))]

        [sock.sv_set(data) for sock, data in zip(self.outputs, zip(*out))]


def register():
    bpy.utils.register_class(SvFollowActiveQuads)


def unregister():
    bpy.utils.unregister_class(SvFollowActiveQuads)
