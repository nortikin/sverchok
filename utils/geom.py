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
None of this file is in a working condition. skip this file.

Eventual purpose of this file is to store the convenience functions which
can be used for regular nodes or as part of recipes for script nodes. These
functions will initially be sub optimal quick implementations, then optimized
only for speed, never for aesthetics or line count or cleverness.

'''

import math

import bpy
import bmesh
import mathutils
from mathutils import Matrix

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh


identity_matrix = Matrix()

# constants
PI = math.pi
HALF_PI = PI / 2
QUARTER_PI = PI / 4
TAU = PI * 2
TWO_PI = TAU
N = identity_matrix


# ----------------- light weight functions ---------------


def circle(radius=1.0, phase=0, verts=20, matrix=None, mode='pydata'):
    if mode in {'pydata', 'bm'}:
        vertices = []
        theta = TAU / verts
        for i in range(verts):
            rad = i * theta
            vertices.append((math.sin(rad + phase) , math.cos(rad + phase), 0))
        edges = [[i, i+1] for i in range(verts-1)] + [[verts-1, 0]]
        faces = [i for i in range(verts)] + [0]
        if mode == 'pydata':
            return vertices, edges, [faces]
        else:
            return bmesh_from_pydata(vertices, edges, [faces])
    if mode == 'np':
        pass


def arc(radius=1.0, phase=0, angle=TAU, verts=20, matrix=None, mode='pydata'):
    pass

