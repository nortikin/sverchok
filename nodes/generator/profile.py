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

''' by Dealga McArdle | 2014 '''

import parser
from math import *
from string import ascii_lowercase

import bpy
from bpy.props import BoolProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (sv_Vars, updateNode, multi_socket, changable_sockets,
                            dataSpoil, dataCorrect, levelsOflist,
                            SvSetSocketAnyType, SvGetSocketAnyType)



idx_map = {i: j for i, j in enumerate(ascii_lowercase)}



class SvProfileNode(bpy.types.Node, SverchCustomTreeNode):
    ''' 
    SvProfileNode generates a (set of) profiles or elevation segments using
    assignments, variables and a string descriptor like in SVG.

    '''
    bl_idname = 'SvProfileNode'
    bl_label = 'ProfileNode'
    bl_icon = 'OUTLINER_OB_EMPTY'

    profile_str = StringProperty(default="", update=updateNode)


    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "profile_str", text="")

    def init(self, context):
        self.inputs.new('StringsSocket', "a", "a")
        self.inputs.new('StringsSocket', "b", "b")

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def adjust_inputs(self):
        ''' 
        take care of adding new inputs when the last is full 
        -- if needed
        
        warning. 26 inputs is max, you probably want to approach 
        profile creation in a different way.
        '''
        inputs = self.inputs
        if inputs[-1].links:
            new_index = len(inputs)
            new_letter = idx_map.get(new_index, None)
            if new_letter:
                inputs.new('StringsSocket', new_letter, new_letter)
            else:
                print('this implementation goes up to 26 chars only, use SN or EK')
                print('- or contact Dealga')
        elif not inputs[-2].links:
            inputs.remove(inputs[-1])


    def update(self):
        if not ('Edges' in self.outputs):
            return

        inputs = self.inputs
        if not inputs[0].links:
            return

        self.adjust_inputs()
        self.process()


    def process(self):
        pass




def register():
    bpy.utils.register_class(SvProfileNode)


def unregister():
    bpy.utils.unregister_class(SvProfileNode)
