# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import chain, cycle

from collections import namedtuple
from math import pi

import bpy
from mathutils import Quaternion, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


Modes = namedtuple('Modes', ['x', 'y', 'z', 'custom'])
MODE = Modes('X', 'Y', 'Z', 'Custom')
MODE_DIR = Modes(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), None)

QUAT_X90 = Quaternion((1, 0, 0), pi / 2)
QUAT_Y270 = Quaternion((0, 1, 0), -pi / 2)


def get_costume_norm(normal, space_normal, mode=MODE.z):
    space_normal = Vector(space_normal).normalized() if mode == MODE.custom else getattr(MODE_DIR, mode.lower())
    if space_normal == MODE_DIR.z:
        return [normal[:]]
    quat_rotation_xy = Vector((0, -1, 0)).rotation_difference(Vector(space_normal[:2] + (0,)))
    quat_rotation_z = Vector(space_normal[:2] + (0,)).rotation_difference(space_normal)
    quat_rotation = quat_rotation_z @ quat_rotation_xy
    quat = quat_rotation @ QUAT_X90
    if space_normal == MODE_DIR.y:
        #corner case for quaternion
        quat = QUAT_Y270 @ quat
    return [(quat @ normal)[:]]


class SvVectorNormalIn(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: normal

    ...
    ...
    """
    bl_idname = 'SvVectorNormalIn'
    bl_label = 'Vector Normal In'
    bl_icon = 'MOD_BOOLEAN'

    def update_node(self, context):
        def set_hide(socket, state):
            if state != socket.hide:
                socket.hide = state
        if self.mode == 'Custom':
            set_hide(self.inputs['Verts'], False)
        else:
            set_hide(self.inputs['Verts'], True)
        updateNode(self, context)

    mode: bpy.props.EnumProperty(items=[(n, n, '') for n in ('X', 'Y', 'Z', 'Custom')], default='Z',
                                  update=update_node)
    vector: bpy.props.FloatVectorProperty(default=(0.0, 0.0, 1.0), subtype='DIRECTION', update=updateNode)
    custom_vector: bpy.props.FloatVectorProperty(default=(0.0, 0.0, 1.0), update=updateNode)
    draw_3dpanel: bpy.props.BoolProperty(name='Show in 3d panel',
                                         description='Show items of this node in 3d panel of 3d view screen')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'vector', text='')

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'vector', text='Normal', expand=True)
        layout.prop(self, 'draw_3dpanel')

    def draw_socket(self, socket, context, layout):
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_3dpanel(self, layout):
        layout.label(text=f"{self.label or self.name}")
        layout.prop(self, 'vector', text='')

    def sv_init(self, context):
        sock_in = self.inputs.new('SvVerticesSocket', 'Verts')
        sock_in.prop_name = 'custom_vector'
        sock_in.hide = True
        self.outputs.new('SvVerticesSocket', 'Verts').custom_draw = 'draw_socket'

    def process(self):
        out = []
        for space in self.inputs['Verts'].sv_get(deepcopy=False):
            out.append(get_costume_norm(self.vector, space[0], self.mode))
        self.outputs['Verts'].sv_set(out)


def register():
    bpy.utils.register_class(SvVectorNormalIn)


def unregister():
    bpy.utils.unregister_class(SvVectorNormalIn)
