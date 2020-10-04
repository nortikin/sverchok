# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict

from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions, SvNurbsMaths, from_homogenous
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.algorithms import unify_curves_degree
from sverchok.utils.decorators import deprecated

def unify_two_curves(curve1, curve2):
    curve1 = curve1.to_knotvector(curve2)
    curve2 = curve2.to_knotvector(curve1)
    return curve1, curve2

@deprecated("Use sverchok.utils.curve.algorithms.unify_curves_degree")
def unify_degrees(curves):
    max_degree = max(curve.get_degree() for curve in curves)
    curves = [curve.elevate_degree(target=max_degree) for curve in curves]
    return curves

def unify_curves(curves):
    curves = [curve.reparametrize(0.0, 1.0) for curve in curves]

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

