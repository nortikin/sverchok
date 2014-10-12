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
from bpy.props import StringProperty, BoolProperty

from node_tree import SverchCustomTreeNode, SverchCustomTree
from data_structure import changable_sockets, SvGetSocketAnyType, SvSetSocketAnyType


class SvStopperNode(bpy.types.Node, SverchCustomTreeNode):
    ''' A node that stop updates '''
    bl_idname = 'SvStopperNode'
    bl_label = 'Stopper'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def draw_buttons(self, context, layout):
        layout.label("Delete me!")
        layout.label("To start updates")
        
    def init(self, context):
        pass

def register():
    bpy.utils.register_class(SvStopperNode)


def unregister():
    bpy.utils.unregister_class(SvStopperNode)
