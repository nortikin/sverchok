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

        if len(self.inputs) > 0:
            multi_socket(self, min=1)


    def process(self):

        if not self.outputs['data'].is_linked:
            return

        slots = []
        slot_bl_idnames = []
        for socket in self.inputs:
            if socket.is_linked and socket.links:
                if socket.other:
                    slots.append(socket.sv_get())
                    slot_bl_idnames.append(socket.other.bl_idname)

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

        self.set_output_socketype(slot_bl_idnames)
        self.outputs[0].sv_set(result)

    def set_output_socketype(self, slot_bl_idnames):
        """
        1) if the input sockets are a mixed bag of bl_idnames we convert the output socket
        to a generic SvStringsSocket type
        2) if all input sockets where sv_get is successful are of identical bl_idname
        then set the output socket type to match that.
        3) no op if current output socket matches proposed new socket type. 
        """

        if not slot_bl_idnames: return

        num_bl_idnames = len(set(slot_bl_idnames)) 
        new_socket_type = slot_bl_idnames[0] if num_bl_idnames == 1 else "SvStringsSocket"

        if self.outputs[0].bl_idname != new_socket_type:
            self.outputs[0].replace_socket(new_socket_type)

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
