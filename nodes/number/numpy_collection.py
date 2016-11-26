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

import json

import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

readthedocs = 'http://numpy.readthedocs.io/en/latest/reference/'
node_details = {}

"""
node_details['func_name'] = {
    'sig': 'full_signature'
    'inputs': [
        [name, allowed type, default], ...
    ],
    'outputs': [ 
        ['result': 'nd.array', []], ... 
    ],
    'info': readthedocs + specific html link
}
"""

### Generators of array from primitive values ###################

node_details['linspace'] = {
    'sig': 'np.linspace(start, stop, num=50, endpoint=True, retstep=False)',
    'inputs': [
        ['starts', 'scalar', None],
        ['stop', 'scalar', None],
        ['num', 'int', 50],
        ['endpoints', 'bool', True],
        ['retstep', 'bool', False]
    ],
    'outputs': [['result', 'nd.array', []]],
    'info': readthedocs + 'generated/numpy.linspace.html'
}

### Modifiers of array ##########################################

node_details['roll'] = {
    'sig': 'np.roll(a, shift, axis=None)',
    'inputs': [
        ['a', 'array', None],
        ['shift', 'int', 0],
        ['axis', 'int', None] # Optional
    ],
    'outputs': [['result', 'nd.array', []]],
    'info': readthedocs + 'generated/numpy.roll.html'
}

node_details['reshape'] = {
    'sig': "np.reshape(a, newshape, order='C')",
    'inputs': [
        ['a', 'array', None],
        ['newshape', 'modes: int int-tuple', None],
        ['order', 'enum: C F A', 'C'],
    ],
    'outputs': [['result', 'nd.array', []]],
    'info': readthedocs + 'generated/numpy.reshape.html'
}

node_details['transpose'] = {
    'sig': 'np.transpose(a, axes=None)',
    'inputs': [
        ['a', 'array', None],
        ['axes', 'modes: int int-list', None]
    ],
    'outputs': [['result', 'nd.array', []]],
    'info': readthedocs + 'generated/numpy.transpose.html'
}


### Combiner of array ###########################################


# np.meshgrid(x,y,z))

### Class Factory for numpy suite.

def gen_prop_overwrites(prop_dict, name):
    return {
        'descriptor': json.dumps(prop_dict[name]),
        'bl_idname': "SvNP" + name,
        'bl_label': name
    }

def generate_socket(node, kind, item):
    socket = getattr(node, kind)
    socket.new("StringsSocket", 'Result')


class SvNumpyBaseNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = ""
    bl_label = ""

    node_dict = {}
    descriptor = bpy.props.StringProperty()
    sig = bpy.props.StringProperty()
    info = bpy.props.StringProperty()

    def get_node_dict(self):
        self.node_dict[hash(self)] = json.loads(self.descriptor)
        return self.node_dict[hash(self)]

    def sv_init(self, context):
        self.get_node_dict()
        ND = self.node_dict[hash(self)]

        for direction in 'inputs', 'outputs':
            sockets = ND.get(direction)
            if sockets:
                for item in sockets:
                    generate_socket(self, direction, item)

    def process(self):
        ND = self.node_dict.get(hash(self))
        if not ND:
            ND = self.get_node_dict()
            sig = ND['sig']


    def draw_buttons_ext(self, context, l):
        l.label(self.sig)
        l.label('web: ' + self.info)


def make_ugen_class(name, node_details):
    generated_classname = "SvNP" + name
    override = gen_prop_overwrites(node_details, name)
    return type(generated_classname, (SvNumpyBaseNode,), override)


SvNPlinspace = make_ugen_class('linspace', node_details)

classes = [
    SvNPlinspace,

]


def register():
    _ = [bpy.utils.register_class(name) for name in classes]


def unregister():
    _ = [bpy.utils.unregister_class(name) for name in classes]
