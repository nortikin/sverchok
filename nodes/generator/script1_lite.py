# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

import ast
import os
import traceback

import bpy
from bpy.props import StringProperty

from sverchok.utils.sv_panels_tools import sv_get_local_path
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode


UNPARSABLE = None, None
FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)

sock_dict = {
    'v': 'VerticesSocket', 's': 'StringsSocket', 'm': 'MatrixSocket', 'o': 'SvObjectSocket'
}


def parse_socket_line(line):
    lsp = line.strip().split()
    if not len(lsp) == 4:
        print(line, 'is malformed')
        return UNPARSABLE
    else:
        socket_type = sock_dict.get(lsp[3])
        if not socket_type:
            return UNPARSABLE
        return socket_type, lsp[2]

def are_matched(sock_, socket_description):
    return (sock_.bl_idname, sock_.name) == socket_description


class SvScriptNodeLiteCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_ui_callback"
    bl_label = "SNLite callback"

    fn_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)(context)
        return {'FINISHED'}



class SvScriptNodeLite(bpy.types.Node, SverchCustomTreeNode):

    ''' Script node '''
    bl_idname = 'SvScriptNodeLite'
    bl_label = 'Scripted Node Lite'
    bl_icon = 'SCRIPTPLUGINS'

    script_name = StringProperty()
    script_str = StringProperty()

    def sv_init(self, context):
        self.use_custom_color = False


    def load(self, context):
        if not self.script_name:
            return
        self.script_str = bpy.data.texts.get(self.script_name).as_string()
        self.process(context)

    def nuke_me(self, context):
        self.script_str = ''
        self.script_name = ''

    def process(self, context):
        if not all([self.script_name, self.script_str]):
            return

        sockets = {'inputs': [], 'outputs': []}
        if self.update_sockets(sockets):
            self.process_script(sockets)

    def process_script(self, sockets):
        # make inputs local, do function with inputs, return outputs if present
        locals.update({s.name: s.sv_get() for s in self.inputs})
        exec(self.script_str)
        for idx, val in sockets['outputs']:
            self.outputs[idx].sv_set(dict(locals()).get(val))


    def update_sockets(self, sockets):
        for line in self.script_str.split('\n'):
            print(line)
            if line.startswith('# in'):
                sockets['inputs'].append(parse_socket_line(line))
            elif line.startswith('# out'):
                sockets['outputs'].append(parse_socket_line(line))
            else:
                break

        if not sockets['inputs']:
            return

        print(sockets)

        for k, v in sockets.items():
            for idx, (socket_description) in enumerate(v):
                print(idx, socket_description)
                if socket_description is UNPARSABLE:
                    return

                sock_ = getattr(self, k)
                if len(sock_) < idx:
                    if not are_matched(sock_[idx], socket_description):
                        modify_socket(sock_, idx, socket_description)
                else:
                    sock_.new(*socket_description)
        
        return True


    def draw_buttons(self, context, layout):
        sn_callback = 'node.scriptlite_ui_callback'

        col = layout.column(align=True)
        row = col.row()

        if not self.script_str:
            row.prop_search(self, 'script_name', bpy.data, 'texts', text='', icon='TEXT')
            row.operator(sn_callback, text='', icon='PLUGIN').fn_name = 'load'
        else:
            row.operator(sn_callback, text='Reload').fn_name = 'load'
            row.operator(sn_callback, text='Clear').fn_name = 'nuke_me'



classes = [SvScriptNodeLiteCallBack, SvScriptNodeLite]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
