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
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

def create_uvmap(obj_in, uv_name):
    #Create basic UV map for object in scene with current name
    [obj.data.uv_textures.new(uv_name) for obj in obj_in 
        if not obj.data.uv_textures.get(uv_name, False)]
    
def set_uvmap(uv_name, loop_ver, obj_in):
    #Set custom UV maps with current name for current objects in scene
    for uv_obj, obj in zip(loop_ver, obj_in):
        
        xy_uv = [(u,v) for u,v,_ in uv_obj]
        per_loop_list = [uv for pair in xy_uv for uv in pair]
    
        obj.data.uv_layers[uv_name].data.foreach_set("uv", per_loop_list)

class SvSetUVMap(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Set UV Map
    Tooltip: This is bridge between ordinary data of sverchok and space of UV mapping
    
    How to wrapping a mesh is your headache.) So you absolutely free in this.
    """
    
    bl_idname = 'SvSetUVMap'
    bl_label = 'Set UV Map'
    bl_icon = 'GROUP_UVS'
    
    UV_name = StringProperty(name='Name', default='SVMap', update=updateNode)
    
    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Loops vertices')
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('SvObjectSocket', 'Object')
        
    def draw_buttons(self, context, layout):
        layout.prop(self, 'UV_name')
        
    def process(self):
            
        if self.inputs['Object'].is_linked or len(self.inputs['Object'].values()[0]) != 0:
            obj_in  = self.inputs['Object'].sv_get()
            uv_name = self.UV_name
            
            create_uvmap(obj_in, uv_name)
    
            if self.inputs['Loops vertices'].is_linked:
                loop_ver = self.inputs['Loops vertices'].sv_get()
                
                set_uvmap(uv_name, loop_ver, obj_in)

    
def register():
    bpy.utils.register_class(SvSetUVMap)

def unregister():
    bpy.utils.unregister_class(SvSetUVMap)
