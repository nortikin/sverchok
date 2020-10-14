 # This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (list_match_func, list_match_modes, zip_long_repeat, multi_socket, updateNode, levels_of_list_or_np)

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

def match_and_join(slots, level, wrap, match_func):
    result = []
    if level == 1:
        for sb in slots:
            result.extend([sb] if wrap else sb)
    else:
        for s in zip(*match_func(slots)):
            result.append(match_and_join(s, level-1, wrap, match_func))

    return result

def match_and_join_mix(slots, level, wrap, match_func):
    result = []
    if level == 1:
        for sb in zip(*slots):
            result.extend([sb] if wrap else sb)
    else:
        for s in zip(*match_func(slots)):
            result.append(match_and_join_mix(s, level-1, wrap, match_func))

    return result


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
        name='Mix', description='Grouping similar to zip()',
        default=False, update=updateNode)

    wrap_check: BoolProperty(
        name='Wrap', description='Grouping similar to append(list)',
        default=False, update=updateNode)

    match_and_join: BoolProperty(
        name='Match', description='Grouping similar to zip()',
        default=False, update=updateNode)

    list_match: EnumProperty(
        name="Match",
        description="Behavior on different list lengths",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

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
        if self.numpy_mode:
            layout.prop(self, "mix_check", text="mix")
        else:
            if self.match_and_join:
                row1 = layout.row()
                row1.prop(self, "match_and_join")
                row1.prop(self, "list_match", text="")
            else:
                layout.prop(self, "match_and_join")

            row = layout.row()
            row.prop(self, "mix_check", text="Mix")
            row.prop(self, "wrap_check", text="Wrap")
        layout.prop(self, "JoinLevel", text="JoinLevel lists")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "numpy_mode", toggle=False, text='NumPy mode')

    def rclick_menu(self, context, layout):
        if self.numpy_mode:
            layout.prop(self, "mix_check", text="mix")
        else:
            if self.match_and_join:
                row1 = layout.row()
                row1.prop(self, "match_and_join")
                layout.prop_menu_enum(self, "list_match", text="Match method")
            else:
                layout.prop(self, "match_and_join")


            layout.prop(self, "mix_check", text="Mix")
            layout.prop(self, "wrap_check", text="Wrap")
        layout.prop(self, "JoinLevel", text="JoinLevel lists")
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
        if self.match_and_join:
            match_func = list_match_func[self.list_match]
            if self.mix_check:
                result = match_and_join_mix(slots, self.JoinLevel, self.wrap_check, match_func)
            else:
                result = match_and_join(slots, self.JoinLevel, self.wrap_check, match_func)
        else:
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
