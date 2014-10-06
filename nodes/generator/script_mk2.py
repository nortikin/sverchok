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

import inspect
import os

import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatVectorProperty,
    IntVectorProperty
)

from utils.sv_tools import sv_get_local_path
from utils.sv_script import SvScript
from node_tree import SverchCustomTreeNode
from data_structure import (
    dataCorrect, updateNode, SvSetSocketAnyType, SvGetSocketAnyType, node_id)

sv_path = os.path.dirname(sv_get_local_path()[0])


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



socket_types = {
    'v': 'VerticesSocket',
    's': 'StringsSocket',
    'm': 'MatrixSocket'
}

# for number lists
defaults = [0 for i in range(32)]

class SvScriptNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    
    bl_idname = 'SvScriptNodeMK2'
    bl_label = 'Script Node 2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def avail_templates(self, context):
        templates_path = os.path.join(sv_path, "node_scripts", "SN2-templates")
        items = [(t, t, "") for t in next(os.walk(templates_path))[2]]
        items.sort(key=lambda x:x[0].upper())
        return items

    files_popup = EnumProperty(
        items=avail_templates,
        name='template_files',
        description='choose file to load as template')

    script_objects = {}
    
    n_id = StringProperty()
    
    # Also used to keep track if a script is loaded.
    script_str = StringProperty()
    script_file_name = StringProperty(name = "Text file", description = "Text file containing script")
    
    int_list = IntVectorProperty(
        name='int_list', description="Integer list",
        default=defaults, size=32, update=updateNode)

    float_list = FloatVectorProperty(
        name='float_list', description="Float list",
        default=defaults, size=32, update=updateNode)
    
    def load_script(self):
        try:
            code = compile(self.script_str, '<string>', 'exec', optimize=2)
            # insert classes that we can inherit from
            local_space = {cls.__name__:cls for cls in SvScript.__subclasses__()}
            local_space["SvScript"] = SvScript
            
            exec(code, globals(),local_space)
            print(local_space)
        except SyntaxError as err:
            print("Script Node, load error: {}".format(err))
            return
        except TypeError:
            print("No script found")
            return
        locals()
        for name in code.co_names:
            print(name)
            try: 
                script_class = local_space.get(name)
                if inspect.isclass(script_class):
                    script = script_class()
                    if isinstance(script, SvScript):
                        print("Script Node found script {}".format(name))
                        self.script = script
                        globals().update(local_space)
            except Exception as Err:
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
                if len(args) > 1 and args[1] not in self.outputs:
                    stype = socket_types[args[0]]
                    self.outputs.new(stype, args[1])
    
    def clear(self):
        self.script_str = ""
        del self.script
        self.inputs.clear()
        self.outputs.clear()
    
    
    #  reload/load are very similar...
    #  should be purged or re structured
    #  kept for a short while more    
    
    def reload(self):
        self.script_str = bpy.data.texts[self.script_file_name].as_string()
        print("reloading...")
        self.load_script()
        self.create_sockets()
    
    def load(self):
        self.script_str = bpy.data.texts[self.script_file_name].as_string()
        print("loading...")
        self.load_script()
        self.create_sockets()
    
    def update(self):
        if not self.script_str:
            return
            
        script = self.script
        
        if not script:
            self.reload()
            # if create socket another update event will fire anyway
            # needs some more testing
            return
        if hasattr(script, 'update'):
            script.update()
        else:
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
    
    # property function for accessing self.script
    def _set_script(self, value):
        n_id = node_id(self)
        value.node = self
        self.script_objects[n_id] = value
        
    def _del_script(self):       
        n_id = node_id(self)
        if n_id in self.script_objects:
            del self.script_objects[n_id]
    
    def _get_script(self):
        n_id = node_id(self)
        script = self.script_objects.get(n_id)
        if script:
            script.node = self # paranoid update often safety setting
        return script
        
    script = property(_get_script, _set_script, _del_script, "The script object for this node")
    
    
    
    def draw_buttons(self, context, layout):
        
        col = layout.column(align=True)
        row = col.row()
        script = self.script
        if not self.script_str:
            row.prop(self, 'files_popup', '')
            import_operator = row.operator('node.sverchok_script2_template', text='', icon='IMPORT')
            import_operator.script_name = self.files_popup
            row = col.row()
            row.prop_search(self, 'script_file_name', bpy.data, 'texts', text='', icon='TEXT')
            row.operator('node.sverchok_text_callback', text='', icon='PLUGIN').fn_name = 'load'
        else:
            row = col.row()
            row.operator("node.sverchok_text_callback", text='Reload').fn_name = 'reload'
            row.operator("node.sverchok_text_callback", text='Clear').fn_name = 'clear'
            if hasattr(script, "draw_buttons"):
                script.draw_buttons(context, layout)
    
    def draw_label(self):
        script = self.script
        if script:
            if hasattr(script, 'name'):
                return script.name
            else:
                return script.__class__.__name__
        else:
            return self.bl_label
    
        

def register():
    bpy.utils.register_class(SvScriptNodeMK2)    
    bpy.utils.register_class(SvDefaultScript2Template)


def unregister():
    bpy.utils.unregister_class(SvScriptNodeMK2)
    bpy.utils.unregister_class(SvDefaultScript2Template)
