# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty
import bmesh
from mathutils import Vector

from node_tree import SverchCustomTreeNode, VerticesSocket, StringsSocket
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


# class DrawHTML(object):

#     def __init__(self, node):
#         pass

#     def populate_html(self):
#         pass

#     def get_html(self):
#         return self.html


class WebModalTimerOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.web_modal_timer_operator"
    bl_label = "Web Modal Timer Operator"

    _timer = None
    mode = StringProperty(default='')
    node_name = StringProperty(default='')
    node_group = StringProperty(default='')

    def modal(self, context, event):
        ng = bpy.data.node_groups.get(self.node_group)
        if ng: 
            n = ng.nodes[self.node_name]
        else:
            return {'PASS_THROUGH'}
 
        if (event.type == 'TIMER'):
            if not n.active:
                self.cancel(context)
                return {'FINISHED'}
            print('meee!')

        return {'PASS_THROUGH'}

    def event_dispatcher(self, context, type_op):
        if type_op == 'start':
            context.node.active = True
            wm = context.window_manager
            self._timer = wm.event_timer_add(1, context.window)
            wm.modal_handler_add(self)

        if type_op == 'end':
            context.node.active = False

    def execute(self, context):
        n = context.node
        self.node_name = context.node.name
        self.node_group = context.node.id_data.name

        self.event_dispatcher(context, self.mode)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class SvWebsocketNode(bpy.types.Node, SverchCustomTreeNode):
    ''' SvWebsocketNode '''
    bl_idname = 'SvWebsocketNode'
    bl_label = 'WebsocketNode'
    bl_icon = 'OUTLINER_OB_EMPTY'

    draw_to_host = BoolProperty(description="switch it on and off", default=0, name='draw_to_host')
    active = BoolProperty(description="current state", default=0, name='comms on')
    State = FloatProperty(default=1.0, name='State')

    def init(self, context):
        self.inputs.new('StringsSocket', "State", "State").prop_name = 'State'
        self.inputs.new('VerticesSocket', "coords_3d", "coords_3d")

    def draw_buttons(self, context, layout):
        row = layout.row()
        flash_operator = 'wm.web_modal_timer_operator'
        row.operator(flash_operator, text='start').mode = 'start'
        row.operator(flash_operator, text='stop').mode = 'end'

    def update(self):
        if not len(self.inputs) == 2:
            return

        #if self.draw_to_host and not self.active:
        #    web_obj = DrawHTML()
        pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvWebsocketNode)
    bpy.utils.register_class(WebModalTimerOperator)


def unregister():
    bpy.utils.unregister_class(SvWebsocketNode)
    bpy.utils.unregister_class(WebModalTimerOperator)
