# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve import knotvector as sv_knotvector

from sverchok.dependencies import FreeCAD
if FreeCAD is not None:
    from FreeCAD import Base
    import Part
    from Part import Geom2d

class SvSolidEdgeCurve(SvCurve):
    __description__ = "Solid Edge"
    def __init__(self, solid_edge):
        self.edge = solid_edge
        self.curve = solid_edge.Curve
        self.u_bounds = (self.edge.FirstParameter, self.edge.LastParameter)

    def evaluate(self, t):
        return np.array(self.curve.value(t))

    def evaluate_array(self, ts):
        t_out = []
        for t in ts:
            t_out.append(self.curve.value(t))
        return np.array(t_out)

    def tangent(self, t):
        return np.array(self.edge.tangentAt(t))

    def tangent_array(self, ts):
        tangents = []
        for t in ts:
            tangents.append(self.edge.tangentAt(t))
        return np.array(tangents)

    def get_u_bounds(self):
        return self.u_bounds

    def to_nurbs(self, implementation = SvNurbsCurve.NATIVE):
        curve = self.curve.toBSpline(*self.u_bounds)
        curve.transform(self.edge.Matrix)
        control_points = curve.getPoles()
        #print(control_points)
        curve = SvNurbsCurve.build(implementation,
                    curve.Degree, curve.KnotSequence,
                    control_points,
                    curve.getWeights())
        #curve.u_bounds = self.u_bounds
        return curve

class SvFreeCadCurve(SvCurve):
    __description__ = "FreeCAD"
    def __init__(self, curve, bounds, ndim=3):
        self.curve = curve
        self.u_bounds = bounds
        self.ndim = ndim

    def _convert(self, p):
        if self.ndim == 2:
            return [p.x, p.y, 0]
        else:
            return [p.x, p.y, p.z]

    def evaluate(self, t):
        p = self.curve.value(t)
        return np.array(self._convert(p))

    def evaluate_array(self, ts):
        return np.vectorize(self.evaluate, signature='()->(3)')(ts)

    def tangent(self, t):
        p = self.edge.tangentAt(t)
        return np.array(self._convert(p))

    def tangent_array(self, ts):
        return np.vectorize(self.tangent, signature='()->(3)')(ts)

    def get_u_bounds(self):
        return self.u_bounds

    #def get_u_bounds(self):
    #    return (self.curve.FirstParameter, self.curve.LastParameter)

class SvFreeCadNurbsCurve(SvNurbsCurve):
    def __init__(self, curve, ndim=3):
        self.curve = curve
        self.ndim = ndim

    @classmethod
    def build(cls, implementation, degree, knotvector, control_points, weights=None, normalize_knots=False):
        n = len(control_points)
        if weights is None:
            weights = np.ones((n,))

        if normalize_knots:
            knotvector = sv_knotvector.normalize(knotvector)

        pts = [Base.Vector(t[0], t[1], t[2]) for t in control_points]
        ms = sv_knotvector.to_multiplicity(knotvector)
        knots = [p[0] for p in ms]
        mults = [p[1] for p in ms]

        curve = Part.BSplineCurve()
        curve.buildFromPolesMultsKnots(pts, mults, knots, False, degree, weights)
        return SvFreeCadNurbsCurve(curve)

    @classmethod
    def build_2d(cls, degree, knotvector, control_points, weights=None):
        n = len(control_points)
        if weights is None:
            weights = np.ones((n,))

        pts = [Base.Vector2d(t[0], t[1]) for t in control_points]
        ms = sv_knotvector.to_multiplicity(knotvector)
        knots = [p[0] for p in ms]
        mults = [p[1] for p in ms]

        curve = Geom2d.BSplineCurve2d()
        curve.buildFromPolesMultsKnots(pts, mults, knots, False, degree, weights)
        return SvFreeCadNurbsCurve(curve, ndim=2)
    
    def is_closed(self, eps=None):
        return self.curve.isClosed()
    
    def _convert(self, p):
        if self.ndim == 2:
            return [p.x, p.y, 0]
        else:
            return [p.x, p.y, p.z]

    def evaluate(self, t):
        pt = self.curve.value(t)
        return np.array(self._convert(pt))

    def evaluate_array(self, ts):
        return np.vectorize(self.evaluate, signature='()->(3)')(ts)
    
    def tangent(self, t):
        v = self.curve.tangent(t)
        return np.array(self._convert(v))
    
    def tangent_array(self, ts):
        return np.vectorize(self.tangent, signature='()->(3)')(ts)    

    def get_u_bounds(self):
        return (self.curve.FirstParameter, self.curve.LastParameter)

    def get_knotvector(self):
        knots = self.curve.getKnots()
        mults = self.curve.getMultiplicities()
        ms = zip(knots, mults)
        return sv_knotvector.from_multiplicity(ms)

    def get_degree(self):
        return self.curve.Degree

    def get_control_points(self):
        poles = self.curve.getPoles()
        poles = [self._convert(p) for p in poles]
        return np.array(poles)

    def get_weights(self):
        return np.array(self.curve.getWeights())

SvNurbsMaths.curve_classes[SvNurbsMaths.FREECAD] = SvFreeCadNurbsCurve

