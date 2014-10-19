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
from bpy.props import StringProperty, EnumProperty

from node_tree import SverchCustomTreeNode
from data_structure import multi_socket, node_id
from core.update_system import make_tree_from_nodes, do_update
import ast

class StoreSockets:
    
    socket_data = StringProperty()

    def collect(self):
        out = {}
        if self.outputs:
            data = [(s.bl_idname, s.name) for s in self.outputs]
            out["outputs"] = data
        if self.inputs:
            data = [(s.bl_idname, s.name) for s in self.inputs]
            out["inputs"] = data
        self.socket_data = str(out)
            
    def load(self):
        data = ast.literal_eval(self.socket_data)
        for k,values in data.items():
            sockets = getattr(self, k)
            sockets.clear()
            for s in values:
                sockets.new(*s)
        
    def process(self):
        pass
    
    
class SvGroupNode(bpy.types.Node, SverchCustomTreeNode, StoreSockets):
    '''
    Sverchok Group node
    '''
    bl_idname = 'SvGroupNode'
    bl_label = 'Group'
    bl_icon = 'OUTLINER_OB_EMPTY'

    group_name = StringProperty()
    
    def draw_buttons(self, context, layout):
        if self.id_data.bl_idname == "SverchCustomTreeType":
            op = layout.operator("node.sv_node_group_edit")
            op.group_name = self.group_name
            
    def process(self):
        group_ng = bpy.data.node_groups[self.group_name]
        in_node = find_node("SvGroupInputsNode", group_ng)
        out_node = find_node('SvGroupOutputsNode', group_ng)
        for socket in self.inputs:
            if socket.links:
                data = socket.sv_get(deepcopy=False)
                in_node.outputs[socket.name].sv_set(data)
        #  get update list
        #  could be cached
        ul = make_tree_from_nodes([out_node.name], group_ng, down=False)
        print(ul)
        do_update(ul, group_ng.nodes)
        # set output sockets correctly
        for socket in self.outputs:
            if socket.links:
                data = out_node.inputs[socket.name].sv_get(deepcopy=False)
                socket.sv_set(data)

def find_node(id_name, ng):
    for n in ng.nodes:
        if n.bl_idname == id_name:
            return n
    raise NotFoundErr
    

class SvGroupInputsNode(bpy.types.Node, SverchCustomTreeNode, StoreSockets):
    bl_idname = 'SvGroupInputsNode'
    bl_label = 'Group Inputs'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def draw_buttons(self, context, layout):
        if self.id_data.bl_idname == "SverchCustomTreeType":
            op = layout.operator("node.sv_node_group_done")
            op.frame_name = self.parent.name
    
    
class SvGroupOutputsNode(bpy.types.Node, SverchCustomTreeNode, StoreSockets):
    bl_idname = 'SvGroupOutputsNode'
    bl_label = 'Group outputs'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def draw_buttons(self, context, layout):
        if self.id_data.bl_idname == "SverchCustomTreeType":
            op = layout.operator("node.sv_node_group_done")
            op.frame_name = self.parent.name

    
    
def register():
    bpy.utils.register_class(SvGroupNode)
    bpy.utils.register_class(SvGroupInputsNode)
    bpy.utils.register_class(SvGroupOutputsNode)

def unregister():
    bpy.utils.unregister_class(SvGroupNode)
    bpy.utils.unregister_class(SvGroupInputsNode)
    bpy.utils.unregister_class(SvGroupOutputsNode)
