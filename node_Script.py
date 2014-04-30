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

    def find_variables(script_str):
        import re

        lines = script_str.split('\n')
        lines_b = [i for i in lines if ('def sv_main') in i]

        if len(lines_b) == 1:

            # yes, I could do this with capture groups.
            function_line = lines_b[0]
            pattern1 = '=(.+?)[,\)]'
            param_values = re.findall(pattern1, function_line)

        else:
            print('your def sv_main must contain variable_names and defaults')
            return False

        return param_values

    '''
    this section shall
    - retrieve variables
    - return None in the case of any failure
    '''
    params = find_variables(script_str)
    if params:
        params = list(map(ast.literal_eval, params))
    else:
        print('see demo files for NodeScript')
        return

    exec(script_str)
    f = vars()

    # this will return a callable function if sv_main is found, else None
    return [f.get('sv_main', None), params]


class SvDefaultScriptTemplate(bpy.types.Operator):

    ''' Creates template text file to start making your own script '''
    bl_idname = 'node.sverchok_script_template'
    bl_label = 'Template'
    bl_options = {'REGISTER'}

    script_name = StringProperty(name='name', default='')

    def execute(self, context):
        if self.script_name in bpy.data.texts:
            msg = 'template exists already'
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}

        new_template = bpy.data.texts.new(self.script_name)

        sv_path = os.path.dirname(os.path.realpath(__file__))
        script_dir = "node_script_templates"
        path_to_template = os.path.join(sv_path, script_dir, self.script_name)

        with open(path_to_template) as f:
            template_str = f.read()
            bpy.data.texts[self.script_name].from_string(template_str)
            return {'FINISHED'}

        return {'CANCELLED'}


class SvScriptOp(bpy.types.Operator):

    """ Load Script as Generator """
    bl_idname = "node.sverchok_script_input"
    bl_label = "Sverchok script input"
    bl_options = {'REGISTER', 'UNDO'}

    # from object in
    name_obj = StringProperty(name='object name')
    name_tree = StringProperty(name='tree name')

    def execute(self, context):
        print('pressed load')
        node = bpy.data.node_groups[self.name_tree].nodes[self.name_obj]
        node.load()
        return {'FINISHED'}


class SvNodeSelfNuke(bpy.types.Operator):

    bl_idname = "node.sverchok_scriptnode_nuke"
    bl_label = "Sverchok scriptnode nuke"
    bl_options = {'REGISTER', 'UNDO'}

    # from object in
    name_obj = StringProperty(name='object name')
    name_tree = StringProperty(name='tree name')

    def execute(self, context):
        print('pressed nuke, Boom')
        node = bpy.data.node_groups[self.name_tree].nodes[self.name_obj]
        node.nuke_me(context)
        node.script_str = ""
        return {'FINISHED'}


class SvScriptNode(Node, SverchCustomTreeNode):

    ''' Text Input '''
    bl_idname = 'SvScriptNode'
    bl_label = 'Script Generator'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def avail_scripts(self, context):
        scripts = bpy.data.texts
        items = [(t.name, t.name, "") for t in scripts]
        return items

    def avail_templates(self, context):
        sv_path = os.path.dirname(os.path.realpath(__file__))
        script_dir = "node_script_templates"
        path = os.path.join(sv_path, script_dir)
        items = [(t, t, "") for t in next(os.walk(path))[2]]
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

    script_modes = [
        ("Py", "Python", "Python File", "", 1),
        ("coffee", "CoffeeScript", "cf File", "", 2)]

    scriptmode = EnumProperty(
        items=script_modes,
        default='Py',
        update=updateNode)

    script_str = StringProperty(default="")

    node_function = None
    in_sockets = []
    out_sockets = []

    def init(self, context):
        pass

    def nuke_me(self, context):
        in_out = [self.inputs, self.outputs]
        for socket_set in in_out:
            while len(socket_set) > 0:
                socket_set.remove(socket_set[-1])
        # maybe do this with one swoop instead.

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        if not self.script_str:
            row = col.row(align=True)
            row.label(text='DOWNLOAD PY:')
            row = col.row(align=True)
            row.prop(self, 'files_popup', '')
            tem = row.operator(
                'node.sverchok_script_template', text='Template')
            tem.script_name = self.files_popup

            #row = col.row(align=True)
            #row.prop(self, 'scriptmode', 'scriptmode', expand=True)
            row = col.row(align=True)
            row.label(text='USE PY:')
            row = col.row(align=True)
            row.prop(self, "script", "")
            op = row.operator('node.sverchok_script_input', text='Load')
            op.name_tree = self.id_data.name
            op.name_obj = self.name
        else:
            row = col.row()
            col2 = row.column()
            col2.scale_x = 0.05
            col2.label(icon='TEXT', text=' ')
            row.label(text='LOADED:')
            row = col.row()
            row.label(text=self.script)
            row = col.row()
            op = row.operator('node.sverchok_script_input', text='Reload')
            op = row.operator('node.sverchok_scriptnode_nuke', text='Nuke')
            op.name_tree = self.id_data.name
            op.name_obj = self.name

    def create_or_update_sockets(self):
        '''
        - desired features not flly implemente yet (only socket add so far)
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
    - these are done once upon pressing load button, depending on scriptmode
    '''

    def load(self):
        # user picks script from dropdown.
        self.script_str = bpy.data.texts[self.script].as_string()
        if self.scriptmode == 'Py':
            self.load_py()

    def load_py(self):
        details = instrospect_py(self)
        if details:
            if details[0] is None:
                print('should never reach here')
                pass
            self.node_function, params = details
            self.in_sockets, self.out_sockets = self.node_function(*params)

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
        if self.scriptmode == 'Py':
            self.update_py()
        elif self.scriptmode == 'coffee':
            self.update_cf()

    def update_py(self):
        '''
        triggered when update is called, ideally this
        - runs script with default values for those in_sockets not connected
        - does nothing if input is unchanged.
        '''
        if not self.inputs:
            return

        def get_sv_main():
            exec(self.script_str)
            f = vars()
            return f

        f = get_sv_main()
        node_function = f.get('sv_main', None)

        if not node_function:
            return

        defaults = node_function.__defaults__
        input_names = [i.name for i in self.inputs]

        fparams = []
        for param_idx, name in enumerate(input_names):
            links = self.inputs[name].links
            if not links:
                this_val = defaults[param_idx]
            else:
                try:
                    k = str(SvGetSocketAnyType(self, self.inputs[name]))
                    kfree = k[2:-2]
                    this_val = ast.literal_eval(kfree)
                except:
                    this_val = defaults[param_idx]

            fparams.append(this_val)

        if node_function and (len(fparams) == len(input_names)):

            _, out_sockets = node_function(*fparams)
            for socket_type, name, data in out_sockets:
                SvSetSocketAnyType(self, name, data)

    def update_coffee(self):
        pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvScriptOp)
    bpy.utils.register_class(SvScriptNode)
    bpy.utils.register_class(SvNodeSelfNuke)
    bpy.utils.register_class(SvDefaultScriptTemplate)


def unregister():
    bpy.utils.unregister_class(SvNodeSelfNuke)
    bpy.utils.unregister_class(SvDefaultScriptTemplate)
    bpy.utils.unregister_class(SvScriptNode)
    bpy.utils.unregister_class(SvScriptOp)


if __name__ == "__main__":
    register()
