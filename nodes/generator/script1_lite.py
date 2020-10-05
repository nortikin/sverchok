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
import numpy as np

import bpy
from bpy.props import StringProperty, IntVectorProperty, FloatVectorProperty, BoolProperty

from sverchok.utils.sv_update_utils import sv_get_local_path
from sverchok.utils.snlite_importhelper import (
    UNPARSABLE, set_autocolor, parse_sockets, are_matched,
    get_rgb_curve, set_rgb_curve
)
from sverchok.utils.snlite_utils import vectorize, ddir
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode


FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)

sv_path = os.path.dirname(sv_get_local_path()[0])
snlite_template_path = os.path.join(sv_path, 'node_scripts', 'SNLite_templates')

defaults = [0] * 32

template_categories = ['demo', 'bpy_stuff', 'bmesh', 'utils']

class SNLITE_EXCEPTION(Exception): pass

class SV_MT_ScriptNodeLitePyMenu(bpy.types.Menu):
    bl_label = "SNLite templates"
    bl_idname = "SV_MT_ScriptNodeLitePyMenu"

    def draw(self, context):
        if context.active_node:

            node = context.active_node
            if (node.selected_mode == 'To_TextBlok'):
                args = dict(operator='text.open', props_default={'internal': True})
            else:
                args = dict(operator='node.scriptlite_import')

            for folder in template_categories:
                final_path = os.path.join(snlite_template_path, folder)
                self.layout.label(text=folder)
                self.path_menu(searchpaths=[final_path], **args)
                self.layout.row().separator()


class SvScriptNodeLiteCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_ui_callback"
    bl_label = "SNLite callback"
    bl_options = {'INTERNAL'}
    fn_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)()
        return {'FINISHED'}


class SvScriptNodeLiteCustomCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_custom_callback"
    bl_label = "custom SNLite callback"
    bl_options = {'INTERNAL'}
    cb_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        context.node.custom_callback(context, self)
        return {'FINISHED'}


class SvScriptNodeLiteTextImport(bpy.types.Operator):

    bl_idname = "node.scriptlite_import"
    bl_label = "SNLite load"
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        txt = bpy.data.texts.load(self.filepath)
        context.node.script_name = os.path.basename(txt.name)
        context.node.load()
        return {'FINISHED'}


