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

'''
purpose of this file is to store the convenience functions which can be used for regular nodes
or as part of recipes for script nodes. These functions will be optimized only for speed, never
for aesthetics or line count or cleverness.

'''

# constants 

from math import pi as PI 
HALF_PI = PI / 2
QUARTER_PI = PI / 4
TAU = PI * 2
TWO_PI = TAU
N = identity_matrix

# shapes 2d

def circle(radius=(1,), phase=(0,), angle=(TAU,), verts=(20,), matrix=(N,), output='vep', np=False, merge=False):
	'''
    variables: 
        : radius, : phase, : angle, : verts, : matrix
        will be wrapped to a tuple if the input was an int, 
        shorter tuples will repeat to match length of longest input
    switches:
        : output, : np, : merge
        will effect the entirity of the output of this function.
        - merge will produce 

    output can be 'v', 've', 'vep', or 'bm'

    np means it would output a numpy array instead of lists.

	'''
    ...


# shapes 3d
