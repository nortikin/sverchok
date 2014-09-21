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
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatVectorProperty,
    IntVectorProperty
)

from utils.sv_tools import sv_get_local_path
from node_tree import SverchCustomTreeNode
from data_structure import (
    dataCorrect,
    updateNode,
    SvSetSocketAnyType,
    SvGetSocketAnyType
)

FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)

defaults = list(range(32))
sv_path = os.path.dirname(sv_get_local_path()[0])

sock_dict = {
    'v': 'VerticesSocket',
    's': 'StringsSocket',
    'm': 'MatrixSocket'
}


def new_output_socket(node, name, stype):
    socket_type = sock_dict.get(stype)
    if socket_type:
        node.outputs.new(socket_type, name)


def new_input_socket(node, stype, name, dval):
    socket_type = sock_dict.get(stype)
    if socket_type:
        socket = node.inputs.new(socket_type, name)
        socket.default = dval

        if isinstance(dval, (float, int)):
            offset = len(node.inputs)
            if isinstance(dval, float):
                socket.prop_type = "float_list"
                node.float_list[offset] = dval
            else:  # dval is int
                socket.prop_type = "int_list"
                node.int_list[offset] = dval
            socket.prop_index = offset


def introspect_py(node):
    ''' this will return a callable function if sv_main is found, else None '''

    script_str = node.script_str
    script = node.script_name
    node_functor = None
    try:
        exec(script_str)
        f = vars()
        node_functor = f.get('sv_main')
    except UnboundLocalError:
        print('no sv_main found')
    finally:
        if node_functor:
            params = node_functor.__defaults__
            return [node_functor, params, f]


class SvDefaultScriptTemplate(bpy.types.Operator):
    ''' Imports example script or template file in bpy.data.texts'''

    bl_idname = 'node.sverchok_script_template'
    bl_label = 'Template'
    bl_options = {'REGISTER'}

    script_name = StringProperty(name='name', default='')

    def execute(self, context):
        n = context.node
        templates_path = os.path.join(sv_path, "node_scripts", "templates")

        fullpath = [templates_path, self.script_name]
        if not n.user_name == 'templates':
            fullpath.insert(1, n.user_name)

        path_to_template = os.path.join(*fullpath)
        bpy.ops.text.open(
            filepath=path_to_template,
            internal=True)

        n.script_name = self.script_name

        return {'FINISHED'}


class SvScriptUICallbackOp(bpy.types.Operator):
    ''' Used by Scripted Operators '''

    bl_idname = "node.script_ui_callback"
    bl_label = "Sverchok script ui"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')

    def execute(self, context):
        fn_name = self.fn_name
        n = context.node
        node_function = n.node_dict[hash(n)]['node_function']

        f = getattr(node_function, fn_name, None)
        if not f:
            fmsg = "{0} has no function named '{1}'"
            msg = fmsg.format(n.name, fn_name)
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}
        f()
        return {'FINISHED'}


class SvScriptNodeCallbackOp(bpy.types.Operator):
    ''' Used by ScriptNode Operators '''

    bl_idname = "node.sverchok_callback"
    bl_label = "Sverchok scriptnode callback"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')

    def execute(self, context):
        n = context.node
        fn_name = self.fn_name
        f = getattr(n, fn_name, None)

        if not f:
            msg = "{0} has no function named '{1}'".format(n.name, fn_name)
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}

        if fn_name == "load":
            f()
        elif fn_name == "nuke_me":
            f(context)

        return {'FINISHED'}


