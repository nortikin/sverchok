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
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_itertools import recurse_fxy

# ab -> c 
operations_ab_c = {
    "CMP":          lambda a,b: a == b,
    "STARTWITH":    lambda a,b: a.startswith(b)
    "ENDSWITH":     lambda a,b: a.endswith(b)
    "IN":           lambda a,b : b in a
}

operations = operations_ab_c.copy()


class SvTextOpNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Get Attribue of Obj '''
    bl_idname = 'SvTextOpNode'
    bl_label = '=='
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    
    # please extend this
    
    modes = [("CMP", "==", "Compare two strings", "1"),
             ("STARTWITH", "startswith", "", 2),
             ("ENDSWITH",  "endswith",  "", 3),
             ("IN"      ,   "in",    ,  "", 4)]
    
    def mode_switch(self, context):
        # should have socket handling
        updateNode(self, context)
                 
    mode = EnumProperty(name="Op", description="String operation",
                          default="CMP", items=modes,
                          update=mode_switch)
    
    def sv_init(self, context):
        self.inputs.new("SvTextSocket", "A")
        self.inputs.new("SvTextSocket", "B")
        
        self.outputs.new("StringsSocket", "Res")
    
   def process(self):
        # inputs
        if  not self.outputs['Res'].is_linked:
            return
            
        a = self.inputs['A'].sv_get(deepcopy=False)
 
        b = self.inputs['B'].sv_get(deepcopy=False)
        
        # outputs
        out= []
        
        out = recurse_fxy(a, b, operations[self.mode])

        self.outputs['Res'].sv_set(out)
            
def register():
    bpy.utils.register_class(SvTextOpNode)

def unregister():
    bpy.utils.unregister_class(SvTextOpNode)
