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
from bpy.props import StringProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import multi_socket, node_id, replace_socket
from sverchok.core.update_system import make_tree_from_nodes, do_update
import ast


socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]


class SvExpCallbackOperator(bpy.types.Operator):  
    bl_idname = "node.sverchok_exp_cb"
    bl_label = "general cb"
    
    group_name = StringProperty()
    
    def execute(self, context):
        bpy.ops.node.sv_switch_layout(layout_name=self.group_name)
        return {"FINISHED"}
                

class SvGroupNodeExp(bpy.types.NodeCustomGroup, SverchCustomTreeNode):
    bl_idname = 'SvGroupNodeExp'
    bl_label = 'Group Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    group_name = StringProperty()
 
    def init(self, context):

        self.node_tree = bpy.data.node_groups.new('nooobgroup', 'SverchCustomTreeType')
        self.group_name = self.node_tree.name
        self.node_tree.parent = self
        # space = context.space_data
        nodes = self.node_tree.nodes

        inputnode = nodes.new('SvGroupInputsNode')
        outputnode = nodes.new('SvGroupOutputsNode')
        inputnode.location = (-300, 0)
        outputnode.location = (300, 0)


    def update(self):
        '''
        Override inherited
        '''
        pass
        
    def draw_buttons_ext(self, context, layout):
        pass
            
    def draw_buttons(self, context, layout):
        c = layout.column()
        f = c.operator(SvExpCallbackOperator.bl_idname, text='print stuff')
        f.group_name = self.group_name

    def process(self):
        pass

    
    def load(self):
        pass
    

classes = [SvExpCallbackOperator, SvGroupNodeExp]
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
 
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
 
