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


class SvDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Special attribute for keeping meta data which helps to unwrap dictionaries properly for `dictionary out` node
        This attribute should be set only by nodes which create new dictionaries or change existing one
        Order of keys in `self.inputs` dictionary should be the same as order of input data of the dictionary
        `self.inputs` dictionary should keep data in next format:
        {data.id:  # it helps to track data, if is changed `dictionary out` recreate new socket for this data
            {'type': any socket type with which input data is related,
             'name': name of output socket,
             'nest': only for 'SvDictionarySocket' type, should keep dictionary with the same data structure
             }}
             
        For example, there is the dictionary:
        dict('My values': [0,1,2], 'My vertices': [(0,0,0), (1,0,0), (0,1,0)])
        
        Metadata should look in this way:
        self.inputs = {'Values id':
                           {'type': 'SvStringsSocket',
                           {'name': 'My values',
                           {'nest': None
                           }
                      'Vertices id':
                          {'type': 'SvVerticesSocket',
                          {'name': 'My vertices',
                          {'nest': None
                          }
                      }
        """
        self.inputs = dict()


class SvDictionaryIn(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Put given data to dictionary with custom key

    Each key should be unique
    Can have nested dictionaries
    """
    bl_idname = 'SvDictionaryIn'
    bl_label = 'Dictionary in'
    bl_icon = 'GREASEPENCIL'

    def update_node(self, context):
        if not self['update_event']:
            updateNode(self, context)

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
    alert: bpy.props.BoolVectorProperty(size=10)
    key_0: bpy.props.StringProperty(name="", default='Key 1', update=update_node)
    key_1: bpy.props.StringProperty(name="", default='Key 2', update=update_node)
    key_2: bpy.props.StringProperty(name="", default='Key 3', update=update_node)
    key_3: bpy.props.StringProperty(name="", default='Key 4', update=update_node)
    key_4: bpy.props.StringProperty(name="", default='Key 5', update=update_node)
    key_5: bpy.props.StringProperty(name="", default='Key 6', update=update_node)
    key_6: bpy.props.StringProperty(name="", default='Key 7', update=update_node)
    key_7: bpy.props.StringProperty(name="", default='Key 8', update=update_node)
    key_8: bpy.props.StringProperty(name="", default='Key 9', update=update_node)
    key_9: bpy.props.StringProperty(name="", default='Key 10', update=update_node)

    def sv_init(self, context):
        self.inputs.new('SvSeparatorSocket', 'Empty')
        self.outputs.new('SvDictionarySocket', 'Dict')
        self['update_event'] = False  # if True the node does not update upon properties changes

    def update(self):
        # Remove unused sockets
        [self.inputs.remove(sock) for sock in list(self.inputs)[:-1] if not sock.is_linked]

        # add property to new socket and add extra empty socket
        free_keys = self.keys - set(sock.prop_name for sock in list(self.inputs)[:-1])
        if list(self.inputs)[-1].is_linked and len(self.inputs) < 11:
            socket_from = self.inputs[-1].other
            self.inputs.remove(list(self.inputs)[-1])
            re_socket = self.inputs.new(socket_from.bl_idname, 'Data')
            re_socket.sv_is_linked = True
            re_socket.prop_name = free_keys.pop()
            re_socket.custom_draw = 'draw_socket'
            re_link = self.id_data.links.new(socket_from, re_socket)
            re_link.is_valid = True
            self.inputs.new('SvSeparatorSocket', 'Empty')
            self['update_event'] = True
            setattr(self, re_socket.prop_name, re_socket.other.name)
            self['update_event'] = False

    def draw_socket(self, socket, context, layout):
        layout.prop(self, 'up', text='', icon='TRIA_UP')
        layout.prop(self, 'down', text='', icon='TRIA_DOWN')
        layout.alert = self.alert[int(socket.prop_name.rsplit('_', 1)[-1])]
        layout.prop(self, socket.prop_name)

    def validate_names(self):
        # light string properties with equal keys
        used_names = set()
        invalid_names = set()
        for sock in list(self.inputs)[:-1]:
            name = getattr(self, sock.prop_name)
            if name not in used_names:
                used_names.add(name)
            else:
                invalid_names.add(name)
        for sock in list(self.inputs)[:-1]:
            if getattr(self, sock.prop_name) in invalid_names:
                self.alert[int(sock.prop_name.rsplit('_', 1)[-1])] = True
            else:
                self.alert[int(sock.prop_name.rsplit('_', 1)[-1])] = False

    def process(self):

        if not any((sock.links for sock in self.inputs)):
            return

        self.validate_names()

        max_len = max([len(sock.sv_get()) for sock in list(self.inputs)[:-1]])
        data = [chain(sock.sv_get(), cycle([None])) for sock in list(self.inputs)[:-1]]
        keys = [sock.prop_name for sock in list(self.inputs)[:-1]]
        out = []
        for i, *props in zip(range(max_len), *data):
            out_dict = SvDict({getattr(self, key): prop for key, prop in zip(keys, props) if prop is not None})
            for sock in list(self.inputs)[:-1]:
                out_dict.inputs[sock.identifier] = {
                    'type': sock.bl_idname,
                    'name': getattr(self, sock.prop_name),
                    'nest': sock.sv_get()[0].inputs if sock.bl_idname == 'SvDictionarySocket' else None}
            out.append(out_dict)
        self.outputs[0].sv_set(out)


def register():
    [bpy.utils.register_class(cl) for cl in [SvDictionaryIn]]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in [SvDictionaryIn][::-1]]
