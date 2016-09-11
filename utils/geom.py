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
    Note: parameters must be passed as kw arguments
    '''
    @wraps(func)
    def inner(**kwargs):
        names, values = kwargs.keys(), kwargs.values()
        values = match_long_repeat(values)
        multiplex = {k:v for k, v in zip(names, values)}
        for i in range(len(values[0])):
            single_kwargs = {k:v[i] for k, v in multiplex.items()}
            yield func(**single_kwargs)

    return inner


# ----------------- sn1 specific helper for autowrapping to iterables ----
# this will be moved to elsewhere.

def sn1_autowrap(*params):
    for p in params:
        if isinstance(p, (float, int)):
            p = [p]
        yield p


# ----------------- light weight functions ---------------


def circle(radius=1.0, phase=0, nverts=20, matrix=None, mode='pydata'):
    '''
    parameters:
        radius: float
        phase:  where to start the unit circle
        nverts: number of verts of the circle
        matrix: transformation matrix [not implemented yet]
        mode:   'np' or 'pydata'

        :  'pydata'
        usage:
            Verts, Edges, Faces = circle(nverts=20, radius=1.6, mode='pydata')
        info:
            Each return type will be a nested list.
            Verts: will generate [[x0,y0,z0],[x1,y1,z1], ....[xN,yN,zN]]
            Edges: will generate [[a,b],[b,c], ....[n,a]]
            Faces: a single wrapped polygon around the bounds of the shape

        :  'np'
        usage:
            Verts, Edges, Faces = circle(nverts=20, radius=1.6, mode='np')

    outputs Verts, Edges, Faces

        info:
            Each return type will be a numpy array
            Verts: generates [n*4] - Array([[x0,y0,z0,w0],[x1,y1,z1,w1], ....[xN,yN,zN,wN]])
            Edges: will be a [n*2] - Array([[a,b],[b,c], ....[n,a]])
            Faces: a single wrapped polygon around the bounds of the shape

            to convert to pydata please consult the numpy manual.

    '''

    if mode in {'pydata', 'bm'}:

        verts = []
        theta = TAU / nverts
        for i in range(nverts):
            rad = i * theta
            verts.append((math.sin(rad + phase) * radius, math.cos(rad + phase) * radius, 0))

        edges = [[i, i+1] for i in range(nverts-1)] + [[nverts-1, 0]]
        faces = [i for i in range(nverts)]

        if mode == 'pydata':
            return verts, edges, [faces]
        else:
            return bmesh_from_pydata(verts, edges, [faces])

    if mode == 'np':

        t = np.linspace(0, np.pi * 2 * (nverts - 1 / nverts), nverts)
        circ = np.array([np.cos(t + phase) * radius, np.sin(t + phase) * radius, np.zeros(nverts), np.zeros(nverts)])
        verts = np.transpose(circ)
        edges = np.array([[i, i+1] for i in range(nverts-1)] + [[nverts-1, 0]])
        faces = np.array([[i for i in range(nverts)]])
        return verts, edges, faces



def arc(radius=1.0, phase=0, angle=PI, nverts=20, matrix=None, mode='pydata'):
    '''
    arc is similar to circle, with the exception that it does not close.

    parameters:
        radius: float
        phase:  where to start the arc
        nverts: number of verts of the arc
        matrix: transformation matrix [not implemented yet]
        mode:   'np' or 'pydata'

    outputs Verts, Edges, Faces

        info:
            Each return type will be a nested list.
            Verts: will generate [[x0,y0,z0],[x1,y1,z1], ....[xN,yN,zN]]
            Edges: will generate [[a,b],[b,c], ...] (not cyclic)
            Faces: a single wrapped polygon around the bounds of the shape

    '''

    if mode in {'pydata', 'bm'}:

        verts = []
        theta = angle / (nverts-1)
        for i in range(nverts):
            rad = i * theta
            verts.append((math.sin(rad + phase) * radius, math.cos(rad + phase) * radius, 0))

        edges = [[i, i+1] for i in range(nverts-1)]
        faces = [i for i in range(nverts)]

        if mode == 'pydata':
            return verts, edges, [faces]
        else:
            return bmesh_from_pydata(verts, edges, [faces])

    if mode == 'np':

        t = np.linspace(0, angle, nverts)
        circ = np.array([np.cos(t + phase) * radius, np.sin(t + phase) * radius, np.zeros(nverts), np.zeros(nverts)])
        verts = np.transpose(circ)
        edges = np.array([[i, i+1] for i in range(nverts-1)])
        faces = np.array([[i for i in range(nverts)]])
        return verts, edges, faces


def quad(side=1.0, radius=0.0, nverts=5, matrix=None, mode='pydata'):
    '''
    parameters:
        side:   gives the length of side of the rect
        radius: gives the radius of the rounded corners. 
                - If the passed radius is equal to side/2 then you'll get a circle
                - if the passed radius exceeds side/2, then you will get rect
        nverts: if nverts is equal or greater than 2 then you will get rounded courners
                if the above radius is smaller or equal to side/2.
        matrix: ---
        mode:   ---

    outputs Verts, Edges, Faces

        info:
            Each return type will be a nested list.
            Verts: will generate [[x0,y0,z0],[x1,y1,z1], ....[xN,yN,zN]]
            Edges: will generate [[a,b],[b,c], ....[n,a]]
            Faces: a single wrapped polygon around the bounds of the shape


    '''

    if mode in {'pydata', 'bm'}:
        dim = side / 2

        edges, faces = [], []

        if radius > 0.0 and radius < dim and nverts >= 2:
            verts = []
            theta = HALF_PI / (nverts-1)
            ext = dim - radius
            coords = [[ext, ext], [ext, -ext], [-ext, -ext], [-ext, ext]]
            for (x, y), corner in zip(coords, range(4)):
                for i in range(nverts):
                    rad = theta * i
                    verts.append(((math.sin(rad + (corner*HALF_PI)) * radius) + x, (math.cos(rad + (corner*HALF_PI)) * radius) + y, 0))

        elif radius > 0.0 and radius == dim and nverts >= 2:
            verts, edges, faces = circle(radius=dim, nverts=((nverts*4)-4))

        else:
            verts = [[-dim, dim, 0], [dim, dim, 0], [dim, -dim, 0], [-dim, -dim, 0]]
        # elif radius == 0.0 or (radius > 0.0 and radius > dim):
        
        num_verts = len(verts)
        if not edges:
            edges = [[i, i+1] for i in range(num_verts-1)] + [[num_verts-1, 0]]
            faces = [i for i in range(num_verts)]

        if mode == 'pydata':
            return verts, edges, [faces]
        else:
            return bmesh_from_pydata(verts, edges, [faces])

    if mode == 'np':
        pass


def arc_slice(outer_radius=1.0, inner_radius=0.8, phase=0, angle=PI, nverts=20, matrix=None, mode='pydata'):
    if mode in {'pydata', 'bm'}:

        # if outer_radius == inner_radius:
        #    return arc ? :)  or [], [], []

        if outer_radius < inner_radius:
            outer_radius, inner_radius = inner_radius, outer_radius

        verts = []
        theta = angle / (nverts-1)

        for i in range(nverts):
            rad = i * theta
            verts.append((math.sin(rad + phase) * outer_radius, math.cos(rad + phase) * outer_radius, 0))

        for i in reversed(range(nverts)):                
            rad = i * theta
            verts.append((math.sin(rad + phase) * inner_radius, math.cos(rad + phase) * inner_radius, 0))

        num_verts = len(verts)
        edges = [[i, i+1] for i in range(num_verts-1)] + [[num_verts-1, 0]]
        faces = [i for i in range(num_verts)]

        if mode == 'pydata':
            return verts, edges, [faces]
        else:
            return bmesh_from_pydata(verts, edges, [faces])

    if mode == 'np':
        pass


def rect(dim_x=1.0, dim_y=1.62, radius=0.0, nverts=5, matrix=None, mode='pydata'):

    xdim = dim_x / 2
    ydim = dim_y / 2

    if mode in {'pydata', 'bm'}:

        if radius == 0.0:
            verts = [[-xdim, ydim, 0], [xdim, ydim, 0], [xdim, -ydim, 0], [-xdim, -ydim, 0]]

        num_verts = len(verts)
        edges = [[i, i+1] for i in range(num_verts-1)] + [[num_verts-1, 0]]
        faces = [i for i in range(num_verts)]
        
        if mode == 'pydata':
            return verts, edges, [faces]
        else:
            return bmesh_from_pydata(verts, edges, [faces])

    if mode == 'np':
        pass



def iso_grid(numx=5, numy=5, dim=0.5, mode='pydata'):
    if mode in {'pydata', 'bm'}:

        if mode == 'pydata':
            # return vertices, edges, [faces]
            pass
        else:
            # return bmesh_from_pydata(vertices, edges, [faces])
            pass

    if mode == 'np':
        pass


def line(p1=((0,0,0)), p2=((1,0,0)), nverts=2, mode='pydata'):
    if mode in {'pydata', 'bm'}:

        if mode == 'pydata':
            # return vertices, edges, [faces]
            pass
        else:
            # return bmesh_from_pydata(vertices, edges, [faces])
            pass

    if mode == 'np':
        pass


# ----------- vectorized forms


arcs = vectorize(arc)
arc_slices = vectorize(arc_slice)
circles = vectorize(circle)
quads = vectorize(quad)
rects = vectorize(rect)