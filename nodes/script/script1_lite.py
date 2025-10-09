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
import textwrap
import traceback
import numpy as np

import bpy
from bpy.props import StringProperty, IntVectorProperty, FloatVectorProperty, BoolProperty
from sverchok.utils.sv_update_utils import sv_get_local_path
from sverchok.utils.snlite_importhelper import (
    UNPARSABLE, set_autocolor, parse_sockets, are_matched)

from sverchok.utils.snlite_utils import vectorize, ddir, sv_njit, sv_njit_clear
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.console_print import console_print
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.handle_blender_data import keep_enum_reference
from sverchok.utils.snlite_script_searcher import SvSnliteScriptSearch

FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.6, 0.8)

sv_path = os.path.dirname(sv_get_local_path()[0])
snlite_template_path = os.path.join(sv_path, 'node_scripts', 'SNLite_templates')
template_categories = ['demo', 'bpy_stuff', 'bmesh', 'utils', 'templates']

#defaults = [0] * 32

class SNLITE_EXCEPTION(Exception): pass

menu_file_part = 0
menu_file_index = 0
dict_file_name_to_index = dict()

def display_file_name(file_path):
    global menu_file_part
    global menu_file_index
    menu_file_index+=1
    dict_file_name_to_index[file_path] = f'{menu_file_part}.{menu_file_index}.'
    dfn = bpy.path.display_name(file_path)
    dfn = f'{menu_file_part}.{menu_file_index}. {dfn}'
    return dfn


class SV_MT_ScriptNodeLitePyMenu(bpy.types.Menu):
    bl_label = "SNLite templates"
    bl_idname = "SV_MT_ScriptNodeLitePyMenu"

    def draw(self, context):
        global menu_file_part
        global menu_file_index
        global dict_file_name_to_index
        
        if context.active_node:

            node = context.active_node
            if (node.selected_mode == 'To_TextBlok'):
                args = dict(operator='text.open', props_default={'internal': True}, display_name=display_file_name,)
            else:
                args = dict(operator='node.scriptlite_import', display_name=display_file_name,)

            menu_file_part=0
            dict_file_name_to_index = dict()
            for I, folder in enumerate(template_categories):
                menu_file_part+=1
                menu_file_index = 0
                final_path = os.path.join(snlite_template_path, folder)
                self.layout.label(text=f"{menu_file_part}. {folder}")
                self.path_menu(searchpaths=[final_path], **args)
                self.layout.row().separator()


class SvScriptNodeLiteCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_ui_callback"
    bl_label = "SNLite callback"
    bl_options = {'INTERNAL'}
    fn_name: StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)()
        return {'FINISHED'}


class SvScriptNodeLiteCustomCallBack(bpy.types.Operator):

    bl_idname = "node.scriptlite_custom_callback"
    bl_label = "custom SNLite callback"
    bl_options = {'INTERNAL'}
    cb_name: StringProperty(default='')

    def execute(self, context):
        context.node.custom_callback(context, self)
        return {'FINISHED'}


class SvScriptNodeLiteTextImport(bpy.types.Operator):

    bl_idname = "node.scriptlite_import"
    bl_label = "SNLite load"
    filepath: StringProperty()

    def execute(self, context):
        global dict_file_name_to_index
        message = "Error set node script. Try select node 'Script Light'. If this is helpless then write issue."
        def draw(self, context):
            self.layout.label(text=message)

        txt = bpy.data.texts.load(self.filepath)
        # get active node.
        node = None
        if hasattr(context, "node")==True and context.node is not None:
            # blender 3.6.x
            node = context.node
        elif hasattr(context, "active_node")==True and context.active_node is not None:
            # Blender 4.x
            node = context.active_node

        if node is not None:
            if txt.filepath in dict_file_name_to_index:
                node.menu_index = dict_file_name_to_index[txt.filepath]+' '
                node.full_script_name = txt.filepath
            else:
                node.menu_index = ''
            node.script_name = os.path.basename(txt.name)
            node.load()
        else:
            bpy.context.window_manager.popup_menu(draw, title="Error", icon="INFO")
            pass
        return {'FINISHED'}


