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


import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.props import IntProperty, FloatProperty
from node_s import *
from util import *
import ast
import os


FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)


# utility functions


def new_output_socket(node, name, stype):
    socket_type = {
        'v': 'VerticesSocket',
        's': 'StringsSocket',
        'm': 'MatrixSocket'
    }.get(stype, None)

    if socket_type:
        node.outputs.new(socket_type, name, name)


def new_input_socket(node, stype, name, dval):
    socket_type = {
        'v': 'VerticesSocket',
        's': 'StringsSocket',
        'm': 'MatrixSocket'
    }.get(stype, None)

    if socket_type:
        node.inputs.new(socket_type, name, name).default = dval


def instrospect_py(node):
    script_str = node.script_str
    script = node.script

    try:
        exec(script_str)
        f = vars()
        node_functor = f.get('sv_main', None)
    except UnboundLocalError:
        print('see demo files for NodeScript')
        return
    finally:
        '''
        this will return a callable function if sv_main is found, else None
        '''
        if node_functor:
            params = node_functor.__defaults__
            return [node_functor, params, f]


class SvDefaultScriptTemplate(bpy.types.Operator):

    ''' Creates template text file to start making your own script '''
    bl_idname = 'node.sverchok_script_template'
    bl_label = 'Template'
    bl_options = {'REGISTER'}

    script_name = StringProperty(name='name', default='')

    def execute(self, context):
        # if a script is already in text.data list then 001 .002
        # are automatically append by ops.text.open
        sv_path = os.path.dirname(os.path.realpath(__file__))
        script_dir = "node_script_templates"
        path_to_template = os.path.join(sv_path, script_dir, self.script_name)
        bpy.ops.text.open(filepath=path_to_template, internal=True)
        return {'FINISHED'}


class SvScriptUICallbackOp(bpy.types.Operator):

    bl_idname = "node.script_ui_callback"
    bl_label = "Sverchok script ui"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')

    def execute(self, context):
        n = context.node
        node_function = n.node_dict[hash(n)]['node_function']
        fn_name = self.fn_name

        f = getattr(node_function, fn_name, None)
        if not f:
            msg = "{0} has no function named '{1}'".format(n.name, fn_name)
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}

        f()
        return {'FINISHED'}


class SvScriptNodeCallbackOp(bpy.types.Operator):

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


