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

# author Linus Yng


import ast
import os

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty

from utils.sv_tools import sv_get_local_path
from node_tree import SverchCustomTreeNode
from data_structure import (
    dataCorrect, updateNode, SvSetSocketAnyType, SvGetSocketAnyType, node_id)

sv_path = os.path.dirname(sv_get_local_path()[0])


def recursive_depth(l):
    if isinstance(l, (list, tuple)) and l:
        return 1 + recursive_depth(l[0])
    elif isinstance(l, (int, float, str)):
        return 0
    else:
        return None

def vectorize(*args, **kwargs):
    # find level
    
    if (isinstance(l1, (int, float)) and isinstance(l2, (int, float))):
            return f(l1, l2)
            
    if (isinstance(l2, (list, tuple)) and isinstance(l1, (list, tuple))):
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        res = []
        res_append = res.append
        for x, y in zip_longest(l1, l2, fillvalue=fl):
            res_append(self.recurse_fxy(x, y, f))
        return res
    
    # non matching levels    
    if isinstance(l1, (list, tuple)) and isinstance(l2, (int, float)):
        return self.recurse_fxy(l1, [l2], f)
    if isinstance(l1, (int, float)) and isinstance(l2, (list, tuple)):
        return self.recurse_fxy([l1], l2, f)



class SvDefaultScript2Template(bpy.types.Operator):
    ''' Imports example script or template file in bpy.data.texts'''

    bl_idname = 'node.sverchok_script2_template'
    bl_label = 'Template'
    bl_options = {'REGISTER'}

    script_name = StringProperty(name='name', default='')

    def execute(self, context):
        # if a script is already in text.data list then 001 .002
        # are automatically append by ops.text.open
        templates_path = os.path.join(sv_path, "node_scripts", "SN2-templates")
        path_to_template = os.path.join(templates_path, self.script_name)
        bpy.ops.text.open(filepath=path_to_template, internal=True)
        return {'FINISHED'}


class SvScript:
    
    node = None
    
    
    def get_data(self):
        '''Support function to get raw data from node'''
        node = self.node
        if node:
            return [(s.name, s.sv_get()) for s in node.inputs if s.links]
        else:
            raise Error
    
    def set_data(self, data):
        '''
        Support function to set data
        '''
        node = self.node
        for name, d in data.items():
            node.outputs[name].sv_set(d)
        
        
socket_types = {
    'v': 'VerticesSocket',
    's': 'StringsSocket',
    'm': 'MatrixSocket'
}

class SvScriptNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    
    bl_idname = 'SvScriptNodeMK2'
    bl_label = 'Script Node 2'
    bl_icon = 'OUTLINER_OB_EMPTY'


    # unloaded ui
        
    def avail_scripts(self, context):
        scripts = bpy.data.texts
        items = [(t.name, t.name, "") for t in scripts]
        items.sort(key=lambda x:x[0].upper())
        return items

    def avail_templates(self, context):
        templates_path = os.path.join(sv_path, "node_scripts", "SN2-templates")
        items = [(t, t, "") for t in next(os.walk(templates_path))[2]]
        items.sort(key=lambda x:x[0].upper())
        return items

    files_popup = EnumProperty(
        items=avail_templates,
        name='template_files',
        description='choose file to load as template')

    script_popup = EnumProperty(
        items=avail_scripts,
        name="Texts",
        description="Choose text to load in node")


    script_objects = {}
    script_types = {}
    
    n_id = StringProperty()
    script_str = StringProperty()
    script_name = StringProperty()
    script_file_name = StringProperty()
    
    
    
    def load_script(self):
        try:
            code = compile(self.script_str, '<string>', 'exec')
            global_space = {}
            local_space = {"SvScript": SvScript}
            exec(code, global_space, local_space)
        except SyntaxError as err:
            print("Script Node, load error: {}".format(err))
            return
        except TypeError:
            print("No script found")
            return
        
        for name in code.co_names:
            try: 
                script = local_space[name]()
                if isinstance(script, SvScript):
                    print("Script Node found script {}".format(name))
                    self.script = script
                    self.script_types[name] = local_space[name]
                    if hasattr(script, "name"):
                        self.script_name = script.name
                    else:
                        self.script_name = name
            except Err:
                print("Script Node couldn't load {0}".format(name))
                print(str(Err)) 
                pass
    
    # better logic should be taken from old script node
    def create_sockets(self):
        script = self.script
        if script:
            for args in script.inputs:
                if args[1] in self.inputs:
                    continue
                    
                socket_types
                stype = socket_types[args[0]]
                name = args[1]
                if len(args) == 2:  
                    self.inputs.new(stype, name)
                elif len(args) == 3:
                    socket = self.inputs.new(stype, name)
                    default_value = args[2]
                    offset = len(self.inputs)
                    if isinstance(default_value, int):
                        self.int_list[offset] = default_value
                        socket.prop_type = "int_list"
                    elif isinstance(default_value, float):
                        self.float_list[offset] = default_value
                        socket.prop_type = "float_list"
                    socket.prop_index = offset
                    
            for args in script.outputs:            
                if len(args) == 2 and args[1] not in self.outputs:
                    self.outputs.new("StringsSocket", args[1])
    
    
    def clear(self):
        self.script_name = ""
        self.script_file_name = ""
        del self.script
        self.inputs.clear()
        self.outputs.clear()
        
    
    def reload(self):
        self.script_str = bpy.data.texts[self.script_file_name].as_string()
        print("reloading...")
        self.load_script()
        self.create_sockets()
    
    def load(self):
        self.script_file_name = self.script_popup
        self.script_str = bpy.data.texts[self.script_file_name].as_string()
        print("loading...")
        self.load_script()
        self.create_sockets()
    
    def update(self):
        if not self.script_name:
            return
        script = self.script
        if not script:
            self.reload()
            # if create socket another update event will fire anyway
            return
        # basic sanity
        if len(script.inputs) != len(self.inputs):
            return
        if len(script.outputs) != len(self.outputs):
            return
        # check if no default and not linked, return
        for data, socket in zip(script.inputs, self.inputs): 
            if len(data) == 2 and not socket.links:
                return
        self.process()
    
    def process(self):
        script = self.script
        if not script:
            return
        script.process()
        
                        
    def copy(self, node):
        self.n_id = ""
        node_id(self)
                
    def init(self, context):
        node_id(self)
    
    def set_script(self, value):
        n_id = node_id(self)
        value.node = self
        self.script_objects[n_id] = value
        
    def del_script(self):
        n_id = node_id(self)
        if n_id in self.script_objects:
            del self.script_objects[n_id]
    
    def get_script(self):
        n_id = node_id(self)
        script = self.script_objects.get(n_id)
        if script:
            script.node = self # paranoid update often safety setting
        return script
        
    script = property(get_script, set_script, del_script, "The script object for this node")
    
    
    
    def draw_buttons(self, context, layout):
        
        col = layout.column(align=True)
        
        if not self.script_name:
            row = col.row(align=True)
            row.label(text='IMPORT PY:')
            row = col.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(self, 'files_popup', '')
            row.operator(
                'node.sverchok_script2_template',
                text='', icon='IMPORT').script_name = self.files_popup
            row = col.row(align=True)
            row.label(text='USE PY:')
            row = col.row(align=True)
            #row.prop(self, "script_popup", "")
            row.prop_search(self, 'script_popup', bpy.data, 'texts', text='', icon='TEXT')
            row.operator('node.sverchok_text_callback', text='', icon='PLUGIN').fn_name = 'load'

        else:
            script = self.script
            row = col.row()
            col2 = row.column()
            col2.scale_x = 0.05
            col2.label(icon='TEXT', text=' ')
            row.label(text='LOADED: {0}'.format(self.script_file_name))
            row = col.row()
            row.label(text=self.script_name)
            row = col.row()
            row.operator("node.sverchok_text_callback", text='Reload').fn_name = 'reload'
            row.operator("node.sverchok_text_callback", text='Clear').fn_name = 'clear'

                    
    def draw_buttons_ext(self, context, layout):
        pass
    
    def draw_label(self):
        if self.script_name:
            return self.script_name
        else:
            return self.bl_label
    
        

def register():
    bpy.utils.register_class(SvScriptNodeMK2)    
    bpy.utils.register_class(SvDefaultScript2Template)


def unregister():
    bpy.utils.unregister_class(SvScriptNodeMK2)
    bpy.utils.unregister_class(SvDefaultScript2Template)
