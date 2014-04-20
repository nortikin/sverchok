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
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.props import IntProperty, FloatProperty
from node_s import *
from util import *
import ast

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
        lines_a = [i for i in lines if script in i]
        lines_b = [i for i in lines if ('def sv_main') in i]

        if len(lines_a) == 1:
            pattern = '\{(\d+?)\}'
            f = re.findall(pattern, lines_a[0])
            num_params = len(f)
        else:
            print('expected something like: scriptname = sv_main({0},{1},..)')
            return False, False

        if len(lines_b) == 1:
            pattern2 = '=(.+?)[,\)]'
            param_values = re.findall(pattern2, lines_b[0])
        else:
            print('your def sv_main must contain variable_names and defaults')
            return False, False

        return num_params, param_values

    '''
    this section shall
    - retrieve variables
    - return None in the case of any failure
    '''
    nparams, params = find_variables(script_str)
    if all([nparams, params]):
        params = list(map(ast.literal_eval, params))
    else:
        print('see demo files for NodeScript')
        return

    exec(script_str.format(*params))
    f = vars()

    # this will return a callable function if sv_main is found, else None
    return [f.get('sv_main', None), params]

class SvDefaultScriptTemplate(bpy.types.Operator):
    ''' Creates template text file for making own script '''
    bl_idname = 'node.sverchok_script_template'
    bl_label = 'Template'
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        texts = bpy.data.texts.items()
        exists = False
        for t in texts:
            if bpy.data.texts[t[0]].name == 'template':
                exists = True
                break
        bpy.context.area.type = 'TEXT_EDITOR'
        if not exists:
            bpy.ops.text.new()
            texts_new = bpy.data.texts.items()
            for t in texts_new:
                if t not in texts:
                    bpy.data.texts[t[0]].name = 'template'
        bpy.ops.text.select_all()
        template = '''def sv_main(data=23,step=1):
    
    # in boilerplate - make your own sockets
    in_sockets = [
        ['s', 'Vertices',  data],
        ['s', 'Step', step],
    ]
    
    # import libreryes - your defined
    from util import sv_zip
    from math import sin
    
    # your's code here
    out_x = [i for i in range(int(data))]
    out_y = [0 for i in range(int(data))]
    out_z = [sin(i*step) for i in range(int(data))]
    out = [list(sv_zip(out_x,out_y,out_z))]
    edg=[[i,i-1] for i, ed in enumerate(out_x) if i>0]
     
    # out boilerplate - set your own sockets packet
    out_sockets = [
        ['v', 'Out', out],
        ['s', 'edg', [edg]],
    ]

    return in_sockets, out_sockets

if __name__ == "__main__":
    # here is yors script's name - must be the same as in blender's text datablock
    template = sv_main({0},{1})'''
        
        bpy.data.texts['template'].from_string(template)
        bpy.context.area.type = 'NODE_EDITOR'
        return {'FINISHED'}
                        

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


class SvScriptNode(Node, SverchCustomTreeNode):
    ''' Text Input '''
    bl_idname = 'SvScriptNode'
    bl_label = 'Script Generator'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def avail_scripts(self, context):
        scripts = bpy.data.texts
        items = [(t.name, t.name, "") for t in scripts]
        return items

    script = EnumProperty(
        items=avail_scripts,
        name="Texts",
        description="Choose text to load",
        update=updateNode)

    script_modes = [
        ("Py", "Python", "Python File", "", 1),
        ("coffee", "CoffeeScript", "cf File", "", 2)]

    scriptmode = EnumProperty(
        items=script_modes,
        default='Py',
        update=updateNode)

    # stores the script as a string
    script_str = StringProperty(default="")

    #parametric_in = {}
    node_function = None
    in_sockets = []
    out_sockets = []

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):
        layout.prop(self, "script", "Select Script")
        layout.prop(self, 'scriptmode', 'scriptmode', expand=True)

        row = layout.row(align=True)
        if not self.script_str:
            row.operator('node.sverchok_script_template', text='Template')
        op = row.operator('node.sverchok_script_input', text='Load')
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

        input_names = [i.name for i in self.inputs]
        params = []
        for name in input_names:
            links = self.inputs[name].links
            if not links:
                continue

            k = str(SvGetSocketAnyType(self, self.inputs[name]))
            kfree = k[2:-2]
            params.append(ast.literal_eval(kfree))

        # for now inputs in script must be matched by socket inputs.
        if len(params) == len(input_names):
            #print(params)
            pass
        else:
            return

        def get_sv_main(params):
            exec(self.script_str.format(*params))
            f = vars()
            return f

        f = get_sv_main(params)
        node_function = f.get('sv_main', None)

        if node_function:
            in_sockets, out_sockets = node_function(*params)

            for socket_type, name, data in out_sockets:
                SvSetSocketAnyType(self, name, data)

    def update_coffee(self):
        pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvScriptOp)
    bpy.utils.register_class(SvScriptNode)
    bpy.utils.register_class(SvDefaultScriptTemplate)


def unregister():
    bpy.utils.unregister_class(SvDefaultScriptTemplate)
    bpy.utils.unregister_class(SvScriptNode)
    bpy.utils.unregister_class(SvScriptOp)


if __name__ == "__main__":
    register()
