# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (changable_sockets, multi_socket, updateNode)

from sverchok.utils.listutils import joiner, myZip_2, wrapper_2

class ListJoinNode(bpy.types.Node, SverchCustomTreeNode):
    ''' ListJoin node '''
    bl_idname = 'ListJoinNode'
    bl_label = 'List Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_JOIN'

    JoinLevel: IntProperty(
        name='JoinLevel', description='Choose join level of data (see help)',
        default=1, min=1,  update=updateNode)

    mix_check: BoolProperty(
        name='mix', description='Grouping similar to zip()',
        default=False, update=updateNode)

    wrap_check: BoolProperty(
        name='wrap', description='Grouping similar to append(list)',
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
        layout.prop(self, "wrap_check", text="wrap")
        layout.prop(self, "JoinLevel", text="JoinLevel lists")

    def update(self):
        # inputs
        multi_socket(self, min=1)

        if 'data' in self.inputs and len(self.inputs['data'].links) > 0:
            inputsocketname = 'data'
            outputsocketname = ['data']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        if not self.outputs['data'].is_linked:
            return

        slots = []
        for socket in self.inputs:
            if socket.is_linked:
                slots.append(socket.sv_get())
        if len(slots) == 0:
            return

        list_result = joiner(slots, self.JoinLevel)
        result = list_result.copy()
        if self.mix_check:
            list_mix = myZip_2(slots, self.JoinLevel)
            result = list_mix.copy()

        if self.wrap_check:
            list_wrap = wrapper_2(slots, list_result, self.JoinLevel)
            result = list_wrap.copy()

            if self.mix_check:
                list_wrap_mix = wrapper_2(slots, list_mix, self.JoinLevel)
                result = list_wrap_mix.copy()

        self.outputs[0].sv_set(result)


    def draw_label(self):
        """ this gives quick param display for when the node is minimzed """
        mixing = "M" if self.mix_check else ""
        wrapping = "W" if self.wrap_check else ""
        level = str(self.JoinLevel)
        fstr = " Lv={0} {1}{2}".format(level, mixing, wrapping)
        return self.name + fstr


def register():
    bpy.utils.register_class(ListJoinNode)


def unregister():
    bpy.utils.unregister_class(ListJoinNode)
