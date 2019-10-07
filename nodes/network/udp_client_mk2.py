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

import socket
import threading, time, ast

import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.utils.profile import profile
from sverchok.data_structure import updateNode


class SvUDP(bpy.types.Operator):
    
    '''
    Making flag of run for threading function active, so
    UDP networking can sent and receive something
    '''

    bl_idname = "node.svudp"
    bl_label = "Start or stop UDP node"

    fn_name = StringProperty(default='')
    node_name = StringProperty(default='')
    tree_name = StringProperty(default='')

    def execute(self, context):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        if self.tree_name and self.node_name:
            ng = bpy.data.node_groups[self.tree_name]
            node = ng.nodes[self.node_name]
        else:
            node = context.node
        if self.fn_name == 'Run':
            context.scene.svUDPrun = True
            ev = threading.Thread(target=node.recv_msg, args=(context,))
            ev.start()
        else:
            context.scene.svUDPrun = False
        return {'FINISHED'}

class SvUdpClientNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    
    '''
    You acn send and receive UDP signal, 
    that will auto parced from string value to list of data
    If error accures with ast, than data is wrong.
    Follow data structure. At least it has to be [[]] container
    '''

    bl_idname = 'SvUdpClientNodeMK2'
    bl_label = 'UDP Client mk2'

    def send_msg(self, context):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.sendto(bytes(self.send, 'UTF-8'), (self.ip, self.port))


    def recv_msg(self,context):
        while context.scene.svUDPrun == True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((self.ip, self.port))
                sock.settimeout(self.timeout)
                data = sock.recv(self.buffer_size)
                if data:
                    self.receive = data.decode('UTF-8')
            except socket.timeout:
                pass


    send = StringProperty(name='send',
                          description='Message to send',
                          default='message',
                          update=send_msg)

    receive = StringProperty(name='receive',
                             description='Received message',
                             default='',
                             update=updateNode)

    ip = StringProperty(name='ip',
                        description='IP address of server',
                        default='127.0.0.1')

    port = IntProperty(name='port',
                       description='Port number to send message',
                       default=9250)

    buffer_size = IntProperty(name='buffer_size',
                              description='Size of buffer',
                              default=8192)

    timeout = FloatProperty(name='timeout',
                            description='Timeout (sec)',
                            default=0.5)

    def draw_buttons(self, context, layout):
        if context.scene.svUDPrun == True:
            t = 'Stop'
        else:
            t = 'Run'
        layout.operator('node.svudp', text=t).fn_name = t
        layout.prop(self, 'ip', text='IP')
        layout.prop(self, 'port', text='Port')
        layout.prop(self, 'buffer_size', text='Buffer')
        layout.prop(self, 'timeout', text='Timeout')

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'send') #.prop_name = 'send'
        self.outputs.new('StringsSocket', 'receive')
        ev = threading.Thread(target=self.recv_msg, args=(context,))
        ev.start()
        

    @profile
    def process(self):
        if not bpy.context.scene.svUDPrun:
            return
        if self.inputs[0].is_linked:
            input_value = self.inputs[0].sv_get()
            if self.send != str(input_value):
                
                self.send = str(input_value)
                self.send_msg(bpy.context)

        elif self.outputs['receive'].is_linked:
            self.outputs['receive'].sv_set(ast.literal_eval(self.receive))


def register():
    bpy.utils.register_class(SvUdpClientNodeMK2)
    bpy.utils.register_class(SvUDP)
    bpy.types.Scene.svUDPrun = bpy.props.BoolProperty(False)


def unregister():
    del bpy.types.Scene.svUDPrun
    bpy.utils.unregister_class(SvUDP)
    bpy.utils.unregister_class(SvUdpClientNodeMK2)

if __name__ == '__main__':
    register()
