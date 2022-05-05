# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict
import math

from mathutils import Vector
import mathutils.geometry

from sverchok.utils.math import distribute_int
from sverchok.utils.geom import Spline, linear_approximation, intersect_segment_segment
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions, SvNurbsMaths, from_homogenous, CantInsertKnotException
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import unify_curves_degree, SvCurveLengthSolver
from sverchok.utils.decorators import deprecated
from sverchok.utils.logging import getLogger
from sverchok.dependencies import scipy

if scipy is not None:
    import scipy.optimize

def unify_two_curves(curve1, curve2):
    return unify_curves([curve1, curve2])
    #curve1 = curve1.to_knotvector(curve2)
    #curve2 = curve2.to_knotvector(curve1)
    #return curve1, curve2

@deprecated("Use sverchok.utils.curve.algorithms.unify_curves_degree")
def unify_degrees(curves):
    max_degree = max(curve.get_degree() for curve in curves)
    curves = [curve.elevate_degree(target=max_degree) for curve in curves]
    return curves

class KnotvectorDict(object):
    def __init__(self, accuracy):
        self.multiplicities = []
        self.accuracy = accuracy
        self.done_knots = set()
        self.skip_insertions = defaultdict(list)

    def tolerance(self):
        return 10**(-self.accuracy)

    def update(self, curve_idx, knot, multiplicity):
        found_idx = None
        found_knot = None
        for idx, (c, k, m) in enumerate(self.multiplicities):
            if curve_idx != c:
                if abs(knot - k) < self.tolerance():
                    #print(f"Found: #{curve_idx}: added {knot} ~= existing {k}")
                    if (curve_idx, k) not in self.done_knots:
                        found_idx = idx
                        found_knot = k
                        break
        if found_idx is not None:
            self.multiplicities[found_idx] = (curve_idx, knot, multiplicity)
            self.skip_insertions[curve_idx].append(found_knot)
        else:
            self.multiplicities.append((curve_idx, knot, multiplicity))

        self.done_knots.add((curve_idx, knot))

    def get(self, knot):
        result = 0
        for c, k, m in self.multiplicities:
            if abs(knot - k) < self.tolerance():
                result = max(result, m)
        return result

    def __repr__(self):
        items = [f"c#{c}: {k}: {m}" for c, k, m in self.multiplicities]
        s = ", ".join(items)
        return "{" + s + "}"

    def items(self):
        max_per_knot = defaultdict(int)
        for c, k, m in self.multiplicities:
            max_per_knot[k] = max(max_per_knot[k], m)
        keys = sorted(max_per_knot.keys())
        return [(key, max_per_knot[key]) for key in keys]

def unify_curves(curves, method='UNIFY', accuracy=6):
    tolerance = 10**(-accuracy)
    curves = [curve.reparametrize(0.0, 1.0) for curve in curves]

    if method == 'UNIFY':
        dst_knots = KnotvectorDict(accuracy)
        for i, curve in enumerate(curves):
            m = sv_knotvector.to_multiplicity(curve.get_knotvector(), tolerance**2)
            #print(f"Curve #{i}: degree={curve.get_degree()}, cpts={len(curve.get_control_points())}, {m}")
            for u, count in m:
                dst_knots.update(i, u, count)

        result = []
#     for i, curve1 in enumerate(curves):
#         for j, curve2 in enumerate(curves):
#             if i != j:
#                 curve1 = curve1.to_knotvector(curve2)
#         result.append(curve1)

        for idx, curve in enumerate(curves):
            diffs = []
            #kv = np.round(curve.get_knotvector(), accuracy)
            #curve = curve.copy(knotvector = kv)
            #print('next curve', curve.get_knotvector())
            ms = dict(sv_knotvector.to_multiplicity(curve.get_knotvector(), tolerance**2))
            for dst_u, dst_multiplicity in dst_knots.items():
                src_multiplicity = ms.get(dst_u, 0)
                diff = dst_multiplicity - src_multiplicity
                #print(f"C#{idx}: U = {dst_u}, was = {src_multiplicity}, need = {dst_multiplicity}, diff = {diff}")
                diffs.append((dst_u, diff))
            #print(f"Src {ms}, dst {dst_knots} => diff {diffs}")

            for u, diff in diffs:
                if diff > 0:
                    curve = curve.insert_knot(u, diff)
