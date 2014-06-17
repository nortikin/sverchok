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
from bpy.props import IntProperty, FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, fullList,
                            SvSetSocketAnyType, SvGetSocketAnyType)

class LineNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Line '''
    bl_idname = 'LineNode'
    bl_label = 'Line'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_ = IntProperty(name = 'N Verts', description='Nº Vertices', 
                    default=2, min=2,
                    options={'ANIMATABLE'}, update=updateNode)
    step_ = FloatProperty(name = 'Step', description='Step length',
                    default=1.0, options={'ANIMATABLE'},
                    update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'int_'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step_'
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        pass
        #layout.prop(self, "int_", text="Nº Vert")
        #layout.prop(self, "step_", text="Step")

    def update(self):
        # inputs
        if 'Nº Vertices' in self.inputs and self.inputs['Nº Vertices'].links:
            Integer_ = SvGetSocketAnyType(self,self.inputs['Nº Vertices'])[0]
        else:
            Integer_ = [self.int_]

        if 'Step' in self.inputs and self.inputs['Step'].links:
            Step_ = SvGetSocketAnyType(self,self.inputs['Step'])[0]
            
            if len(Integer_) > len(Step_):
                fullList(Step_, len(Integer_))
            X=[]
            for j, k in enumerate(Integer_):
                listVert = []
                for i in range(k):
                    listVert.append(i*Step_[j])
                X.append(listVert)

        else:
            Step = self.step_
            X = [[Step*(i) for i in range(Integer)] for Integer in Integer_]
            
        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:

            points = []
            for X_obj in X:
                Y = [0.0]
                Z = [0.0]
                max_num = len(X_obj)
                fullList(Y,max_num)
                fullList(Z,max_num)
                points.append(list(zip(X_obj,Y,Z)))
            SvSetSocketAnyType(self, 'Vertices',points)

        if 'Edges' in self.outputs and self.outputs['Edges'].links:

            edg = []
            for Integer in Integer_:
                listEdg_obj = []
                for i in range(Integer-1):
                    listEdg_obj.append((i, i+1))
                edg.append(list(listEdg_obj))

            SvSetSocketAnyType(self, 'Edges',edg)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(LineNode)


def unregister():
    bpy.utils.unregister_class(LineNode)
