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

def group_make(self, new_group_name):
    self.node_tree = bpy.data.node_groups.new(new_group_name, 'SverchCustomTreeType')
    self.group_name = self.node_tree.name

    nodes = self.node_tree.nodes
    inputnode = nodes.new('SvGroupInputsNode')
    outputnode = nodes.new('SvGroupOutputsNode')
    inputnode.location = (-300, 0)
    outputnode.location = (300, 0)
    return self.node_tree

class SvGroupEdit(bpy.types.Operator):
    bl_idname = "node.sv_group_edit"
    bl_label = "edits an sv group"
    
    group_name = StringProperty()
    
    def execute(self, context):
        node = context.node
        ng = bpy.data.node_groups

        group_node = ng.get(self.group_name)
        if not group_node:
            group_node = group_make(node, new_group_name=self.group_name)
        
        bpy.ops.node.sv_switch_layout(layout_name=self.group_name)
        
        # by switching, space_data is now different
        parent_tree_name = node.id_data.name
        path = context.space_data.path
        path.clear()
        path.append(ng[parent_tree_name]) # below the green opacity layer
        path.append(ng[self.group_name])  # top level

        # this should happen in the `tree_path_parent` operator, but the doesn't seem to.
        # context.space_data.node_tree = bpy.data.node_groups[self.group_name]
        return {"FINISHED"}

class SvTreePathParent(bpy.types.Operator):
    '''Go to parent node tree'''
    bl_idname = "node.sv_tree_path_parent"
    bl_label = "Parent Sv Node Tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and len(space.path) > 1

    def execute(self, context):
        space = context.space_data
        space.path.pop()
        context.space_data.node_tree = space.path[0]
        return {'FINISHED'}


class SvGroupNodeExp(bpy.types.NodeCustomGroup, SverchCustomTreeNode):
    bl_idname = 'SvGroupNodeExp'
    bl_label = 'Group Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    group_name = StringProperty()
 
    def update(self):
        ''' Override inherited '''
        pass
        
    def draw_buttons_ext(self, context, layout):
        pass
            
    def draw_buttons(self, context, layout):
        c = layout.column()
        c.prop(self, 'group_name', text='name')

        d = layout.column()
        d.active = bool(self.group_name)
        f = d.operator('node.sv_group_edit', text='edit!')
        f.group_name = self.group_name

    def process(self):
        pass
    
    def load(self):
        pass
    

classes = [SvGroupEdit, SvTreePathParent, SvGroupNodeExp]
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
 
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
 