#                     if u in dst_knots.skip_insertions[idx]:
#                         pass
#                         print(f"C: skip insertion T = {u}")
#                     else:
#                         #kv = curve.get_knotvector()
#                         print(f"C: Insert T = {u} x {diff}")
#                         curve = curve.insert_knot(u, diff)
            result.append(curve)
            
        return result

    elif method == 'AVERAGE':
        kvs = [len(curve.get_control_points()) for curve in curves]
        max_kv, min_kv = max(kvs), min(kvs)
        if max_kv != min_kv:
            raise Exception(f"Knotvector averaging is not applicable: Curves have different number of control points: {kvs}")

        knotvectors = np.array([curve.get_knotvector() for curve in curves])
        knotvector_u = knotvectors.mean(axis=0)

        result = [curve.copy(knotvector = knotvector_u) for curve in curves]
        return result

def interpolate_nurbs_curve(cls, degree, points, metric='DISTANCE', tknots=None):
    n = len(points)
    if points.ndim != 2:
        raise Exception(f"Array of points was expected, but got {points.shape}: {points}")
    ndim = points.shape[1] # 3 or 4
    if ndim not in {3,4}:
        raise Exception(f"Only 3D and 4D points are supported, but ndim={ndim}")
    #points3d = points[:,:3]
    #print("pts:", points)
    if tknots is None:
        tknots = Spline.create_knots(points, metric=metric) # In 3D or in 4D, in general?
    knotvector = sv_knotvector.from_tknots(degree, tknots)
    functions = SvNurbsBasisFunctions(knotvector)
    coeffs_by_row = [functions.function(idx, degree)(tknots) for idx in range(n)]
    A = np.zeros((ndim*n, ndim*n))
    for equation_idx, t in enumerate(tknots):
        for unknown_idx in range(n):
            coeff = coeffs_by_row[unknown_idx][equation_idx]
            row = ndim*equation_idx
            col = ndim*unknown_idx
            for d in range(ndim):
                A[row+d, col+d] = coeff
    B = np.zeros((ndim*n,1))
    for point_idx, point in enumerate(points):
        row = ndim*point_idx
        B[row:row+ndim] = point[:,np.newaxis]

    x = np.linalg.solve(A, B)

    control_points = []
    for i in range(n):
        row = i*ndim
        control = x[row:row+ndim,0].T
        control_points.append(control)
    control_points = np.array(control_points)
    if ndim == 3:
        weights = np.ones((n,))
    else: # 4
        control_points, weights = from_homogenous(control_points)

    if type(cls) == type:
        return cls.build(cls.get_nurbs_implementation(),
                    degree, knotvector,
                    control_points, weights)
    elif isinstance(cls, str):
        return SvNurbsMaths.build_curve(cls,
                    degree, knotvector,
                    control_points, weights)
    else:
        raise TypeError(f"Unsupported type of `cls` parameter: {type(cls)}")

def concatenate_nurbs_curves(curves, tolerance=1e-6):
    if not curves:
        raise Exception("List of curves must be not empty")
    curves = unify_curves_degree(curves)
    result = curves[0]
    for i, curve in enumerate(curves[1:]):
        try:
            result = result.concatenate(curve, tolerance=tolerance)
        except Exception as e:
            raise Exception(f"Can't append curve #{i+1}: {e}")
    return result

def nurbs_curve_to_xoy(curve, target_normal=None):
    cpts = curve.get_control_points()

    approx = linear_approximation(cpts)
    plane = approx.most_similar_plane()
    normal = plane.normal

    if target_normal is not None:
        a = np.dot(normal, target_normal)
        if a > 0:
            normal = -normal

    xx = cpts[-1] - cpts[0]
    xx /= np.linalg.norm(xx)

    yy = np.cross(normal, xx)

    matrix = np.stack((xx, yy, normal)).T
    matrix = np.linalg.inv(matrix)
    center = approx.center
    new_cpts = np.array([matrix @ (cpt - center) for cpt in cpts])
    return curve.copy(control_points = new_cpts)

