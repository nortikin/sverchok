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

import sys
import ast
import traceback

import bpy
from bpy.props import StringProperty

from sverchok.utils.sv_panels_tools import sv_get_local_path
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode, replace_socket

UNPARSABLE = None, None, None, None
FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)

sock_dict = {
    'v': 'VerticesSocket', 's': 'StringsSocket', 'm': 'MatrixSocket', 'o': 'SvObjectSocket'
}


def processed(str_in):
    _, b = str_in.split('=')
    return ast.literal_eval(b)


def parse_socket_line(line):
    lsp = line.strip().split()
    if not len(lsp) in {3, 5}:
        print(line, 'is malformed')
        return UNPARSABLE
    else:
        socket_type = sock_dict.get(lsp[2])
        socket_name = lsp[1]
        if not socket_type:
            return UNPARSABLE
        elif len(lsp) == 3:
            return socket_type, socket_name, None, None
        else:
            default = processed(lsp[3])
            nested = processed(lsp[4])
            return socket_type, socket_name, default, nested


def are_matched(sock_, socket_description):
    return (sock_.bl_idname, sock_.name) == socket_description[:2]


class SvScriptNodeLiteCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_ui_callback"
    bl_label = "SNLite callback"
    fn_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)()
        return {'FINISHED'}


class SvScriptNodeLite(bpy.types.Node, SverchCustomTreeNode):

    ''' Script node Lite'''
    bl_idname = 'SvScriptNodeLite'
    bl_label = 'Scripted Node Lite'
    bl_icon = 'SCRIPTPLUGINS'

    script_name = StringProperty()
    script_str = StringProperty()
    node_dict = {}


    def parse_sockets(self):
        sockets = {'inputs': [], 'outputs': []}
        quotes = 0
        for line in self.script_str.split('\n'):
            L = line.strip()
            if L.startswith('"""'):
                quotes += 1
                if quotes == 2:
                    break
            elif L.startswith('in ') or L.startswith('out '):
                socket_dir = L.split(' ')[0] + 'puts'
                sockets[socket_dir].append(parse_socket_line(L))

        return sockets


    def update_sockets(self):
        sockets = self.parse_sockets()
        if not sockets['inputs']:
            return

        for k, v in sockets.items():
            for idx, (socket_description) in enumerate(v):
                if socket_description is UNPARSABLE:
                    return

                sock_ = getattr(self, k)

                if len(sock_) < idx:
                    if not are_matched(sock_[idx], socket_description):
                        replace_socket(sock_[idx], *socket_description[:2])
                else:
                    if len(sock_) >= len(v):
                        break

                    sock_.new(*socket_description[:2])
        
        self.node_dict[hash(self)] = {}
        self.node_dict[hash(self)]['sockets'] = sockets
        return True


    def sv_init(self, context):
        self.use_custom_color = False


    def load(self):
        if not self.script_name:
            return
        self.script_str = bpy.data.texts.get(self.script_name).as_string()

        if self.update_sockets():
            self.process()


    def nuke_me(self):
        self.script_str = ''
        self.script_name = ''
        self.node_dict[hash(self)] = {}
        for socket_set in [self.inputs, self.outputs]:
            socket_set.clear()        


    def process(self):
        if not all([self.script_name, self.script_str]):
            return
        self.process_script()


    def make_new_locals(self):

        # make .blend reload event work, without this the self.node_dict is empty.
        if not self.node_dict:
            self.update_sockets()

        # make inputs local, do function with inputs, return outputs if present
        sockets = self.node_dict[hash(self)]['sockets']
        local_dict = {}
        for idx, s in enumerate(self.inputs):
            sock_desc = sockets['inputs'][idx]
            
            if s.is_linked:
                val = s.sv_get(default=[[]])
                if sock_desc[3]:
                    val = {0: val, 1: val[0], 2: val[0][0]}.get(sock_desc[3])
            else:
                val = sock_desc[2]
            local_dict[s.name] = val

        return local_dict


    def process_script(self):
        locals().update(self.make_new_locals())

        try:
            exec(self.script_str)
            for idx, _socket in enumerate(self.outputs):
                vals = locals()[_socket.name]
                self.outputs[idx].sv_set(vals)

        except Exception as err:
            # this does not find the line in the exec string ( I KNOW )
            sys.stderr.write('ERROR: %s\n' % str(err))
            print(sys.exc_info()[-1].tb_frame.f_code)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            print('failed execution')



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
