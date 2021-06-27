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
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions, SvNurbsMaths, from_homogenous
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import unify_curves_degree
from sverchok.utils.decorators import deprecated
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

def unify_curves(curves, method='UNIFY'):
    curves = [curve.reparametrize(0.0, 1.0) for curve in curves]

    if method == 'UNIFY':
        dst_knots = defaultdict(int)
        for curve in curves:
            m = sv_knotvector.to_multiplicity(curve.get_knotvector())
            for u, count in m:
                u = round(u, 6)
                dst_knots[u] = max(dst_knots[u], count)

        result = []
#     for i, curve1 in enumerate(curves):
#         for j, curve2 in enumerate(curves):
#             if i != j:
#                 curve1 = curve1.to_knotvector(curve2)
#         result.append(curve1)

        for curve in curves:
            diffs = []
            kv = np.round(curve.get_knotvector(), 6)
            ms = dict(sv_knotvector.to_multiplicity(kv))
            for dst_u, dst_multiplicity in dst_knots.items():
                src_multiplicity = ms.get(dst_u, 0)
                diff = dst_multiplicity - src_multiplicity
                diffs.append((dst_u, diff))
            #print(f"Src {ms}, dst {dst_knots} => diff {diffs}")

            for u, diff in diffs:
                if diff > 0:
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
    cpts = curve.get_control_points()
    direction = cpts[-1] - cpts[0]
    direction /= np.linalg.norm(direction)

    for cpt1, cpt2 in zip(cpts, cpts[1:]):
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

def _intersect_curves_equation(curve1, curve2, method='SLSQP', precision=0.001):
    t1_min, t1_max = curve1.get_u_bounds()
    t2_min, t2_max = curve2.get_u_bounds()

    lower = np.array([t1_min, t2_min])
    upper = np.array([t1_max, t2_max])

    line1 = _check_is_line(curve1)
    line2 = _check_is_line(curve2)

    if line1 and line2:
        v1, v2 = line1
        v3, v4 = line2
        #print(f"Call L: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")
        r = intersect_segment_segment(v1, v2, v3, v4)
        if not r:
            #print(f"({v1} - {v2}) x ({v3} - {v4}): no intersection")
            return []
        else:
            u, v, pt = r
            t1 = (1-u)*t1_min + u*t1_max
            t2 = (1-v)*t2_min + v*t2_max
            return [(t1, t2, pt)]

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
#         print(f"=> {ts} => {rs}")

    #print(f"Call R: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")
    #res = scipy.optimize.root(constrained_goal, x0, method='hybr', tol=0.001)
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
            #print(f"Found: T1 {t1}, T2 {t2}, Pt1 {pt1}, Pt2 {pt2}")
            pt = (pt1 + pt2) * 0.5
            return [(t1, t2, pt)]
        else:
            print(f"numeric method found a point, but it's too far: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]: {dist}")
            return []
    else:
        print(f"numeric method fail: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]: {res.message}")
        return []

def intersect_nurbs_curves(curve1, curve2, method='SLSQP', numeric_precision=0.001):

    bbox_tolerance = 1e-4

    def _intersect(curve1, curve2, c1_bounds, c2_bounds):
        t1_min, t1_max = c1_bounds
        t2_min, t2_max = c2_bounds

        #print(f"check: [{t1_min} - {t1_max}] x [{t2_min} - {t2_max}]")

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