def nurbs_curve_matrix(curve):
    cpts = curve.get_control_points()

    approx = linear_approximation(cpts)
    plane = approx.most_similar_plane()
    normal = plane.normal

    xx = cpts[-1] - cpts[0]
    xx /= np.linalg.norm(xx)

    yy = np.cross(normal, xx)

    matrix = np.stack((xx, yy, normal)).T
    return matrix

def _check_is_line(curve, eps=0.001):
    if curve.is_line(eps):
        cpts = curve.get_control_points()
        return (cpts[0], cpts[-1])
    else:
        return False

def _get_curve_direction(curve):
    cpts = curve.get_control_points()
    return (cpts[0], cpts[-1])

def locate_p(p1, p2, p, tolerance=1e-3):
    if abs(p1[0] - p2[0]) > tolerance:
        return (p[0] - p1[0]) / (p2[0] - p1[0])
    elif abs(p1[1] - p2[1]) > tolerance:
        return (p[1] - p1[1]) / (p2[1] - p1[1])
    else:
        return (p[2] - p1[2]) / (p2[2] - p1[2])

def intersect_segment_segment_mu(v1, v2, v3, v4, tolerance=1e-3):
    r1, r2 = mathutils.geometry.intersect_line_line(v1, v2, v3, v4)
    if (r1 - r2).length < tolerance:
        v = 0.5 * (r1 + r2)
        v = np.array(v)
        t1 = locate_p (v1, v2, v, tolerance)
        t2 = locate_p (v3, v4, v, tolerance)
        return t1, t2, v
    return None

def _intersect_curves_line(curve1, curve2, precision=0.001, logger=None):
    if logger is None:
        logger = getLogger()

    t1_min, t1_max = curve1.get_u_bounds()
    t2_min, t2_max = curve2.get_u_bounds()

    v1, v2 = _get_curve_direction(curve1)
    v3, v4 = _get_curve_direction(curve2)

    logger.debug(f"Call L: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")
    r = intersect_segment_segment(v1, v2, v3, v4, tolerance=precision, endpoint_tolerance=0.0)
    if not r:
        logger.debug(f"({v1} - {v2}) x ({v3} - {v4}): no intersection")
        return []
    else:
        u, v, pt = r
        t1 = (1-u)*t1_min + u*t1_max
        t2 = (1-v)*t2_min + v*t2_max
        return [(t1, t2, pt)]

def _intersect_curves_equation(curve1, curve2, method='SLSQP', precision=0.001, logger=None):
    if logger is None:
        logger = getLogger()

    t1_min, t1_max = curve1.get_u_bounds()
    t2_min, t2_max = curve2.get_u_bounds()

    def goal(ts):
        p1 = curve1.evaluate(ts[0])
        p2 = curve2.evaluate(ts[1])
        r = (p2 - p1).max()
        return r
        #return np.array([r, r])

    mid1 = (t1_min + t1_max) * 0.5
    mid2 = (t2_min + t2_max) * 0.5

    x0 = np.array([mid1, mid2])

#     def callback(ts, rs):
#         logger.debug(f"=> {ts} => {rs}")

    #logger.debug(f"Call R: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")

    # Find minimum distance between two curves with a numeric method.
    # If this minimum distance is small enough, we will say that curves
    # do intersect.
    res = scipy.optimize.minimize(goal, x0, method=method,
                bounds = [(t1_min, t1_max), (t2_min, t2_max)],
                tol = 0.5 * precision)
    if res.success:
        t1, t2 = tuple(res.x)
        t1 = np.clip(t1, t1_min, t1_max)
        t2 = np.clip(t2, t2_min, t2_max)
        pt1 = curve1.evaluate(t1)
        pt2 = curve2.evaluate(t2)
        dist = np.linalg.norm(pt2 - pt1)
        if dist < precision:
            #logger.debug(f"Found: T1 {t1}, T2 {t2}, Pt1 {pt1}, Pt2 {pt2}")
            pt = (pt1 + pt2) * 0.5
            return [(t1, t2, pt)]
        else:
            logger.debug(f"numeric method found a point, but it's too far: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]: {dist}")
            return []
    else:
        logger.debug(f"numeric method fail: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]: {res.message}")
        return []

