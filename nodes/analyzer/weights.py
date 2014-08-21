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
import parser
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty
from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import (SvGetSocketAnyType, updateNode)

class SvVertexGroupNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Vertex Group '''
    bl_idname = 'SvVertexGroupNode'
    bl_label = 'weights'
    bl_icon = 'OUTLINER_OB_EMPTY'


    allind = BoolProperty(name='All vertices', description='use all vertices of object', default=False, update=updateNode)
    clear = BoolProperty(name='clear unused', description='clear weight of unindexed vertices', default=False, update=updateNode)
    
    
    formula = StringProperty(name='formula', description='name of object to operate on', default='Cube', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="")
        row = layout.row(align=True)
        row.prop(self, "allind", text="All vertices")
        row.prop(self, "clear", text="clear unused")
        

    x_ = IntProperty(name='VertIND' , description='indixes of corresponding vertices', default=1, update=updateNode)
    y_ = FloatProperty(name='Weights', description='weights for corresponding vertices', default=0.0, precision=3, update=updateNode)


    def init(self, context):
        self.inputs.new('StringsSocket', "VertIND").prop_name = 'x_'
        self.inputs.new('StringsSocket', "Weights").prop_name = 'y_'

    
    def update(self):
        
        obj= bpy.data.objects[self.formula]
        if self.allind:
            verts = [[i.index for i in obj.data.vertices]]
        else:
            
            if 'VertIND' in self.inputs and self.inputs['VertIND'].links and \
               type(self.inputs['VertIND'].links[0].from_socket) == StringsSocket:
                verts = SvGetSocketAnyType(self, self.inputs['VertIND'])
            else:
                verts = [[self.x_]]
            
        if 'Weights' in self.inputs and self.inputs['Weights'].links and \
           type(self.inputs['Weights'].links[0].from_socket) == StringsSocket:
            if len(SvGetSocketAnyType(self, self.inputs['Weights'])[0])>1:
                 wei = SvGetSocketAnyType(self, self.inputs['Weights'])
            else:
                 wei = [SvGetSocketAnyType(self, self.inputs['Weights'])[0]*len(verts[0])]
        else:
            wei = [[self.y_]*len(verts[0])]


        
        obj.data.update()
        

        if obj.vertex_groups.active and obj.vertex_groups.active.name.find( 'Sv_VGroup' ) != -1:
    
            if self.clear:
                obj.vertex_groups.active.add([i.index for i in obj.data.vertices], 0, "REPLACE")
            g=0
            while g!= len(wei[0]):
                obj.vertex_groups.active.add([verts[0][g]], wei[0][g], "REPLACE")
                g=g+1
    
        else:
            obj.vertex_groups.active= obj.vertex_groups.new(name='Sv_VGroup')

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvVertexGroupNode)

def unregister():
    bpy.utils.unregister_class(SvVertexGroupNode)
