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
functions will initially be sub optimal quick implementations, then optimized only for speed, never for aesthetics or line count or cleverness.

'''

import math
from math import sin, cos, sqrt, acos, pi, atan
import numpy as np
from numpy import linalg
from functools import wraps
import time

import bpy
import bmesh
import mathutils
from mathutils import Matrix, Vector
from mathutils.geometry import interpolate_bezier, intersect_line_line, intersect_point_line


from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.data_structure import match_long_repeat
from sverchok.utils.logging import debug, info

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

def sn1_autodict(names, var_dict):
    return {k:v for k, v in var_dict.items() if k in set(names.split(' '))}


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
    '''
    this generator makes a flat donut section. Like arc, but with a inner and outer radius to determine
    the thickness of the slice.

    '''
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
        verts = []

        if radius == 0.0 or nverts < 2:
            verts = [[-xdim, ydim, 0], [xdim, ydim, 0], [xdim, -ydim, 0], [-xdim, -ydim, 0]]

        elif radius > 0.0 and radius < min(abs(dim_x), abs(dim_y)) and nverts >= 2:
            theta = HALF_PI / (nverts-1)
            xdim = xdim - radius
            ydim = ydim - radius
            coords = [[xdim, ydim], [xdim, -ydim], [-xdim, -ydim], [-xdim, ydim]]
            for (x, y), corner in zip(coords, range(4)):
                for i in range(nverts):
                    rad = theta * i
                    verts.append(((math.sin(rad + (corner*HALF_PI)) * radius) + x, (math.cos(rad + (corner*HALF_PI)) * radius) + y, 0))

        num_verts = len(verts)
        edges = [[i, i+1] for i in range(num_verts-1)] + [[num_verts-1, 0]]
        faces = [i for i in range(num_verts)]

        if mode == 'pydata':
            return verts, edges, [faces]
        else:
            return bmesh_from_pydata(verts, edges, [faces])

    if mode == 'np':
        pass



def grid(dim_x=1.0, dim_y=1.62, nx=2, ny=2, anchor=0, matrix=None, mode='pydata'):
    '''

    dim_x   -   total dimension on x side
    dim_y   -   total dimension on y side
    nx      -   num verts on x side
    ny      -   num verts on y side
    anchor  -   1 --- 2 --- 3
                -           -
                8     0     4
                -           -
                7 --- 6 --- 5
                default is centered (0)

    '''

    xside = dim_x / 2
    yside = dim_y / 2
    nx = max(2, nx)
    ny = max(2, ny)

    anchors = {
        1: (0,      dim_x, 0,      dim_y),
        2: (-xside, xside, 0,      dim_y),
        3: (-dim_x, 0,     0,      dim_y),
        4: (-dim_x, 0,     -yside, yside),
        5: (-dim_x, 0,     0,     -dim_y),
        6: (-xside, xside, 0,     -dim_y),
        7: (0,      dim_x, 0,     -dim_y),
        8: (0,      dim_x, -yside, yside),
        0: (-xside, xside, -yside, yside)
    }.get(anchor, (-xside, xside, -yside, yside))


    if mode in {'pydata', 'bm'}:
        verts = []
        faces = []
        add_face = faces.append
        total_range = ((ny-1) * (nx))

        a, b = anchors[:2]
        c, d = anchors[2:]
        x = np.linspace(a, b, nx)
        y = np.linspace(c, d, ny)
        f = np.vstack(np.meshgrid(x, y, 0)).reshape(3, -1).T
        verts = f.tolist()

        for i in range(total_range):
            if not ((i + 1) % nx == 0):  # +1 is the shift
                add_face([i, i+nx, i+nx+1, i+1])  # clockwise

        if mode == 'pydata':
            return verts, [], faces
        else:
            return bmesh_from_pydata(vert, [], faces)


    if mode == 'np':
        pass


def line(p1=[(0,0,0)], p2=[(1,0,0)], nverts=2, mode='pydata'):
    '''
    line(p1=[(0,0,0)], p2=[(1,0,0)], nverts=2, mode='pydata')
    not finished..

    '''
    nv = nverts

    if mode in {'pydata', 'bm'}:
        verts = []
        edges = []

        num_verts = 0
        for v1, v2 in zip(p1, p2):
            if nv == 2:
                verts.extend([v1, v2])
            elif nv > 2:
                x_seg = (v2[0] - v1[0]) / (nv-1)
                y_seg = (v2[1] - v1[1]) / (nv-1)
                z_seg = (v2[2] - v1[2]) / (nv-1)
                verts.append(v1)
                verts.extend([[v1[0] + (x_seg * i), v1[1] + (y_seg * i), v1[2] + (z_seg * i)] for i in range(1, nv-1)])
                verts.append(v2)

            edges.extend([[i + num_verts, i + 1 + num_verts] for i in range(nv-1)])
            num_verts = len(verts)

        if mode == 'pydata':
            return verts, edges
        else:
            return bmesh_from_pydata(verts, edges, [])

    if mode == 'np':
        pass


# ----------- vectorized forms


arcs = vectorize(arc)
arc_slices = vectorize(arc_slice)
circles = vectorize(circle)
quads = vectorize(quad)
rects = vectorize(rect)
lines = vectorize(line)
grids = vectorize(grid)

################################################
# Newer implementation of spline interpolation
# by zeffii, ly29 and portnov
# based on implementation from looptools 4.5.2 done by Bart Crouch
# factored out from interpolation_mk3 node
################################################

class Spline(object):
    """
    Base abstract class for LinearSpline and CubicSpline.
    """
    @classmethod
    def create_knots(cls, pts, metric="DISTANCE"):
        if metric == "DISTANCE":
            tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
            tknots = np.insert(tmp, 0, 0).cumsum()
            tknots = tknots / tknots[-1]
        elif metric == "MANHATTAN":
            tmp = np.sum(np.absolute(pts[:-1] - pts[1:]), 1)
            tknots = np.insert(tmp, 0, 0).cumsum()
            tknots = tknots / tknots[-1]
        elif metric == "POINTS":
            tknots = np.linspace(0, 1, len(pts))
        elif metric == "CHEBYSHEV":
            tknots = np.max(np.absolute(pts[1:] - pts[:-1]), 1)
            tknots = np.insert(tknots, 0, 0).cumsum()
            tknots = tknots / tknots[-1]
        elif metric == "X":
            tknots = pts[:,0]
            tknots = tknots - tknots[0]
            tknots = tknots / tknots[-1]
        elif metric == "Y":
            tknots = pts[:,1]
            tknots = tknots - tknots[0]
            tknots = tknots / tknots[-1]
        elif metric == "Z":
            tknots = pts[:,2]
            tknots = tknots - tknots[0]
            tknots = tknots / tknots[-1]

        return tknots

    def __init__(self):
        # Caches
        # t -> vertex
        self._single_eval_cache = {}

    def length(self, t_in):
        """
        t_in: np.array with values in [0,1]
        """
        t_in = t_in.copy()
        t_in.sort()
        points_on_spline = self.eval(t_in)
        t = points_on_spline[:-1] - points_on_spline[1:]
        norms = np.linalg.norm(t, axis=1)
        return norms.sum()
    
    def eval_at_point(self, t):
        """
        Evaluate spline at single point.
        t: float in [0,1].
        Returns vector in Sverchok format (tuple of floats).
        """
        result = self._single_eval_cache.get(t, None)
        if result is not None:
            return result
        else:
            result = self.eval(np.array([t]))
            result = tuple(result[0])
            self._single_eval_cache[t] = result
            return result

class CubicSpline(Spline):
    def __init__(self, vertices, tknots = None, metric = None, is_cyclic = False):
        """
        vertices: vertices in Sverchok's format (list of tuples)
        tknots: np.array of shape (n-1,). If not provided - calculated automatically based on metric
        metric: string, one of "DISTANCE", "MANHATTAN", "POINTS", "CHEBYSHEV". Mandatory if tknots
                is not provided
        is_cyclic: whether the spline is cyclic

        creates a cubic spline thorugh the locations given in vertices
        """

        super().__init__()

        if is_cyclic:

            locs = np.array(vertices[-4:] + vertices + vertices[:4])
            if tknots is None:
                if metric is None:
                    raise Exception("CubicSpline: either tknots or metric must be specified")
                tknots = Spline.create_knots(locs, metric)
                scale = 1 / (tknots[-4] - tknots[4])
                base = tknots[4]
                tknots -= base
                tknots *= scale
        else:
            locs = np.array(vertices)
            if tknots is None:
                if metric is None:
                    raise Exception("CubicSpline: either tknots or metric must be specified")
                tknots = Spline.create_knots(locs, metric)

        self.tknots = tknots
        self.is_cyclic = is_cyclic

        n = len(locs)
        if n < 2:
            raise Exception("Cubic spline can't be build from less than 3 vertices")

        # a = locs
        h = tknots[1:] - tknots[:-1]
        h[h == 0] = 1e-8
        q = np.zeros((n - 1, 3))
        q[1:] = 3 / h[1:, np.newaxis] * (locs[2:] - locs[1:-1]) - 3 / \
            h[:-1, np.newaxis] * (locs[1:-1] - locs[:-2])

        l = np.zeros((n, 3))
        l[0, :] = 1.0
        u = np.zeros((n - 1, 3))
        z = np.zeros((n, 3))

        for i in range(1, n - 1):
            l[i] = 2 * (tknots[i + 1] - tknots[i - 1]) - h[i - 1] * u[i - 1]
            l[i, l[i] == 0] = 1e-8
            u[i] = h[i] / l[i]
            z[i] = (q[i] - h[i - 1] * z[i - 1]) / l[i]
        l[-1, :] = 1.0
        z[-1] = 0.0

        b = np.zeros((n - 1, 3))
        c = np.zeros((n, 3))

        for i in range(n - 2, -1, -1):
            c[i] = z[i] - u[i] * c[i + 1]
        b = (locs[1:] - locs[:-1]) / h[:, np.newaxis] - h[:, np.newaxis] * (c[1:] + 2 * c[:-1]) / 3
        d = (c[1:] - c[:-1]) / (3 * h[:, np.newaxis])

        splines = np.zeros((n - 1, 5, 3))
        splines[:, 0] = locs[:-1]
        splines[:, 1] = b
        splines[:, 2] = c[:-1]
        splines[:, 3] = d
        splines[:, 4] = tknots[:-1, np.newaxis]
        
        self.splines = splines

    def eval(self, t_in, tknots = None):
        """
        Evaluate the spline at the points in t_in, which must be an array
        with values in [0,1]
        returns and np array with the corresponding points
        """

        if tknots is None:
            tknots = self.tknots

        index = tknots.searchsorted(t_in, side='left') - 1
        index = index.clip(0, len(self.splines) - 1)
        to_calc = self.splines[index]
        ax, bx, cx, dx, tx = np.swapaxes(to_calc, 0, 1)
        t_r = t_in[:, np.newaxis] - tx
        out = ax + t_r * (bx + t_r * (cx + t_r * dx))
        return out

    def tangent(self, t_in, h=0.001, tknots=None):
        """
        Calc numerical tangents for spline at t_in
        """

        if tknots is None:
            tknots = self.tknots

        t_ph = t_in + h
        t_mh = t_in - h
        t_less_than_0 = t_mh < 0.0
        t_great_than_1 = t_ph > 1.0
        t_mh[t_less_than_0] += h
        t_ph[t_great_than_1] -= h
        tanget_ph = self.eval(t_ph)
        tanget_mh = self.eval(t_mh)
        tanget = tanget_ph - tanget_mh
        tanget[t_less_than_0 | t_great_than_1] *= 2
        return tanget

class LinearSpline(Spline):
    def __init__(self, vertices, tknots = None, metric = None, is_cyclic = False):
        """
        vertices: vertices in Sverchok's format (list of tuples)
        tknots: np.array of shape (n-1,). If not provided - calculated automatically based on metric
        metric: string, one of "DISTANCE", "MANHATTAN", "POINTS", "CHEBYSHEV". Mandatory if tknots
                is not provided
        is_cyclic: whether the spline is cyclic

        creates a cubic spline thorugh the locations given in vertices
        """

        super().__init__()

        if is_cyclic:
            pts = np.array(vertices + [vertices[0]])
        else:
            pts = np.array(vertices)

        if tknots is None:
            if metric is None:
                raise Exception("LinearSpline: either tknots or metric must be specified")
            tknots = Spline.create_knots(pts, metric)

        self.pts = pts
        self.tknots = tknots
        self.is_cyclic = is_cyclic

    def eval(self, t_in, tknots = None):
        """
        Eval the liner spline f(t) = x,y,z through the points
        in pts given the knots in tknots at the point in t_in
        """

        if tknots is None:
            tknots = self.tknots
            
        ptsT = self.pts.T
        out = np.zeros((3, len(t_in)))
        for i in range(3):
            out[i] = np.interp(t_in, tknots, ptsT[i])
        return out.T

    def tangent(self, t_in, tknots = None, h = None):
        if tknots is None:
            tknots = self.tknots

        lookup_segments = GenerateLookup(self.is_cyclic, self.pts.tolist())
        return np.array([lookup_segments.find_bucket(f) for f in t_in])

class Spline2D(object):
    """
    2D Spline (surface).
    Composed by putting 1D splines along V direction, and then interpolating
    across them (in U direction) by using another series of 1D splines.
    U and V splines can both be either linear or cubic.
    The spline can optionally be cyclic in U and/or V directions
    (so it can form a cylindrical or thoroidal surface).
    This is implemented partly in pure python, partly in numpy, so the performance
    is not very good. The performance is not very bad either, because of caching.
    """
    def __init__(self, vertices,
            u_spline_constructor = CubicSpline, v_spline_constructor = None,
            metric = "DISTANCE",
            is_cyclic_u = False, is_cyclic_v = False):
        """
        vertices: Vertices in Sverchok format, i.e. list of list of 3-tuples.
        u_spline_constructor: constructor of Spline objects.
        v_spline_constructor: constructor of Spline objects. Defaults to u_spline_constructor.
        is_cyclic_u: whether the spline is cyclic in the U direction
        is_cyclic_v: whether the spline is cyclic in the V direction
        metric: string, one of "DISTANCE", "MANHATTAN", "POINTS", "CHEBYSHEV".
        """
        self.vertices = np.array(vertices)
        if v_spline_constructor is None:
            v_spline_constructor = u_spline_constructor
        self.u_spline_constructor = u_spline_constructor
        self.v_spline_constructor = v_spline_constructor
        self.metric = metric
        self.is_cyclic_u = is_cyclic_u
        self.is_cyclic_v = is_cyclic_v

        self._v_splines = [v_spline_constructor(verts, is_cyclic=is_cyclic_v, metric=metric) for verts in vertices]

        # Caches
        # v -> Spline
        self._u_splines = {}
        # (u,v) -> vertex
        self._eval_cache = {}
        # (u,v) -> normal
        self._normal_cache = {}

    def get_u_spline(self, v, vertices):
        """Get a spline along U direction for specified value of V coordinate"""
        spline = self._u_splines.get(v, None)
        if spline is not None:
            return spline
        else:
            spline = self.u_spline_constructor(vertices, is_cyclic=self.is_cyclic_u, metric=self.metric)
            self._u_splines[v] = spline
            return spline

    def eval(self, u, v):
        """
        u, v: floats in [0, 1].
        Returns 3-tuple of floats.

        Evaluate the spline at single point.
        """

        result = self._eval_cache.get((u,v), None)
        if result is not None:
            return result
        else:
            spline_vertices = [spline.eval_at_point(v) for spline in self._v_splines]
            u_spline = self.get_u_spline(v, spline_vertices)
            result = u_spline.eval_at_point(u)
            self._eval_cache[(u,v)] = result
            return result

    def normal(self, u, v, h=0.001):
        """
        u, v: floats in [0,1].
        h: step for numeric differentials calculation.
        Returns 3-tuple of floats.

        Get the normal vector for spline at specific point.
        """

        result = self._normal_cache.get((u,v), None)
        if result is not None:
            return result
        else:
            point = np.array(self.eval(u, v))
            point_u = np.array(self.eval(u+h, v))
            point_v = np.array(self.eval(u, v+h))
            du = (point_u - point)/h
            dv = (point_v - point)/h
            n = np.cross(du, dv)
            norm = np.linalg.norm(n)
            if norm != 0:
                n = n / norm
            #debug("DU: {}, DV: {}, N: {}".format(du, dv, n))
            result = tuple(n)
            self._normal_cache[(u,v)] = result
            return result

class GenerateLookup():

    def __init__(self, cyclic, vlist):
        self.lookup = {}
        self.summed_lengths = []
        self.indiv_lengths = []
        self.normals = []
        self.buckets = []
        if cyclic:
            vlist = vlist + [vlist[0]]

        self.get_seq_len(vlist)
        self.acquire_lookup_table()
        self.get_buckets()
        # for idx, (k, v) in enumerate(sorted(self.lookup.items())):
        #     debug(k, v)

    def find_bucket(self, factor):
        for bucket_min, bucket_max in zip(self.buckets[:-1], self.buckets[1:]):
            if bucket_min <= factor < bucket_max:
                tval = self.lookup.get(bucket_min)  # , self.lookup.get(self.buckets[-1]))

                return tval

        # return last bucket just in case
        return self.lookup.get(self.buckets[-1])

    def get_buckets(self):
        self.buckets = [(clen / self.total_length) for clen in self.summed_lengths]
    
    def acquire_lookup_table(self):
        for current_length, segment_normal in zip(self.summed_lengths, self.normals):
            self.lookup[current_length / self.total_length] = segment_normal
        
    def get_seq_len(self, vlist):
        add_len = self.indiv_lengths.append
        add_normal = self.normals.append
        add_to_sumlist = self.summed_lengths.append
        current_length = 0.0
        for idx in range(len(vlist)-1):
            v = vlist[idx][0]-vlist[idx+1][0], vlist[idx][1]-vlist[idx+1][1], vlist[idx][2]-vlist[idx+1][2]
            length = math.sqrt((v[0]*v[0]) + (v[1]*v[1]) + (v[2]*v[2]))
            add_normal(v)
            add_len(length)
            add_to_sumlist(current_length)
            current_length += length

        self.total_length = sum(self.indiv_lengths)
            
def householder(u):
    '''
    Calculate Householder reflection matrix.

    u: mathutils.Vector or tuple of 3 floats.
    returns mathutils.Matrix.
    '''
    x,y,z = u[0], u[1], u[2]
    m = Matrix([[x*x, x*y, x*z, 0], [x*y, y*y, y*z, 0], [x*z, y*z, z*z, 0], [0,0,0,0]])
    h = Matrix() - 2*m
    return h

def autorotate_householder(e1, xx):
    '''
    A matrix of transformation which will transform xx vector into e1,
    calculated via Householder matrix.
    See http://en.wikipedia.org/wiki/QR_decomposition

    e1, xx: mathutils.Vector.
    returns mathutils.Matrix.
    '''

    sign = -1
    alpha = xx.length * sign
    u = xx - alpha*e1
    v = u.normalized()
    q = householder(v)
    return q

def autorotate_track(e1, xx, up):
    '''
    A matrix of transformation which will transform xx vector into e1,
    calculated via Blender's to_track_quat method.

    e1: string, one of "X", "Y", "Z"
    xx: mathutils.Vector.
    up: string, one of "X", "Y", "Z".
    returns mathutils.Matrix.
    '''
    rotation = xx.to_track_quat(e1, up)
    return rotation.to_matrix().to_4x4()

def autorotate_diff(e1, xx):
    '''
    A matrix of transformation which will transform xx vector into e1,
    calculated via Blender's rotation_difference method.

    e1, xx: mathutils.Vector.
    returns mathutils.Matrix.
    '''
    return xx.rotation_difference(e1).to_matrix().to_4x4()

def diameter(vertices, axis):
    """
    Calculate diameter of set of vertices along specified axis.
    
    vertices: list of mathutils.Vector or of 3-tuples of floats.
    axis: either
        * integer: 0, 1 or 2 for X, Y or Z
        * string: 'X', 'Y' or 'Z'
        * 3-tuple of floats or Vector: any direction
        * None: calculate diameter regardless of direction
    returns float.
    """
    if axis is None:
        distances = [(mathutils.Vector(v1) - mathutils.Vector(v2)).length for v1 in vertices for v2 in vertices]
        return max(distances)
    elif isinstance(axis, tuple) or isinstance(axis, Vector):
        axis = mathutils.Vector(axis).normalized()
        ds = [mathutils.Vector(vertex).dot(axis) for vertex in vertices]
        M = max(ds)
        m = min(ds)
        return (M-m)
    else:
        if axis == 'X':
            axis = 0
        elif axis == 'Y':
            axis = 1
        elif axis == 'Z':
            axis = 2
        elif isinstance(axis, str):
            raise Exception("Unknown axis: {}".format(axis))

        xs = [vertex[axis] for vertex in vertices]
        M = max(xs)
        m = min(xs)
        return (M-m)

def center(data):
    """
    input: data - a list of 3-tuples or numpy array of same shape
    output: 3-tuple - arithmetical average of input vertices (barycenter)
    """
    array = np.array(data)
    n = array.shape[0]
    center = array.sum(axis=0) / n
    return tuple(center)

def interpolate_quadratic_bezier(knot1, handle, knot2, resolution):
    """
    Interpolate a quadartic bezier spline segment.
    Quadratic bezier curve is defined by two knots (at the beginning and at the
    end of segment) and one handle.

    Quadratic bezier curves is a special case of cubic bezier curves, which
    are implemented in blender. So this function just converts input data
    and calls for interpolate_bezier.
    """
    if not isinstance(knot1, mathutils.Vector):
        knot1 = mathutils.Vector(knot1)
    if not isinstance(knot2, mathutils.Vector):
        knot2 = mathutils.Vector(knot2)
    if not isinstance(handle, mathutils.Vector):
        handle = mathutils.Vector(handle)

    handle1 = knot1 + (2.0/3.0) * (handle - knot1)
    handle2 = handle + (1.0/3.0) * (knot2 - handle)
    return interpolate_bezier(knot1, handle1, handle2, knot2, resolution)

def calc_normal(vertices):
    """
    Calculate normal for a face defined by specified vertices.
    For tris or quads, mathutils.geometry.normal() is used.
    Ngon will be triangulated, and then the average normal of
    all resulting tris will be returned.

    input: list of 3-tuples or list of mathutils.Vector.
    output: mathutils.Vector.
    """
    n = len(vertices)
    vertices = list(map(mathutils.Vector, vertices))
    if n <= 4:
        return mathutils.geometry.normal(*vertices)
    else:
        # Triangluate
        triangle_idxs = [[0, k, k+1] for k in range(1, n-1)]
        triangles = [[vertices[i] for i in idxs] for idxs in triangle_idxs]
        subnormals = [mathutils.geometry.normal(*triangle) for triangle in triangles]
        return mathutils.Vector(center(subnormals))

class PlaneEquation(object):
    """
    An object, containing the coefficients A, B, C, D in the equation of a
    plane:
        
        A*x + B*y + C*z + D = 0
    """
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def __repr__(self):
        return "[{}, {}, {}, {}]".format(self.a, self.b, self.c, self.d)
    
    def __str__(self):
        return "{}x + {}y + {}z + {} = 0".format(self.a, self.b, self.c, self.d)

    @classmethod
    def from_normal_and_point(cls, normal, point):
        a, b, c = tuple(normal)
        cx, cy, cz = tuple(point)
        d = - (a*cx + b*cy + c*cz)
        return PlaneEquation(a, b, c, d)

    @classmethod
    def from_three_points(cls, p1, p2, p3):
        x1, y1, z1 = p1[0], p1[1], p1[2]
        x2, y2, z2 = p2[0], p2[1], p2[2]
        x3, y3, z3 = p3[0], p3[1], p3[2]

        a = (y2 - y1)*(z3-z1) - (z2 - z1)*(y3 - y1)
        b = - (x2 - x1)*(z3-z1) + (z2 - z1)*(x3 - x1)
        c = (x2 - x1)*(y3 - y1) - (y2 - y1)*(x3 - x1)

        return PlaneEquation.from_normal_and_point((a, b, c), p1)

    @classmethod
    def from_point_and_two_vectors(cls, point, v1, v2):
        normal = v1.cross(v2)
        return PlaneEquation.from_normal_and_point(normal, point)

    @classmethod
    def from_coordinate_plane(cls, plane_name):
        if plane_name == 'XY':
            return PlaneEquation(0, 0, 1, 0)
        elif plane_name == 'YZ':
            return PlaneEquation(1, 0, 0, 0)
        elif plane_name == 'XZ':
            return PlaneEquation(0, 1, 0, 0)
        else:
            raise Exception("Unknown coordinate plane name")

    def normalized(self):
        """
        Return equation, which defines exactly the same plane, but with coefficients adjusted so that

            A^2 + B^2 + C^2 = 1

        holds.
        """
        normal = self.normal.length
        if abs(normal) < 1e-8:
            raise Exception("Normal of the plane is (nearly) zero: ({}, {}, {})".format(self.a, self.b, self.c))
        return PlaneEquation(a/normal, b/normal, c/normal, d/normal)
    
    def check(self, point, eps=1e-6):
        """
        Check if specified point belongs to the plane.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        x, y, z = point[0], point[1], point[2]
        value = a*x + b*y + c*z + d
        return abs(value) < eps

    def two_vectors(self):
        """
        Return two vectors that are parallel two this plane.
        Note: the two vectors returned are orthogonal.

        output: (Vector, Vector)
        """
        v1 = self.normal.orthogonal()
        v2 = v1.cross(self.normal)
        return v1, v2


    def evaluate(self, u, v):
        """
        Return a point on the plane by it's UV coordinates.
        UV coordinates origin is self.point.
        Orientation of UV coordinates system is undefined.
        Scale of UV coordinates system is defined by coordinates
        of self.normal. One can use plane.normalized().evaluate()
        to make sure that the scale of UV coordinates system is 1:1.

        input: two floats.
        output: Vector.
        """
        p0 = self.nearest_point_to_origin()
        v1, v2 = self.two_vectors()
        return p0 + u*v1 + v*v2

    @property
    def normal(self):
        return mathutils.Vector((self.a, self.b, self.c))

    @normal.setter
    def normal(self, normal):
        self.a = normal[0]
        self.b = normal[1]
        self.c = normal[2]

    def nearest_point_to_origin(self):
        """
        Returns the point on plane which is the nearest
        to the origin (0, 0, 0).
        output: Vector.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        sqr = a*a + b*b + c*c
        if sqr < 1e-8:
            raise Exception("Plane normal is (almost) zero!")
        return mathutils.Vector(((- a*d)/sqr, (- b*d)/sqr, (- c*d)/sqr))
    
    def distance_to_point(self, point):
        """
        Return distance from specified point to this plane.
        input: Vector or 3-tuple
        output: float.
        """
        point_on_plane = self.nearest_point_to_origin()
        return mathutils.geometry.distance_point_to_plane(mathutils.Vector(point), point_on_plane, self.normal)

    def distance_to_points(self, points):
        """
        Return distances from specified points to this plane.
        input: list of 3-tuples, or numpy array of same shape
        output: numpy array of floats.
        """
        # Distance from (x,y,z) to the plane is given by formula:
        # 
        #          | A x + B y + C z + D |
        #   rho = -------------------------
        #           sqrt(A^2 + B^2 + C^2)
        #
        points = np.array(points)
        a, b, c, d = self.a, self.b, self.c, self.d
        # (A x + B y + C z) is a scalar product of (x, y, z) and (A, B, C)
        numerators = abs(points.dot([a, b, c]) + d)
        denominator = math.sqrt(a*a + b*b + c*c)
        return numerators / denominator

    def intersect_with_line(self, line, min_det=1e-8):
        """
        Calculate intersection between this plane and specified line.
        input: line - an instance of LineEquation.
        output: Vector.
        """
        a, b, c = line.a, line.b, line.c
        x0, y0, z0 = line.x0, line.y0, line.z0

        # Here we numerically solve the system of linear equations:
        #
        #   /    x - x0   y - y0   z - z0
        #   |    ------ = ------ = ------, (line)
        #   /      A        B        C                (*)
        #   `
        #   |   Ap x + Bp y + Cp z + Dp = 0    (plane)
        #    `
        # 
        # with relation to x, y, z.
        # It is possible that any two of A, B, C are equal to zero,
        # but not all three of them.
        # Depending on which of A, B, C is not zero, we should
        # consider different representations of line equation.
        #
        # For example, if B != 0, we can represent (*) as
        #
        #   B (x - x0) = A (y - y0),
        #   C (y - y0) = B (z - z0),
        #   Ap x + Bp x + Cp z + Dp = 0.
        #
        # But, if B == 0, then this representation will contain
        # two exactly equivalent equations:
        # 
        #   0 = A (y - y0),
        #   C (y - y0) = 0,
        #   Ap x + 0 + Cp z + Dp = 0.
        #
        # In this case, the system will become singular; so
        # we must choose another representation of (*) system.

        epsilon = 1e-8

        #info("Line: %s", line)

        if abs(a) > epsilon:
            matrix = np.array([
                        [b, -a, 0],
                        [c, 0, -a],
                        [self.a, self.b, self.c]])
            free = np.array([
                        b*x0 - a*y0,
                        c*x0 - a*z0,
                        -self.d])
        elif abs(b) > epsilon:
            matrix = np.array([
                        [b, -a, 0],
                        [0, c, -b],
                        [self.a, self.b, self.c]])

            free = np.array([
                        b*x0 - a*y0,
                        c*y0 - b*z0,
                        -self.d])
        elif abs(c) > epsilon:
            matrix = np.array([
                        [c, 0, -a],
                        [0, c, -b],
                        [self.a, self.b, self.c]])
            free = np.array([
                        c*x0 - a*z0,
                        c*y0 - b*z0,
                        -self.d])
        else:
            raise Exception("Invalid plane: all coefficients are (nearly) zero: {}, {}, {}".format(a, b, c))

        det = linalg.det(matrix)
        if abs(det) < min_det:
            return None
            #raise Exception("Plane: {}, line: {}, det: {}".format(self, line, det))

        result = np.linalg.solve(matrix, free)
        x, y, z = result[0], result[1], result[2]
        return mathutils.Vector((x, y, z))

    def side_of_point(self, point, eps=1e-8):
        """
        Determine the side on which the point is with relation to this plane.

        input: Vector or 3-tuple or numpy array of same shape
        output: +1 if the point is at one side of the plane; 
                -1 if the point is at another side;
                0 if the point belongs to the plane.
                "Positive" side of the plane is defined by direction of
                normal vector.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        x, y, z = point[0], point[1], point[2]
        value = a*x + b*y + c*z + d
        if abs(value) < eps:
            return 0
        elif value > 0:
            return +1
        else:
            return -1

    def side_of_points(self, points):
        """
        For each point, determine the side on which the point is with relation to this plane.

        input: numpy array of shape (n, 3)
        output: numpy array of shape (n,):
                +1 if the point is at one side of the plane; 
                -1 if the point is at another side;
                0 if the point belongs to the plane.
                "Positive" side of the plane is defined by direction of
                normal vector.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        values = points.dot([a,b,c]) + d
        return np.sign(values)

    def projection_of_point(self, point):
        """
        Return a projection of specified point to this plane.
        input: Vector or 3-tuple.
        output: Vector.
        """
        normal = self.normal.normalized()
        distance = abs(self.distance_to_point(point))
        sign = self.side_of_point(point)
        result = Vector(point) - sign * distance * normal
        #info("P(%s): %s - %s * [%s] * %s = %s", point, point, sign, distance, normal, result)
        return result
    
    def projection_of_points(self, points):
        """
        Return projections of specified points to this plane.
        input: list of Vector or list of 3-tuples or numpy array of shape (n, 3).
        output: numpy array of shape (n, 3).
        """
        points = np.array(points)
        normal = np.array(self.normal.normalized())
        distances = self.distance_to_points(points)
        signs = self.side_of_points(points)
        signed_distances = np.multiply(signs, distances)
        scaled_normals = np.outer(signed_distances, normal)
        return points - scaled_normals

    def projection_of_vector(self, v1, v2):
        v1p = self.projection_of_point(v1)
        v2p = self.projection_of_point(v2)
        return v2p - v1p

    def intersect_with_plane(self, plane2):
        """
        Return an intersection of this plane with another one.
        
        input: PlaneEquation
        output: LineEquation or None, in case two planes are parallel.
        """
        if self.is_parallel(plane2):
            debug("{} is parallel to {}".format(self, plane2))
            return None

        # We need an arbitrary point on this plane and two vectors.
        # Draw two lines in this plane and see for theirs intersection
        # with another plane.
        p0 = self.nearest_point_to_origin()
        v1, v2 = self.two_vectors()
        # it might be that p0 belongs to plane2; in that case we choose
        # another point in the same plane
        if plane2.check(p0):
            # Since v1 and v2 are orthogonal, it may not be that they are
            # both parallel to plane2.
            if not plane2.is_parallel(v1):
                p0 = p0 + v1
            else:
                p0 = p0 + v2
        line1 = LineEquation.from_direction_and_point(v1, p0)
        line2 = LineEquation.from_direction_and_point(v2, p0)

        # it might be that one of vectors we chose is parallel to plane2
        # (since we are choosing them arbitrarily); but from the way
        # we are choosing v1 and v2, we know they are orthogonal.
        # So if wee just rotate them by pi/4, they will no longer be
        # parallel to plane2.
        if plane2.is_parallel(line1) or plane2.is_parallel(line2):
            v1_new = v1 + v2
            v2_new = v1 - v2
            info("{}, {} => {}, {}".format(v1, v2, v1_new, v2_new))
            line1 = LineEquation.from_direction_and_point(v1_new, p0)
            line2 = LineEquation.from_direction_and_point(v2_new, p0)

        p1 = plane2.intersect_with_line(line1)
        p2 = plane2.intersect_with_line(line2)
        return LineEquation.from_two_points(p1, p2)

    def is_parallel(self, other):
        """
        Check if other object is parallel to this plane.
        input: PlaneEquation, LineEquation or Vector.
        output: boolean.
        """
        if isinstance(other, PlaneEquation):
            return abs(self.normal.angle(other.normal)) < 1e-8
        elif isinstance(other, LineEquation):
            return abs(self.normal.dot(other.direction)) < 1e-8
        elif isinstance(other, mathutils.Vector):
            return abs(self.normal.dot(other)) < 1e-8
        else:
            raise Exception("Don't know how to check is_parallel for {}".format(type(other)))

class LineEquation(object):
    """
    An object, containing the coefficients A, B, C, x0, y0, z0 in the
    equation of a line:

            x - x0   y - y0   z - z0
            ------ = ------ = ------,
               A       B        C
    """

    def __init__(self, a, b, c, point):
        epsilon = 1e-8
        if abs(a) < epsilon and abs(b) < epsilon and abs(c) < epsilon:
            raise Exception("Direction is (nearly) zero: {}, {}, {}".format(a, b, c))
        self.a = a
        self.b = b
        self.c = c
        self.point = point

    @classmethod
    def from_two_points(cls, p1, p2):
        if (mathutils.Vector(p1) - mathutils.Vector(p2)).length < 1e-8:
            raise Exception("Two points are (almost) the same: {}, {}".format(p1, p2))
        x1, y1, z1 = p1[0], p1[1], p1[2]
        x2, y2, z2 = p2[0], p2[1], p2[2]

        a = x2 - x1
        b = y2 - y1
        c = z2 - z1

        return LineEquation(a, b, c, p1)

    @classmethod
    def from_direction_and_point(cls, direction, point):
        a, b, c = tuple(direction)
        return LineEquation(a, b, c, point)

    @classmethod
    def from_coordinate_axis(cls, axis_name):
        if axis_name == 'X':
            return LineEquation(1, 0, 0, (0, 0, 0))
        elif axis_name == 'Y':
            return LineEquation(0, 1, 0, (0, 0, 0))
        elif axis_name == 'Z':
            return LineEquation(0, 0, 1, (0, 0, 0))
        else:
            raise Exception("Unknown axis name")

    def check(self, point, eps=1e-6):
        """
        Check if the specified point belongs to the line.
        """
        a, b, c = self.a, self.b, self.c
        x0, y0, z0 = self.x0, self.y0, self.z0
        x, y, z = point[0], point[1], point[2]

        value1 = b * (x - x0) - a * (y - y0)
        value2 = c * (y - y0) - b * (z - z0)

        return abs(value1) < eps and abs(value2) < eps

    @property
    def x0(self):
        return self.point[0]
    
    @x0.setter
    def x0(self, x0):
        self.point[0] = x0

    @property
    def y0(self):
        return self.point[1]
    
    @y0.setter
    def y0(self, y0):
        self.point[1] = y0

    @property
    def z0(self):
        return self.point[2]
    
    @z0.setter
    def z0(self, z0):
        self.point[2] = z0

    @property
    def direction(self):
        return mathutils.Vector((self.a, self.b, self.c))

    @direction.setter
    def direction(self, vector):
        self.a = vector[0]
        self.b = vector[1]
        self.c = vector[2]

    def __repr__(self):
        return "[{}, {}, {}, ({}, {}, {})]".format(self.a, self.b, self.c, self.x0, self.y0, self.z0)
    
    def __str__(self):
        return "(x - {})/{} = (y - {})/{} = (z - {})/{}".format(self.x0, self.a, self.y0, self.b, self.z0, self.c)

    def distance_to_point(self, point):
        """
        Return the distance between the specified point and this line.
        input: Vector or 3-tuple.
        output: float.
        """
        # TODO: there should be more effective way to do this
        projection = self.projection_of_point(point)
        return (mathutils.Vector(point) - projection).length

    def projection_of_point(self, point):
        """
        Return the projection of the specified point on this line.
        input: Vector or 3-tuple.
        output: Vector.
        """
        # Draw a plane, which has the same normal as
        # this line's direction vector, and which contains the
        # given point
        plane = PlaneEquation.from_normal_and_point(self.direction, point)
        # Then find an intersection of that plane with this line.
        return plane.intersect_with_line(self)

class LineEquation2D(object):
    def __init__(self, a, b, c):
        epsilon = 1e-8
        if abs(a) < epsilon and abs(b) < epsilon:
            raise Exception(f"Direction is (nearly) zero: {a}, {b}")
        self.a = a
        self.b = b
        self.c = c

    def __repr__(self):
        return f"{self.a}*x + {self.b}*y + {self.c} = 0"

    @classmethod
    def from_normal_and_point(cls, normal, point):
        a, b = tuple(normal)
        cx, cy = tuple(point)
        c = - (a*cx + b*cy)
        return LineEquation2D(a, b, c)

    @classmethod
    def from_direction_and_point(cls, direction, point):
        dx, dy = tuple(direction)
        return LineEquation2D.from_normal_and_point((-dy, dx), point)

    @classmethod
    def from_two_points(cls, v1, v2):
        x1,y1 = tuple(v1)
        x2,y2 = tuple(v2)
        a = y2 - y1
        b = x1 - x2
        c = y1*x2 - x1*y2
        epsilon = 1e-8
        if abs(a) < epsilon and abs(b) < epsilon:
            raise Exception(f"Two points are too close: {v1}, {v2}")
        return LineEquation2D(a, b, c)

    @classmethod
    def from_coordinate_axis(cls, axis_name):
        if axis_name == 'X':
            return LineEquation2D(0, 1, 0)
        elif axis_name == 'Y':
            return LineEquation2D(1, 0, 0)
        else:
            raise Exception("Unknown coordinate axis name")

    @property
    def normal(self):
        return Vector((self.a, self.b))

    @normal.setter
    def normal(self, normal):
        self.a = normal[0]
        self.b = normal[1]

    @property
    def direction(self):
        return Vector((-self.b, self.a))

    @direction.setter
    def direction(self, direction):
        self.a = - direvtion[1]
        self.b = direction[0]

    def nearest_point_to_origin(self):
        a, b, c = self.a, self.b, self.c
        sqr = a*a + b*b
        return Vector(( (-a*c)/sqr, (-b*c)/sqr ))

    def two_points(self):
        p1 = self.nearest_point_to_origin()
        p2 = p1 + self.direction
        return p1, p2

    def check(self, point, eps=1e-6):
        a, b, c = self.a, self.b, self.c
        x, y, z = tuple(point)
        value = a*x + b*y + c
        return abs(value) < eps

    def side_of_point(self, point, eps=1e-8):
        a, b, c = self.a, self.b, self.c
        x, y = tuple(point)
        value = a*x + b*y + c
        if abs(value) < eps:
            return 0
        elif value > 0:
            return +1
        else:
            return -1

    def distance_to_point(self, point):
        a, b, c = self.a, self.b, self.c
        x, y = tuple(point)
        value = a*x + b*y + c
        numerator = abs(value)
        denominator = sqrt(a*a + b*b)
        return numerator / denominator

    def projection_of_point(self, point):
        normal = self.normal.normalized()
        distance = self.distance_to_point(point)
        sign = self.side_of_point(point)
        return Vector(point) - sign * distance * normal

    def intersect_with_line(self, line2, min_det=1e-8):
        """
        Find intersection between two lines.
        """
        #
        #   /
        #   |  A1 x + B1 y + C1 = 0
        #  /
        #  \
        #   |  A2 x + B2 y + C2 = 0
        #   \
        #
        matrix = np.array([
                    [self.a, self.b],
                    [line2.a, line2.b]
                ])
        free = np.array([
                    -self.c,
                    -line2.c
                ])

        det = linalg.det(matrix)
        if abs(det) < min_det:
            return None

        result = np.linalg.solve(matrix, free)
        x, y = tuple(result)
        return Vector((x, y))

class CircleEquation2D(object):
    def __init__(self, center, radius):
        if not isinstance(center, Vector):
            center = Vector(center)
        self.center = center
        self.radius = radius

    def __str__(self):
        return f"(x - {self.center.x})^2 + (y - {self.center.y})^2 = {self.radius}^2"

    def evaluate(self, point):
        x, y = tuple(point)
        x0, y0 = tuple(self.center)
        r = self.radius
        return (x - x0)**2 + (y - y0)**2 - r**2

    def check(self, point, eps=1e-8):
        value = self.evaluate(point)
        return abs(value) < eps

    def intersect_with_line(self, line2):
        line_p1, line_p2 = line2.two_points()
        r = mathutils.geometry.intersect_line_sphere_2d(line_p1, line_p2, self.center, self.radius, False)
        return r

    def intersect_with_segment(self, p1, p2):
        return mathutils.geometry.intersect_line_sphere_2d(p1, p2, self.center, self.radius, True)

    def intersect_with_circle(self, circle2):
        return mathutils.geometry.intersect_sphere_sphere_2d(self.center, self.radius, circle2.center, circle2.radius)

    def projection_of_point(self, point, nearest=True):
        line = LineEquation2D.from_two_points(self.center, point)
        p1, p2 = self.intersect_with_line(line)
        if nearest:
            if p1 is None and p2 is None:
                return None
            if p1 is None and p2 is not None:
                return p2
            if p1 is not None and p2 is None:
                return p1
            rho1 = (point - p1).length
            rho2 = (point - p2).length
            if rho1 < rho2:
                return p1
            else:
                return p2
        else:
            return p1, p2

    def contains(self, point, include_bound=True, eps=1e-8):
        value = self.evaluate(point)
        on_edge = abs(value) < eps
        if include_bound:
            return (value < 0) or on_edge
        else:
            return value < 0

class Ellipse3D(object):
    """
    Class describing an ellipse in 3D.
    """
    def __init__(self, center, semi_major_axis, semi_minor_axis):
        """
        input: center - mathutils.Vector.
               semi_major_axis, semi_minor_axis - mathutils.Vector (pointing from center).
        """
        self.center = center
        self.semi_major_axis = semi_major_axis
        self.semi_minor_axis = semi_minor_axis

    @property
    def a(self):
        """
        Length of the semi-major axis
        """
        return self.semi_major_axis.length

    @property
    def b(self):
        """
        Length of the semi-minor axis
        """
        return self.semi_minor_axis.length

    @property
    def c(self):
        """
        Distance from the center of the ellipse to it's focal points.
        """
        a = self.a
        b = self.b
        return sqrt(a*a - b*b)

    @property
    def eccentricity(self):
        return self.c / self.a

    def normal(self):
        return self.semi_major_axis.cross(self.semi_minor_axis).normalized()

    def get_matrix(self):
        matrix = Matrix([self.semi_major_axis.normalized(), self.semi_minor_axis.normalized(), self.normal()]).to_4x4().inverted()
        matrix.translation = self.center
        return matrix

    def focal_points(self):
        c = self.c
        dv = self.semi_major_axis.normalized() * c
        f1 = self.center - dv
        f2 = self.center + dv
        return [f1, f2]

    @property
    def f1(self):
        c = self.c
        dv = self.semi_major_axis.normalized() * c
        return self.center - dv

    @property
    def f2(self):
        c = self.c
        dv = self.semi_major_axis.normalized() * c
        return self.center + dv

class Triangle(object):
    """
    Class containing general information about a triangle (in 3D).
    A triangle is defined by three vertices.
    """
    def __init__(self, v1, v2, v3):
        """
        inputs: v1, v2, v3 - mathutils.Vector.
        """
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    @property
    def vertices(self):
        """
        List of triangle vertices.
        """
        return [self.v1, self.v2, self.v3]

    def centroid(self):
        """
        Centroid (barycenter) of the triangle.
        """
        return (self.v1 + self.v2 + self.v3) / 3.0

    def normal(self):
        """
        Triangle plane normal.
        """
        return mathutils.geometry.normal(self.v1, self.v2, self.v3)

    def area(self):
        """
        Triangle area.
        """
        return mathutils.geometry.area_tri(self.v1, self.v2, self.v3)

    def perimeter(self):
        """
        Triangle perimeter.
        """
        dv1 = self.v2 - self.v1
        dv2 = self.v3 - self.v1
        dv3 = self.v3 - self.v2
        return dv1.length + dv2.length + dv3.length

    def inscribed_circle_radius(self):
        """
        The radius of the inscribed circle.
        """
        return 2 * self.area() / self.perimeter()

    def inscribed_circle_center(self):
        """
        The center of the inscribed circle.
        returns: mathutils.Vector.
        """
        side_1 = (self.v2 - self.v3).length
        side_2 = (self.v1 - self.v3).length
        side_3 = (self.v1 - self.v2).length
        return (side_1 * self.v1 + side_2 * self.v2 + side_3 * self.v3) / self.perimeter()

    def inscribed_circle(self):
        """
        Inscribed circle.
        Returns: an instance of CircleApproximationData.
        """
        circle = CircleApproximationData()
        side_1 = (self.v2 - self.v3).length
        side_2 = (self.v1 - self.v3).length
        side_3 = (self.v1 - self.v2).length
        perimeter = side_1 + side_2 + side_3
        center = (side_1 * self.v1 + side_2 * self.v2 + side_3 * self.v3) / perimeter
        circle.radius = 2 * self.area() / perimeter
        circle.center = np.array(center)
        circle.normal = np.array(self.normal())
        return circle
    
    def steiner_circumellipse(self):
        """
        Steiner ellipse (circumellipse) of the triangle,
        i.e. an ellipse that touches the triangle at it's vertices
        and whose center is the triangle's centroid.
        returns: an instance of Ellipse3D.
        """
        s = self.centroid()
        a,b,c = self.vertices
        sc = c - s
        ab = b - a
        f1 = sc
        f2 = ab / sqrt(3.0)
        f1sq = f1.length_squared
        f2sq = f2.length_squared
        #if f1sq < f2sq:
        #    f1, f2 = f2, f1
        #    f1sq, f2sq = f2sq, f1sq
        f1f2 = f1.dot(f2)
        if abs(f1f2) < 1e-6:
            t0 = 0.0
            p1 = f1
            p2 = f2
        else:
            A = 2 * f1f2
            B = f1sq - f2sq
            tan_2t0 = A / B
            t0 = atan(tan_2t0)/2.0
            cos_t0 = cos(t0)
            sin_t0 = sin(t0)
            #C = sqrt(A*A + B*B)
            #cos_2t0 = B / C
            #cos_t0 = sqrt((1 + cos_2t0)/2.0)
            #sin_t0 = sqrt((1 - cos_2t0)/2.0)
            p1 = f1 * cos_t0 + f2 * sin_t0
            p2 = - f1 * sin_t0 + f2 * cos_t0
        if p1.length < p2.length:
            p1, p2 = -p2, p1
        return Ellipse3D(s, p1, p2)

    def steiner_inellipse(self):
        """
        Steiner inellipse of the triangle,
        i.e. an ellipse inscribed in the triangle and tangent
        to the triangle's sides at their midpoints.
        returns: an instance of Ellipse3D.
        """
        ellipse = self.steiner_circumellipse()
        return Ellipse3D(ellipse.center, ellipse.semi_major_axis / 2.0, ellipse.semi_minor_axis / 2.0)

class LinearApproximationData(object):
    """
    This class contains results of linear approximation calculation.
    It's instance is returned by linear_approximation() method.
    """
    def __init__(self):
        self.center = None
        self.eigenvalues = None
        self.eigenvectors = None

    def most_similar_plane(self):
        """
        Return coefficients of an equation of a plane, which
        is the best linear approximation for input vertices.

        output: an instance of PlaneEquation class.
        """

        idx = np.argmin(self.eigenvalues)
        normal = self.eigenvectors[:, idx]
        return PlaneEquation.from_normal_and_point(normal, self.center)

    def most_similar_line(self):
        """
        Return coefficients of an equation of a plane, which
        is the best linear approximation for input vertices.

        output: an instance of LineEquation class.
        """

        idx = np.argmax(self.eigenvalues)
        eigenvector = self.eigenvectors[:, idx]
        a, b, c = tuple(eigenvector)

        return LineEquation(a, b, c, self.center)

def linear_approximation(data):
    """
    Calculate best linear approximation for a list of vertices.
    Input vertices can be approximated by a plane or by a line,
    or both.

    input: list of 3-tuples.
    output: an instance of LinearApproximationData class.
    """
    result = LinearApproximationData()

    result.center = cx,cy,cz = center(data)
    
    xs = [x[0]-cx for x in data]
    ys = [x[1]-cy for x in data]
    zs = [x[2]-cz for x in data]
    
    sx2 = sum(x**2 for x in xs)
    sy2 = sum(y**2 for y in ys)
    sz2 = sum(z**2 for z in zs)
    
    sxy = sum(x*y for (x,y) in zip(xs,ys))
    sxz = sum(x*z for (x,z) in zip(xs,zs))
    syz = sum(y*z for (y,z) in zip(ys,zs))
    
    n = len(data)

    # This is not that trivial, one can show that
    # eigenvalues and eigenvectors of a matrix composed
    # this way will provide exactly the solutions of
    # least squares problem for input vertices.
    # The nice part is that by calculating these values
    # we obtain both approximations - by line and by plane -
    # at the same time. The eigenvector which corresponds to
    # the minimal of eigenvalues will provide a normal for
    # the approximating plane. The eigenvector which corresponds
    # to the maximal of eigenvalues will provide a direction
    # for the approximating line.
    
    matrix = np.array([
        [sx2, sxy, sxz],
        [sxy, sy2, syz],
        [sxz, syz, sz2]
        ])
    
    result.eigenvalues, result.eigenvectors = linalg.eig(matrix)
    return result

class SphericalApproximationData(object):
    """
    This class contains results of approximation of
    vertices by a sphere.
    It's instance is returned by spherical_approximation() method.
    """
    def __init__(self):
        self.radius = 0
        self.center = None
        self.residues = None

    def get_projections(self, vertices):
        """
        Calculate projections of vertices to the sphere.
        """
        vertices = np.array(vertices) - self.center
        norms = np.linalg.norm(vertices, axis=1)[np.newaxis].T
        normalized = vertices / norms
        return self.radius * normalized + self.center

def spherical_approximation(data):
    """
    Calculate best approximation of the list of vertices
    by a sphere.

    input: list of 3-tuples.
    output. an instance of SphericalApproximationData class.
    """

    data = np.array(data)
    data_x = data[:,0]
    data_y = data[:,1]
    data_z = data[:,2]
    n = len(data)

    # Compose an overdetermined system of linear equations
    # from
    # (xi-x0)^2 + (yi-y0)^2 + (zi-z0)^2 = R^2
    #   ||
    #   V
    # xi^2 + yi^2 + zi^2 = 2xi*x0 + 2yi*y0 + 2zi*z0 + R^2 - x0^2 - y0^2 - z0^2
    #
    # In this system, we know all xi, yi, zi, and want to find x0, y0, z0 and R^2.

    A = np.zeros((n, 4))
    A[:,0] = data_x * 2
    A[:,1] = data_y * 2
    A[:,2] = data_z * 2
    A[:,3] = 1

    f = np.zeros((n, 1))
    f[:,0] = (data_x * data_x) + (data_y * data_y) + (data_z * data_z)

    C, residues, rank, singval = np.linalg.lstsq(A, f)
    r2 = (C[0]*C[0]) + (C[1]*C[1]) + (C[2]*C[2]) + C[3]

    result = SphericalApproximationData()
    result.radius = sqrt(r2)
    result.center = C[:3].T[0]
    result.residues = residues
    return result

class CircleApproximationData(object):
    """
    This class contains results of approximation of set of vertices
    by a circle (lying in 2D or 3D).
    It's instances are returned form circle_approximation_2d() and
    circle_approximation() methods.
    The `normal` member is None for 2D approximation.
    """
    def __init__(self):
        self.radius = 0
        self.center = None
        self.normal = None

    def get_matrix(self):
        """
        Calculate the matrix, Z axis of which is
        parallel to the plane's normal.
        """
        normal = Vector(self.normal)
        e1 = normal.orthogonal()
        e2 = normal.cross(e1)
        e1, e2 = e1.normalized(), e2.normalized()
        m = Matrix([e1, e2, normal]).inverted().to_4x4()
        m.translation = Vector(self.center)
        return m

    def get_projections(self, vertices):
        """
        Calculate projections of vertices to the
        circle. This method works with 3D circles only
        (i.e., requires `normal` to be specified).
        """
        vertices = np.array(vertices)
        plane = PlaneEquation.from_normal_and_point(self.normal, self.center)
        projected = plane.projection_of_points(vertices)
        centered = projected - self.center
        norms = np.linalg.norm(centered, axis=1)[np.newaxis].T
        normalized = centered / norms
        return self.radius * normalized + self.center

def circle_approximation_2d(data, mean_is_zero=False):
    """
    Calculate best approximation of set of 2D vertices
    by a 2D circle.

    input: list of 2-tuples or np.array of shape (n, 2). 
    output: an instance of CircleApproximationData class.
    """
    data = np.array(data)
    data_x = data[:,0]
    data_y = data[:,1]
    n = len(data)
    if mean_is_zero:
        mean_x = 0
        mean_y = 0
    else:
        mean_x = data_x.mean()
        mean_y = data_y.mean()
        data_x = data_x - mean_x
        data_y = data_y - mean_y

    # One can show that the solution of linear system below
    # gives the solution to least squares problem
    #
    # (xi - x0)^2 + (yi - y0)2 - R^2 --> min
    #
    # knowing that mean(xi) == mean(yi) == 0.

    su2 = (data_x*data_x).sum()
    sv2 = (data_y*data_y).sum()
    su3 = (data_x*data_x*data_x).sum()
    sv3 = (data_y*data_y*data_y).sum()
    suv = (data_x*data_y).sum()
    suvv = (data_x*data_y*data_y).sum()
    svuu = (data_y*data_x*data_x).sum()

    A = np.array([
            [su2, suv],
            [suv, sv2]
        ])

    B = np.array([[(su3 + suvv)/2.0], [(sv3 + svuu)/2.0]])

    C = np.linalg.solve(A, B)
    r2 = (C[0]*C[0]) + (C[1]*C[1]) + (su2 + sv2)/n

    result = CircleApproximationData()
    result.radius = sqrt(r2)
    result.center = C[:2].T[0] + np.array([mean_x, mean_y])
    return result

def circle_approximation(data):
    """
    Calculate best approximation of set of 3D vertices
    by a circle lying in 3D space.

    input: list of 3-tuples
    output: an instance of CircleApproximationData class.
    """
    # Approximate vertices with a plane
    linear = linear_approximation(data)
    plane = linear.most_similar_plane()
    data = np.array(data)
    # Project all vertices to the plane and shift everything to origin
    projected = plane.projection_of_points(data)
    linear_center = np.array(linear.center)
    centered = projected - linear_center
    # Map all vertices onto plane Z == 0
    e1, e2 = plane.two_vectors()
    e1, e2 = e1.normalized(), e2.normalized()
    matrix = np.array([e1, e2, plane.normal])
    on_plane = np.apply_along_axis(lambda v: matrix @ v, 1, centered)# All vectors here have Z == 0
    # Calculate circluar approximation in 2D
    circle_2d = circle_approximation_2d(on_plane[:,0:2], mean_is_zero=True)
    # Map the center back into 3D space
    matrix_inv = np.linalg.inv(matrix)

    result = CircleApproximationData()
    result.radius = circle_2d.radius
    center = np.array((circle_2d.center[0], circle_2d.center[1], 0))
    result.center = np.matmul(matrix_inv, center) + linear_center
    result.normal = plane.normal
    return result

def multiply_vectors(M, vlist):
    # (4*4 matrix)  X   (3*1 vector)

    for i, v in enumerate(vlist):
        # write _in place_
        vlist[i] = (
            M[0][0]*v[0] + M[0][1]*v[1] + M[0][2]*v[2] + M[0][3]* 1.0,
            M[1][0]*v[0] + M[1][1]*v[1] + M[1][2]*v[2] + M[1][3]* 1.0, 
            M[2][0]*v[0] + M[2][1]*v[1] + M[2][2]*v[2] + M[2][3]* 1.0
        )

    return vlist

def multiply_vectors_deep(M, vlist):
    """ returns a new list of vectors as tuples, transformed by matrix M (= Matrix() or 4*4 list) """
    # (4*4 matrix)  X   (3*1 vector)
    nlist = []
    concat = nlist.append
    for i, v in enumerate(vlist):
        concat((
            M[0][0]*v[0] + M[0][1]*v[1] + M[0][2]*v[2] + M[0][3]* 1.0,
            M[1][0]*v[0] + M[1][1]*v[1] + M[1][2]*v[2] + M[1][3]* 1.0, 
            M[2][0]*v[0] + M[2][1]*v[1] + M[2][2]*v[2] + M[2][3]* 1.0
        ))

    return nlist

def point_in_segment(point, origin, end, tolerance):
    '''Checks if the sum of lengths is greater than the length of the segment'''
    dist_p_in_segment = (point - origin).length + (point - end).length - (origin - end).length
    is_p_in_segment = abs(dist_p_in_segment) < tolerance
    return is_p_in_segment

def distance_line_line(line_a, line_b, result, gates, tolerance):
    '''
    Pass the data to the mathutils function
    Deals with lines as endless objects defined by a AB segment
    A and B will be the first and last vertices of the input list
    In case of parallel lines it will return the origin of the first line as the closest point
    '''
    line_origin_a = Vector(line_a[0])
    line_end_a = Vector(line_a[-1])
    line_origin_b = Vector(line_b[0])
    line_end_b = Vector(line_b[-1])

    inter_p = intersect_line_line(line_origin_a, line_end_a, line_origin_b, line_end_b)
    if inter_p:
        dist = (inter_p[0] - inter_p[1]).length
        intersect = dist < tolerance
        is_a_in_segment = point_in_segment(inter_p[0], line_origin_a, line_end_a, tolerance)
        is_b_in_segment = point_in_segment(inter_p[1], line_origin_b, line_end_b, tolerance)

        local_result = [dist, intersect, list(inter_p[1]), list(inter_p[0]), is_a_in_segment, is_b_in_segment]
    else:
        inter_p = intersect_point_line(line_origin_a, line_origin_b, line_end_b)
        dist = (inter_p[0] - line_origin_b).length
        intersect = dist < tolerance
        closest_in_segment = 0 <= inter_p[1] <= 1
        local_result = [dist, intersect, line_a[0], list(inter_p[0]), True, closest_in_segment]


    for i, res in enumerate(result):
        if gates[i]:
            res.append([local_result[i]])

def rotate_vector_around_vector(v, k, theta):
    """
    Rotate vector v around vector k by theta angle.
    input: v, k - 3-tuples or Vectors; theta - float, in radians.
    output: Vector.

    This implements Rodrigues' formula: https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
    """
    if not isinstance(v, Vector):
        v = Vector(v)
    if not isinstance(k, Vector):
        k = Vector(k)
    k = k.normalized()

    ct, st = cos(theta), sin(theta)

    return ct * v + st * (k.cross(v)) + (1 - ct) * (k.dot(v)) * k

