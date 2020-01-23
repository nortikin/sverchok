# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from collections import namedtuple

import bpy
import bmesh
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


MeshMode = namedtuple('MeshMode', ['verts', 'edges', 'faces'])
MODE = MeshMode('Verts', 'Edges', 'Faces')


def get_origin(verts, edges=None, faces=None, mode=MODE.faces):
    bm = bmesh.new(use_operators=False)
    bm_verts = [bm.verts.new(co) for co in verts]
    [bm.edges.new([bm_verts[i] for i in edge]) for edge in edges or []]
    [bm.faces.new([bm_verts[i] for i in face]) for face in faces or []]
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    if mode == MODE.verts:
        origins = [vert.co for vert in bm_verts]
        normals = [vert.normal for vert in bm_verts]
        tangents = [get_vert_tang(v) for v in bm_verts]
    elif mode == MODE.edges:
        if edges is None and faces is None:
            raise ValueError("Edges or Faces should be connected")
        origins =[e.verts[0].co.lerp(e.verts[1].co, 0.5) for e in bm.edges]
        normals, tangents = zip(*[get_edge_normal_tang(e) for e in bm.edges])
    elif mode == MODE.faces:
        if faces is None:
            raise ValueError("Faces should be connected")
        origins = [f.calc_center_median() for f in bm.faces]
        normals = [f.normal for f in bm.faces]
        tangents = [get_face_tangent(f) for f in bm.faces]
    else:
        raise ValueError(f"Unknown mode: {mode}")

    bm.free()
    matrixes = [build_matrix(orig, norm, tang) for orig, norm, tang in zip(origins, normals, tangents)]
    return [[v[:] for v in origins], [v[:] for v in normals], [v[:] for v in tangents], matrixes]


def get_vert_tang(vert):
    if len(vert.link_edges) == 2:
        return vert.link_loops[0].calc_tangent().cross(vert.normal)
    elif vert.normal == Vector((0, 0, 1)):
        return Vector((-1, 0, 0))
    elif vert.normal == Vector((0, 0, -1)):
        return Vector((1, 0, 0))
    else:
        return vert.normal.cross(vert.normal.cross(Vector((0, 0, 1)))).normalized()


def get_edge_normal_tang(edge):
    direct = (edge.verts[1].co - edge.verts[0].co).normalized()
    _normal = (edge.verts[0].normal + edge.verts[1].normal).normalized()
    tang = direct.cross(_normal)
    normal = tang.cross(direct)
    return normal, tang


def get_face_tangent(face):
    if len(face.edges) > 3:
        return face.calc_tangent_edge_pair().normalized() * -1
    else:
        return face.calc_tangent_edge_diagonal()


def build_matrix(center, normal, tangent):
    x_axis = tangent.cross(normal)
    return Matrix(list(zip(x_axis.resized(4), tangent.resized(4), normal.resized(4), center.to_4d())))


class SvOrigins(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: origin center normal tangent matrix

    ...
    ...
    """
    bl_idname = 'SvOrigins'
    bl_label = 'Origins'
    bl_icon = 'MOD_BOOLEAN'
    sv_icon = 'SV_CENTER_POLYGONS'

    mode_items = [(k, k, "", i) for i, k in enumerate(MODE)]

    mode: bpy.props.EnumProperty(items=mode_items, update=updateNode)
    flat_matrix: bpy.props.BoolProperty(default=True, name="Flat matrixes list", update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'flat_matrix')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', 'Origin')
        self.outputs.new('SvVerticesSocket', "Normal")
        self.outputs.new('SvVerticesSocket', "Tangent")
        self.outputs.new('SvMatrixSocket', "Matrix")

    def process(self):
        if not self.inputs['Verts'].is_linked:
            return
        if self.mode == MODE.faces and not self.inputs['Faces'].is_linked:
            return
        if self.mode == MODE.edges and not any([self.inputs[n].is_linked for n in ['Edges', 'Faces']]):
            return

        out = []
        for v, e, f in zip(*[sock.sv_get(deepcopy=False, default=[None]) for sock in self.inputs]):
            out.append(get_origin(v, e, f, self.mode))
        if self.flat_matrix:
            [sock.sv_set(data) for sock, data in zip(self.outputs[0:-1], zip(*out))]
            self.outputs['Matrix'].sv_set([m for data_set in out for m in data_set[-1]])
        else:
            [sock.sv_set(data) for sock, data in zip(self.outputs, zip(*out))]


def register():
    bpy.utils.register_class(SvOrigins)


def unregister():
    bpy.utils.unregister_class(SvOrigins)
