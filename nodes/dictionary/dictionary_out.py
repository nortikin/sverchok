# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import chain, cycle

import bpy
from mathutils import Matrix, Quaternion

from sverchok.node_tree import SverchCustomTreeNode


def get_socket_type(data, sub_cls=None, size=None):
    """
    If input dictionary does not have metadata
    this function is used for determining type of output socket according given data type
    :param data: any data
    :param sub_cls: always None, for internal usage only
    :param size: always None, for internal usage only
    :return: returns one of Sverchok socket type, string
    """
    types = {bpy.types.Object: 'SvObjectSocket',
             Matrix: 'SvMatrixSocket',
             Quaternion: 'SvQuaternionSocket',
             float: ('SvStringsSocket', 'SvVerticesSocket', 'SvColorSocket'),
             int: 'SvStringsSocket'}

    if type(data) is dict:
        return 'SvDictionarySocket'
    if hasattr(data, '__iter__'):
        return get_socket_type(data[0], type(data), len(data))
    elif type(data) in types:
        socket_type = types[type(data)]
        if socket_type == ('SvStringsSocket', 'SvVerticesSocket', 'SvColorSocket'):
            if sub_cls is tuple:
                return 'SvVerticesSocket' if size == 3 else 'SvColorSocket'
            else:
                return 'SvStringsSocket'
        else:
            return socket_type
    else:
        raise TypeError(f"Which type of socket this type ({type(data)}) of data should be?")


class SvDictionaryOut(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Unwrap given dictionary

    For each key of dictionary new socket is created
    Keys of first given dictionary in a list are taken in account
    """
    bl_idname = 'SvDictionaryOut'
    bl_label = 'Dictionary out'
    bl_icon = 'OUTLINER_DATA_GP_LAYER'

    def sv_init(self, context):
        self.inputs.new('SvDictionarySocket', 'Dict')
        self['order'] = []  # keeps keys of given dictionary since last update event

    def update(self):
        if not self.id_data.skip_tree_update:
            if self.inputs['Dict'].links:  # if link is unconnected from the socket, `is_linked` is steal True
                self.rebuild_output()
            else:
                self.outputs.clear()
                self['order'] = []

    def rebuild_output(self):
        # draw output sockets according given keys of input dictionary
        # dictionary with metadata kept in `inputs` attribute can be handled
        # this can be called during node update event and from process of the node (after update event)
        out_dict = self.inputs['Dict'].sv_get()[0]
        if hasattr(out_dict, 'inputs'):
            # handle dictionary with metadata
            if self['order'] != list(out_dict.inputs.keys()):
                # order is changed, sockets should be rebuild
                with self.sv_throttle_tree_update():
                    links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
                    self.outputs.clear()
                    new_order = []
                    new_socks = []
                    for key, data in out_dict.inputs.items():
                        sock = self.outputs.new(data['type'], data['name'])
                        new_order.append(key)
                        new_socks.append(sock)
                    self['order'] = new_order
                    [self.id_data.links.new(sock, other_socket) for sock in new_socks if sock.name in links
                                                                for other_socket in links[sock.name]]
            else:
                # order is unchanged but renaming of sockets should be done anywhere
                # in case keys of a dictionary was changed
                for sock, sock_id in zip(self.outputs, self['order']):
                    sock.name = out_dict.inputs[sock_id]['name']
        else:
            # handle dictionary without metadata
            if self['order'] != list(self.inputs['Dict'].sv_get()[0].keys()):
                with self.sv_throttle_tree_update():
                    links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
                    self.outputs.clear()
                    new_socks = [self.outputs.new(get_socket_type(data), key) for key, data in
                                 self.inputs['Dict'].sv_get()[0].items()]
                    self['order'] = list(self.inputs['Dict'].sv_get()[0].keys())
                    [self.id_data.links.new(sock, other_socket) for sock in new_socks if sock.name in links
                                                                for other_socket in links[sock.name]]

    def process(self):

        if not self.inputs['Dict'].links:
            return

        self.rebuild_output()

        out = {key: [] for key in self.inputs['Dict'].sv_get()[0]}
        for d in self.inputs['Dict'].sv_get():
            for key in d:
                if key in out:
                    out[key].append(d[key])

        [self.outputs[key].sv_set(out[key]) for key in out if key in self.outputs]


def register():
    [bpy.utils.register_class(cl) for cl in [SvDictionaryOut]]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in [SvDictionaryOut][::-1]]
