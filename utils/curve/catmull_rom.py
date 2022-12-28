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
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves

bezierM = np.zeros((4,4))
bezierM[:,0] = 1.0
bezierM[3,:] = 1.0
bezierM[1,1] = 1.0/3.0
bezierM[2,1] = 2.0/3.0
bezierM[2,2] = 1.0/3.0
        
class SvCatmullRomCurve(SvCurve):
    """
    Non-uniform Catmull-Rom cubic spline.
    See https://en.wikipedia.org/wiki/Centripetal_Catmull%E2%80%93Rom_spline
    """
    def __init__(self, tknots, points):
        self.points = np.asarray(points)
        self.tknots = np.asarray(tknots)
        self.__description__ = f"Catmull-Rom[{len(self.points)}]"

    @classmethod
    def build(self, points, tknots=None, metric='DISTANCE', cyclic=False):
        points = np.asarray(points)
        if tknots is not None:
            tknots = np.asarray(tknots)
        else:
            tknots = Spline.create_knots(points, metric=metric)

        if cyclic:
            points = np.concatenate(([points[-1]], points), axis=0)
            points = np.append(points, [points[1], points[2]], axis=0)

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

            t0 = 2*tknots[0] - tknots[1]
            tn = 2*tknots[-1] - tknots[-2]
            tknots = np.insert(tknots, 0, t0, axis=0)
            tknots = np.append(tknots, [tn], axis=0)

        return SvCatmullRomCurve(tknots, points)

    def get_u_bounds(self):
        return self.tknots[1], self.tknots[-2]

    def get_end_points(self):
        return self.points[1], self.points[-2]

    def get_degree(self):
        return 3

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

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
        U[:,0,1] = t0
        U[:,0,2] = t0**2
        U[:,0,3] = t0**3
        U[:,1,1] = dt30
        U[:,1,2] = 2*t0*dt30
        U[:,1,3] = 3*t0**2*dt30
        U[:,2,2] = dt30**2
        U[:,2,3] = 3*t0*dt30**2
        U[:,3,3] = dt30**3
        
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
            bezier = SvBezierCurve(cpts)
            ts = self.tknots[i:i+4]
            t1 = (ts[1] - ts[0]) / (ts[3] - ts[0])
            t2 = (ts[2] - ts[0]) / (ts[3] - ts[0])
            segment = bezier.cut_segment(t1, t2)
            segments.append(segment)
        return segments

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        return concatenate_nurbs_curves(self.to_bezier_segments())

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

    def reverse(self):
        points = self.points[::-1]
        t0 = self.tknots[0]
        tn = self.tknots[-1]
        tknots = tn + t0 - self.tknots[::-1]
        return SvCatmullRomCurve(tknots, points)

    def get_bounding_box(self):
        return bounding_box(self.points)

    def reparametrize(self, new_t_min, new_t_max):
        t0 = self.tknots[0]
        tn = self.tknots[-1]
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

