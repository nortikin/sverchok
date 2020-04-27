 # This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (multi_socket, updateNode, levels_of_list_or_np)

from sverchok.utils.listutils import joiner, myZip_2, wrapper_2
import numpy as np


def python_join(slots, level, mix, wrap):
    if wrap:
        if mix:
            list_mix = myZip_2(slots, level)
            list_wrap_mix = wrapper_2(slots, list_mix, level)
            result = list_wrap_mix.copy()
        else:
            list_result = joiner(slots, level)
            list_wrap = wrapper_2(slots, list_result, level)
            result = list_wrap.copy()
    else:
        if mix:
            list_mix = myZip_2(slots, level)
            result = list_mix.copy()
        else:
            list_result = joiner(slots, level)
            result = list_result.copy()
    return result

def np_object_level_2_join(slots):
    return [np.concatenate([l for s in slots for l in s], axis=0)]

def np_object_level_2_mix(slots):
    return [np.concatenate([l for s in zip(*slots) for l in zip(*s)], axis=0)]

def np_general_wrapper(slots, level, end_level, func):
    if level == end_level:
        return func(slots)
    return [np_general_wrapper(slots, level-1, end_level, func)]

def np_multi_object_level_3_join(slots):
    return [[np.concatenate([l0 for s in slots for l in s for l0 in l])]]

def np_multi_object_level_3_mix(slots):
    return [[np.concatenate([l0 for s in zip(*slots) for l in zip(*s) for l0 in zip(*l)])]]

def numpy_join(slots, level, mix, true_depth):

    if  true_depth == 1 and level > 1:
        if mix:
            return np_general_wrapper(slots, level, 2, np_object_level_2_mix)
        return np_general_wrapper(slots, level, 2, np_object_level_2_join)

    if true_depth == 2 and level > 2:
        if mix:
            return np_general_wrapper(slots, level, 3, np_multi_object_level_3_mix)
        return np_general_wrapper(slots, level, 3, np_multi_object_level_3_join)

    return python_join(slots, level, mix, False)

class ListJoinNode(bpy.types.Node, SverchCustomTreeNode):
    ''' ListJoin node '''
    bl_idname = 'ListJoinNode'
    bl_label = 'List Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_JOIN'

    JoinLevel: IntProperty(
        name='JoinLevel', description='Choose join level of data (see help)',
        default=1, min=1, update=updateNode)

    mix_check: BoolProperty(
        name='mix', description='Grouping similar to zip()',
        default=False, update=updateNode)

    wrap_check: BoolProperty(
        name='wrap', description='Grouping similar to append(list)',
        default=False, update=updateNode)

    numpy_mode: BoolProperty(
        name='NumPy Mode', description='better to work with lists of NumPy arrays',
        default=False, update=updateNode)

    typ: StringProperty(name='typ', default='')
    newsock: BoolProperty(name='newsock', default=False)


    base_name = 'data '
    multi_socket_type = 'SvStringsSocket'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'data')
        self.outputs.new('SvStringsSocket', 'data')

    def draw_buttons(self, context, layout):

        layout.prop(self, "mix_check", text="mix")
        if not self.numpy_mode:
            layout.prop(self, "wrap_check", text="wrap")
        layout.prop(self, "JoinLevel", text="JoinLevel lists")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "numpy_mode", toggle=False, text='NumPy mode')

    def rclick_menu(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "numpy_mode", toggle=True, text='NumPy mode')


    def sv_update(self):

        if len(self.outputs) > 0:
            multi_socket(self, min=1)
        self.set_output_socketype([sock.other.bl_idname for sock in self.inputs if sock.links and sock.other])

    def process(self):

        if not self.outputs['data'].links:
            return

        slots = []
        for socket in self.inputs:
            if socket.is_linked and socket.links:
                slots.append(socket.sv_get())
        if len(slots) == 0:
            return

        if self.numpy_mode:
            if self.outputs[0].bl_idname == 'SvVerticesSocket':
                min_axis = 2
            else:
                min_axis = 1
            depth = levels_of_list_or_np(slots[0])
            true_depth = depth - min_axis
            result = numpy_join(slots, self.JoinLevel, self.mix_check, true_depth)
        else:
            result = python_join(slots, self.JoinLevel, self.mix_check, self.wrap_check)

        self.outputs[0].sv_set(result)

    def set_output_socketype(self, slot_bl_idnames):
        """
        1) if the input sockets are a mixed bag of bl_idnames we convert the output socket
        to a generic SvStringsSocket type
        2) if all input sockets where sv_get is successful are of identical bl_idname
        then set the output socket type to match that.
        3) no op if current output socket matches proposed new socket type.
        """

        if not slot_bl_idnames:
            return

        num_bl_idnames = len(set(slot_bl_idnames))
        new_socket_type = slot_bl_idnames[0] if num_bl_idnames == 1 else "SvStringsSocket"

        if self.outputs[0].bl_idname != new_socket_type:
            self.outputs[0].replace_socket(new_socket_type)

    def draw_label(self):
        """ this gives quick param display for when the node is minimzed """
        mixing = "M" if self.mix_check else ""
        wrapping = "W" if self.wrap_check and not self.numpy_mode else ""
        numpy_m = "NP " if self.numpy_mode else ""
        level = str(self.JoinLevel)
        fstr = " Lv={0} {1}{2}{3}".format(level, numpy_m, mixing, wrapping)
        return self.name + fstr


def register():
    bpy.utils.register_class(ListJoinNode)


def unregister():
    bpy.utils.unregister_class(ListJoinNode)
