# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import chain, cycle

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def get_quaternion(verts_a, verts_b):
    """
    returns quaternion which represent rotation from vertices A to vertices B
    :param verts_a: list of tuple(float, float, float)
    :param verts_b: list of tuple(float, float, float)
    :return: list of quaternions
    """
    max_len = max([len(verts_a), len(verts_b)])
    verts_a = iter_last(verts_a)
    verts_b = iter_last(verts_b)
    return [Vector(va).rotation_difference(vb) for i, va, vb in zip(range(max_len), verts_a, verts_b)]


def iter_last(l):
    return chain(l, cycle([l[-1]]))


class SvRotationDifference(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Quaternion

    creates quaternion which represent rotation from vertices A to vertices B
    """
    bl_idname = 'SvRotationDifference'
    bl_label = 'Rotation difference'
    bl_icon = 'MOD_BOOLEAN'

    vec1: bpy.props.FloatVectorProperty(default=(1, 0, 0), update=updateNode)
    vec2: bpy.props.FloatVectorProperty(default=(0, 1, 0), update=updateNode)
    is_flatten: bpy.props.BoolProperty(name="Flat output", update=updateNode, default=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'is_flatten')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts_A').prop_name = 'vec1'
        self.inputs.new('SvVerticesSocket', "Verts_B").prop_name = 'vec2'
        self.outputs.new('SvQuaternionSocket', 'Quaternions')

    def process(self):
        max_len = max([len(sock.sv_get(deepcopy=False)) for sock in self.inputs])
        inputs = [iter_last(sock.sv_get(default=False)) for sock in self.inputs]
        out = [get_quaternion(v1, v2) for i, v1, v2 in zip(range(max_len), *inputs)]
        self.outputs['Quaternions'].sv_set([q for l in out for q in l] if self.is_flatten else out)


def register():
    bpy.utils.register_class(SvRotationDifference)


def unregister():
    bpy.utils.unregister_class(SvRotationDifference)
