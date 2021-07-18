# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict

from mathutils import Vector
import mathutils.geometry

from sverchok.utils.geom import Spline, linear_approximation, intersect_segment_segment
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions, SvNurbsMaths, from_homogenous, CantInsertKnotException
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import unify_curves_degree
from sverchok.utils.decorators import deprecated
from sverchok.utils.logging import getLogger
from sverchok.dependencies import scipy

if scipy is not None:
    import scipy.optimize

def unify_two_curves(curve1, curve2):
    curve1 = curve1.to_knotvector(curve2)
    curve2 = curve2.to_knotvector(curve1)
    return curve1, curve2

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
                #print(f"U = {dst_u}, was = {src_multiplicity}, need = {dst_multiplicity}, diff = {diff}")
                diffs.append((dst_u, diff))
            #print(f"Src {ms}, dst {dst_knots} => diff {diffs}")

            for u, diff in diffs:
                if diff > 0:
                    if u in dst_knots.skip_insertions[idx]:
                        pass
                        #print(f"C: skip insertion T = {u}")
                    else:
                        #kv = curve.get_knotvector()
                        #print(f"C: Insert T = {u} x {diff}")
                        curve = curve.insert_knot(u, diff)
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

def concatenate_nurbs_curves(curves):
    if not curves:
        raise Exception("List of curves must be not empty")
    curves = unify_curves_degree(curves)
    result = curves[0]
    for i, curve in enumerate(curves[1:]):
        try:
            result = result.concatenate(curve)
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
    # Check that the provided curve is nearly a straight line segment.
    # This implementation depends heavily on the fact that this curve is
    # NURBS. It uses so-called "godograph property". In short, this 
    # property states that edges of curve's control polygon determine
    # maximum variation of curve's tangent vector.

    cpts = curve.get_control_points()
    # direction from first to last point of the curve
    direction = cpts[-1] - cpts[0]
    direction /= np.linalg.norm(direction)

    for cpt1, cpt2 in zip(cpts, cpts[1:]):
        # for each edge of control polygon,
        # check that it constitutes a small enough
        # angle with `direction`. If not, this is
        # clearly not a straight line.
        dv = cpt2 - cpt1
        dv /= np.linalg.norm(dv)
        angle = np.arccos(np.dot(dv, direction))
        if angle > eps:
            #print(f"A: {direction} x {dv} => {angle}")
            return False

    return (cpts[0], cpts[-1])

def intersect_segment_segment_mu(v1, v2, v3, v4):
    tolerance = 1e-3
    r1, r2 = mathutils.geometry.intersect_line_line(v1, v2, v3, v4)
    if (r1 - r2).length < tolerance:
        v = 0.5 * (r1 + r2)
        return np.array(v)
    return None

def _intersect_curves_equation(curve1, curve2, method='SLSQP', precision=0.001, logger=None):
    if logger is None:
        logger = getLogger()

    t1_min, t1_max = curve1.get_u_bounds()
    t2_min, t2_max = curve2.get_u_bounds()

    lower = np.array([t1_min, t2_min])
    upper = np.array([t1_max, t2_max])

    def linear_intersection():
        # If both curves look very much like straight line segments,
        # then we can calculate their intersections by solving simple
        # linear equations.
        line1 = _check_is_line(curve1)
        line2 = _check_is_line(curve2)

        if line1 and line2:
            v1, v2 = line1
            v3, v4 = line2
            logger.debug(f"Call L: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")
            r = intersect_segment_segment(v1, v2, v3, v4)
            if not r:
                logger.debug(f"({v1} - {v2}) x ({v3} - {v4}): no intersection")
                return None
            else:
                u, v, pt = r
                t1 = (1-u)*t1_min + u*t1_max
                t2 = (1-v)*t2_min + v*t2_max
                return [(t1, t2, pt)]

    r = linear_intersection()
    if r is not None:
        return r

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

def intersect_nurbs_curves(curve1, curve2, method='SLSQP', numeric_precision=0.001, logger=None):
    if logger is None:
        logger = getLogger()

    bbox_tolerance = 1e-4

    # "Recursive bounding box" algorithm:
    # * if bounding boxes of two curves do not intersect, then curves do not intersect
    # * Otherwise, split each curves in half, and check if bounding boxes of these halves intersect.
    # * When this subdivision gives very small parts of curves, try to find intersections numerically.
    #
    # This implementation depends heavily on the fact that curves are NURBS. Because only NURBS curves
    # give us a simple way to calculate bounding box of the curve: it's a bounding box of curve's
    # control points.

    def _intersect(curve1, curve2, c1_bounds, c2_bounds):
        if curve1 is None or curve2 is None:
            return []

        t1_min, t1_max = c1_bounds
        t2_min, t2_max = c2_bounds

        #logger.debug(f"check: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")

        bbox1 = curve1.get_bounding_box().increase(bbox_tolerance)
        bbox2 = curve2.get_bounding_box().increase(bbox_tolerance)
        if not bbox1.intersects(bbox2):
            return []

        THRESHOLD = 0.01

        if bbox1.size() < THRESHOLD and bbox2.size() < THRESHOLD:
        #if _check_is_line(curve1) and _check_is_line(curve2):
            return _intersect_curves_equation(curve1, curve2, method=method, precision=numeric_precision)

        mid1 = (t1_min + t1_max) * 0.5
        mid2 = (t2_min + t2_max) * 0.5

        c11,c12 = curve1.split_at(mid1)
        c21,c22 = curve2.split_at(mid2)

        r1 = _intersect(c11,c21, (t1_min, mid1), (t2_min, mid2))
        r2 = _intersect(c11,c22, (t1_min, mid1), (mid2, t2_max))
        r3 = _intersect(c12,c21, (mid1, t1_max), (t2_min, mid2))
        r4 = _intersect(c12,c22, (mid1, t1_max), (mid2, t2_max))

        return r1 + r2 + r3 + r4
    
    return _intersect(curve1, curve2, curve1.get_u_bounds(), curve2.get_u_bounds())

def remove_excessive_knots(curve, tolerance=1e-6):
    kv = curve.get_knotvector()
    for u in sv_knotvector.get_internal_knots(kv):
        curve = curve.remove_knot(u, count='ALL', if_possible=True, tolerance=tolerance)
    return curve

def refine_curve(curve, samples):
    t_min, t_max = curve.get_u_bounds()
    ts = np.linspace(t_min, t_max, num=samples+1, endpoint=False)[1:]
    for t in ts:
        try:
            curve = curve.insert_knot(t, count=1)
        except CantInsertKnotException:
            break
    return curve

