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


class SvDictionaryIn(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...
    ...

    ...
    """
    bl_idname = 'SvDictionaryIn'
    bl_label = 'Dictionary in'
    bl_icon = 'MOD_BOOLEAN'

    def lift_item(self, context):
        if self.up:
            sock_ind = list(self.inputs).index(context.socket)
            if sock_ind > 0:
                self.inputs.move(sock_ind, sock_ind - 1)
            self.up = False

    def down_item(self, context):
        if self.down:
            sock_ind = list(self.inputs).index(context.socket)
            if sock_ind < len(self.inputs) - 2:
                self.inputs.move(sock_ind, sock_ind + 1)
            self.down = False

    keys = set(f"key_{i}" for i in range(10))

    up: bpy.props.BoolProperty(update=lift_item)
    down: bpy.props.BoolProperty(update=down_item)
    key_0: bpy.props.StringProperty(name="", default='Key 1', update=updateNode)
    key_1: bpy.props.StringProperty(name="", default='Key 2', update=updateNode)
    key_2: bpy.props.StringProperty(name="", default='Key 3', update=updateNode)
    key_3: bpy.props.StringProperty(name="", default='Key 4', update=updateNode)
    key_4: bpy.props.StringProperty(name="", default='Key 5', update=updateNode)
    key_5: bpy.props.StringProperty(name="", default='Key 6', update=updateNode)
    key_6: bpy.props.StringProperty(name="", default='Key 7', update=updateNode)
    key_7: bpy.props.StringProperty(name="", default='Key 8', update=updateNode)
    key_8: bpy.props.StringProperty(name="", default='Key 9', update=updateNode)
    key_9: bpy.props.StringProperty(name="", default='Key 10', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSeparatorSocket', 'Empty')
        self.outputs.new('SvDictionarySocket', 'Dict')['keys'] = []

    def update(self):
        print(f'Update {self.name}')
        # Remove unused sockets
        for sock in self.inputs:
            if sock.bl_idname != 'SvSeparatorSocket' and not sock.links:
                self.inputs.remove(sock)

        # add property to new socket and add extra empty socket
        free_keys = self.keys - set(sock.prop_name for sock in self.inputs if sock.bl_idname != 'SvSeparatorSocket')
        if list(self.inputs)[-1].links and len(self.inputs) < 11:
            socket_from = self.inputs[-1].other
            self.inputs.remove(list(self.inputs)[-1])
            re_socket = self.inputs.new(socket_from.bl_idname, 'Dict in sock')
            re_socket.prop_name = free_keys.pop()
            re_socket.custom_draw = 'draw_socket'
            re_link = self.id_data.links.new(socket_from, re_socket)
            re_link.is_valid = True
            self.inputs.new('SvSeparatorSocket', 'Empty')

        # set order of output data
        self.outputs['Dict']['order'] = [(getattr(self, sock.prop_name), sock.bl_idname) for sock in list(self.inputs)[:-1]]
        print("Socket order", self.outputs['Dict']['order'])

    def draw_socket(self, socket, context, layout):
        layout.prop(self, 'up', text='', icon='TRIA_UP')
        layout.prop(self, 'down', text='', icon='TRIA_DOWN')
        layout.prop(self, socket.prop_name)

    def process(self):

        if not any((sock.links for sock in self.inputs)):
            return

        max_len = max([len(sock.sv_get()) for sock in list(self.inputs)[:-1]])
        data = [chain(sock.sv_get(), cycle([None])) for sock in list(self.inputs)[:-1]]
        keys = [sock.prop_name for sock in list(self.inputs)[:-1]]
        out = []
        for i, *props in zip(range(max_len), *data):
            out.append({getattr(self, key): prop for key, prop in zip(keys, props) if prop is not None})
        self.outputs[0].sv_set(out)


def register():
    [bpy.utils.register_class(cl) for cl in [SvDictionaryIn]]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in [SvDictionaryIn][::-1]]