class SvScriptNodeLite(SverchCustomTreeNode, bpy.types.Node):

    """
    Triggers: snl
    Tooltip: Script Node Lite
    
    This code represents a conscious weighing of conveniences to the user, vs somewhat harder to understand
    code under the hood. This code evolved as design specs changed, while providing continued support for
    previous implementation details.
    """

    bl_idname = 'SvScriptNodeLite'
    bl_label = 'Scripted Node Lite'
    bl_icon = 'SCRIPTPLUGINS'
    is_scene_dependent = True
    is_animation_dependent = True

    @property
    def current_node_dict(self):
        return self.node_dict.get(hash(self))
    
    def reset_node_dict_instance(self):
        self.node_dict[hash(self)] = {}

    def return_enumeration(self, enum_name=""):
        if (ND := self.current_node_dict):
            if (enum_list := ND['sockets'][enum_name]):
                return [(ce, ce, '', idx) for idx, ce in enumerate(enum_list)]

        return [("A", "A", '', 0), ("B", "B", '', 1)]

    def extract_code(self, ast_node, joined=False):
        code_lines = self.script_str.split('\n')[ast_node.lineno-1:ast_node.end_lineno]
        return '\n'.join(code_lines) if joined else code_lines

    def custom_callback(self, context, operator):
        if (ND := self.current_node_dict):
            ND['sockets']['callbacks'][operator.cb_name](self, context)

    def make_operator(self, new_func_name, force=False):
        if (ND := self.current_node_dict):
            callbacks = ND['sockets']['callbacks']
            if not (new_func_name in callbacks) or force:
                # here node refers to an ast node (a syntax tree node), not a node tree node
                ast_node = self.get_node_from_function_name(new_func_name)
                code = self.extract_code(ast_node, joined=True)
                # locals().update(self.make_new_locals())  # maybe..
                locals().update(self.snlite_aliases)
                exec(code, locals(), locals())
                callbacks[new_func_name] = locals()[new_func_name]

    @property
    def sv_internal_links(self):
        if (ND := self.current_node_dict) and 'sockets' in ND:
            if (func := ND['sockets'].get("sv_internal_links")):
                return func(self)
        
        return list(zip(self.inputs[:], self.outputs[:]))

    menu_index: StringProperty()
    full_script_name: StringProperty()
    script_name: StringProperty()
    script_str: StringProperty()
    node_dict = {}
    user_dict = {}

    halt_updates: BoolProperty(name="snlite halting token")

    def get_user_dict(self):
        if not self.user_dict.get(hash(self)):
            self.user_dict[hash(self)] = {}
        return self.user_dict[hash(self)]

    def reset_user_dict(self, hard=False):
        if hard:
            # will reset all user_dicts in all instances of snlite.
            # you probably don't want to do this, but for debugging it can be useful.
            self.user_dict = {}

        self.user_dict[hash(self)] = {}


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
        items=keep_enum_reference(
            lambda self, c: self.return_enumeration(enum_name='custom_enum')),
        description="enum 1", update=updateNode)
    custom_enum_2: bpy.props.EnumProperty(
        items=keep_enum_reference(
            lambda self, c: self.return_enumeration(enum_name='custom_enum_2')),
        description="enum 2", update=updateNode)

    snlite_raise_exception: BoolProperty(name="raise exception")

    def draw_label(self):
        if self.script_name:
            return f"SN: {self.menu_index}{self.script_name}"
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
                self.info(f"{socket_description}, {idx}, was unparsable")
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

        try:
            self.halt_updates = True

            if default_value is not None:
                if isinstance(default_value, float):
                    if not socket.use_prop or socket.default_property_type != 'float':
                        socket.use_prop = True
                        socket.default_property_type = 'float'
                        socket.default_float_property = default_value
                elif isinstance(default_value, int):
                    if not socket.use_prop or socket.default_property_type != 'int':
                        socket.use_prop = True
                        socket.default_property_type = 'int'
                        socket.default_int_property = default_value
                else:
                    # unsupported type
                    socket.use_prop = False
            else:
                socket.use_prop = False

        except:
            self.info('some failure in the add_props_to_sockets function. ouch.')

        self.halt_updates = False

    def flush_excess_sockets(self, k, v):
        sockets = getattr(self, k)
        if len(sockets) > len(v):
            num_to_remove = (len(sockets) - len(v))
            for _ in range(num_to_remove):
                sockets.remove(sockets[-1])

    def update_sockets(self):
        socket_info = parse_sockets(self)
        #if not socket_info['inputs']:
        #    return

        for k, v in socket_info.items():
            if not (k in {'inputs', 'outputs'}):
                continue

            if not self.add_or_update_sockets(k, v):
                self.info(f'failed to load sockets for {k}')
                return

            self.flush_excess_sockets(k, v)

        self.reset_node_dict_instance()
        self.current_node_dict['sockets'] = socket_info
        return True

    def sv_init(self, context):
        self.width = 220
        self.use_custom_color = False

    def load(self):
        if not self.script_name:
            return

        text = self.get_bpy_data_from_name(self.script_name, bpy.data.texts)
        if text and hasattr(text, "as_string"):
            self.script_str = text.as_string()
            # self.process_node(None)

        else:
            self.info(f'bpy.data.texts not read yet, self.script_name="{self.script_name}"')
            if self.script_str:
                self.info('but script loaded locally anyway.')

        if self.update_sockets():
            self.injected_state = False
            self.process()

    def nuke_me(self):
        self.script_str = ''
        self.script_name = ''
        self.reset_node_dict_instance()
        for socket_set in [self.inputs, self.outputs]:
            socket_set.clear()

    def sv_copy(self, node):
        self.reset_node_dict_instance()
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
        ND = self.current_node_dict
        if not ND:
            self.info('hash invalidated')
            self.injected_state = False
            self.update_sockets()
            ND = self.current_node_dict
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

            # setting the label of the connected socket.
            if len(sock_desc) == 5:
                display_name = sock_desc[4]
                if display_name:

                    # if label is not yet set or the label is currently
                    # different to the proposed label, change it.
                    if not s.label or (s.label != display_name):
                       s.label = display_name

            else:
                if s.label:
                    s.label = ''

            local_dict[s.name] = val

        return local_dict

    def detect_indentation_from_snippet(self, lines):
        for line in lines:
            if line.startswith(" "): return "    "
            elif line.startswith("\t"): return "\t"
        print(f"no indentation detected..{lines}")
        return "  "

    def get_node_from_function_name(self, func_name):
        """
        "node" here refers to an ast.node entity for the named function
        found in the self.script_str 
        """
        tree = ast.parse(self.script_str)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return node

    def get_function_code(self, func_name, end=""):
        if (ast_node:= self.get_node_from_function_name(func_name)):
            
            if not end:
                return self.extract_code(ast_node, joined=True)
            else:
                # snlite will inject tail-code
                code = self.extract_code(ast_node)
                indentation = self.detect_indentation_from_snippet(code)
                code.append(f"{indentation}{end}\n")
                return "\n".join(code)

    def inject_state(self, local_variables):
        if (setup_result := self.get_function_code("setup", end="return locals()")):
            exec(setup_result, local_variables, local_variables)
            setup_locals = local_variables.get('setup')()
            local_variables.update(setup_locals)
            local_variables['socket_info']['setup_state'] = setup_locals
            self.injected_state = True

    def inject_function(self, local_variables, func_name=None, end=""):
        if (result := self.get_function_code(func_name, end="pass")):
            exec(result, local_variables, local_variables)
            func = local_variables.get(func_name)
            local_variables['socket_info'][func_name] = func

    @property
    def snlite_aliases(self):
        return {
            'vectorize': vectorize,
            'bpy': bpy,
            'np': np,
            'ddir': ddir,
            'get_user_dict': self.get_user_dict,
            'reset_user_dict': self.reset_user_dict,
            'cprint': lambda message: console_print(message, self),
            'console_print': console_print,
            'sv_njit': sv_njit,
            'sv_njit_clear': sv_njit_clear,
            'bmesh_from_pydata': bmesh_from_pydata,
            'pydata_from_bmesh': pydata_from_bmesh
        }

    def process_script(self):
        __local__dict__ = self.make_new_locals()
        locals().update(__local__dict__)
        locals().update(self.snlite_aliases)

        for output in self.outputs:
            locals().update({output.name: []})

        try:
            socket_info = self.current_node_dict['sockets']

            # inject once!
            if not self.injected_state:
                self.inject_state(locals())
                self.inject_function(locals(), func_name="ui", end="pass")
                self.inject_function(locals(), func_name="sv_internal_links")
            else:
                locals().update(socket_info['setup_state'])

            if self.inject_params:
                locals().update({'parameters': [__local__dict__.get(s.name) for s in self.inputs]})

            if socket_info['inputs_required']:
                # if not fully connected do not raise.
                # should inform the user that the execution was halted because not 
                # enough input was provided for the script to do anything useful.
                if not self.socket_requirements_met(socket_info):
                    return

            exec(self.script_str, locals(), locals())

            for idx, _socket in enumerate(self.outputs):
                vals = locals()[_socket.name]
                self.outputs[idx].sv_set(vals)

            set_autocolor(self, True, READY_COLOR)


        except Exception as err:


            self.info(f"Unexpected error: {sys.exc_info()[0]}")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lineno = traceback.extract_tb(exc_traceback)[-1][1]
            self.info(f'on line: {lineno}')

            show = traceback.print_exception
            show(exc_type, exc_value, exc_traceback, limit=6, file=sys.stdout)

            if self.snlite_raise_exception:
                raise

    def socket_requirements_met(self, socket_info):
        required_count = 0
        requirements = socket_info['inputs_required']
        for socket_name in requirements:
            if self.inputs.get(socket_name):
                obtained_data = self.inputs[socket_name].sv_get(default=None)
                if obtained_data is None:
                    continue
                try:
                    if obtained_data:
                        if isinstance(obtained_data[0], np.ndarray) and obtained_data[0].any():
                            required_count += 1
                            continue
                        if obtained_data[0]:
                            required_count += 1
                except Exception as err:
                    # print("ending early 2", err)
                    ...
        
        requirements_met = required_count == len(requirements)
        if requirements_met:
            return True
        
        self.info(f"end execution early because required sockets are not connected {requirements}")


    def custom_draw(self, context, layout):
        tk = self.current_node_dict
        if not tk or not tk.get('sockets'):
            return

        if (snlite_info := tk['sockets']):

            # snlite supplied custom file handler solution
            if (fh := snlite_info.get('display_file_handler')):
                layout.prop_search(self, 'user_filename', bpy.data, 'texts', text='filename')

            # user supplied custom draw function
            if (f := snlite_info.get('ui')):
                f(self, context, layout)

    def sv_draw_buttons(self, context, layout):
        sn_callback = 'node.scriptlite_ui_callback'

        if not self.script_str:
            col = layout.column(align=True)
            row = col.row()
            row.prop_search(self, 'script_name', bpy.data, 'texts', text='', icon='TEXT')
            row.operator(sn_callback, text='', icon='PLUGIN').fn_name = 'load'
            self.wrapper_tracked_ui_draw_op(row, SvSnliteScriptSearch.bl_idname, text="", icon="VIEWZOOM")
        else:
            col = layout.column(align=True)
            row = col.row()
            row.operator(sn_callback, text='Reload').fn_name = 'load'
            row.operator(sn_callback, text='Clear').fn_name = 'nuke_me'

        self.custom_draw(context, layout)

    def sv_draw_buttons_ext(self, _, layout):
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)
        col = layout.column()
        col.menu(SV_MT_ScriptNodeLitePyMenu.bl_idname)

        box = layout.box()
        r = box.row()
        r.label(text="extra snlite features")
        r = box.row()
        r.prop(self, "snlite_raise_exception", toggle=True, text="raise errors to tree level")



    # ---- IO Json storage is handled in this node locally ----

    def save_to_json(self, node_data: dict):
        texts = bpy.data.texts

        includes = node_data.get('includes')
        if includes:
            for include_name, include_content in includes.items():
                new_text = texts.new(include_name)
                new_text.from_string(include_content)

                if include_name == new_text.name:
                    continue

                multi_string_msg = textwrap.dedent(f"""\
                | in {self.name} the importer encountered
                | an include called {include_name}. While trying
                | to write this file to bpy.data.texts another file
                | with the same name was encountered. The importer
                | automatically made a datablock called {new_text.name}.
                """)
                self.info(multi_string_msg)

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
        if import_version < 1.0:
            params = node_data.get('params')
            script_name = params.get('script_name')
            script_content = params.get('script_str')
        else:
            script_name = self.script_name
            script_content = self.script_str

        if script_name:
            texts = bpy.data.texts
            if script_name and not (script_name in texts):
                new_text = texts.new(script_name)
                new_text.from_string(script_content)
            elif script_name and (script_name in texts):
                # This was added to fix existing texts with the same name but no / different content.
                if texts[script_name].as_string() == script_content:
                    self.debug(f'SN skipping text named "{script_name}" - their content are the same')
                else:
                    self.info(f'SN text named "{script_name}" already found, but content differs')
                    new_text = texts.new(script_name)
                    new_text.from_string(script_content)
                    script_name = new_text.name
                    self.info(f'SN text named replaced with "{script_name}"')

            self.script_name = script_name
            self.script_str = script_content

        self.load()

        # this check and function call is needed to allow loading node trees directly
        # from a .blend in order to export them via create_dict_of_tree
        if not self.node_dict or not self.current_node_dict:
            self.make_new_locals()

        storage = self.current_node_dict['sockets']
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
