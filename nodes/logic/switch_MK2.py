# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from itertools import repeat, chain, compress

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import get_other_socket, updateNode, replace_socket, match_long_repeat


def switch_data(state, a, b):
    """
    Merge data from a and b inputs according bool value(s) of state input
    :param state: list of bool values or numpy bool array
    :param a: any SV object like: list of values, list of vectors, matrix, Blender object, numpy array, None, []
    :param b: any SV object like: list of values, list of vectors, matrix, Blender object, numpy array, None, []
    :return: merged list of a and b inputs
    """
    a = None if hasattr(a, '__iter__') and len(a) == 0 else a
    b = None if hasattr(b, '__iter__') and len(b) == 0 else b
    if all([isinstance(a, np.ndarray), isinstance(b, np.ndarray)]) or \
            (any([isinstance(a, np.ndarray), isinstance(b, np.ndarray)]) and
                (any([a is None, b is None]) or
                 any([hasattr(a, '__iter__') and len(a) == 1, hasattr(b, '__iter__') and len(b) == 1]))):
        return switch_data_np(state, a, b)

    max_len = max([len(x) for x in [state, a, b] if hasattr(x, '__iter__')])
    iter_s = state if len(state) >= max_len else chain(state, repeat(state[-1], max_len - len(state)))
    iter_a = None if not hasattr(a, '__iter__') else \
                a if len(a) >= max_len else chain(a, repeat(a[-1], max_len - len(a)))
    iter_b = None if not hasattr(b, '__iter__') else \
                b if len(b) >= max_len else chain(b, repeat(b[-1], max_len - len(b)))

    if iter_a is not None and iter_b is not None:
        return [a if s else b for s, a, b in zip(iter_s, iter_a, iter_b)]
    elif iter_a is not None or iter_b is not None:
        if b is None:
            return list(compress(iter_a, iter_s))
        elif a is None:
            return list(compress(iter_b, (not s for s in iter_s)))
        else:
            return a if state[0] else b
    else:
        a = [] if a is None else a
        b = [] if b is None else b
        return a if state[0] else b


def switch_data_np(states, a, b):
    """
    Merge data from a and b inputs according bool value(s) of state input
    a or b should be numpy array
    :param states: list of bool values
    :param a: numpy array or None or [one value]
    :param b: numpy array or None or [one value]
    :return: merged numpy array
    """
    max_len = max([ar.shape[0] for ar in [a, b] if isinstance(ar, np.ndarray)] + [len(states)])
    states = np.concatenate((np.array(states, dtype=bool), np.full(max_len - len(states), bool(states[-1]))))
    if isinstance(a, np.ndarray):
        a = a if a.shape[0] == max_len else np.concatenate((a, np.full(max_len - a.shape[0], a[-1])))
    elif hasattr(a, '__iter__'):
        a = np.full(max_len, a[-1])
    if isinstance(b, np.ndarray):
        b = b if b.shape[0] == max_len else np.concatenate((b, np.full(max_len - b.shape[0], b[-1])))
    elif hasattr(b, '__iter__'):
        b = np.full(max_len, b[-1])

    if a is None or b is None:
        return np.compress(states, a) if b is None else np.compress(~states, b)
    elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        return np.where(states, a, b)
    else:
        raise ValueError(f"Wrong input type of a-{type(a)} or b-{type(b)}, ndarray, None or bool expected")


class SvSwitchNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Switch MK2
    Tooltip: This version is more clever of previous one

    You can deal with empty data connected to input sockets (True or False)
    """
    bl_idname = 'SvSwitchNodeMK2'
    bl_label = 'Switch'
    bl_icon = 'ACTION_TWEAK'
    sv_icon = 'SV_SWITCH'

    input_items = [("True", "True", "", 0),
                   ("False", "False", "", 1),
                   ("None", "None", "", 2)]

    py_items = {"True": [[True]], "False": [[False]], "None": [None]}

    def update_node(self, context):
        with self.sv_throttle_tree_update():
            self.rebuild_out_sockets()
        updateNode(self, context)

    def change_sockets(self, context):
        with self.sv_throttle_tree_update():
            pre_num = len(self.inputs) // 2
            diff = self.socket_number - pre_num
            if diff > 0:
                for i in range(diff):
                    num = pre_num + i
                    self.inputs.new("SvStringsSocket", f'A_{num}').prop_name = f'A_{num}'
                    self.inputs.new("SvStringsSocket", f'B_{num}').prop_name = f'B_{num}'
                    self.outputs.new("SvStringsSocket", f"Out_{num}")

            elif diff < 0:
                for i in range(abs(diff)):
                    self.inputs.remove(self.inputs[-1])
                    self.inputs.remove(self.inputs[-1])
                    self.outputs.remove(self.outputs[-1])

    def rebuild_out_sockets(self):
        links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
        self.outputs.clear()
        new_socks = []
        for i, (sock_a, sock_b) in enumerate(zip(list(self.inputs)[1::2], list(self.inputs)[2::2])):
            sock_a_link = get_other_socket(sock_a) if sock_a.links else None
            sock_b_link = get_other_socket(sock_b) if sock_b.links else None
            if sock_a_link and sock_b_link:
                if sock_a_link.bl_idname == sock_b_link.bl_idname:
                    new_socks.append(self.outputs.new(sock_a_link.bl_idname, f"Out_{i}"))
                else:
                    new_socks.append(self.outputs.new("SvStringsSocket", f"Out_{i}"))
            elif sock_a_link and getattr(self, sock_b.prop_name) == 'None':
                new_socks.append(self.outputs.new(sock_a_link.bl_idname, f"Out_{i}"))
            elif sock_b_link and getattr(self, sock_a.prop_name) == 'None':
                new_socks.append(self.outputs.new(sock_b_link.bl_idname, f"Out_{i}"))
            else:
                new_socks.append(self.outputs.new("SvStringsSocket", f"Out_{i}"))
        new_links = [self.id_data.links.new(sock, other_socket) for sock in new_socks if sock.name in links
                                                                for other_socket in links[sock.name]]
        for link in new_links:
            link.is_valid = True

    switch_state: bpy.props.EnumProperty(items=input_items[:2], name="state", default="False", update=update_node)
    socket_number: bpy.props.IntProperty(name="count", min=1, max=10, default=1, update=change_sockets)

    for i in range(10):
        vars()['__annotations__'][f'A_{i}'] = bpy.props.EnumProperty(items=input_items, name=f'A_{i}', default="True",
                                                                     update=update_node)
        vars()['__annotations__'][f'B_{i}'] = bpy.props.EnumProperty(items=input_items, name=f'B_{i}', default="False",
                                                                     update=update_node)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "State").prop_name = 'switch_state'
        self.inputs.new("SvStringsSocket", "A_0").prop_name = 'A_0'
        self.inputs.new("SvStringsSocket", "B_0").prop_name = 'B_0'
        self.outputs.new("SvStringsSocket", "Out_0")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'socket_number', text="in/out number")

    def update(self):
        if not self.id_data.skip_tree_update:
            self.rebuild_out_sockets()

    def process(self):
        for sock_a, sock_b, sock_out in zip(list(self.inputs)[1::2], list(self.inputs)[2::2], self.outputs):
            state = self.inputs[0].sv_get() if self.inputs[0].is_linked else self.py_items[self.switch_state]
            data_a = sock_a.sv_get() if sock_a.is_linked else self.py_items[getattr(self, sock_a.prop_name)]
            data_b = sock_b.sv_get() if sock_b.is_linked else self.py_items[getattr(self, sock_b.prop_name)]
            out = []
            for s, a, b in zip(*match_long_repeat([state, data_a, data_b])):
                out.append(switch_data(s, a, b))
            sock_out.sv_set(out)


def register():
    bpy.utils.register_class(SvSwitchNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvSwitchNodeMK2)
