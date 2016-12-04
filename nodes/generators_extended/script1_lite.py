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

import os
import sys
import ast
import json
import traceback

import bpy
from bpy.props import StringProperty, IntVectorProperty, FloatVectorProperty, BoolProperty

from sverchok.utils.sv_panels_tools import sv_get_local_path
from sverchok.utils.snlite_importhelper import (
    UNPARSABLE, set_autocolor, parse_sockets, are_matched,
    get_rgb_curve, set_rgb_curve
)
from sverchok.utils.snlite_utils import vectorize

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, replace_socket


FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)

sv_path = os.path.dirname(sv_get_local_path()[0])
snlite_template_path = os.path.join(sv_path, 'node_scripts', 'SNLite_templates')

defaults = list(range(32))


class SvScriptNodeLitePyMenu(bpy.types.Menu):
    bl_label = "SNLite templates"
    bl_idname = "SvScriptNodeLitePyMenu"

    def draw(self, context):
        if context.active_node:
            node = context.active_node
            if node.selected_mode == 'To TextBlok':
                self.path_menu([snlite_template_path], "text.open", {"internal": True})
            else:
                self.path_menu([snlite_template_path], "node.scriptlite_import")


class SvScriptNodeLiteCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_ui_callback"
    bl_label = "SNLite callback"
    fn_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)()
        return {'FINISHED'}


class SvScriptNodeLiteTextImport(bpy.types.Operator):

    bl_idname = "node.scriptlite_import"
    bl_label = "SNLite load"
    filepath = bpy.props.StringProperty()

    def execute(self, context):
        txt = bpy.data.texts.load(self.filepath)
        context.node.script_name = os.path.basename(txt.name)
        context.node.load()
        return {'FINISHED'}


