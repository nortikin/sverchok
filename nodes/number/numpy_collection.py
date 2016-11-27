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

import numpy as np

import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e)
from sverchok.utils.numpy_nodify_helper import (
    node_details, augment_node_dict, all_linked,
    generate_classes, register_multiple, unregister_multiple
)

NODE_LINSPACE = True
NODE_ROLL = False
NODE_RESHAPE = False
NODE_TRANSPOSE = False

# readthedocs = 'http://numpy.readthedocs.io/en/latest/reference/'


if NODE_LINSPACE:

    #     'inputs': [
    #         ['start', 'scalar', None, {}],
    #         ['stop', 'scalar', None],
    #         ['num', 'int', 50],
    #         ['endpoints', 'bool', True],
    #         ['retstep', 'bool', False]
    #     ],
    #     'outputs': [['result', 'nd.array', []]],


    def sv_init(self, context):
        self.inputs.new("StringsSocket", "start")
        self.inputs.new("StringsSocket", "stop")
        self.inputs.new("StringsSocket", "num")
        self.outputs.new("StringsSocket", "nd.array")

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        if not all_linked(outputs[0], inputs[0], inputs[1]): return
    
    temp_dict = {
        'sv_init': sv_init,
        'process': process,
        'sig': 'np.linspace(start, stop, num=50, endpoint=True, retstep=False)',
        'info': readthedocs + 'generated/numpy.linspace.html'
    }

    augment_node_dict('linspace', temp_dict)

#     T = ['MESH', 'CURVE', 'SURFACE']
#        'sig': EnumProperty(default='MESH', items=e(T), update=updateNode),


# node_details['roll'] = {
#     'sig': 'np.roll(a, shift, axis=None)',
#     'inputs': [
#         ['a', 'array', None],
#         ['shift', 'int', 0],
#         ['axis', 'int', None] # Optional
#     ],
#     'outputs': [['result', 'nd.array', []]],
#     'info': readthedocs + 'generated/numpy.roll.html'
# }

# T = ['MESH','CURVE','SURFACE']
# node_details['reshape'] = {
#     'sig': "np.reshape(a, newshape, order='C')",
#     'inputs': [
#         ['a', 'array', None],
#         ['newshape', 'modes: int int-tuple', None],
#         ['order', 'enum: C F A', 'C'],
#     ],
#     'props': EnumProperty(default='MESH', items=e(T), update=updateNode),
#     'outputs': [['result', 'nd.array', []]],
#     'info': readthedocs + 'generated/numpy.reshape.html'
# }

# node_details['transpose'] = {
#     'sig': 'np.transpose(a, axes=None)',
#     'inputs': [
#         ['a', 'array', None],
#         ['axes', 'modes: int int-list', None]
#     ],
#     'outputs': [['result', 'nd.array', []]],
#     'info': readthedocs + 'generated/numpy.transpose.html'
# }

# # np.meshgrid(x,y,z))



classes = generate_classes(node_details)

def register():
    register_multiple(classes)

def unregister():
    unregister_multiple(classes)
