# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.geom import Spline
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy import interpolate

def scipy_nurbs_approximate(points, weights=None, metric='DISTANCE', degree=3, filter_doubles = None, smoothing=None, is_cyclic=False):
    points = np.asarray(points)
    if weights is not None and len(points) != len(weights):
        raise Exception("Number of weights must be equal to number of points")
    if filter_doubles is not None:
        good = np.where(np.linalg.norm(np.diff(points, axis=0), axis=1) > filter_doubles)
        points = np.r_[points[good], points[-1][np.newaxis]]
        if weights is not None:
            weights = np.r_[weights[good], weights[-1]]
    if is_cyclic:
        if (points[0] != points[-1]).any():
            points = np.vstack((points, points[0]))
            if weights is not None:
                weights = np.insert(weights, -1, weights[0])
    points_orig = points
    points = points.T

    kwargs = dict()
    if weights is not None:
        kwargs['w'] = np.asarray(weights)
    if metric is not None:
        tknots = Spline.create_knots(points.T, metric)
        if len(tknots) != len(points.T):
            raise Exception(f"Number of T knots ({len(tknots)}) is not equal to number of points ({len(points.T)})")
        kwargs['u'] = tknots
    if degree is not None:
        kwargs['k'] = degree
    if smoothing is not None:
        kwargs['s'] = smoothing
    if is_cyclic:
        kwargs['per'] = 1

    tck, u = interpolate.splprep(points, **kwargs)
    knotvector = tck[0]
    control_points = np.stack(tck[1]).T
    degree = tck[2]
    curve = SvNurbsCurve.build(SvNurbsCurve.NATIVE,
                degree, knotvector,
                control_points)
    if is_cyclic:
        curve = curve.cut_segment(0.0, 1.00)
    #curve.u_bounds = (0.0, 1.0)
    return curve