class SvScriptNode(Node, SverchCustomTreeNode):

    ''' Script node '''
    bl_idname = 'SvScriptNode'
    bl_label = 'Script Generator'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def avail_scripts(self, context):
        scripts = bpy.data.texts
        items = [(t.name, t.name, "") for t in scripts]
        # changes order for old files...
        #items.sort(key=lambda x:x[0].upper())
        return items

    def avail_templates(self, context):
        sv_path = os.path.dirname(os.path.realpath(__file__))
        script_dir = "node_script_templates"
        path = os.path.join(sv_path, script_dir)
        items = [(t, t, "") for t in next(os.walk(path))[2]]
        # changes order for old files
        #items.sort(key=lambda x:x[0].upper())
        return items

    files_popup = EnumProperty(
        items=avail_templates,
        name='template_files',
        description='choose file to load as template',
        update=updateNode)

    script = EnumProperty(
        items=avail_scripts,
        name="Texts",
        description="Choose text to load in node",
        update=updateNode)

    script_name = StringProperty(default="")
    script_str = StringProperty(default="")
    button_names = StringProperty(default="")
    has_buttons = BoolProperty(default=False)

    node_dict = {}
    in_sockets = []
    out_sockets = []

    def init(self, context):
        self.node_dict[hash(self)] = {}
        pass

    def nuke_me(self, context):
        in_out = [self.inputs, self.outputs]
        for socket_set in in_out:
            socket_set.clear()

        if 'node_function' in self.node_dict[hash(self)]:
            del self.node_dict[hash(self)]['node_function']

        self.use_custom_color = False
        self.script_name = ""
        self.script_str = ""
        self.button_names = ""
        self.has_buttons = False

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        if not self.script_str:
            row = col.row(align=True)
            row.label(text='IMPORT PY:')
            row = col.row(align=True)
            row.prop(self, 'files_popup', '')
            tem = row.operator(
                'node.sverchok_script_template', text='Import Template')
            tem.script_name = self.files_popup

            row = col.row(align=True)
            row.label(text='USE PY:')
            row = col.row(align=True)
            row.prop(self, "script", "")
            row.operator('node.sverchok_callback', text='Load').fn_name = 'load'

        else:
            row = col.row()
            col2 = row.column()
            col2.scale_x = 0.05
            col2.label(icon='TEXT', text=' ')
            row.label(text='LOADED:')
            row = col.row()
            # backwards compability
            script_name = self.script_name if self.script_name else self.script
            row.label(text=script_name)
            row = col.row()
            row.operator('node.sverchok_callback', text='Reload').fn_name = 'load'
            row.operator('node.sverchok_callback', text='Clear').fn_name = 'nuke_me'

            if self.has_buttons:
                for fname in self.button_names.split('|'):
                    row = col.row()
                    row.operator('node.script_ui_callback', text=fname).fn_name = fname

    def create_or_update_sockets(self):
        '''
        - desired features not fully implemented yet (only socket add so far)
        - Load may be pressed to import an updated function
        - tries to preserve existing sockets or add new ones if needed
        '''
        for socket_type, name, data in self.out_sockets:
            if not (name in self.outputs):
                new_output_socket(self, name, socket_type)
                SvSetSocketAnyType(self, name, data)  # can output w/out input

        for socket_type, name, dval in self.in_sockets:
            if not (name in self.inputs):
                new_input_socket(self, socket_type, name, dval)

        self.use_custom_color = True
        self.color = READY_COLOR

    '''
    load(_*)
    - these are done once upon load or reload button presses
    '''

    def load(self):
        self.script_str = bpy.data.texts[self.script].as_string()
        self.script_name = self.script
        self.label = self.script_name.split('.')[0]
        self.load_function()

    def load_function(self):
        self.node_dict[hash(self)] = {}
        self.button_names = ""
        self.has_buttons = False
        self.load_py()

    def load_py(self):
        details = instrospect_py(self)
        if details:

            if None in details:
                if not details[1]:
                    print('sv_main() must take arguments')
                print('should never reach here')
                return

            node_function, params, f = details
            del f['sv_main']
            del f['script_str']
            globals().update(f)

            self.node_dict[hash(self)]['node_function'] = node_function

            function_output = node_function(*params)
            num_return_params = len(function_output)

            if num_return_params == 2:
                self.in_sockets, self.out_sockets = function_output
            if num_return_params == 3:
                self.has_buttons = True
                self.in_sockets, self.out_sockets, ui_ops = function_output

            if self.has_buttons:
                named_buttons = []
                for button_name, button_function in ui_ops:
                    f = self.node_dict[hash(self)]['node_function']
                    setattr(f, button_name, button_function)
                    named_buttons.append(button_name)
                self.button_names = "|".join(named_buttons)

            print('found {0} in sock requests'.format(len(self.in_sockets)))
            print('found {0} out sock requests'.format(len(self.out_sockets)))

            if self.in_sockets and self.out_sockets:
                self.create_or_update_sockets()
            return

        print('load_py, failed because introspection failed')
        self.use_custom_color = True
        self.color = FAIL_COLOR

    def load_cf(self):
        pass

    '''
    update(_*)
    - performed whenever Sverchok is scheduled to update.
    - also triggered by socket updates
    '''

    def update(self):
        if not self.inputs:
            return

        if not hash(self) in self.node_dict:
            if self.script_str:
                self.load_function()
            else:
                self.load()
        # backwards compability 
        if self.script_str and not self.script_name:
            self.script_name = self.script

        self.update_py()

    def update_py(self):

        node_function = self.node_dict[hash(self)].get('node_function', None)
        if not node_function:
            return

        defaults = node_function.__defaults__
        input_names = [i.name for i in self.inputs]

        fparams = []
        for param_idx, name in enumerate(input_names):
            links = self.inputs[name].links
            this_val = defaults[param_idx]

            if links:
                if isinstance(this_val, list):
                    try:
                        this_val = SvGetSocketAnyType(self, self.inputs[param_idx])
                        this_val = dataCorrect(this_val)
                    except:
                        this_val = defaults[param_idx]
                elif isinstance(this_val, (int, float)):
                    try:
                        k = str(SvGetSocketAnyType(self, self.inputs[name]))
                        kfree = k[2:-2]
                        this_val = ast.literal_eval(kfree)
                    except:
                        this_val = defaults[param_idx]

            fparams.append(this_val)

        if node_function and (len(fparams) == len(input_names)):

            fn_return_values = node_function(*fparams)
            out_sockets = fn_return_values[1]

            for socket_type, name, data in out_sockets:
                SvSetSocketAnyType(self, name, data)

    def update_coffee(self):
        pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvScriptNode)
    bpy.utils.register_class(SvDefaultScriptTemplate)
    bpy.utils.register_class(SvScriptNodeCallbackOp)
    bpy.utils.register_class(SvScriptUICallbackOp)


def unregister():
    bpy.utils.unregister_class(SvDefaultScriptTemplate)
    bpy.utils.unregister_class(SvScriptNode)
    bpy.utils.unregister_class(SvScriptNodeCallbackOp)
    bpy.utils.unregister_class(SvScriptUICallbackOp)
