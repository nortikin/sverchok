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
from ast import literal_eval
from math import *
from string import ascii_lowercase

import bpy
from bpy.props import BoolProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, dataCorrect, SvSetSocketAnyType, SvGetSocketAnyType)


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
        takes care of adding new inputs until reaching 26, think of using SN or EK
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

        outputs = self.outputs
        if not outputs[0].links:
            # 0 = verts, this at least needs a connection
            return

        self.process()


    def meta_getter(self, idx, fallback):
        pass

    def homogenize_input(self):
        '''
        this function finds the longest input list, and adjusts all others to match it.
        '''
        segments = {}
        for i, input_ in enumerate(self.inputs):

            # not using .get for dict lookup because they should all be valid and known.
            letter = idx_map[i]


            segments[letter] = if input_.links


    def process(self):
        segments = self.homogenize_input()

        for segment in segments:
            fstr = {}

            result = literal_eval(self.profile_str)


        pass




def register():
    bpy.utils.register_class(SvProfileNode)


def unregister():
    bpy.utils.unregister_class(SvProfileNode)
