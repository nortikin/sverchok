# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.geom import Spline, LineEquation, bounding_box, are_points_coplanar, get_common_plane
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.bezier import SvBezierCurve, SvCubicBezierCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves

bezierM = np.zeros((4,4))
bezierM[:,0] = 1.0
bezierM[3,:] = 1.0
bezierM[1,1] = 1.0/3.0
bezierM[2,1] = 2.0/3.0
bezierM[2,2] = 1.0/3.0

def prepare_data(tknots, points, cyclic=False):
    """
    Prepare tknots and points for use in Catmull-Rom spline:
    * For non-cyclic curve, add one point in the beginning, by mirroring
      the 2nd point around the first, and one point in the end, in a similar
      way. Similarly, mirror T knot values.
    * For a cyclic curve, add one point in the beginning, equal to the last
      of initial points; and add two points in the end, equal to the first
      and the second of initial points, to make a wrap.
    """
    if cyclic:
        points = np.concatenate(([points[-1]], points), axis=0)
        points = np.append(points, [points[1], points[2]], axis=0)

        if tknots is not None:
            dt0 = tknots[1] - tknots[0]
            dt1 = tknots[-1] - tknots[-2]
            dt = (dt0 + dt1) * 0.5
            tknots = np.concatenate(([tknots[0] - dt], tknots), axis=0)
            tknots = np.append(tknots, [tknots[-1] + dt, tknots[-1] + dt + dt0], axis=0)
    else:
        p0 = 2*points[0] - points[1]
        pn = 2*points[-1] - points[-2]
        points = np.insert(points, 0, p0, axis=0)
        points = np.append(points, [pn], axis=0)

        if tknots is not None:
            t0 = 2*tknots[0] - tknots[1]
            tn = 2*tknots[-1] - tknots[-2]
            tknots = np.insert(tknots, 0, t0, axis=0)
            tknots = np.append(tknots, [tn], axis=0)
    return tknots, points

