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
from node_s import *
from util import *
from mathutils import Vector, Matrix


class VectorMathNode(Node, SverchCustomTreeNode):
    ''' VectorMathNode '''
    bl_idname = 'VectorMathNode'
    bl_label = 'Vector Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
 
# vector math functions
  # normalize, length 
    mode_items = [
        ("CROSS",       "Cross product",        ""), 
        ("DOT",         "Dot product",          ""), 
        ("ADD",         "Add",                  ""),   
        ("SUB",         "Sub",                  ""),
        ("LEN",         "Length",               ""),
        ("DISTANCE",    "Distance",             ""),
        ("NORMALIZE",   "Normalize",            ""),
        ("NEG",         "Negate",               ""),       
        ]
        
        
    items_=bpy.props.EnumProperty( items = mode_items, name="Function", 
            description="Function choice", default="CROSS", update=updateNode)
    #matches default of CROSS product
    scalar_output_socket = False
    
    def draw_buttons(self, context, layout):
        layout.prop(self,"items_","Functions:");

    def init(self, context):
        self.inputs.new('VerticesSocket', "U", "u") 
        self.inputs.new('VerticesSocket', "V", "v")        
        self.outputs.new('VerticesSocket', "W", "W")
        

    def update(self):
    
        scalar_out = {
            "DOT"       :   (lambda u,v  : u.dot(v) , 2),
            "DISTANCE"  :   (lambda u,v : (u-v).length, 2),
            "LEN"       :   (lambda u   : u.length,1)
         }
         
        vector_out = {
            "CROSS"     :   (lambda u,v : u.cross(v) , 2),
            "ADD"       :   (lambda u,v : u + v, 2),
            "SUB"       :   (lambda u,v : u - v, 2),
            "NORMALIZE" :   (lambda u   : u.normalized(), 1),
            "NEG"       :   (lambda u   : -u, 1)
        }   
                   
    # check and adjust outputs and input size
        
        if self.items_ in scalar_out:
            nrInputs = scalar_out[self.items_][1]
            if 'W' in self.outputs:
                self.outputs.remove(self.outputs['W'])
                self.outputs.new('StringsSocket', "out", "out")  
            self.scalar_output_socket = True
                
        elif self.items_ in vector_out:
            nrInputs = vector_out[self.items_][1]
            if 'out' in self.outputs:
                self.outputs.remove(self.outputs['out'])
                self.outputs.new('VerticesSocket', "W", "W")
            self.scalar_output_socket = False
    # adjust inputs
        
        if nrInputs < len(self.inputs):
            self.inputs.remove(self.inputs['V'])
        elif nrInputs > len(self.inputs):
            self.inputs.new('VerticesSocket', "V", "v")        
   
        self.label=self.items_     

# get inputs
        
        if 'U' in self.inputs and len(self.inputs['U'].links)>0 and \
            type(self.inputs['U'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['U'].node.socket_value_update:
                self.inputs['U'].node.update()
            vector1 = self.inputs['U'].links[0].from_socket.VerticesProperty
        else:
            vector1 = []
        
        if 'V' in self.inputs and len(self.inputs['V'].links)>0 and \
            type(self.inputs['V'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['V'].node.socket_value_update:
                self.inputs['V'].node.update()
            vector2 = self.inputs['V'].links[0].from_socket.VerticesProperty
        else:   
            vector2 = []
                   
        # vector-output
        if 'W' in self.outputs and len(self.outputs['W'].links)>0:
            if not self.outputs['W'].node.socket_value_update:
                self.outputs['W'].node.update()
            result = []
       
            if nrInputs == 1:
                if len(vector1):
                    u = eval(vector1)
                    result = self.recurse_fx(u,vector_out[self.items_][0])
            if nrInputs == 2:
                if len(vector1) and len(vector2):
                    u = eval(vector1)
                    v = eval(vector2)
                    result = self.recurse_fxy(u,v,vector_out[self.items_][0])                 
            self.outputs['W'].VerticesProperty = str(result)
   
        #scalar-output    
        if 'out' in self.outputs and len(self.outputs['out'].links)>0:
            if not self.outputs['out'].node.socket_value_update:
                self.outputs['out'].node.update() 
            result = []   
            if nrInputs == 1:
                if len(vector1):
                    u = eval(vector1)
                    result = self.recurse_fx(u,scalar_out[self.items_][0])            
            if nrInputs == 2:
                if len(vector1) and len(vector2):
                    u = eval(vector1)
                    v = eval(vector2)
                    result = self.recurse_fxy(u,v,scalar_out[self.items_][0])
                    
            self.outputs['out'].StringsProperty = str(result)
                    

# apply f to all values recursively  
        
    def recurse_fx(self, l,f):
        if type(l) is tuple:
            w = f(Vector(l))
            if self.scalar_output_socket:
                return w
            else:
                return w.to_tuple()     
        else:
            t = []
            for i in l:
                t.append(self.recurse_fx(i,f))
        return t
        
# match length of lists, 
# taken from mathNode
 
    def recurse_fxy(self,l1, l2, f):
        if type(l1) is tuple and \
           type(l2) is tuple:
                w=f(Vector(l1),Vector(l2))
                if self.scalar_output_socket:
                    return w
                else:
                    return w.to_tuple()
        if type(l1) is list and type (l2) is list:
            max_obj = max(len(l1),len(l2)) 
            fullList(l1,max_obj)
            fullList(l2,max_obj)    
            res = []
            for i in range(len(l1)):
                res.append( self.recurse_fxy(l1[i], l2[i],f))
            return res    
        if type(l1) is list and type(l2) is tuple:
            return self.recurse_fxy(l1,[l2],f)
        if type(l2) is list and type(l1) is tuple:
            return self.recurse_fxy([l1],l2,f)
            
            
    def update_socket(self, context):
        self.update()        
   
    

def register():
    bpy.utils.register_class(VectorMathNode)
    
def unregister():
    bpy.utils.unregister_class(VectorMathNode)

if __name__ == "__main__":
    register()