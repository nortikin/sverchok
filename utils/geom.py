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

Eventual purpose of this file is to store the convenience functions which
can be used for regular nodes or as part of recipes for script nodes. These
functions will initially be sub optimal quick implementations, 
then optimized only for speed, never for aesthetics or line count or cleverness.

'''

import math
from math import sin, cos, sqrt, acos, pi, atan
import numpy as np
from numpy import linalg
from functools import wraps
import mathutils
from mathutils import Matrix, Vector
from mathutils.geometry import interpolate_bezier, intersect_line_line, intersect_point_line

from sverchok.utils.modules.geom_primitives import (
    circle, arc, quad, arc_slice, rect, grid, line)

from sverchok.data_structure import match_long_repeat
from sverchok.utils.math import np_mixed_product
from sverchok.utils.sv_logging import sv_logger

# njit is a light-wrapper around numba.njit, if found
from sverchok.dependencies import numba  # not strictly needed i think...
from sverchok.utils.decorators_compilation import njit

def bounding_box_aligned(verts, evec_external=None, factor=1.0):
    ''' Build bounding box around vectors. If evec_external is not none then it can be used with factor.
    if evec_external is none then factor is not using.
    Function calc bounding box around vertexes. If evec_external is not none then function calc
    bounding box aligned with evec_external. If factor==0 then used exec. If factor==1 then used
    evec_external. Else used factor as interpolation beetwing evec and evec_external.
    res=[[0,0,0], [0,1,0], [1,1,0], [1,0,0], [0,0,1], [0,1,1], [1,1,1], [1,0,1],]; 1-used axis
    rrc - vertices of aligned bounding box
    max - matrix of transformation of box with size 1,1,1 to evec_target
    abbox_size - is a vector of sizes by axis (an order of XYZ can be differ of source verts)
    '''

    def realign_evec(evec):
        # make evecs orthogonals each other:
        vecs = [[0,1,2], [1,2,0], [2,0,1]]
        evec_dots = np.array( [abs(np.dot( evec.T[ivect[0]], evec.T[ivect[1]] )) for ivect in vecs] )  # get dots product vectors each other
        if np.all(evec_dots<1e-8):  # if all vectors are very close to orthonormals each other. May be replased by a future algorithm
            evec_dots_sort = [0]
        else:
            evec_dots_sort = np.argsort(evec_dots)
        #print(f'sort: {vecs[evec_dots_sort[0]]}')
        v0 = evec.T[ vecs[evec_dots_sort[0]][0] ]  # main vector
        v1 = evec.T[ vecs[evec_dots_sort[0]][1] ]  # closest by dot product
        v2 = evec.T[ vecs[evec_dots_sort[0]][2] ]  # get last vector
        v0_v1_cross = np.cross( v0, v1 )
        v1 = np.cross( v0, v0_v1_cross ) # orthogonal v1 to v0 from v1 source position
        if np.dot(v0_v1_cross, v2)<0:  # build last vector as orthogonal to v0 and v1
            v2 = - v0_v1_cross
        else:
            v2 =   v0_v1_cross
        res = np.dstack( (v0, v1, v2) )[0]
        return res

    # based on "3D Oriented bounding boxes": https://logicatcore.github.io/scratchpad/lidar/sensor-fusion/jupyter/2021/04/20/3D-Oriented-Bounding-Box.html
    data = np.vstack(np.array(verts, dtype=np.float64).transpose())
    means = np.mean(data, axis=1)

    if evec_external is not None:
        T, R, S = evec_external.decompose()
        if factor==1.0:
            evec_target = np.array(R.to_matrix())
            pass
        else:
            cov = np.cov(data)
            evalue, evec = np.linalg.eig(cov) # some times evec vectors are not perpendicular each other. What to do for this?
            evec = realign_evec(evec)
            evec = Matrix(evec).lerp( R.to_matrix(), factor)
            evec_target = np.array(evec)
    else:
        cov = np.cov(data)
        evalue, evec = np.linalg.eig(cov) # some times evec vectors are not perpendicular each other. What to do for this?
        evec_target = realign_evec(evec)

    centered_data = data - means[:,np.newaxis]
    aligned_coords = np.matmul(evec_target.T, centered_data)
    xmin, xmax, ymin, ymax, zmin, zmax = np.min(aligned_coords[0, :]), np.max(aligned_coords[0, :]), np.min(aligned_coords[1, :]), np.max(aligned_coords[1, :]), np.min(aligned_coords[2, :]), np.max(aligned_coords[2, :])
    abbox_size = [ xmax-xmin, ymax-ymin, zmax-zmin]
    abbox_center = [ (xmax+xmin)/2, (ymax+ymin)/2, (zmax+zmin)/2 ]

    rectCoords = lambda x1, y1, z1, x2, y2, z2: np.array([[x1, x1, x2, x2, x1, x1, x2, x2],
                                                          [y1, y2, y2, y1, y1, y2, y2, y1],
                                                          [z1, z1, z1, z1, z2, z2, z2, z2]])

    rrc = np.matmul(evec_target, rectCoords(xmin, ymin, zmin, xmax, ymax, zmax))
    rrc += means[:, np.newaxis]
    rrc = rrc.transpose()
    abbox_center = np.mean( rrc, axis=0 )
    mat_scale = Matrix()
    mat_scale[0][0], mat_scale[1][1], mat_scale[2][2] = abbox_size
    mat = mathutils.Matrix.Translation(abbox_center) @ Matrix(evec_target).to_euler().to_matrix().to_4x4() @ mat_scale
    return rrc, mat, abbox_size  # verts, matrix (not use for a while)

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
    Will create a yielding vectorized generator of the
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
        #if not isinstance(pts, np.ndarray):
        #    raise TypeError(f"Unexpected data: {pts}")
        if metric == "DISTANCE":
            tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
            tknots = np.insert(tmp, 0, 0).cumsum()
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        elif metric == "MANHATTAN":
            tmp = np.sum(np.absolute(pts[:-1] - pts[1:]), 1)
            tknots = np.insert(tmp, 0, 0).cumsum()
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        elif metric == "POINTS":
            tknots = np.linspace(0, 1, len(pts))
        elif metric == "CHEBYSHEV":
            tknots = np.max(np.absolute(pts[1:] - pts[:-1]), 1)
            tknots = np.insert(tknots, 0, 0).cumsum()
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        elif metric == 'CENTRIPETAL':
            tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
            tmp = np.sqrt(tmp)
            tknots = np.insert(tmp, 0, 0).cumsum()
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        elif metric == "X":
            tknots = pts[:,0]
            tknots = tknots - tknots[0]
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        elif metric == "Y":
            tknots = pts[:,1]
            tknots = tknots - tknots[0]
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        elif metric == "Z":
            tknots = pts[:,2]
            tknots = tknots - tknots[0]
            if tknots[-1] != 0:
                tknots = tknots / tknots[-1]
        else:
            raise Exception(f"Unsupported metric: {metric}")

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

    @classmethod
    def create(cls, vertices, tknots = None, metric = None, is_cyclic = False):
        raise Exception("Unsupported spline type")

    @classmethod
    def resample(cls, old_ts, old_values, new_ts):
        verts = np.array([[t,y,0.0] for t,y in zip(old_ts, old_values)])
        spline = cls.create(verts, tknots=old_ts)
        new_verts = spline.eval(new_ts)
        return new_verts[:,1]

class CubicSpline(Spline):
    def __init__(self, vertices, tknots = None, metric = None, is_cyclic = False):
        """
        vertices: vertices in Sverchok's format (list of tuples)
        tknots: np.array of shape (n-1,). If not provided - calculated automatically based on metric
        metric: string, one of "DISTANCE", "MANHATTAN", "POINTS", "CHEBYSHEV". Mandatory if tknots
                is not provided
        is_cyclic: whether the spline is cyclic

        creates a cubic spline through the locations given in vertices
        """

        super().__init__()


        if is_cyclic:

            #print(describe_data_shape(vertices))
            if len(vertices) == 3:
                va, vb, vc = vertices[0], vertices[1], vertices[2]
                locs = np.array([vc, va, vb, vc, va, vb, vc, va, vb, vc, va])
            else:
                locs = np.concatenate((vertices[-4:], vertices, vertices[:4]), axis=0)

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
        self.pts = np.array(vertices)

        n = len(locs)
        if n < 2:
            raise Exception("Cubic spline can't be built from less than 3 vertices")

        @njit(cache=True)
        def calc_cubic_splines(tknots, n, locs):
            """
            returns splines
            """
            h = tknots[1:] - tknots[:-1]
            h[h == 0] = 1e-8

            delta_i = (locs[2:] - locs[1:-1])
            delta_j = (locs[1:-1] - locs[:-2])
            nn = (3 / h[1:].reshape((-1, 1)) * delta_i) - (3 / h[:-1].reshape((-1, 1)) * delta_j)
            q = np.vstack((np.array([[0.0, 0.0, 0.0]]), nn))
            l = np.zeros((n, 3))
            l[0, :] = 1.0
            u = np.zeros((n - 1, 3))
            z = np.zeros((n, 3))

            for i in range(1, n - 1):
                l[i] = 2 * (tknots[i + 1] - tknots[i - 1]) - h[i - 1] * u[i - 1]
                for idx in range(len(l[i])):  # range(l[i].shape[0]):
                    if l[i][idx] == 0:
                        l[i][idx] = 1e-8
                u[i] = h[i] / l[i]
                z[i] = (q[i] - h[i - 1] * z[i - 1]) / l[i]

            l[-1, :] = 1.0
            z[-1] = 0.0

            b = np.zeros((n - 1, 3))
            c = np.zeros((n, 3))
            for i in range(n - 2, -1, -1):
                c[i] = z[i] - u[i] * c[i + 1]

            h_flat = h.reshape((-1, 1))
            b = (locs[1:] - locs[:-1]) / h_flat - h_flat * (c[1:] + 2 * c[:-1]) / 3
            d = (c[1:] - c[:-1]) / (3 * h_flat)

            splines = np.zeros((n - 1, 5, 3))
            splines[:, 0] = locs[:-1]
            splines[:, 1] = b
            splines[:, 2] = c[:-1]
            splines[:, 3] = d
            splines[:, 4] = tknots[:-1].reshape((-1, 1))
            return splines
        
        self.splines = calc_cubic_splines(tknots, n, locs)

    @classmethod
    def create(cls, vertices, tknots = None, metric = None, is_cyclic = False):
        return CubicSpline(vertices, tknots=tknots, metric=metric, is_cyclic=is_cyclic)

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

    def get_degree(self):
        return 3

    def get_t_segments(self):
        N = len(self.pts)
        if self.is_cyclic:
            index = np.array(range(4, 4+N+1))
        else:
            index = np.array(range(N-1))
        return list(zip(self.tknots[index], self.tknots[index+1]))

    def get_control_points(self, index=None):
        """
        Returns: np.array of shape (M, 4, 3),
                 where M is the number of Bezier segments, i.e.
                 M = N - 1, where N is the number of points being interpolated.
        """
        if index is None:
            N = len(self.pts)
            if self.is_cyclic:
                index = np.array(range(4, 4+N))
            else:
                index = np.array(range(N-1))
        #n = len(index)
        to_calc = self.splines[index]
        a, b, c, d, tx = np.swapaxes(to_calc, 0, 1)
        tknots = np.append(self.tknots, 1.0)
        T = (tknots[index+1] - tknots[index])[np.newaxis].T

        p0 = a
        p1 = (T*b+3*a)/3.0
        p2 = (T**2*c+2*T*b+3*a)/3.0
        p3 = T**3*d+T**2*c+T*b+a

        return np.transpose(np.array([p0, p1, p2, p3]), axes=(1,0,2))

#     def integrate(self, t_in, tknots=None):
#         if tknots is None:
#             tknots = self.tknots
# 
#         index = tknots.searchsorted(t_in, side='left') - 1
#         index = index.clip(0, len(self.splines) - 1)
#         to_calc = self.splines[index]
#         ax, bx, cx, dx, tx = np.swapaxes(to_calc, 0, 1)
#         bx /= 2.0
#         cx /= 3.0
#         dx /= 4.0
#         t_r = t_in[:, np.newaxis] - tx
#         out = ax + t_r * (bx + t_r * (cx + t_r * dx))
#         out = t_r * out
#         return out

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
        return tanget / h

class LinearSpline(Spline):
    def __init__(self, vertices, tknots = None, metric = None, is_cyclic = False):
        """
        vertices: vertices in Sverchok's format (list of tuples)
        tknots: np.array of shape (n-1,). If not provided - calculated automatically based on metric
        metric: string, one of "DISTANCE", "MANHATTAN", "POINTS", "CHEBYSHEV". Mandatory if tknots
                is not provided
        is_cyclic: whether the spline is cyclic

        creates a cubic spline through the locations given in vertices
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

    @classmethod
    def create(cls, vertices, tknots = None, metric = None, is_cyclic = False):
        return LinearSpline(vertices, tknots=tknots, metric=metric, is_cyclic=is_cyclic)

    def get_t_segments(self):
        return list(zip(self.tknots, self.tknots[1:]))

    def get_degree(self):
        return 1

    def get_control_points(self):
        starts = self.pts[:-1]
        ends = self.pts[1:]
        return np.transpose(np.stack((starts, ends)), axes=(1,0,2))

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
    (so it can form a cylindrical or toroidal surface).
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
            # sv_logger.debug("DU: {}, DV: {}, N: {}".format(du, dv, n))
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
        #     sv_logger.debug(k, v)

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
    elif isinstance(axis, tuple) or isinstance(axis, Vector) or isinstance(axis, list):
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
    Args:
        data: a list of 3-tuples or numpy array of same shape

    Returns:
        3-tuple - arithmetical average of input vertices (barycenter)
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

    Args:
        vertices: list of 3-tuples or list of mathutils.Vector.

    Returns:
        mathutils.Vector.
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
        if (a*a + b*b + c*c) < 1e-8:
            raise Exception("Plane normal is (almost) zero!")
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

    @classmethod
    def from_coordinate_value(cls, axis, value):
        if axis in 'XYZ':
            axis = 'XYZ'.index(axis)
        elif axis not in {0, 1, 2}:
            raise Exception("Unknown coordinate axis")
        
        point = np.zeros((3,), dtype=np.float64)
        normal = np.zeros((3,), dtype=np.float64)

        point[axis] = value
        normal[axis] = 1.0

        return PlaneEquation.from_normal_and_point(normal, point)

    @classmethod
    def from_matrix(cls, matrix, normal_axis='Z'):
        if normal_axis == 'X':
            normal = Vector((1,0,0))
        elif normal_axis == 'Y':
            normal = Vector((0,1,0))
        elif normal_axis == 'Z':
            normal = Vector((0,0,1))
        else:
            raise Exception(f"Unsupported normal_axis = {normal_axis}; supported are: X,Y,Z")
        normal = (matrix @ normal) - matrix.translation
        point = matrix.translation
        return PlaneEquation.from_normal_and_point(normal, point)

    def normalized(self):
        """
        Return equation, which defines exactly the same plane, but with coefficients adjusted so that

            A^2 + B^2 + C^2 = 1

        holds.
        """
        normal = self.normal.length
        if abs(normal) < 1e-8:
            raise Exception("Normal of the plane is (nearly) zero: ({}, {}, {})".format(self.a, self.b, self.c))
        return PlaneEquation(self.a/normal, self.b/normal, self.c/normal, self.d/normal)
    
    def check(self, point, eps=1e-6):
        """
        Check if specified point belongs to the plane.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        x, y, z = point[0], point[1], point[2]
        value = a*x + b*y + c*z + d
        return abs(value) < eps

    def eval_point(self, point):
        a, b, c, d = self.a, self.b, self.c, self.d
        x, y, z = point[0], point[1], point[2]
        return a*x + b*y + c*z + d

    def second_vector(self):
        eps = 1e-6
        if abs(self.c) > eps:
            v = Vector((1, 0, -self.a/self.c))
        elif abs(self.a) > eps:
            v = Vector((-self.b/self.a, 1, 0))
        elif abs(self.b) > eps:
            v = Vector((1, -self.a/self.b, 0))
        else:
            raise Exception("plane normal is (almost) zero")
        return v

    def two_vectors(self, normalize=False):
        """
        Return two vectors that are parallel two this plane.
        Note: the two vectors returned are orthogonal.
        Lengths of the returned vector is arbitrary.

        output: (Vector, Vector)
        """
        v1 = self.second_vector()
        v2 = v1.cross(self.normal)
        if normalize:
            v1.normalize()
            v2.normalize()
        return v1, v2

    def get_matrix(self, invert_y=False):
        x = self.second_vector().normalized()
        z = self.normal.normalized()
        y = z.cross(x).normalized()
        if invert_y:
            y = - y
        return Matrix([x, y, z]).transposed()

    def point_uv_projection(self, point):
        point = Vector(point) - self.nearest_point_to_origin()
        matrix = self.get_matrix(invert_y=True).inverted()
        uvw = matrix @ point
        return uvw.xy

    def evaluate(self, u, v, normalize=False):
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
        v1, v2 = self.two_vectors(normalize)
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
        p = self.normalized()
        a, b, c, d = p.a, p.b, p.c, p.d
        x, y, z = point
        numerator = abs(a*x + b*y + c*z + d)
        #denominator = sqrt(a*a + b*b* + c*c)
        return numerator
        #point_on_plane = self.nearest_point_to_origin()
        #return mathutils.geometry.distance_point_to_plane(mathutils.Vector(point), point_on_plane, self.normal)

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
        points = np.asarray(points)
        a, b, c, d = self.a, self.b, self.c, self.d
        # (A x + B y + C z) is a scalar product of (x, y, z) and (A, B, C)
        numerators = abs(points.dot([a, b, c]) + d)
        denominator = math.sqrt(a*a + b*b + c*c)
        return numerators / denominator

    def intersect_with_line(self, line, min_det=1e-12):
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
                        [self.a, self.b, self.c]], dtype=np.float64)
            free = np.array([
                        b*x0 - a*y0,
                        c*x0 - a*z0,
                        -self.d], dtype=np.float64)
        elif abs(b) > epsilon:
            matrix = np.array([
                        [b, -a, 0],
                        [0, c, -b],
                        [self.a, self.b, self.c]], dtype=np.float64)

            free = np.array([
                        b*x0 - a*y0,
                        c*y0 - b*z0,
                        -self.d], dtype=np.float64)
        elif abs(c) > epsilon:
            matrix = np.array([
                        [c, 0, -a],
                        [0, c, -b],
                        [self.a, self.b, self.c]], dtype=np.float64)
            free = np.array([
                        c*x0 - a*z0,
                        c*y0 - b*z0,
                        -self.d], dtype=np.float64)
        else:
            raise Exception("Invalid plane: all coefficients are (nearly) zero: {}, {}, {}".format(a, b, c))

        det = linalg.det(matrix)
        if abs(det) < min_det:
            print(f"No intersection: det = {det}")
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
        result = np.asarray(point) - sign * distance * np.asarray(normal)
        #info("P(%s): %s - %s * [%s] * %s = %s", point, point, sign, distance, normal, result)
        return Vector(result)
    
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

    def projection_of_matrix(self, matrix, direction_axis='Z', track_axis='X'):
        if direction_axis == track_axis:
            raise Exception("Direction axis must differ from tracked axis")

        direction_axis_idx = 'XYZ'.index(direction_axis)
        track_axis_idx = 'XYZ'.index(track_axis)
        #third_axis_idx = list(set([0,1,2]).difference([direction_axis_idx, track_axis_idx]))[0]

        xx = Vector((1, 0, 0))
        yy = Vector((0, 1, 0))
        zz = Vector((0, 0, 1))
        axes = [xx, yy, zz]

        z_axis_v = axes[direction_axis_idx]
        x_axis_v = axes[(direction_axis_idx+1)%3]
        y_axis_v = axes[(direction_axis_idx+2)%3]

        direction = matrix @ z_axis_v
        x_axis = matrix @ x_axis_v
        y_axis = matrix @ y_axis_v

        orig_point = matrix.translation
        line = LineEquation.from_direction_and_point(direction, orig_point)
        point = self.intersect_with_line(line)

        new_x_axis = self.projection_of_vector(orig_point, orig_point + x_axis).normalized()
        new_y_axis = self.projection_of_vector(orig_point, orig_point + y_axis).normalized()
        new_z_axis = new_x_axis.cross(new_y_axis).normalized()
        if (track_axis_idx + 1) % 3 == direction_axis_idx:
            new_y_axis = new_z_axis.cross(new_x_axis)
        else:
            new_x_axis = new_y_axis.cross(new_z_axis)
        
        new_matrix = Matrix([new_x_axis, new_y_axis, new_z_axis]).transposed().to_4x4()
        new_matrix.translation = point
        
        return new_matrix

    def intersect_with_plane(self, plane2):
        """
        Return an intersection of this plane with another one.
        
        input: PlaneEquation
        output: LineEquation or None, in case two planes are parallel.
        """
        if self.is_parallel(plane2):
            sv_logger.debug("{} is parallel to {}".format(self, plane2))
            return None

        direction = self.normal.cross(plane2.normal)

        A = np.array([[self.a, self.b, self.c], [plane2.a, plane2.b, plane2.c]])
        B = np.array([[-self.d], [-plane2.d]])

        A1 = np.linalg.pinv(A)
        p1 = (A1 @ B).T[0]

        return LineEquation.from_direction_and_point(direction, p1)

    def is_parallel(self, other, eps=1e-8):
        """
        Check if other object is parallel to this plane.
        input: PlaneEquation, LineEquation or Vector.
        output: boolean.
        """
        if isinstance(other, PlaneEquation):
            return abs(self.normal.angle(other.normal)) < eps
        elif isinstance(other, LineEquation):
            return abs(self.normal.dot(other.direction)) < eps
        elif isinstance(other, mathutils.Vector):
            return abs(self.normal.dot(other)) < eps
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

    def normalized(self):
        a1, b1, c1 = tuple(self.direction.normalized())
        eq = LineEquation(a1, b1, c1, self.point)
        return eq

    @classmethod
    def from_two_points(cls, p1, p2):
        if p1 is None or p2 is None:
            raise TypeError("None was passed instead of one of points")
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

    def eval_point(self, point):
        a, b, c = self.a, self.b, self.c
        x0, y0, z0 = self.x0, self.y0, self.z0
        x, y, z = point[0], point[1], point[2]

        value1 = b * (x - x0) - a * (y - y0)
        value2 = c * (y - y0) - b * (z - z0)
        return abs(value1) + abs(value2)

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

    def distance_to_points(self, points):
        """
        Return the distance between the specified points and this line.
        input: np.array of shape (n, 3)
        output: np.array of shape (n,)
        """
        direction = np.array(self.direction)
        point = np.array(self.point)
        dv1 = point - points
        dv1sq = (dv1 * dv1).sum(axis=1)
        numerator = (dv1 * direction).sum(axis=1)**2
        denominator = np.dot(direction, direction)
        result = np.sqrt(dv1sq - numerator / denominator)
        return result

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

    def projection_of_points(self, points):
        """
        Return the projections of the specified points on this line.
        input: np.array of shape (n, 3)
        output: np.array of shape (n, 3)
        """
        direction = np.array(self.direction)
        unit_direction = direction / np.linalg.norm(direction)
        unit_direction = unit_direction[np.newaxis]
        center = np.array(self.point)
        to_points = points - center
        projection_lengths = (to_points * unit_direction).sum(axis=1) # np.dot(to_points, unit_direction)
        projection_lengths = projection_lengths[np.newaxis].T
        projections = projection_lengths * unit_direction
        return center + projections
    
    def distance_to_line(self, line2, parallel_threshold=1e-6):
        r1 = self.point
        r2 = line2.point
        s1 = self.direction
        s2 = line2.direction
        num = np_mixed_product(r2-r1, s1, s2)
        denom = np.linalg.norm(np.cross(s1, s2))
        if denom < parallel_threshold:
            raise Exception("Lines are (almost) parallel")
        return abs(num) / denom

    def intersect_with_line_coplanar(self, line2):
        pt1 = self.point
        dir1 = self.direction
        dir2 = line2.direction
        pt11 = pt1 + dir1
        normal = dir1.cross(dir2)
        pt12 = pt1 + normal
        plane = PlaneEquation.from_three_points(pt1, pt11, pt12)
        return plane.intersect_with_line(line2)

def distance(v1, v2):
    v1 = np.asarray(v1)
    v2 = np.asarray(v2)
    return np.linalg.norm(v1 - v2)

def locate_linear(p1, p2, p):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    dxs = np.array([dx, dy, dz])

    i = np.argmax(abs(dxs))
    u = (p[i] - p1[i]) / dxs[i]
    #print(f"L: {p1} - {p2}: {p} => {u}")
    return u

def intersect_segment_segment(v1, v2, v3, v4, endpoint_tolerance=1e-3, tolerance=1e-3):
    x1,y1,z1 = v1
    x2,y2,z2 = v2
    x3,y3,z3 = v3
    x4,y4,z4 = v4

    #d1 = distance(v1, v2)
    #d2 = distance(v3, v4)
    #m = np.array([v2-v1, v3-v1, v4-v1])
    #det_m = np.linalg.det(m)
    #if abs(det_m) > 1e-6:
    #    print(f"Det_m: {det_m}")
    #    return None

    line1 = LineEquation.from_two_points(v1, v2)
    line2 = LineEquation.from_two_points(v3, v4)
    dist = line1.distance_to_line(line2)
    if dist > tolerance:
        #print(f"Distance: {dist}")
        return None

    ds = line1.distance_to_points([v3, v4])
    if ds[0] < tolerance:
        u = locate_linear(v1, v2, v3)
        return u, 0.0, np.asarray(v3)
    if ds[1] < tolerance:
        u = locate_linear(v1, v2, v4)
        return u, 1.0, np.asarray(v4)

    ds = line2.distance_to_points([v1, v2])
    if ds[0] < tolerance:
        v = locate_linear(v3, v4, v1)
        return 0.0, v, np.asarray(v1)
    if ds[1] < tolerance:
        v = locate_linear(v3, v4, v2)
        return 1.0, v, np.asarray(v2)

    denom = np.linalg.det(np.array([
            [x1-x2, x4-x3],
            [y1-y2, y4-y3]
        ]))

    num1 = np.linalg.det(np.array([
            [x4-x2, x4-x3],
            [y4-y2, y4-y3]
        ]))
    num2 = np.linalg.det(np.array([
            [x1-x2, x4-x2],
            [y1-y2, y4-y2]
        ]))

    u = num1 / denom
    v = num2 / denom

    et = endpoint_tolerance
    if not ((0.0-et <= u <= 1.0+et) and (0.0-et <= v <= 1.0+et)):
        #print(f"U = {u}, V = {v}, Dist={dist}")
        return None
#     if u < 0.0:
#         u = 0.0
#     if u > 1.0:
#         u = 1.0
#     if v < 0.0:
#         v = 0.0
#     if v > 0.0:
#         v = 1.0

    x = u*(x1-x2) + x2
    y = u*(y1-y2) + y2
    z = u*(z1-z2) + z2
    pt = np.array([x,y,z])

    return u, v, pt

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
        if a < b:
            raise Exception("Major semi-axis of the ellipse can not be smaller than minor semi-axis")
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

    def circumscribed_circle_radius(self):
        a = (self.v2 - self.v1).length
        b = (self.v3 - self.v1).length
        c = (self.v3 - self.v2).length
        p = (a+b+c)/2.0
        return (a*b*c) / (4 * sqrt(p*(p-a)*(p-b)*(p-c)))

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
        Returns: an instance of CircleEquation3D.
        """
        circle = CircleEquation3D()
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

class BoundingBox(object):
    """
    Class representing bounding box, i.e. a box with all planes parallel to coordinate planes.
    """
    def __init__(self, min_x=0, max_x=0, min_y=0, max_y=0, min_z=0, max_z=0):
        self.min = np.array([min_x, min_y, min_z])
        self.max = np.array([max_x, max_y, max_z])
        self._mean = None
        self._radius = None

    def mean(self):
        if self._mean is None:
            self._mean = 0.5 * (self.min + self.max)
        return self._mean

    def radius(self):
        if self._radius is None:
            mean = self.mean()
            self._radius = np.linalg.norm(mean - self.min)
        return self._radius

    @property
    def min_x(self):
        return self.min[0]

    @property
    def min_y(self):
        return self.min[1]

    @property
    def min_z(self):
        return self.min[2]

    @min_x.setter
    def min_x(self, value):
        self.min[0] = value

    @min_y.setter
    def min_y(self, value):
        self.min[1] = value

    @min_z.setter
    def min_z(self, value):
        self.min[2] = value

    @property
    def max_x(self):
        return self.max[0]

    @property
    def max_y(self):
        return self.max[1]

    @property
    def max_z(self):
        return self.max[2]

    @max_x.setter
    def max_x(self, value):
        self.max[0] = value

    @max_y.setter
    def max_y(self, value):
        self.max[1] = value

    @max_z.setter
    def max_z(self, value):
        self.max[2] = value

    @property
    def size_x(self):
        return self.max[0] - self.min[0]

    @property
    def size_y(self):
        return self.max[1] - self.min[1]

    @property
    def size_z(self):
        return self.max[2] - self.min[2]

    def size(self):
        return (self.max - self.min).max()

    def increase(self, delta):
        mean = self.mean()
        d = 0.5*delta
        box = BoundingBox(self.min_x - d, self.max_x + d,
                self.min_y - d, self.max_y + d,
                self.min_z - d, self.max_z + d)
        return box

    def contains(self, point):
        return (point >= self.min).all() and (point <= self.max).all()

    def __contains__(self, point):
        return self.contains(point)

#     def is_empty(self):
#         return (self.min == self.max).all()

#     def intersect(self, box):
#         r = BoundingBox()
#         box.min = np.maximum(self.min, box.min)
#         box.max = np.minimum(self.max, box.max)
#         return r

    def intersects(self, box):
        x = (box.min_x > self.max_x) or (box.max_x < self.min_x)
        y = (box.min_y > self.max_y) or (box.max_y < self.min_y)
        z = (box.min_z > self.max_z) or (box.max_z < self.min_z)
        result = not (x or y or z)
        #print(f"{self} x {box} => {result}")
        return result

    def get_plane(self, axis, side):
        if axis in 'XYZ':
            axis = 'XYZ'.index(axis)
        elif axis not in {0, 1, 2}:
            raise Exception("Unknown coordinate axis")
        if side == 'MIN':
            value = self.min[axis]
        elif side == 'MAX':
            value = self.max[axis]
        else:
            raise Exception("Unknown bounding box side")
        return PlaneEquation.from_coordinate_value(axis, value)

    def __repr__(self):
        return f"<BBox: {self.min} .. {self.max}>"

def bounding_box(vectors):
    """
    Calculate bounding box for a set of points.

    Args:
        vectors: list of 3-tuples or np.ndarray of shape (n,3).

    Returns:
        an instance of BoundingBox.
    """
    vectors = np.asarray(vectors)
    r = BoundingBox()
    r.min = vectors.min(axis=0)
    r.max = vectors.max(axis=0)
    return r

def intersects_line_bbox(line, bbox):
    """
    Check if line intersects specified bounding box.

    Args:
        line: an instance of LineEquation
        bbox: an instance of BoundingBox

    Returns:
        boolean.
    """
    planes = [bbox.get_plane(axis, side) for axis in [0,1,2] for side in ['MIN', 'MAX']]
    intersections = [plane.intersect_with_line(line) is not None for plane in planes]
    good = [point for point in intersections if point in bbox]
    return len(good) > 0

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

        Returns: an instance of PlaneEquation class.
        """

        idx = np.argmin(self.eigenvalues)
        normal = self.eigenvectors[:, idx]
        return PlaneEquation.from_normal_and_point(normal, self.center)

    def most_similar_line(self):
        """
        Return coefficients of an equation of a plane, which
        is the best linear approximation for input vertices.

        Returns: an instance of LineEquation class.
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

    Args:
        data: list of 3-tuples.

    Returns:
        an instance of LinearApproximationData class.
    """

    data = np.asarray(data)
    n = data.shape[-2]
    center = data.sum(axis=0) / n
    data0 = data - center
    
    xs = data0[:,0]
    ys = data0[:,1]
    zs = data0[:,2]
    
    sx2 = (xs**2).sum(axis=0)
    sy2 = (ys**2).sum(axis=0)
    sz2 = (zs**2).sum(axis=0)

    sxy = (xs*ys).sum(axis=0)
    sxz = (xs*zs).sum(axis=0)
    syz = (ys*zs).sum(axis=0)

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
    
    result = LinearApproximationData()
    result.center = tuple(center)
    result.eigenvalues, result.eigenvectors = linalg.eig(matrix)
    return result

def are_points_coplanar(points, tolerance=1e-6):
    """
    Check if points lie in the same plane.

    Args:
        points: list of 3-tuples or np.array of shape (n,3)
        tolerance: maximum allowable distance from plane to the point

    Returns:
        True if all points lie in the same plane.
    """
    plane = linear_approximation(points).most_similar_plane()
    max_distance = abs(plane.distance_to_points(points)).max()
    return max_distance < tolerance

def get_common_plane(points, tolerance=1e-6):
    """
    Get a plane in which all points lie, or None.

    Args:
        points: list of 3-tuples or np.array of shape (n,3)
        tolerance: maximum allowable distance from plane to the point

    Returns:
        If all points line in the same plane, return that plane (an instance of
        PlaneEquation class).  Otherwise, return None.
    """
    plane = linear_approximation(points).most_similar_plane()
    max_distance = abs(plane.distance_to_points(points)).max()
    if max_distance < tolerance:
        return plane
    else:
        return None

def linear_approximation_array(data):
    data = np.asarray(data)
    n = data.shape[-2]
    center = data.mean(axis=1)
    data0 = data - np.transpose(center[np.newaxis], axes=(1,0,2))

    ndim = data.ndim
    xs = data0.take(indices=0, axis=ndim-1)
    ys = data0.take(indices=1, axis=ndim-1)
    zs = data0.take(indices=2, axis=ndim-1)
    
    sx2 = (xs**2).sum(axis=ndim-2)
    sy2 = (ys**2).sum(axis=ndim-2)
    sz2 = (zs**2).sum(axis=ndim-2)

    sxy = (xs*ys).sum(axis=ndim-2)
    sxz = (xs*zs).sum(axis=ndim-2)
    syz = (ys*zs).sum(axis=ndim-2)

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

    axes = (ndim-1,) + tuple(range(ndim-1))
    matrix = np.transpose(matrix, axes=axes)

    eigvals, eigvecs = linalg.eig(matrix)

    results = []
    for vals, vecs, ct in zip(eigvals, eigvecs, center):
        result = LinearApproximationData()
        result.center = tuple(ct)
        result.eigenvalues = vals
        result.eigenvectors = vecs
        results.append(result)
    return results

class SphericalApproximationData(object):
    """
    This class contains results of approximation of
    vertices by a sphere.

    It's instance is returned by spherical_approximation() method.
    """
    def __init__(self, center=None, radius=0.0):
        self.radius = radius
        self.center = center
        self.residues = None

    def get_projections(self, vertices):
        """
        Calculate projections of vertices to the sphere.
        """
        vertices = np.asarray(vertices) - self.center
        norms = np.linalg.norm(vertices, axis=1)[np.newaxis].T
        normalized = vertices / norms
        return self.radius * normalized + self.center

    def projection_of_points(self, points):
        return self.get_projections(points)

SphereEquation = SphericalApproximationData

def spherical_approximation(data):
    """
    Calculate best approximation of the list of vertices
    by a sphere.

    Args:
        data: list of 3-tuples.

    Returns:
        an instance of SphericalApproximationData class.
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

class CircleEquation3D(object):
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
        self.point1 = None
        self.arc_angle = None

    @classmethod
    def from_center_radius_normal(cls, center, radius, normal):
        circle = CircleEquation3D()
        circle.center = np.array(center)
        circle.radius = radius
        circle.normal = np.array(normal)
        return circle

    @classmethod
    def from_center_point_normal(cls, center, point, normal):
        center = Vector(center)
        point = Vector(point)
        normal = Vector(normal)

        radius = (point - center).length
        circle = CircleEquation3D.from_center_radius_normal(center, radius, normal)
        circle.point1 = np.array(point)
        return circle

    @classmethod
    def from_axis_point(cls, point_on_axis, direction, point):
        point_on_axis = Vector(point_on_axis)
        direction = Vector(direction)
        point = Vector(point)

        axis = LineEquation.from_direction_and_point(direction, point_on_axis)
        center = axis.projection_of_point(point)
        return CircleEquation3D.from_center_point_normal(center, point, direction)

    def get_matrix(self):
        """
        Calculate the matrix, Z axis of which is
        parallel to the plane's normal.
        """
        normal = Vector(self.normal)
        if self.point1 is None:
            e1 = normal.orthogonal()
        else:
            e1 = Vector(self.point1) - Vector(self.center)
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

        input: list of 3-tuples, or list of Vectors, or np.ndarray of shape (n,3).
        returns: np.ndarray of shape (n,3).
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

    Args:
        data: list of 2-tuples or np.array of shape (n, 2). 

    Returns:
        an instance of CircleEquation3D class.
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

    result = CircleEquation3D()
    result.radius = sqrt(r2)
    result.center = C[:2].T[0] + np.array([mean_x, mean_y])
    return result

CircleApproximationData = CircleEquation3D

def circle_approximation(data):
    """
    Calculate best approximation of set of 3D vertices
    by a circle lying in 3D space.

    Args:
        data: list of 3-tuples

    Returns:
        an instance of CircleEquation3D class.
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
    # Calculate circular approximation in 2D
    circle_2d = circle_approximation_2d(on_plane[:,0:2], mean_is_zero=True)
    # Map the center back into 3D space
    matrix_inv = np.linalg.inv(matrix)

    result = CircleEquation3D()
    result.radius = circle_2d.radius
    center = np.array((circle_2d.center[0], circle_2d.center[1], 0))
    result.center = np.matmul(matrix_inv, center) + linear_center
    result.normal = plane.normal
    return result

def circle_by_three_points(p1, p2, p3):
    """
    Calculate parameters of the circle (or circular arc)
    by three points on this circle.

    Args:
        p1, p2, p3: 3-tuples or mathutils.Vectors

    Returns:
        an CircleEquation3D instance.

    factored out from basic_3pt_arc.py.
    """
    v1, v2, v3 = Vector(p1), Vector(p2), Vector(p3)
    edge1 = v2 - v1
    edge2 = v3 - v2
    edge1_mid = v1.lerp(v2, 0.5)
    edge2_mid = v2.lerp(v3, 0.5)

    plane0 = PlaneEquation.from_three_points(v1, v2, v3)#.normalized()
    plane1 = PlaneEquation.from_normal_and_point(edge1, edge1_mid)#.normalized()
    plane2 = PlaneEquation.from_normal_and_point(edge2, edge2_mid)#.normalized()
    axis = plane1.intersect_with_plane(plane2)
    if not axis:
        return None
    center = plane0.intersect_with_line(axis)

    dv1 = np.array(v1 - center)
    dv3 = np.array(v3 - center)
    radius = np.linalg.norm(dv1)

    # find arc angle.
    e1 = np.array(v1 - v2)
    e2 = np.array(v3 - v2)
    cs = e1.dot(e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
    interior_angle = np.arccos(cs)
    beta = 2*math.pi - 2*interior_angle

    normal = - np.cross(e1,e2)

    circle = CircleEquation3D()
    circle.radius = radius
    circle.center = center
    circle.normal = Vector(normal).normalized() # axis.direction
    circle.point1 = np.array(v1)
    circle.arc_angle = beta
    return circle

def circle_by_start_end_tangent(start, end, tangent):
    """
    Build a circular arc from starting point, end point
    and the tangent vector at the start point.

    Args:
        start, end, tangent: mathutils.Vectors or 3-tuples or np.arrays of shape (3,).

    Returns:
        instance of CircleEquation3D.
    """
    start = Vector(start)
    end = Vector(end)
    tangent = Vector(tangent)
    middle = 0.5*(start + end)
    diff = end - start
    middle_plane = PlaneEquation.from_normal_and_point(diff, middle)
    tangent_plane = PlaneEquation.from_point_and_two_vectors(start, tangent, diff)
    start_plane = PlaneEquation.from_normal_and_point(tangent, start)
    normal_line = start_plane.intersect_with_plane(tangent_plane)
    circle = CircleEquation3D()
    center = middle_plane.intersect_with_line(normal_line)
    circle.center = np.array(center)
    circle.radius = (center - start).length
    circle.normal = np.array(tangent_plane.normal)
    circle.point1 = np.array(start)
    circle.arc_angle = (start - center).angle(end - center, 0)
    if tangent.dot(diff) < 0:
        circle.arc_angle = 2*pi - circle.arc_angle
    return circle

def circle_by_two_derivatives(start, tangent, second):
    start = Vector(start)
    tangent = Vector(tangent)
    second = Vector(second)

    radius = tangent.length
    deriv_diff = (second - second.project(tangent)).normalized()
    center = start + radius * deriv_diff
    normal = tangent.cross(deriv_diff).normalized()

    circle = CircleEquation3D()
    circle.center = np.array(center)
    circle.radius = radius
    circle.normal = np.array(normal)
    circle.point1 = np.array(start)
    return circle

class CylinderEquation(object):
    """
    A class representing (infinite) cylindrical surface.
    """
    def __init__(self, axis, radius):
        """
        Args:
            axis: an instance of LineEquation
            radius: float
        """
        self.axis = axis
        self.radius = radius

    @classmethod
    def from_point_direction_radius(cls, point, direction, radius):
        axis = LineEquation.from_direction_and_point(direction, point)
        return CylinderEquation(axis, radius)

    def projection_of_points(self, points):
        points = np.asarray(points)
        projection_to_line = self.axis.projection_of_points(points)
        radial = points - projection_to_line
        radius = self.radius * radial / np.linalg.norm(radial, axis=1, keepdims=True)
        projections = projection_to_line + radius
        return projections

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
        is_a_in_segment = point_in_segment(inter_p[1], line_origin_b, line_end_b, tolerance)
        is_b_in_segment = point_in_segment(inter_p[0], line_origin_a, line_end_a, tolerance)

        local_result = [dist, intersect, list(inter_p[1]), list(inter_p[0]), is_a_in_segment, is_b_in_segment]
    else:
        inter_p = intersect_point_line(line_origin_a, line_origin_b, line_end_b)
        dist = (inter_p[0] - line_origin_a).length
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

def rotate_vector_around_vector_np(v, k, theta):
    """
    Rotate vector v around vector k by theta angle.
    input: v, k - np.array of shape (3,); theta - float, in radians.
    output: np.array.

    This implements Rodrigues' formula: https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
    """
    if not isinstance(v, np.ndarray):
        v = np.array(v)
    if not isinstance(k, np.ndarray):
        k = np.array(k)
    if k.ndim == 1:
        k = k[np.newaxis]
    k = k / np.linalg.norm(k, axis=1)

    if isinstance(theta, np.ndarray):
        ct, st = np.cos(theta)[np.newaxis].T, np.sin(theta)[np.newaxis].T
    else:
        ct, st = cos(theta), sin(theta)

    s1 = ct * v
    s2 = st * np.cross(k, v)
    p1 = 1.0 - ct
    p2 = np.apply_along_axis(lambda vi : k.dot(vi), 1, v)
    s3 = p1 * p2 * k
    return s1 + s2 + s3

def calc_bounds(vertices, allowance=0):
    x_min = min(v[0] for v in vertices)
    y_min = min(v[1] for v in vertices)
    z_min = min(v[2] for v in vertices)
    x_max = max(v[0] for v in vertices)
    y_max = max(v[1] for v in vertices)
    z_max = max(v[2] for v in vertices)
    return (x_min - allowance, x_max + allowance,
            y_min - allowance, y_max + allowance,
            z_min - allowance, z_max + allowance)

TRIVIAL='TRIVIAL'
def bounding_sphere(vertices, algorithm=TRIVIAL):
    if algorithm != TRIVIAL:
        raise Exception("Unsupported algorithm")
    c = center(vertices)
    vertices = np.array(vertices) - np.array(c)
    norms = np.linalg.norm(vertices, axis=1)
    radius = norms.max()
    return c, radius

def scale_relative(points, center, scale):
    """
    Scale points with relation to specified center.

    Args:
        points: points to be scaled - np.array of shape (n,3)
        center: the center of scale - np.array of shape (3,)
        scale: scale coefficient

    Returns:
        np.array of shape (n,3)
    """
    points = np.asarray(points)
    center = np.asarray(center)
    points -= center

    points = points * scale

    return (points + center).tolist()

