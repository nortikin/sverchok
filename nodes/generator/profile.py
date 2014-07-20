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
from data_structure import fullList, updateNode, dataCorrect, SvSetSocketAnyType, SvGetSocketAnyType


idx_map = {i: j for i, j in enumerate(ascii_lowercase)}


class SvProfileNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    SvProfileNode generates one or more profiles / elevation segments using;
    assignments, variables, and a string descriptor similar to SVG.

    This node expects simple input, or vectorized input.
    - Feed it input like [[0, 0, 0, 0.4, 0.4]] per input.
    - input can be of any length
    - sockets with no input are automatically 0, not None
    - The longest input array will be used to extend the shorter ones, using last value repeat.
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
        takes care of adding new inputs until reaching 26,
        think of using SN or EK if you get that far.
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
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        if not ('Edges' in self.outputs):
            return

        elif len([1 for inputs in self.inputs if inputs.links]) == 0:
            ''' must have at least one input... '''
            return

        self.adjust_inputs()

        # 0 == verts, this is a minim requirement.
        if not self.outputs[0].links:
            return

        self.process()

    def meta_get(self, s_name, fallback, level):
        '''
        private function for the processing function, accepts level 0..2
        - if socket has no links, then return fallback value
        - s_name can be an index instead of socket name
        '''
        inputs = self.inputs
        if inputs[s_name].links:
            socket_in = SvGetSocketAnyType(self, inputs[s_name])
            if level == 1:
                data = dataCorrect(socket_in)[0]
            elif level == 2:
                data = dataCorrect(socket_in)[0][0]
            else:
                data = dataCorrect(socket_in)
            return data
        else:
            return fallback

    def homogenize_input(self, segments, longest):
        '''
        edit segments in place, extend all to match length of longest
        '''
        f = lambda l: [item for sublist in l for item in sublist]

        for letter, letter_dict in segments.items():
            if letter_dict['length'] < longest:
                fullList(letter_dict['data'], longest)
                # letter_dict['data'] = f(letter_dict['data'])

    def get_input(self):
        '''
        collect all input socket data, and track the longest sequence.
        '''
        segments = {}
        longest = 0
        for i, input_ in enumerate(self.inputs):
            letter = idx_map[i]

            ''' get socket data, or use a fallback '''
            data = self.meta_get(i, [[0]], 1)

            num_datapoints = len(data)
            segments[letter] = {'length': num_datapoints, 'data': data}

            if num_datapoints > longest:
                longest = num_datapoints

        return segments, longest

    def process(self):
        segments, longest = self.get_input()

        if longest < 1:
            print('logic error, longest < 1')
            return

        self.homogenize_input(segments, longest)

        full_result_verts = []
        full_result_edges = []

        print(segments)

        for idx in range(longest):
            for letter, data in segments.items():

                ''' this brings these named parameters in local scope '''
                print(letter, '->', data['data'][idx])
                fstr = '{l} = {d}'.format(l=letter, d=data['data'][idx])
                # exec(fstr)
                print(fstr)

            ''' this assumes all variables used in profile_str are local now '''
            # result = literal_eval(self.profile_str)
            # full_result_verts.append(result)

        if full_result_verts:
            SvSetSocketAnyType(self, 'Verts', full_result_verts)

            #if self.inputs['Edges'].links:
            #   SvSetSocketAnyType(self, 'Edges', full_result_edges)
        print('here --- ')


def register():
    bpy.utils.register_class(SvProfileNode)


def unregister():
    bpy.utils.unregister_class(SvProfileNode)
