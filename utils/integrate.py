# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.geom import CubicSpline

class TrapezoidIntegral(object):
    """
    Calculate approximate indefinite integral from points
    by trapezoid formula.
    """
    def __init__(self, ts, xs, ys):
        self.ts = ts
        self.xs = xs
        self.ys = ys
        self.summands = None

    def calc(self):
        dxs = self.xs[1:] - self.xs[:-1]
        summands_left = self.ys[:-1] * dxs
        summands_right = self.ys[1:] * dxs

        summands = (summands_left + summands_right) / 2.0
        self.summands = np.cumsum(summands)
        self.summands = np.insert(self.summands, 0, 0)

    def evaluate_linear(self, ts):
        return np.interp(ts, self.ts, self.summands)

    def evaluate_cubic(self, ts):
        xs = self.ts
        ys = self.summands
        zs = np.zeros_like(xs, dtype=np.float64)
        verts = np.stack((xs, ys, zs)).T
        spline = CubicSpline(verts, tknots=xs, is_cyclic=False)
        return spline.eval(ts)[:,1]

