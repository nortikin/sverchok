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

# Matrix are assumed to be in format
# [M1 M2 Mn ...] per Matrix_generate and Matrix_listing
# Instead of empty matrix input identity matrix is used.
# So only one matrix input is needed for useful result
# Factor a list of value float values between 0.0 and 1.0,


class MatrixInterpolationNode(Node, SverchCustomTreeNode):
    ''' Interpolate between two matrices '''
    bl_idname = 'MatrixInterpolationNode'
    bl_label = 'Matrix Interpolation'
    bl_icon = 'OUTLINER_OB_EMPTY'
 
    factor_ = bpy.props.FloatProperty(name = 'factor1_', description='Factor1', default=0.5,\
                                     min=0.0,max=1.0, options={'ANIMATABLE'}, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self,"factor_","Factor:");

    def init(self, context):
        self.inputs.new('StringsSocket', "Factor", "Factor")
        self.inputs.new('MatrixSocket', "A", "A") 
        self.inputs.new('MatrixSocket', "B", "B")        
        self.outputs.new('MatrixSocket', "C", "C")
        

    def update(self):
        #inputs 
        
        A = []
        B = []
        factor = [] # 0 is valid value so I use [] as placeholder
        
        if 'A' in self.inputs and self.inputs['A'].links and \
            type(self.inputs['A'].links[0].from_socket) == MatrixSocket:
            if not self.inputs['A'].node.socket_value_update:
                self.inputs['A'].node.update()
            A = Matrix_generate(eval(self.inputs['A'].links[0].from_socket.MatrixProperty))
        if not A:
            A = [Matrix.Identity(4)]
        
        if 'B' in self.inputs and self.inputs['B'].links and \
            type(self.inputs['B'].links[0].from_socket) == MatrixSocket:
            if not self.inputs['B'].node.socket_value_update:
                self.inputs['B'].node.update()
            B = Matrix_generate(eval(self.inputs['B'].links[0].from_socket.MatrixProperty))
        if not B:
            B = [Matrix.Identity(4)]
                
        if 'Factor' in self.inputs and self.inputs['Factor'].links and \
            type(self.inputs['Factor'].links[0].from_socket) == StringsSocket:
            if not self.inputs['Factor'].node.socket_value_update:
                self.inputs['Factor'].node.update()
            factor = eval(self.inputs['Factor'].links[0].from_socket.StringsProperty)

        if not factor:
            factor = [[self.factor_]]
      
        if 'C' in self.outputs and self.outputs['C'].links: 
            if not self.outputs['C'].node.socket_value_update:
                self.outputs['C'].node.update()
            matrixes_=[]
# match inputs, first matrix A and B using fullList
# then extend the factor list if necessary,             
# A and B should control length of list, not interpolation lists
            max_l = max(len(A),len(B))
            fullList(A,max_l)
            fullList(B,max_l)
            if len(factor) < max_l:
                fullList(factor,max_l)
            for i in range(max_l):
                for k in range(len(factor[i])):
                    matrixes_.append(A[i].lerp(B[i], factor[i][k]))
                    
            if not matrixes_:
                return
                       
            matrixes = Matrix_listing(matrixes_)
            self.outputs['C'].MatrixProperty = str(matrixes)            
    
            
            
    def update_socket(self, context):
        self.update()        
   
    

def register():
    bpy.utils.register_class(MatrixInterpolationNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixInterpolationNode)

if __name__ == "__main__":
    register()