def _intersect_endpoints(segment1, segment2, tolerance=0.001):
    cpts1 = segment1.get_control_points()
    cpts2 = segment2.get_control_points()
    s1, e1 = cpts1[0], cpts1[-1]
    s2, e2 = cpts2[0], cpts2[-1]

    t1_min, t1_max = segment1.get_u_bounds()
    t2_min, t2_max = segment2.get_u_bounds()

    if np.linalg.norm(s1 - s2) < tolerance:
        return t1_min, t2_min, 0.5*(s1+s2)
    elif np.linalg.norm(e1 -  e2) < tolerance:
        return t1_max, t2_max, 0.5*(e1+e2)
    elif np.linalg.norm(s1 - e2) < tolerance:
        return t1_min, t2_max, 0.5*(s1+e2)
    elif np.linalg.norm(e1 - s2) < tolerance:
        return t1_max, t2_min, 0.5*(e1+s2)
    else:
        return None

def intersect_nurbs_curves(curve1, curve2, method='SLSQP', numeric_precision=0.001, logger=None):
    if logger is None:
        logger = getLogger()

    u1_min, u1_max = curve1.get_u_bounds()
    u2_min, u2_max = curve2.get_u_bounds()

    expected_subdivisions = 10

    max_dt1 = (u1_max - u1_min) / expected_subdivisions
    max_dt2 = (u2_max - u2_min) / expected_subdivisions

    # Float precision problems workaround
    bbox_tolerance = 1e-4

    # "Recursive bounding box" algorithm:
    # * if bounding boxes of two curves do not intersect, then curves do not intersect
    # * Otherwise, split each curves in half, and check if bounding boxes of these halves intersect.
    # * When this subdivision gives very small parts of curves, try to find intersections numerically.
    #
    # This implementation depends heavily on the fact that curves are NURBS. Because only NURBS curves
    # give us a simple way to calculate bounding box of the curve: it's a bounding box of curve's
    # control points.

    def _intersect(curve1, curve2, c1_bounds, c2_bounds, i=0):
        if curve1 is None or curve2 is None:
            return []

        t1_min, t1_max = c1_bounds
        t2_min, t2_max = c2_bounds

        #logger.debug(f"check: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")

        bbox1 = curve1.get_bounding_box().increase(bbox_tolerance)
        bbox2 = curve2.get_bounding_box().increase(bbox_tolerance)
        if not bbox1.intersects(bbox2):
            return []

        r = _intersect_endpoints(curve1, curve2, numeric_precision)
        if r:
            logger.debug("Endpoint intersection after %d iterations; bbox1: %s, bbox2: %s", i, bbox1.size(), bbox2.size())
            return [r]

        THRESHOLD = 0.02

        if curve1.is_line(numeric_precision) and curve2.is_line(numeric_precision):
            logger.debug("Calling Lin() after %d iterations", i)
            r = _intersect_curves_line(curve1, curve2, numeric_precision, logger=logger)
            if r:
                return r

        if bbox1.size() < THRESHOLD and bbox2.size() < THRESHOLD:
            logger.debug("Calling Eq() after %d iterations", i)
            return _intersect_curves_equation(curve1, curve2, method=method, precision=numeric_precision, logger=logger)

        mid1 = (t1_min + t1_max) * 0.5
        mid2 = (t2_min + t2_max) * 0.5

        c11,c12 = curve1.split_at(mid1)
        c21,c22 = curve2.split_at(mid2)

        r1 = _intersect(c11,c21, (t1_min, mid1), (t2_min, mid2), i+1)
        r2 = _intersect(c11,c22, (t1_min, mid1), (mid2, t2_max), i+1)
        r3 = _intersect(c12,c21, (mid1, t1_max), (t2_min, mid2), i+1)
        r4 = _intersect(c12,c22, (mid1, t1_max), (mid2, t2_max), i+1)

        return r1 + r2 + r3 + r4
    
    return _intersect(curve1, curve2, curve1.get_u_bounds(), curve2.get_u_bounds())

def remove_excessive_knots(curve, tolerance=1e-6):
    kv = curve.get_knotvector()
    for u in sv_knotvector.get_internal_knots(kv):
        curve = curve.remove_knot(u, count='ALL', if_possible=True, tolerance=tolerance)
    return curve

