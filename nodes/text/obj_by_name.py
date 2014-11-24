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
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode

#
#  this is just very short demo node.

class SvObjByNameNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Get obj by name '''
    bl_idname = 'SvObjByNameNode'
    bl_label = 'Obj by name'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    
    def sv_init(self, context):
        self.inputs.new("SvTextSocket", "Name")
        
        self.outputs.new("SvObjectSocket", "Obj")
    
        
    def process(self):
        out = []
        names = self.inputs[0].sv_get()
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj:
                out.append(obj)
        self.outputs[0].sv_set(out)

            
def register():
    bpy.utils.register_class(SvObjByNameNode)

def unregister():
    bpy.utils.unregister_class(SvObjByNameNode)


