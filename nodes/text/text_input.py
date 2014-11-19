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

import ast
import traceback

import bpy
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#
#
#  this is just very short demo node.

class SvTextInNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Get Attribue of Obj '''
    bl_idname = 'SvTextInNode'
    bl_label = 'TextIn'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    text = StringProperty(update=updateNode)
    
    def sv_init(self, context):
        self.outputs.new("Textsocket", "Text")
    
    def process(self):
        self.outputs[0].sv_set([self.text])

            
def register():
    bpy.utils.register_class(SvCmpNode)

def unregister():
    bpy.utils.unregister_class(SvCmpNode)


