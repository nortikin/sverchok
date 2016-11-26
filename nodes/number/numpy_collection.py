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
    'sig': 'np.linspace(start, stop, num=50, endpoint=True, retstep=False)'
    'inputs': [
        ['starts', 'scalar', None],
        ['stop', 'scalar', None],
        ['num', 'int', 50],
        ['endpoints', 'bool', True],
        ['retstep', 'bool', False]
    ],
    'outputs': [ ['result': 'nd.array', []] ],
    'info': readthedocs + 'generated/numpy.linspace.html'
}

### Modifiers of array ##########################################

node_details['roll'] = {
    'sig': 'np.roll(a, shift, axis=None)'
    'inputs': [
        ['a', 'array', None],
        ['shift', 'int', 0],
        ['axis', 'int', None] # Optional
    ],
    'outputs': [ ['result': 'nd.array', []] ],
    'info': readthedocs + 'generated/numpy.roll.html'
}

node_details['reshape'] = {
    'sig': "np.reshape(a, newshape, order='C')"
    'inputs': [
        ['a', 'array', None],
        ['newshape', 'modes: int int-tuple', None],
        ['order', 'enum: C F A', 'C'],
    ],
    'outputs': [ ['result': 'nd.array', []] ],
    'info': readthedocs + 'generated/numpy.reshape.html'
}

# np.T
node_details['transpose'] = {
    'sig': 'np.transpose(a, axes=None)'
    'inputs': [
        ['a', 'array', None],
        ['axes', 'modes: int int-list', None]
    ],
    'outputs': [ ['result': 'nd.array', []] ],
    'info': readthedocs + 'generated/numpy.transpose.html'
}


### Combiner of array ###########################################


# np.meshgrid(x,y,z))






