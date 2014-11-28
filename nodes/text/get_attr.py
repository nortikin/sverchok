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
from sverchok.data_structure import updateNode
from sverchok.utils.sv_itertools import sv_zip_longest



class SvGetAttrNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Get Attribue of Obj '''
    bl_idname = 'SvGetAttrNode'
    bl_label = 'Get attr'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    
    def sv_init(self, context):
        self.inputs.new("SvObjectSocket", "Objects")
        self.inputs.new("SvTextSocket", "Attr")
        
        self.outputs.new("SvTextSocket", "Attr")
    
        
    def process(self):
        out = []
        objs = self.inputs[0].sv_get()
        attrs = self.inputs[1].sv_get()
        for obj,attr in sv_zip_longest(objs, attrs):
            name = str(eval("obj"+"."+attr))
            out.append(name)
        self.outputs[0].sv_set(out)

            
def register():
    bpy.utils.register_class(SvGetAttrNode)

def unregister():
    bpy.utils.unregister_class(SvGetAttrNode)