REFINE_TRIVIAL = 'TRIVIAL'
REFINE_DISTRIBUTE = 'DISTRIBUTE'

def refine_curve(curve, samples, algorithm=REFINE_DISTRIBUTE, refine_max=False, solver=None):
    if refine_max:
        degree = curve.get_degree()
        inserts_count = degree
    else:
        inserts_count = 1

    if algorithm == REFINE_TRIVIAL:
        t_min, t_max = curve.get_u_bounds()
        ts = np.linspace(t_min, t_max, num=samples+1, endpoint=False)[1:]
        for t in ts:
            try:
                curve = curve.insert_knot(t, count=inserts_count)
            except CantInsertKnotException:
                break

    elif algorithm == REFINE_DISTRIBUTE:
        existing_knots = np.unique(curve.get_knotvector())
        if solver is not None:
            length_params = solver.calc_length_params(existing_knots)
            sizes = length_params[1:] - length_params[:-1]

            #print(f"K: {existing_knots} => Ls {length_params} => Sz {sizes}")
            counts = distribute_int(samples, sizes)
            for l1, l2, count in zip(length_params[1:], length_params[:-1], counts):
                ls = np.linspace(l1, l2, num=count+2, endpoint=True)[1:-1]
                ts = solver.solve(ls)
                for t in ts:
                    try:
                        curve = curve.insert_knot(t, count=inserts_count, if_possible=True)
                    except CantInsertKnotException:
                        continue
        else:
            sizes = existing_knots[1:] - existing_knots[:-1]

            counts = distribute_int(samples, sizes)
            for t1, t2, count in zip(existing_knots[1:], existing_knots[:-1], counts):
                ts = np.linspace(t1, t2, num=count+2, endpoint=True)[1:-1]
                for t in ts:
                    try:
                        curve = curve.insert_knot(t, count=inserts_count, if_possible=True)
                    except CantInsertKnotException:
                        continue

    else:
        raise Exception("Unsupported algorithm")

    return curve

class SvNurbsCurveLengthSolver(SvCurveLengthSolver):
    def __init__(self, curve):
        self.curve = curve
        self._reverse_spline = None
        self._prime_spline = None

    def _calc_tknots(self, resolution, tolerance):

        def middle(segment):
            u1, u2 = segment.get_u_bounds()
            u = (u1+u2)*0.5
            return u
        
        def split(segment):
            u = middle(segment)
            return segment.split_at(u)
        
        def calc_tknots(segment):
            if segment.is_line(tolerance, use_length_tolerance=True):
                u1, u2 = segment.get_u_bounds()
                return set([u1, u2])
            else:
                segment1, segment2 = split(segment)
                knots1 = calc_tknots(segment1)
                knots2 = calc_tknots(segment2)
                knots = knots1.union(knots2)
                return knots

        t_min, t_max = self.curve.get_u_bounds()
        init_knots = np.linspace(t_min, t_max, num=resolution)
        segments = [self.curve.cut_segment(u1, u2) for u1, u2 in zip(init_knots, init_knots[1:])]

        all_knots = set()
        for segment in segments:
            knots = calc_tknots(segment)
            all_knots = all_knots.union(knots)

        return np.array(sorted(all_knots))

    def prepare(self, mode, resolution=50, tolerance=1e-3):
        if tolerance is None:
            tolerance = 1e-3
        tknots = self._calc_tknots(resolution, tolerance)
        lengths = self.calc_length_segments(tknots)
        self._length_params = np.cumsum(np.insert(lengths, 0, 0))
        self._reverse_spline = self._make_spline(mode, tknots, self._length_params)
        self._prime_spline = self._make_spline(mode, self._length_params, tknots)

def cast_nurbs_curve(curve, target, coeff=1.0):
    if not hasattr(target, 'projection_of_points'):
        raise TypeError("Target object does not support projection_of_points method")

    cpts = curve.get_control_points()
    target_cpts = target.projection_of_points(cpts)

    result_cpts = (1-coeff) * cpts + coeff * target_cpts

    return curve.copy(control_points = result_cpts)

