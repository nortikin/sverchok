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
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty

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

readthedocs = 'http://numpy.readthedocs.io/en/latest/reference/'

S = StringProperty

if NODE_LINSPACE:

    def sv_init(self, context):
        self.inputs.new("StringsSocket", "start")
        self.inputs.new("StringsSocket", "stop")
        num = self.inputs.new("StringsSocket", "num")
        num.prop_name = 'num'
        self.outputs.new("StringsSocket", "nd.array")

    def draw_buttons(self, context, layout):
        r = layout.row()
        r.prop(self, 'endpoint', toggle=True)
        r.prop(self, 'retstep', toggle=True)

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        if not all_linked(outputs[0], inputs[0], inputs[1]):
            return

        start, stop, num = [s.sv_get()[0][0] for s in inputs]
        outputs[0].sv_set([np.linspace(start, stop, num, self.endpoint, self.retstep)])
    
    temp_dict = {
        'sv_doc': S(default="""
            inputs
                start    (scalar)  (default=None)
                stop     (scalar)  (default=None)
                num      (int)     (default=50)
                endpoint (bool)    (default=True)
                retstep  (bool)    (default=False)
            outputs
                result   (nd.array)
        """),
        'endpoint': BoolProperty(default=True),
        'retstep': BoolProperty(default=False),
        'num': IntProperty(default=50),
        'sv_init': sv_init,
        'process': process,
        'draw_buttons': draw_buttons,
        'sig': S(default='np.linspace(start, stop, num=50, endpoint=True, retstep=False)'),
        'info': S(default=readthedocs + 'generated/numpy.linspace.html')
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
