# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle, chain
import numpy as np

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.sv_bmesh_utils import bmesh_from_edit_mesh


def set_custom_map(obj, verts=None, faces=None, uv_name='SVMap', matrix=None):
    """
    Cretes new UV layer if need and apply given coordinates (XY) to UV layer
    :param obj: Blender mesh object
    :param verts: list of tuple(float, float, float)
    :param faces: list of list of int
    :param uv_name: name of UV layer
    :param matrix: mathutils Matrix if deformation is needed
    :return: None
    """
    verts = [] if verts is None else verts
    faces = [] if faces is None else faces

    if uv_name not in obj.data.uv_layers:
        obj.data.uv_layers.new(name=uv_name)
    if obj.mode == 'EDIT':
        set_uv_edit_mode(verts, faces, obj.data, uv_name, matrix)
    else:
        set_uv(verts, faces, obj, uv_name, matrix)
    obj.data.update()


def set_uv(verts, faces, obj, uv_name, matrix=None):
    # Apply coordinates to UV layer
    unpack_uv = np.zeros((len(obj.data.loops) * 2), dtype=float)

    in_loops = []
    # it requires checking whether given faces have the same number of loops as in the object
    # otherwise loops array of one polygon will shift to another what makes it difficult to debug
    for face, obj_face in zip(faces or [], obj.data.polygons):
        for i, _ in zip(repeat_last(face), obj_face.vertices):
            in_loops.append(verts[i])

    if verts and faces:
        for i, co in zip(range(0, len(obj.data.loops) * 2, 2), in_loops):
            uv = Vector(co[:2]) if matrix is None else (matrix @ Vector(co))[:2]
            unpack_uv[i: i+2] = uv
    obj.data.uv_layers[uv_name].data.foreach_set("uv", unpack_uv)


def set_uv_edit_mode(verts: list, faces: list, mesh: bpy.types.Mesh, uv_name: str, matrix=None):
    with bmesh_from_edit_mesh(mesh) as bm:
        uv_layer = bm.loops.layers.uv.get(uv_name)
        for f, bmf in zip(repeat_last(faces), bm.faces):
            for i, bml in zip(repeat_last(f), bmf.loops):
                co = verts[i]
                uv = Vector(co[:2]) if matrix is None else (matrix @ Vector(co))[:2]
                bml[uv_layer].uv = uv


class SvSetCustomUVMap(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: Set custom UV map to Blender mesh

    3D coordinates can be putted,
    it will works as flat projection
    """
    bl_idname = 'SvSetCustomUVMap'
    bl_label = 'Set custom UV map'
    bl_icon = 'GROUP_UVS'

    uv_name: bpy.props.StringProperty(name='Uv name', default='SVMap', description='Name of UV layer',
                                      update=updateNode)

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        layout.prop(self, 'uv_name', text='', icon='GROUP_UVS')

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('SvVerticesSocket', 'UV verts')
        self.inputs.new('SvStringsSocket', 'UV faces')
        self.inputs.new('SvMatrixSocket', 'Matrix')
        self.outputs.new('SvObjectSocket', "Objects")

    def process(self):
        if not self.inputs['Objects'].is_linked:
            return

        input = chain([self.inputs['Objects'].sv_get()],
                      [chain(sock.sv_get(deepcopy=False), cycle([sock.sv_get(deepcopy=False)[-1]]))
                       if sock.is_linked else cycle([None]) for sock in list(self.inputs)[1:]])
        for ob, v, f, m in zip(*input):
            set_custom_map(ob, v, f, self.uv_name, m)

        self.outputs['Objects'].sv_set(self.inputs['Objects'].sv_get())


def register():
    bpy.utils.register_class(SvSetCustomUVMap)


def unregister():
    bpy.utils.unregister_class(SvSetCustomUVMap)