class SvUniformCatmullRomCurve(SvCurve):
    """
    Uniform Catmull-Rom spline, allowing to specify
    tension value for each segment.
    """
    def __init__(self, points, tensions):
        self.points = np.asarray(points)
        self.tensions = np.asarray(tensions)
        self.__description__ = f"Uniform Catmull-Rom[{len(self.points)}]"

    @classmethod
    def build(cls, points, cyclic=False, tensions=None):
        points = np.asarray(points)
        if tensions is None:
            tensions = np.ones((len(points)-3,))
        _, points = prepare_data(None, points, cyclic=cyclic)
        if cyclic:
            t0 = tensions[0]
            tn = tensions[-1]
            ts = (t0 + tn)*0.5
            tensions = np.insert(tensions, 0, ts, axis=0)
            tensions = np.append(tensions, [ts], axis=0)
        else:
            tensions = np.insert(tensions, 0, 1.0, axis=0)
            tensions = np.append(tensions, [1.0], axis=0)

        return SvUniformCatmullRomCurve(points, tensions)

    def get_u_bounds(self):
        n = len(self.points)
        return (0.0, float(n)-3)

    def get_end_points(self):
        return self.points[1], self.points[-2]

    def get_degree(self):
        return 3

    def _make_uniform_tknots(self):
        n = len(self.points)
        return np.arange(-1.0, n-1)

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        # Calculate non-uniform Catmull-Rom spline
        # by Barry & Goldman formulas.
        n = len(self.points)
        tknots = self._make_uniform_tknots()
        i = tknots.searchsorted(ts, side='right')-1
        i = np.clip(i, 1, n-3)
        u = ts - tknots[i]
        n_points = len(ts)

        tau = self.tensions[i]

        M = np.zeros((n_points,4,4))
        M[:,0,1] = 2.0
        M[:,1,0] = -tau
        M[:,1,2] = tau
        M[:,2,0] = 2*tau
        M[:,2,1] = tau - 6
        M[:,2,2] = -2*(tau-3)
        M[:,2,3] = -tau
        M[:,3,0] = -tau
        M[:,3,1] = 4-tau
        M[:,3,2] = tau-4
        M[:,3,3] = tau
        M *= 0.5

        P = np.empty((n_points,4,3))
        P[:,0] = self.points[i-1]
        P[:,1] = self.points[i]
        P[:,2] = self.points[i+1]
        P[:,3] = self.points[i+2]

        U = np.ones((n_points,1,4))
        U[:,0,1] = u
        U[:,0,2] = u**2
        U[:,0,3] = u**3

        R = U @ M @ P

        return R[:,0,:]

    def to_bezier_segments(self):
        segments = []
        n = len(self.points)
        for i in range(n-3):
            spline_cpts = self.points[i:i+4]
            print(f"I {i} => tension {self.tensions[i+1]}")
            segment = uniform_catmull_rom_bezier_segment(spline_cpts, self.tensions[i+1])
            segments.append(segment)
        return segments

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        return concatenate_nurbs_curves(self.to_bezier_segments(), tolerance=None)

    def get_control_points(self):
        return self.to_nurbs().get_control_points()

    def is_line(self):
        pts = self.points
        begin, end = pts[0], pts[-1]
        # direction from first to last point of the curve
        direction = end - begin
        if np.linalg.norm(direction) < tolerance:
            return True
        line = LineEquation.from_direction_and_point(direction, begin)
        distances = line.distance_to_points(pts[1:-1])
        # Technically, this means that all control points lie
        # inside the cylinder, defined as "distance from line < tolerance";
        # As a consequence, the convex hull of control points lie in the
        # same cylinder; and the curve lies in that convex hull.
        return (distances < tolerance).all()

    def get_bounding_box(self):
        return bounding_box(self.points)

    def reverse(self):
        return SvUniformCatmullRomCurve(self.points[::-1])

    def reparametrize(self, new_t_min, new_t_max):
        tknots = self._make_uniform_tknots()
        t0 = tknots[0]
        tn = tknots[-1]
        tknots = (new_t_max - new_t_min) * (self.tknots - t0) / (tn - t0) + new_t_min
        return SvCatmullRomCurve(tknots, self.points)

    def is_rational(self):
        return False

    def is_planar(self, tolerance=1e-6):
        return are_points_coplanar(self.points, tolerance)

    def get_plane(self, tolerance=1e-6):
        return get_common_plane(self.points, tolerance)

    def concatenate(self, curve2, tolerance=None):
        curve2 = SvNurbsMaths.to_nurbs_curve(curve2)
        if curve2 is None:
            raise UnsupportedCurveTypeException("Second curve is not a NURBS")
        return self.to_nurbs().concatenate(curve2, tolerance=tolerance)

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)
    
    def extrude_along_vector(self, vector):
        return self.to_nurbs().extrude_along_vector(vector)

    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)

    def lerp_to(self, curve2, coefficient):
        return self.to_nurbs().lerp_to(curve2, coefficient)

    def split_at(self, t):
        return self.to_nurbs().reparametrize(*self.get_u_bounds()).split_at(t)
        
