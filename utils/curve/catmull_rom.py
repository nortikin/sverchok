# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.geom import Spline
from sverchok.utils.curve.core import SvCurve

class SvCatmullRomCurve(SvCurve):
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
            points = np.insert(points, 0, points[-1], axis=0)
            points = np.append(points, [points[-1]], axis=0)

            dt0 = tknots[1] - tknots[0]
            dt1 = tknots[-1] - tknots[-2]
            dt = (dt0 + dt1) * 0.5
            t0 = tknots[0] - dt
            tn = tknots[-1] + dt
            tknots = np.insert(tknots, 0, t0, axis=0)
            tknots = np.append(tknots, [tn], axis=0)
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
    