class SvScriptNodeLite(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' snl SN Lite /// a lite version of SN '''

    bl_idname = 'SvScriptNodeLite'
    bl_label = 'Scripted Node Lite'
    bl_icon = 'SCRIPTPLUGINS'

    def custom_enum_func(self, context):
        ND = self.node_dict.get(hash(self))
        if ND:
            enum_list = ND['sockets']['custom_enum']
            if enum_list:
                return [(ce, ce, '', idx) for idx, ce in enumerate(enum_list)]

        return [("A", "A", '', 0), ("B", "B", '', 1)]

    def custom_enum_func_2(self, context):
        ND = self.node_dict.get(hash(self))
        if ND:
            enum_list = ND['sockets']['custom_enum_2']
            if enum_list:
                return [(ce, ce, '', idx) for idx, ce in enumerate(enum_list)]

        return [("A", "A", '', 0), ("B", "B", '', 1)]


    def custom_callback(self, context, operator):
        ND = self.node_dict.get(hash(self))
        if ND:
            ND['sockets']['callbacks'][operator.cb_name](self, context)


    def make_operator(self, new_func_name, force=False):
        ND = self.node_dict.get(hash(self))
        if ND:
            callbacks = ND['sockets']['callbacks']
            if not (new_func_name in callbacks) or force:
                # here node refers to an ast node (a syntax tree node), not a node tree node
                ast_node = self.get_node_from_function_name(new_func_name)
                slice_begin, slice_end = ast_node.body[0].lineno-1, ast_node.body[-1].lineno
                code = '\n'.join(self.script_str.split('\n')[slice_begin-1:slice_end+1])

                exec(code, locals(), locals())
                callbacks[new_func_name] = locals()[new_func_name]


    script_name: StringProperty()
    script_str: StringProperty()
    node_dict = {}

    halt_updates: BoolProperty(name="snlite halting token")

    def updateNode2(self, context):
        if not self.halt_updates:
            updateNode(self, context)

    mode_options = [
        ("To_TextBlok", "To TextBlok", "", 0),
        ("To_Node", "To Node", "", 1),
    ]

    selected_mode: bpy.props.EnumProperty(
        items=mode_options,
        description="load the template directly to the node or add to textblocks",
        default="To_Node",
        update=updateNode
    )

    inject_params: BoolProperty()
    injected_state: BoolProperty(default=False)
    user_filename: StringProperty(update=updateNode)
    n_id: StringProperty(default='')

    custom_enum: bpy.props.EnumProperty(
        items=custom_enum_func, description="custom enum", update=updateNode
    )
    custom_enum_2: bpy.props.EnumProperty(
        items=custom_enum_func_2, description="custom enum 2", update=updateNode
    )


    snlite_raise_exception: BoolProperty(name="raise exception")

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
            """
            Socket description at the moment of typing is list of: [
            socket_type: str, 
            socket_name: str, 
            default: int value, float value or None,
            nested: int]
            """
            default_value = socket_description[2]

            if socket_description is UNPARSABLE:
                print(socket_description, idx, 'was unparsable')
                return

            if len(sockets) > 0 and idx in set(range(len(sockets))):
                if not are_matched(sockets[idx], socket_description):
                    socket = sockets[idx].replace_socket(*socket_description[:2])
                else:
                    socket = sockets[idx]
            else:
                socket = sockets.new(*socket_description[:2])

            self.add_prop_to_socket(socket, default_value)

        return True

    def add_prop_to_socket(self, socket, default_value):

        self.id_data.freeze(hard=True)
        try:
            self.halt_updates = True

            if default_value:
                if isinstance(default_value, float):
                    socket.use_prop = True
                    socket.default_property_type = 'float'
                    socket.default_float_property = default_value
                elif isinstance(default_value, int):
                    socket.use_prop = True
                    socket.default_property_type = 'int'
                    socket.default_int_property = default_value
                else:
                    # unsupported type
                    socket.use_prop = False
            else:
                socket.use_prop = False

        except:
            print('some failure in the add_props_to_sockets function. ouch.')

        self.halt_updates = False
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

        self.node_dict[hash(self)] = {}
        self.node_dict[hash(self)]['sockets'] = socket_info

        return True




    def sv_init(self, context):
        self.use_custom_color = False


    def load(self):
        if not self.script_name:
            return

        text = self.get_bpy_data_from_name(self.script_name, bpy.data.texts)
        if text:
            self.script_str = text.as_string()
        else:
            print(f'bpy.data.texts not read yet, self.script_name="{self.script_name}"')
            if self.script_str:
                print('but script loaded locally anyway.')

        if self.update_sockets():
            self.injected_state = False
            self.process()


    def nuke_me(self):
        self.script_str = ''
        self.script_name = ''
        self.node_dict[hash(self)] = {}
        for socket_set in [self.inputs, self.outputs]:
            socket_set.clear()

    def sv_copy(self, node):
        self.node_dict[hash(self)] = {}
        self.load()
        self.n_id = ""

    def process(self):
        if not all([self.script_name, self.script_str]):
            return
        self.process_script()


    def make_new_locals(self):

        # make .blend reload event work, without this the self.node_dict is empty.
        if not self.node_dict:
            # self.load()
            self.injected_state = False
            self.update_sockets()

        # make inputs local, do function with inputs, return outputs if present
        ND = self.node_dict.get(hash(self))
        if not ND:
            print('hash invalidated')
            self.injected_state = False
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
                    t = s.sv_get()
                    if t and t[0] and len(t[0]) > 0:
                        val = t[0][0]

            local_dict[s.name] = val

        return local_dict

    def get_node_from_function_name(self, func_name):
        """
        this seems to get enough info for a snlite stateful setup function.

        """
        tree = ast.parse(self.script_str)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return node


    def get_setup_code(self):
        ast_node = self.get_node_from_function_name('setup')
        if ast_node:
            begin_setup = ast_node.body[0].lineno - 1
            end_setup = ast_node.body[-1].lineno
            code = '\n'.join(self.script_str.split('\n')[begin_setup:end_setup])
            return 'def setup():\n\n' + code + '\n    return locals()\n'


    def get_ui_code(self):
        ast_node = self.get_node_from_function_name('ui')
        if ast_node:
            begin_setup = ast_node.body[0].lineno - 1
            end_setup = ast_node.body[-1].lineno
            code = '\n'.join(self.script_str.split('\n')[begin_setup:end_setup])
            return 'def ui(self, context, layout):\n\n' + code + '\n\n'


    def inject_state(self, local_variables):
        setup_result = self.get_setup_code()
        if setup_result:
            exec(setup_result, local_variables, local_variables)
            setup_locals = local_variables.get('setup')()
            local_variables.update(setup_locals)
            local_variables['socket_info']['setup_state'] = setup_locals
            self.injected_state = True


    def inject_draw_buttons(self, local_variables):
        draw_ui_result = self.get_ui_code()
        if draw_ui_result:
            exec(draw_ui_result, local_variables, local_variables)
            ui_func = local_variables.get('ui')
            local_variables['socket_info']['drawfunc'] = ui_func


    def process_script(self):
        __local__dict__ = self.make_new_locals()
        locals().update(__local__dict__)
        locals().update({
            'vectorize': vectorize,
            'bpy': bpy,
            'np': np,
            'ddir': ddir,
            'bmesh_from_pydata': bmesh_from_pydata,
            'pydata_from_bmesh': pydata_from_bmesh
        })

        for output in self.outputs:
            locals().update({output.name: []})

        try:
            socket_info = self.node_dict[hash(self)]['sockets']

            # inject once!
            if not self.injected_state:
                self.inject_state(locals())
                self.inject_draw_buttons(locals())
            else:
                locals().update(socket_info['setup_state'])

            if self.inject_params:
                locals().update({'parameters': [__local__dict__.get(s.name) for s in self.inputs]})

            exec(self.script_str, locals(), locals())

            for idx, _socket in enumerate(self.outputs):
                vals = locals()[_socket.name]
                self.outputs[idx].sv_set(vals)

            set_autocolor(self, True, READY_COLOR)

        except Exception as err:

            print("Unexpected error:", sys.exc_info()[0])
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lineno = traceback.extract_tb(exc_traceback)[-1][1]
            print('on line: ', lineno)
            show = traceback.print_exception
            show(exc_type, exc_value, exc_traceback, limit=6, file=sys.stdout)
            if hasattr(self, "snlite_raise_exception") and self.snlite_raise_exception:
                raise #   SNLITE_EXCEPTION(sys.exc_info()[2]) from err

    def custom_draw(self, context, layout):
        tk = self.node_dict.get(hash(self))
        if not tk or not tk.get('sockets'):
            return

        snlite_info = tk['sockets']
        if snlite_info:

            # snlite supplied custom file handler solution
            fh = snlite_info.get('display_file_handler')
            if fh:
                layout.prop_search(self, 'user_filename', bpy.data, 'texts', text='filename')

            # user supplied custom draw function
            f = snlite_info.get('drawfunc')
            if f:
                f(self, context, layout)


    def draw_buttons(self, context, layout):
        sn_callback = 'node.scriptlite_ui_callback'

        if not self.script_str:
            col = layout.column(align=True)
            row = col.row()
            row.prop_search(self, 'script_name', bpy.data, 'texts', text='', icon='TEXT')
            row.operator(sn_callback, text='', icon='PLUGIN').fn_name = 'load'
        else:
            self.draw_animatable_buttons(layout, icon_only=True)
            col = layout.column(align=True)
            row = col.row()
            row.operator(sn_callback, text='Reload').fn_name = 'load'
            row.operator(sn_callback, text='Clear').fn_name = 'nuke_me'

        self.custom_draw(context, layout)


    def draw_buttons_ext(self, _, layout):
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)
        col = layout.column()
        col.menu(SV_MT_ScriptNodeLitePyMenu.bl_idname)

        box = layout.box()
        r = box.row()
        r.label(text="extra snlite features")
        if hasattr(self, "snlite_raise_exception"):
            r = box.row()
            r.prop(self, "snlite_raise_exception", toggle=True, text="raise errors to tree level")



    # ---- IO Json storage is handled in this node locally ----

    def save_to_json(self, node_data: dict):
        texts = bpy.data.texts

        data_list = node_data.get('snlite_ui')
        if data_list:
            # self.node_dict[hash(self)]['sockets']['snlite_ui'] = ui_elements
            for data_json_str in data_list:
                data_dict = json.loads(data_json_str)
                if data_dict['bl_idname'] == 'ShaderNodeRGBCurve':
                    set_rgb_curve(data_dict)

        includes = node_data.get('includes')
        if includes:
            for include_name, include_content in includes.items():
                new_text = texts.new(include_name)
                new_text.from_string(include_content)

                if include_name == new_text.name:
                    continue

                print('| in', self.name, 'the importer encountered')
                print('| an include called', include_name, '. While trying')
                print('| to write this file to bpy.data.texts another file')
                print('| with the same name was encountered. The importer')
                print('| automatically made a datablock called', new_text.name)

    def load_from_json(self, node_data: dict, import_version: float):

        '''
        Scripted Node will no longer create alternative versions of a file.
        If a scripted node wants to make a file called 'inverse.py' and the
        current .blend already contains such a file, then for simplicity the
        importer will not try to create 'inverse.001.py' and reference that.
        It will instead do nothing and assume the existing python file is
        functionally the same.

        If you have files that work differently but have the same name, stop.

        '''
        params = node_data.get('params')
        if params:

            script_name = params.get('script_name')
            script_content = params.get('script_str')

            with self.sv_throttle_tree_update():
                texts = bpy.data.texts
                if script_name and not (script_name in texts):
                    new_text = texts.new(script_name)
                    new_text.from_string(script_content)
                elif script_name and (script_name in texts):
                    # This was added to fix existing texts with the same name but no / different content.
                    if texts[script_name].as_string() == script_content:
                        self.debug("SN skipping text named `%s' - their content are the same", script_name)
                    else:
                        self.info("SN text named `%s' already found in current, but content differs", script_name)
                        new_text = texts.new(script_name)
                        new_text.from_string(script_content)
                        script_name = new_text.name
                        self.info('SN text named replaced with %s', script_name)

            self.script_name = script_name
            self.script_str = script_content

        self.load()

        # this check and function call is needed to allow loading node trees directly
        # from a .blend in order to export them via create_dict_of_tree
        if not self.node_dict or not self.node_dict.get(hash(self)):
            self.make_new_locals()

        storage = self.node_dict[hash(self)]['sockets']

        ui_info = storage['snlite_ui']
        node_data['snlite_ui'] = []
        print(ui_info)
        for _, info in enumerate(ui_info):
            mat_name = info['mat_name']
            node_name = info['node_name']
            bl_idname = info['bl_idname']
            if bl_idname == 'ShaderNodeRGBCurve':
                data = get_rgb_curve(mat_name, node_name)
                print(data)
                data_json_str = json.dumps(data)
                node_data['snlite_ui'].append(data_json_str)

        includes = storage['includes']
        if includes:
            node_data['includes'] = {}
            for k, v in includes.items():
                node_data['includes'][k] = v


classes = [
    SvScriptNodeLiteCustomCallBack,
    SvScriptNodeLiteTextImport,
    SV_MT_ScriptNodeLitePyMenu,
    SvScriptNodeLiteCallBack,
    SvScriptNodeLite
]

register, unregister = bpy.utils.register_classes_factory(classes)