class SvScriptNode(bpy.types.Node, SverchCustomTreeNode):

    ''' Script node '''
    bl_idname = 'SvScriptNode'
    bl_label = 'Script Generator'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def avail_templates(self, context):
        fullpath = [sv_path, "node_scripts", "templates"]
        if not self.user_name == 'templates':
            fullpath.append(self.user_name)

        templates_path = os.path.join(*fullpath)
        items = [(t, t, "") for t in next(os.walk(templates_path))[2]]
        return items

    def avail_users(self, context):
        users = 'templates', 'zeffii', 'nikitron', 'ly', 'ko'
        return [(j, j, '') for j in users]

    files_popup = EnumProperty(
        items=avail_templates,
        name='template_files',
        description='choose file to load as template',
        update=updateNode)

    user_name = EnumProperty(
        name='users',
        items=avail_users,
        update=updateNode)

    int_list = IntVectorProperty(
        name='int_list', description="Integer list",
        default=defaults, size=32, update=updateNode)

    float_list = FloatVectorProperty(
        name='float_list', description="Float list",
        default=defaults, size=32, update=updateNode)

    script_name = StringProperty()
    script_str = StringProperty()
    button_names = StringProperty()
    has_buttons = BoolProperty(default=0)

    node_dict = {}

    def init(self, context):
        self.node_dict[hash(self)] = {}
        self.use_custom_color = False

    def load(self):
        if self.script_name:
            self.script_str = bpy.data.texts[self.script_name].as_string()
            self.label = self.script_name
            self.load_function()

    def load_function(self):
        self.reset_node_dict()
        self.load_py()

    def indicate_ready_state(self):
        self.use_custom_color = True
        self.color = READY_COLOR

    def reset_node_dict(self):
        self.node_dict[hash(self)] = {}
        self.button_names = ""
        self.has_buttons = False
        self.use_custom_color = False

    def nuke_me(self, context):
        in_out = [self.inputs, self.outputs]
        for socket_set in in_out:
            socket_set.clear()

        self.reset_node_dict()
        self.script_name = ""
        self.script_str = ""

    def set_node_function(self, node_function):
        self.node_dict[hash(self)]['node_function'] = node_function

    def get_node_function(self):
        return self.node_dict[hash(self)].get('node_function')

    def draw_buttons_ext(self, context, layout):
        col = layout.column()
        col.prop(self, 'user_name')

    def draw_buttons(self, context, layout):
        sv_callback = 'node.sverchok_callback'
        sv_template = 'node.sverchok_script_template'
        sn_callback = 'node.script_ui_callback'

        col = layout.column(align=True)
        row = col.row()

        if not self.script_str:
            row.prop(self, 'files_popup', '')
            import_operator = row.operator(sv_template, text='', icon='IMPORT')
            import_operator.script_name = self.files_popup

            row = col.row()
            row.prop_search(self, 'script_name', bpy.data, 'texts', text='', icon='TEXT')
            row.operator(sv_callback, text='', icon='PLUGIN').fn_name = 'load'

        else:
            row.operator(sv_callback, text='Reload').fn_name = 'load'
            row.operator(sv_callback, text='Clear').fn_name = 'nuke_me'

            if self.has_buttons:
                row = layout.row()
                for fname in self.button_names.split('|'):
                    row.operator(sn_callback, text=fname).fn_name = fname

    def load_py(self):
        details = introspect_py(self)
        if not details:
            print('load_py, failed because introspection failed')
            self.reset_node_dict()
        else:
            self.process_introspected(details)

    def process_introspected(self, details):
        node_function, params, f = details
        del f['sv_main']
        del f['script_str']
        globals().update(f)

        self.set_node_function(node_function)

        # no exception handling, lets get the exact error!
        function_output = node_function(*params)
        num_return_params = len(function_output)

        if num_return_params == 2:
            in_sockets, out_sockets = function_output
        if num_return_params == 3:
            self.has_buttons = True
            in_sockets, out_sockets, ui_ops = function_output

        if self.has_buttons:
            self.process_operator_buttons(ui_ops)

        if in_sockets and out_sockets:
            self.create_or_update_sockets(in_sockets, out_sockets)

        self.indicate_ready_state()

        # except Exception as err:
        #     traceback.format_exc()
        #     self.reset_node_dict()

    def process_operator_buttons(self, ui_ops):
        named_buttons = []
        for button_name, button_function in ui_ops:
            f = self.get_node_function()
            setattr(f, button_name, button_function)
            named_buttons.append(button_name)
        self.button_names = "|".join(named_buttons)

    def create_or_update_sockets(self, in_sockets, out_sockets):
        print('found {0} in sock requests'.format(len(in_sockets)))
        print('found {0} out sock requests'.format(len(out_sockets)))

        outputs = self.outputs
        for socket_type, name, data in out_sockets:
            if not (name in outputs):
                new_output_socket(self, name, socket_type)
                outputs[name].sv_set(data)

        for socket_type, name, dval in in_sockets:
            if not (name in self.inputs):
                new_input_socket(self, socket_type, name, dval)

    def update(self):
        if not self.inputs:
            return

        if not hash(self) in self.node_dict:
            if self.script_str:
                self.load_function()
            else:
                self.load()

        if not self.get_node_function():
            return

        self.process()

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        input_names = [i.name for i in inputs]

        node_function = self.get_node_function()
        defaults = node_function.__defaults__

        fparams = []
        for param_idx, name in enumerate(input_names):
            socket = inputs[name]
            this_val = defaults[param_idx]

            # this deals with incoming links only.
            if socket.links:
                if isinstance(this_val, list):
                    try:
                        this_val = socket.sv_get()
                        this_val = dataCorrect(this_val)
                    except:
                        pass
                elif isinstance(this_val, (int, float)):
                    try:
                        k = str(socket.sv_get())
                        kfree = k[2:-2]
                        this_val = ast.literal_eval(kfree)
                        #this_val = socket.sv_get()[0][0]
                    except:
                        pass

            # this catches movement on UI sliders.
            elif isinstance(this_val, (int, float)):
                # extra pussyfooting for the load sequence.
                t = socket.sv_get()
                if t and t[0] and t[0][0]:
                    this_val = t[0][0]

            fparams.append(this_val)

        if (len(fparams) == len(input_names)):
            out = node_function(*fparams)
            if len(out) == 2:
                _, out_sockets = out

                for _, name, data in out_sockets:
                    outputs[name].sv_set(data)

    def update_socket(self, context):
        self.update()

classes = [
    SvScriptNode,
    SvDefaultScriptTemplate,
    SvScriptNodeCallbackOp,
    SvScriptUICallbackOp
]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
