# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import chain, cycle

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


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
        if self.modes == 'Custom':
            set_hide(self.inputs['Verts'], False)
        else:
            set_hide(self.inputs['Verts'], True)

    modes: bpy.props.EnumProperty(items=[(n, n, '') for n in ('X', 'Y', 'Z', 'Custom')], default='Z',
                                  update=update_node)
    vector: bpy.props.FloatVectorProperty(default=(0.0, 0.0, 1.0), subtype='DIRECTION', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'vector', text='')

    def draw_socket(self, socket, context, layout):
        layout.prop(self, 'modes', expand=True)

    def sv_init(self, context):
        sock_in = self.inputs.new('SvVerticesSocket', 'Verts')
        sock_in.prop_name = 'vector'
        sock_in.hide = True
        self.outputs.new('SvVerticesSocket', 'Verts').custom_draw = 'draw_socket'

    def process(self):
        self.outputs['Verts'].sv_set(self.inputs['Verts'].sv_get())


def register():
    bpy.utils.register_class(SvVectorNormalIn)


def unregister():
    bpy.utils.unregister_class(SvVectorNormalIn)
