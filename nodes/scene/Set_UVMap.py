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
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last

WARNING = []

def create_uvmap(obj_in, uv_name):
    #Create basic UV map for object in scene with current name
    [obj.data.uv_textures.new(uv_name) for obj in obj_in 
        if not obj.data.uv_textures.get(uv_name, False)]
        
def remove_uv(obj_in, uv_name):
    #Remove UV map from objects with current name of map
    [obj.data.uv_textures.remove(obj.data.uv_textures[uv_name]) for obj in obj_in 
        if obj.data.uv_textures.get(uv_name, False)]
        
def make_worning(bo):
    w = lambda n: print("Set UVMap node - input data have wrong size in %d.object." % n)
    [w(n) for n,b in enumerate(bo) if b]
    
def set_uvmap(uv_name, loop_ver, obj_in, mat_in):
    #Set custom UV maps with current name for current objects in scene
    for uv_obj, obj, mat_obj in zip(loop_ver, obj_in, repeat_last(mat_in)):
        
        len_loop = len(obj.data.loops)
        len_uv_in = len(uv_obj)
        WARNING.append(False if len_loop == len_uv_in else True)
        
        if len_loop < len_uv_in:
            uv_obj = uv_obj[0:len_loop]
        elif len_loop > len_uv_in:
            uv_obj = [uv for _, uv in zip(range(len_loop), repeat_last(uv_obj))]
        
        xy_uv = [(u,v) for u,v,_ in uv_obj]
        
        if mat_obj:
            xy_uv = [(mat * Vector(uv).to_3d())[:2] for uv, mat in zip(xy_uv, repeat_last(mat_obj))]
        
        per_loop_list = [uv for pair in xy_uv for uv in pair]
    
        obj.data.uv_layers[uv_name].data.foreach_set("uv", per_loop_list)
        
def deform_baseuv(uv_name, obj_in, mat_in):
    #It removes and creates new map each time before make deform
    for obj, mat in zip(obj_in, repeat_last(mat_in)):

        obj.data.uv_textures.remove(obj.data.uv_textures[uv_name])
        obj.data.uv_textures.new(uv_name)
        
        uv_co = [l.uv for l in obj.data.uv_layers[uv_name].data]
        
        xy_uv = [(m * l.to_3d())[:2] for l, m in zip(uv_co, repeat_last(mat))]
        per_loop_list = [uv for pair in xy_uv for uv in pair]
        
        obj.data.uv_layers[uv_name].data.foreach_set("uv", per_loop_list)
        
def check_data_in(soc):
    #puts data in nested list if necessary
    
    if type(soc.sv_get()[0]) == list:
        return soc.sv_get()
    else:
        return [soc.sv_get()]

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
        self.inputs.new('MatrixSocket', 'Matrix')
        self.inputs.new('SvObjectSocket', 'Object')
        self.outputs.new('SvObjectSocket', 'Object')
        
    def draw_buttons(self, context, layout):
        layout.prop(self, 'UV_name')
        
    def process(self):
            
        if not (self.inputs['Object'].is_linked or len(self.inputs['Object'].values()[0]) != 0):
            return

        obj_in  = self.inputs['Object'].sv_get()
        uv_name = self.UV_name
        mat_in  = (check_data_in(self.inputs['Matrix']) 
                   if self.inputs['Matrix'].is_linked else [False])
        loop_ver = (self.inputs['Loops vertices'].sv_get()
                    if self.inputs['Loops vertices'].is_linked else None)
            
        create_uvmap(obj_in, uv_name)
    
        if self.inputs['Loops vertices'].is_linked:
            #Mode with own unwrapping
            set_uvmap(uv_name, loop_ver, obj_in, mat_in)
            make_worning(WARNING)
                
        elif self.inputs['Matrix'].is_linked:
            #Mode with bas unwrapping
            deform_baseuv(uv_name, obj_in, mat_in)
                
        self.outputs['Object'].sv_set(self.inputs['Object'].sv_get())

    
def register():
    bpy.utils.register_class(SvSetUVMap)

def unregister():
    bpy.utils.unregister_class(SvSetUVMap)