class SvCatmullRomCurve(SvUniformCatmullRomCurve):
    """
    Non-uniform Catmull-Rom cubic spline.
    See https://en.wikipedia.org/wiki/Centripetal_Catmull%E2%80%93Rom_spline
    """
    def __init__(self, tknots, points):
        self.points = np.asarray(points)
        self.tknots = np.asarray(tknots)
        self.__description__ = f"Catmull-Rom[{len(self.points)}]"

    @classmethod
    def build(cls, points, tknots=None, metric='DISTANCE', cyclic=False):
        points = np.asarray(points)
        if tknots is not None:
            tknots = np.asarray(tknots)
        else:
            tknots = Spline.create_knots(points, metric=metric)
        tknots, points = prepare_data(tknots, points, cyclic=cyclic)
        return SvCatmullRomCurve(tknots, points)

    def get_u_bounds(self):
        return self.tknots[1], self.tknots[-2]

    def evaluate_array(self, ts):
        i = self.tknots.searchsorted(ts, side='right')-1
        i = np.clip(i, 1, len(self.tknots)-3)
        tknots = self.tknots[np.newaxis].T
        t0 = tknots[i-1]
        t1 = tknots[i]
        t2 = tknots[i+1]
        t3 = tknots[i+2]

        p0 = self.points[i-1]
        p1 = self.points[i]
        p2 = self.points[i+1]
        p3 = self.points[i+2]

        t20 = t2 - t0
        t31 = t3 - t1
        t10 = t1 - t0
        t21 = t2 - t1
        t32 = t3 - t2

        ts = ts[np.newaxis].T
        t0s = t0 - ts
        t1s = t1 - ts
        t2s = t2 - ts
        t3s = t3 - ts

        a1 = (p0 * t1s - p1 * t0s) / t10
        a2 = (p1 * t2s - p2 * t1s) / t21
        a3 = (p2 * t3s - p3 * t2s) / t32

        b1 = (a1 * t2s - a2 * t0s) / t20
        b2 = (a2 * t3s - a3 * t1s) / t31

        c = (b1 * t2s - b2 * t1s) / t21
        return c

    def get_bezier_control_points(self):
        # The derivation of formulas used in this method is as follows.
        # 1. Take formulas for non-uniform Catmull-Rom splines.
        # 2. Write them in matrix form:
        #
        # C = [ 1, t, t^2, t^3] * M * column(P0, P1, P2, P3)
        #
        # (P0 - P3 are control points for Catmull-Rom spline).
        # Coefficients of the M (4x4) matrix will be some formulas in terms of
        # T knot values (t0 - t3).
        #
        # 3. Write similar equation for cubic Bezier spline:
        #
        # C = [1, t, t^2, t^3] * B * column(B0, B1, B2, B3)
        # (B0 - B3 are control points for Bezier spline).
        # Coefficients for B matrix are well known:
        # 
        #     / 1   0  0 0 \
        # B = | -3  3  0 0 |
        #     |  3 -6  3 0 |
        #     \ -1  3 -3 1 /
        #
        # 4. Equate right-hand sides of these two equations, and note
        # that the component with T is the same, then remaining must be
        # the same too:
        #
        # M * column(P0, P1, P2, P3) = B * column(B0, B1, B2, B3)
        #
        # 5. Then, obviously, we can write
        #
        # column(B0, B1, B2, B3) = B^{-1} * M * column(P0, P1, P2, P3)
        #
        # 6. Above is the formula for Bezier control points, which is valid when
        # T is in [t0 .. t3] segment. But usual formulation of Bezier curve
        # assumes that it's parameter goes from 0 to 1. So, let's introduce
        # a parameter U as
        #
        # u = (t - t0) / (t3 - t0)

        # which goes from 0 to 1 when T goes from t0 to t3. Now if we express
        # u^2 and u^3 in terms of T, we will have
        #
        # [1, u, u^2, u^3] = U * [1, t, t^2, t^3]
        #
        # where U is some 4x4 (lower-triangular) matrix, coefficients of which
        # are some polynomials in terms of t0 and t3.
        #
        # 7. Gathering all the above together, we will have that
        #
        # column(B0', B1', B2', B3') = B^{-1} * U * M * column(P0, P1, P2, P3)
        #
        n = len(self.tknots)
        tk = self.tknots
        t0 = tk[0:n-3]
        t1 = tk[1:n-2]
        t2 = tk[2:n-1]
        t3 = tk[3:n]
        dt10 = t1 - t0
        dt20 = t2 - t0
        dt30 = t3 - t0
        dt21 = t2 - t1
        dt31 = t3 - t1
        dt32 = t3 - t2
        
        t01 = t0*t1
        t02 = t0*t2
        t12 = t1*t2
        t13 = t1*t3
        t23 = t2*t3
        
        t012 = t0*t1*t2
        t013 = t0*t1*t3
        t023 = t0*t2*t3
        t123 = t1*t2*t3

        # Formulas for M matrix coefficients all have rational form:
        # numerator / denominator,
        # where numerator and denominator are some polynomial in terms of t0 - t3.
        # Nice thing is that all formulas in each column of M matrix have the
        # same denominator.
        
        denom = np.zeros((n-3,4,4))
        denom[:,0,0] = 1.0/(dt10*dt20*dt21)
        denom[:,1,1] = 1.0/(dt10*dt21**2*dt31)
        denom[:,2,2] = 1.0/(dt20*dt21**2*dt32)
        denom[:,3,3] = 1.0/(dt21*dt31*dt32)
        
        numer = np.zeros((n-3,4,4))
        numer[:,0,0] = t1*t2**2
        numer[:,0,1] = -t2*(t023 + t1**2*t3 - t013 - t012)
        numer[:,0,2] =  t1*(t123 + t023 - t013 - t0*t2**2)
        numer[:,0,3] = -t1**2*t2
        numer[:,1,0] = -t2*(t2 + 2*t1)
        numer[:,1,1] = t2**2*t3 + t123 + t023 + t1**2*t3 - t013 - t1*t2**2 + t1**2*t2 - 3*t012
        numer[:,1,2] = -(3*t123 + t023 - t013 - t1*t2**2 - t0*t2**2 + t1**2*t2 - t012 - t0*t1**2)
        numer[:,1,3] = t1*(2*t2 + t1)
        numer[:,2,0] = 2*t2 + t1
        numer[:,2,1] = -(2*t23 + t13 - t12 - t02 + t1**2 - 2*t01)
        numer[:,2,2] =   2*t23 + t13 - t2**2 + t12 - t02 - 2*t01
        numer[:,2,3] = -(t2 + 2*t1)
        numer[:,3,0] = -1.0
        numer[:,3,1] = dt30
        numer[:,3,2] = -dt30
        numer[:,3,3] = 1.0
        
        U = np.zeros((n-3,4,4))
        U[:,0,0] = 1.0
        U[:,0,1] = t1
        U[:,0,2] = t1**2
        U[:,0,3] = t1**3
        U[:,1,1] = dt21
        U[:,1,2] = 2*t1*dt21
        U[:,1,3] = 3*t1**2*dt21
        U[:,2,2] = dt21**2
        U[:,2,3] = 3*t1*dt21**2
        U[:,3,3] = dt21**3
        
        bz = np.zeros((n-3,4,4))
        bz[:] = bezierM
        ms = (bz @ U @ numer) @ denom
        cpts = []
        for i,m in enumerate(ms):
            ps = self.points[i:i+4]
            cpt = m @ ps
            cpts.append(cpt)
        return np.array(cpts)

    def to_bezier_segments(self):
        segments = []
        all_cpts = self.get_bezier_control_points()
        for i, cpts in enumerate(all_cpts):
            bezier = SvBezierCurve.from_control_points(cpts)
            segments.append(bezier)
        return segments

    def reverse(self):
        points = self.points[::-1]
        t0 = self.tknots[0]
        tn = self.tknots[-1]
        tknots = tn + t0 - self.tknots[::-1]
        return SvCatmullRomCurve(tknots, points)

    def reparametrize(self, new_t_min, new_t_max):
        t0 = self.tknots[0]
        tn = self.tknots[-1]
        tknots = (new_t_max - new_t_min) * (self.tknots - t0) / (tn - t0) + new_t_min
        return SvCatmullRomCurve(tknots, self.points)

    def split_at(self, t):
        return self.to_nurbs().reparametrize(*self.get_u_bounds()).split_at(t)

def uniform_catmull_rom_bezier_segment(points, tension=1.0):
    v = np.asarray(points)
    p0 = v[1]
    p1 = v[1] + tension*(v[2] - v[0]) / 6
    p2 = v[2] - tension*(v[3] - v[1]) / 6
    p3 = v[2]
    return SvCubicBezierCurve(p0, p1, p2, p3)

def uniform_catmull_rom_bezier_interpolate(points, concatenate=True, cyclic=False, tension=1.0):
    points = np.asarray(points)
    if isinstance(tension, (list, np.ndarray)):
        tensions = tension
    else:
        tensions = np.full((len(points)-3,), tension)
    _, points = prepare_data(None, points, cyclic=cyclic)

    segments = []
    for i in range(len(points)-3):
        spline_cpts = points[i:i+4]
        segment = uniform_catmull_rom_bezier_segment(spline_cpts, tensions[i])
        segments.append(segment)
    if concatenate:
        return concatenate_nurbs_curves(segments)
    else:
        return segments

