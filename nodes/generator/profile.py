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
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty

from node_tree import SverchCustomTreeNode
from data_structure import fullList, updateNode, dataCorrect, SvSetSocketAnyType, SvGetSocketAnyType


idx_map = {i: j for i, j in enumerate(ascii_lowercase)}



class SvProfileNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    SvProfileNode generates one or more profiles / elevation segments using;
    assignments, variables, and a string descriptor similar to SVG.

    This node expects simple input, or vectorized input.
    - sockets with no input are automatically 0, not None
    - The longest input array will be used to extend the shorter ones, using last value repeat.
    '''
    bl_idname = 'SvProfileNode'
    bl_label = 'ProfileNode'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def mode_change(self, context):
        if not (self.selected_axis == self.current_axis):
            self.label = self.selected_axis
            self.current_axis = self.selected_axis
            updateNode(self, context)

    axis_options = [
        ("X", "X", "", 0),
        ("Y", "Y", "", 1),
        ("Z", "Z", "", 2)
    ]
    current_axis = StringProperty(default='Z')

    selected_axis = EnumProperty(
        items=axis_options,
        name="Type of axis",
        description="offers basic axis output vectors X|Y|Z",
        default="Z",
        update=mode_change)

    # profile_str = StringProperty(default="", update=updateNode)
    profile_file = StringProperty(default="", update=updateNode)
    filename = StringProperty(default="")
    posxy = FloatVectorProperty(default=(0.0, 0.0), size=2) # update=updateNode)
    state_idx = IntProperty(default=0)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'selected_axis', expand=True)
        row = layout.row(align=True)
        row.prop(self, "profile_file", text="")

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

        # keeping the file internal for now.
        self.filename = self.profile_file.strip()
        if not (self.filename in bpy.data.texts):
            return

        if not ('Edges' in self.outputs):
            return

        elif len([1 for inputs in self.inputs if inputs.links]) == 0:
            ''' must have at least one input... '''
            return

        self.adjust_inputs()

        # 0 == verts, this is a minimum requirement.
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
        #f = lambda l: [item for sublist in l for item in sublist]

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
            data = self.meta_get(i, [0], 2)

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

        for idx in range(longest):
            result, edges = self.parse_path_file(segments, idx)

            axis_fill = {
                'X': lambda coords: (0, coords[0], coords[1]),
                'Y': lambda coords: (coords[0], 0, coords[1]),
                'Z': lambda coords: (coords[0], coords[1], 0)
                }.get(self.current_axis)

            result = list(map(axis_fill, result[0]))
            full_result_verts.append([result])
            full_result_edges.append([edges])


        if full_result_verts:
            SvSetSocketAnyType(self, 'Verts', full_result_verts)

            if self.outputs['Edges'].links:
                SvSetSocketAnyType(self, 'Edges', full_result_edges)


    def parse_path_file(self, segments, idx):
        ''' 
        This section is partial preprocessor per line found in the file at bpy.data.texts[filename]

        segments is a dict of letters to variables mapping.
        this function expects that all remapable lines contain lower case chars.
        '''
        file_str = bpy.data.texts[self.filename]
        lines = file_str.as_string().split('\n')

        # initial start position, unless specified otherwise.
        posxy = [0, 0]
        result = []
        self.state_idx = 0  # reset this

        final_verts, final_edges = [], []

        for line in lines:
            if not line:
                continue

            # svg type path descriptions, not a full implementation
            section_type = {
                'M': 'move_to_absolute',
                'm': 'move_to_relative',
                'L': 'line_to_absolute',
                'l': 'line_to_relative',
                '#': 'comment'
            }.get(line.strip()[0])

            if (not section_type) or (section_type == 'comment'):
                continue

            '''
            if the user really needs z as last value
            and z is indeed a variable and not intended to 
            close a section, then you must add ;
            '''

            # closed segment detection.
            close_section = False
            last_char = line.strip()[-1]
            if last_char in {'z', 'Z'}:
                '''deal with closing current verts edges combo'''
                line = line.strip()[1:-1].strip()
                close_section = True

            elif last_char in {';'}:
                '''user is crazy and has a..z filled with variables
                good for user.
                '''
                line = line.strip()[1:-1].strip()
                close_section = False

            else:
                '''doesn't end with ; or z, Z '''
                line = line.strip()[1:].strip()

            results = self.parse_path_line(idx, segments, line, section_type, close_section)

            if results:
                verts, edges = results
                final_verts.append(verts)
                final_edges.append(edges)
                self.posxy = verts[-1]

        return final_verts, final_edges

    def parse_path_line(self, idx, segments, line, section_type, close_section):
        ''' 
        expects input like

        M a,b
        m a,b
        L a,e 10.0,34
        L a,e 10.0,34 z
        L a,e 10.0,34 ......x,y y,z;  <- no close, but using z as last variable
        L a,e 10.0,34 ......x,y y,z z  <- both. unlikely but potential scenario
        '''

        ''' these two are very similar crazy code sharing '''
        if section_type in {'move_to_absolute', 'move_to_relative'}:

            ''' no point doing multiple moves, so split on comma and move posxy '''
            temp_str = line.split(',')
            xy = []
            for char in temp_str:
                if char in segments:
                    pushval = segments[char]['data'][idx]
                else:
                    pushval = char
                xy.append(float(char))

            if section_type == 'move_to_relative':
                posxy = (self.posxy[0] + xy[0], self.posxy[1] + xy[1])
            else:
                posxy = (xy[0], xy[1])
            return

        elif section_type == 'line_to_absolute':
            ''' assumes you have posxy (current needle position) where you want it, 
            and draws a line from it to the first set of 2d coordinates, and 
            onwards till complete '''
            # temp_str = temp_str.replace(letter, str(data['data'][idx]))
            line_data = [[self.posxy[0], self.posxy[1]]]
            intermediate_idx = self.state_idx
            self.state_idx += 1

            tempstr = line.split(' ')
            # print(tempstr)
            for t in tempstr:
                components = t.split(',')
                sub_comp = []
                for char in components:
                    char.strip()
                    if char in segments:
                        pushval = segments[char]['data'][idx]
                    else:
                        pushval = float(char)
                    sub_comp.append(pushval)
                    self.state_idx += 1

                line_data.append(sub_comp)

            temp_edges = [[i, i+1] for i in range(intermediate_idx, len(line_data)-1)]

            if close_section:
                temp_edges.append([self.state_idx, intermediate_idx])
            return line_data, temp_edges

        elif section_type == 'line_to_relative':
            pass

        #for letter, data in segments.items():
        #    temp_str = temp_str.replace(letter, str(data['data'][idx]))

        #result = literal_eval(temp_str)




def register():
    bpy.utils.register_class(SvProfileNode)


def unregister():
    bpy.utils.unregister_class(SvProfileNode)