class SvScriptNodeLite(bpy.types.Node, SverchCustomTreeNode):

    ''' Script node Lite'''
    bl_idname = 'SvScriptNodeLite'
    bl_label = 'Scripted Node Lite'
    bl_icon = 'SCRIPTPLUGINS'

    script_name = StringProperty()
    script_str = StringProperty()
    node_dict = {}

    int_list = IntVectorProperty(
        name='int_list', description="Integer list",
        default=defaults, size=32, update=updateNode)

    float_list = FloatVectorProperty(
        name='float_list', description="Float list",
        default=defaults, size=32, update=updateNode)

    mode_options = [
        ("To TextBlok", "To TextBlok", "", 0),
        ("To Node", "To Node", "", 1),
    ]

    selected_mode = bpy.props.EnumProperty(
        items=mode_options,
        description="load the template directly to the node or add to textblocks",
        default="To Node",
        update=updateNode
    )

    inject_params = BoolProperty()

    def draw_label(self):
        if self.script_name:
            return 'SN: ' + self.script_name
        else:
            return self.bl_label


    def add_or_update_sockets(self, k, v):
        '''
        'sockets' are either 'self.inputs' or 'self.outputs'
        '''
        sockets = getattr(self, k)

        for idx, (socket_description) in enumerate(v):
            if socket_description is UNPARSABLE: 
                print(socket_description, idx, 'was unparsable')
                return

            if len(sockets) > 0 and idx in set(range(len(sockets))):
                if not are_matched(sockets[idx], socket_description):
                    replace_socket(sockets[idx], *socket_description[:2])
            else:
                sockets.new(*socket_description[:2])

        return True


    def add_props_to_sockets(self, socket_info):

        self.id_data.freeze(hard=True)
        try:
            for idx, (socket_description) in enumerate(socket_info['inputs']):
                dval = socket_description[2]
                print(idx, socket_description)

                s = self.inputs[idx]

                if isinstance(dval, float):
                    s.prop_type = "float_list"
                    s.prop_index = idx
                    self.float_list[idx] = dval

                elif isinstance(dval, int):
                    s.prop_type = "int_list"
                    s.prop_index = idx
                    self.int_list[idx] = dval
        except:
            print('some failure in the add_props_to_sockets function. ouch.')

        self.id_data.unfreeze(hard=True)

    
    def flush_excess_sockets(self, k, v):
        sockets = getattr(self, k)
        if len(sockets) > len(v):
            num_to_remove = (len(sockets) - len(v))
            for _ in range(num_to_remove):
                sockets.remove(sockets[-1])


    def update_sockets(self):
        socket_info = parse_sockets(self)
        if not socket_info['inputs']:
            return

        for k, v in socket_info.items():
            if not (k in {'inputs', 'outputs'}):
                continue

            if not self.add_or_update_sockets(k, v):
                print('failed to load sockets for ', k)
                return

            self.flush_excess_sockets(k, v)

        self.add_props_to_sockets(socket_info)
        self.node_dict[hash(self)] = {}
        self.node_dict[hash(self)]['sockets'] = socket_info

        return True


    def sv_init(self, context):
        self.use_custom_color = False


    def load(self):
        if not self.script_name:
            return

        if self.script_name in bpy.data.texts:
            self.script_str = bpy.data.texts.get(self.script_name).as_string()
        else:
            print('bpy.data.texts not read yet')
            if self.script_str:
                print('but script loaded locally anyway.')

        if self.update_sockets():
            self.process()


    def nuke_me(self):
        self.script_str = ''
        self.script_name = ''
        self.node_dict[hash(self)] = {}
        for socket_set in [self.inputs, self.outputs]:
            socket_set.clear()        

    def copy(self, node):
        self.node_dict[hash(self)] = {}
        self.load()

    def process(self):
        if not all([self.script_name, self.script_str]):
            return
        self.process_script()


    def make_new_locals(self):

        # make .blend reload event work, without this the self.node_dict is empty.
        if not self.node_dict:
            # self.load()
            self.update_sockets()

        # make inputs local, do function with inputs, return outputs if present
        ND = self.node_dict.get(hash(self))
        if not ND:
            print('hash invalidated')
            self.update_sockets()
            ND = self.node_dict.get(hash(self))
            self.load()

        socket_info = ND['sockets']
        local_dict = {}
        for idx, s in enumerate(self.inputs):
            sock_desc = socket_info['inputs'][idx]
            
            if s.is_linked:
                val = s.sv_get(default=[[]])
                if sock_desc[3]:
                    val = {0: val, 1: val[0], 2: val[0][0]}.get(sock_desc[3])
            else:
                val = sock_desc[2]
                if isinstance(val, (int, float)):
                    # extra pussyfooting for the load sequence.
                    t = s.sv_get(default=[[val]])
                    if t and t[0] and t[0][0]:
                        val = t[0][0]

            local_dict[s.name] = val

        return local_dict


    def process_script(self):
        locals().update(self.make_new_locals())
        locals().update({'vectorize': vectorize})

        try:

            if hasattr(self, 'inject_params'):
                if self.inject_params:
                    parameters = eval("[" + ", ".join([i.name for i in self.inputs]) + "]")

            exec(self.script_str, locals(), locals())
            for idx, _socket in enumerate(self.outputs):
                vals = locals()[_socket.name]
                self.outputs[idx].sv_set(vals)

            socket_info = self.node_dict[hash(self)]['sockets']
            __fnamex = socket_info.get('drawfunc_name')
            if __fnamex:
                socket_info['drawfunc'] = locals()[__fnamex]

            set_autocolor(self, True, READY_COLOR)

        except:
            print("Unexpected error:", sys.exc_info()[0])
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lineno = traceback.extract_tb(exc_traceback)[-1][1]
            print('on line: ', lineno)
            show = traceback.print_exception
            show(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
            set_autocolor(self, True, FAIL_COLOR)
        else:
            return


    def custom_draw(self, context, layout):
        tk = self.node_dict.get(hash(self))
        if not tk or not tk.get('sockets'):
            return

        socket_info = tk['sockets']
        if socket_info:
            f = socket_info.get('drawfunc')
            if f:
                f(self, context, layout)


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

        self.custom_draw(context, layout)


    def draw_buttons_ext(self, _, layout):
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)
        col = layout.column()
        col.menu(SvScriptNodeLitePyMenu.bl_idname)

        if hasattr(self, 'inject_params'):
            row = layout.row()
            row.prop(self, 'inject_params', text='inject parameters')

    # ---- IO Json storage is handled in this node locally ----


    def storage_set_data(self, data_list):
        # self.node_dict[hash(self)]['sockets']['snlite_ui'] = ui_elements
        for data_json_str in data_list:
            data_dict = json.loads(data_json_str)
            if data_dict['bl_idname'] == 'ShaderNodeRGBCurve':
                set_rgb_curve(data_dict)


    def storage_get_data(self, node_dict):
        ui_info = self.node_dict[hash(self)]['sockets']['snlite_ui']
        node_dict['snlite_ui'] = []
        print(ui_info)
        for _, info in enumerate(ui_info):
            mat_name = info['mat_name']
            node_name = info['node_name']
            bl_idname = info['bl_idname']
            if bl_idname == 'ShaderNodeRGBCurve':
                data = get_rgb_curve(mat_name, node_name)
                print(data)
                data_json_str = json.dumps(data)
                node_dict['snlite_ui'].append(data_json_str)


classes = [
    SvScriptNodeLiteTextImport,
    SvScriptNodeLitePyMenu,
    SvScriptNodeLiteCallBack,
    SvScriptNodeLite
]


def register():
    _ = [bpy.utils.register_class(name) for name in classes]


def unregister():
    _ = [bpy.utils.unregister_class(name) for name in classes]
