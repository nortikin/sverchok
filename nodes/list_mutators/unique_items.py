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
import numpy as np
from mathutils import Matrix, Quaternion
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, changable_sockets


def recursive_unique_items(data, level, linked_outputs, output_numpy):
    unique = []
    unique_indices = []
    unique_inverse = []
    unique_count = []

    iterable = isinstance(data[0], (list, tuple, np.ndarray))
    if not level or not iterable:
        np_data = np.array(data)
        if np_data.dtype == object or isinstance(data[0], (Matrix, Quaternion)):
            unique, unique_indices, unique_inverse, unique_count = python_unique(data)
        else:
            unique, unique_indices, unique_inverse, unique_count = numpy_unique(data, linked_outputs, output_numpy)
    else:
        for sublist in data:
            sub_results = recursive_unique_items(sublist, level-1, linked_outputs, output_numpy)
            unique.append(sub_results[0])
            unique_indices.append(sub_results[1])
            unique_inverse.append(sub_results[2])
            unique_count.append(sub_results[3])

    return unique, unique_indices, unique_inverse, unique_count


def python_unique(data):
    unique = [data[0]]
    unique_indices = [0]
    unique_inverse = [0]
    unique_count = [1]
    for index, d in enumerate(data[1:]):
        if d in unique:
            idx = unique.index(d)
            unique_inverse.append(idx)
            unique_count[idx] += 1
        else:
            unique.append(d)
            unique_indices.append(index)
            unique_inverse.append(len(unique)-1)
            unique_count.append(1)

    return unique, unique_indices, unique_inverse, unique_count


def numpy_unique(np_data, linked_outputs, output_numpy):
    unique = []
    unique_indices = []
    unique_inverse = []
    unique_count = []
    if any(linked_outputs):
        arg = {
            'return_index' : linked_outputs[0],
            'return_inverse' : linked_outputs[1],
            'return_counts' : linked_outputs[2],
            'axis': 0
        }
        unique_data = np.unique(np_data, **arg)
        unique = unique_data[0] if output_numpy else unique_data[0].tolist()
        idx = 1
        if linked_outputs[0]:
            unique_indices = unique_data[idx] if output_numpy else unique_data[idx].tolist()
            idx += 1
        if linked_outputs[1]:
            unique_inverse = unique_data[idx] if output_numpy else unique_data[idx].tolist()
            idx += 1
        if linked_outputs[2]:
            unique_count = unique_data[idx] if output_numpy else unique_data[idx].tolist()
    else:
        unique = np.unique(np_data, axis=0) if output_numpy else np.unique(np_data, axis=0).tolist()

    return unique, unique_indices, unique_inverse, unique_count


class SvUniqueItemsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Unique items
    Tooltip: Find the unique elements, where they are and how many repetitions each have
    """

    bl_idname = 'SvUniqueItemsNode'
    bl_label = 'Unique Items'
    bl_icon = 'PIVOT_BOUNDBOX'
    
    level: bpy.props.IntProperty(
        name='Level',
        description="Level where search should be performed",
        default=2, min=0,
        update=updateNode)
    output_numpy: bpy.props.BoolProperty(
        name='Output Numpy',
        description="Output NumPy arrays (faster)",
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.outputs.new('SvStringsSocket', "Items")
        self.outputs.new('SvStringsSocket', "Indices")
        self.outputs.new('SvStringsSocket', "Inverse Indices")
        self.outputs.new('SvStringsSocket', "Counts")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'level')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'level')
        layout.prop(self, 'output_numpy')

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop(self, 'level')
        layout.prop(self, 'output_numpy')

    def sv_update(self):
        '''adapt socket type to input type'''
        if 'Data' in self.inputs and self.inputs['Data'].links:
            inputsocketname = 'Data'
            outputsocketname = ['Items']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):

        if not (self.inputs[0].is_linked and any([s.is_linked for s in self.outputs])):
            return
        data_in = self.inputs[0].sv_get(deepcopy=False)
        linked_outputs = [s.is_linked for s in self.outputs[1:]]
        out_lists = recursive_unique_items(data_in, self.level, linked_outputs, self.output_numpy)
        for s, data_out in zip(self.outputs, out_lists):
            s.sv_set(data_out)



def register():
    bpy.utils.register_class(SvUniqueItemsNode)


def unregister():
    bpy.utils.unregister_class(SvUniqueItemsNode)
