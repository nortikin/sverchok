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
import numpy as np
from functools import wraps

import bpy
import bmesh
import mathutils
from mathutils import Matrix

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.data_structure import match_long_repeat

identity_matrix = Matrix()

# constants
PI = math.pi
HALF_PI = PI / 2
QUARTER_PI = PI / 4
TAU = PI * 2
TWO_PI = TAU
N = identity_matrix

# ----------------- vectorize wrapper ---------------


def vectorize(func):
    '''
    Will create a yeilding vectorized generator of the
    function it is applied to.
    Note: arguments must be list or similar type
    '''
    @wraps(func)
    def inner(*args):
        values = match_long_repeat(args)
        for param in zip(*values):
            yield func(*param)
    return inner


# ----------------- light weight functions ---------------


@vectorize
def circle(radius=1.0, phase=0, nverts=20, matrix=None, mode='pydata'):
    '''
    parameters:
        radius: float
        phase:  where to start the unit circle
        nverts: number of verts of the circle
        matrix: transformation matrix
        mode:   'np' or 'pydata'

        :  'pydata'
        usage:
            Verts, Edges, Faces = circle(nverts=20, radius=1.6, mode='pydata')
        info:
            Each return type will be a nested list.
            Verts: will generate [[x0,y0,z0],[x1,y1,z1], ....[xN,yN,zN]]
            Edges: will generate [[a,yb],[b,c], ....[n,a]]
            Faces: a single wrapped polygon around the bounds of the shape

        :  'np'
        usage:
            Verts, Edges, Faces = circle(nverts=20, radius=1.6, mode='np')
        info:
            Each return type will be a numpy array
            Verts: generates [n*4] - Array([[x0,y0,z0,w0],[x1,y1,z1,w1], ....[xN,yN,zN,wN]])
            Edges: will be a [n*2] - Array([[a,yb],[b,c], ....[n,a]])
            Faces: a single wrapped polygon around the bounds of the shape

            to convert to pydata please consult the numpy manual.

    '''

    if mode in {'pydata', 'bm'}:

        vertices = []
        theta = TAU / nverts
        for i in range(nverts):
            rad = i * theta
            vertices.append((math.sin(rad + phase) * radius, math.cos(rad + phase) * radius, 0))

        edges = [[i, i+1] for i in range(nverts-1)] + [[nverts-1, 0]]
        faces = [i for i in range(nverts)] + [0]

        if mode == 'pydata':
            return vertices, edges, [faces]
        else:
            return bmesh_from_pydata(vertices, edges, [faces])

    if mode == 'np':

        # t = np.linspace(0, np.pi*2, verts+1)[:20]
        t = np.linspace(0, np.pi * 2 * (nverts - 1 / nverts), nverts)
        circ = np.array([np.cos(t + phase) * radius, np.sin(t + phase) * radius, np.zeros(nverts), np.zeros(nverts)])
        vertices = np.transpose(circ)
        edges = np.array([[i, i+1] for i in range(nverts-1)] + [[nverts-1, 0]])
        faces = np.array([[i for i in range(nverts)] + [0]])
        return vertices, edges, faces


def arc(radius=1.0, phase=0, angle=TAU, verts=20, matrix=None, mode='pydata'):
    pass
