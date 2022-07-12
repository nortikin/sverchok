# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import math

from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.primitives import SvLine, SvCircle
from sverchok.utils.curve.biarc import SvBiArc
from sverchok.utils.logging import info

from sverchok.dependencies import FreeCAD
if FreeCAD is not None:
    from FreeCAD import Base
    import Part
    from Part import Geom2d

curve_converters = dict()

def line_to_freecad(line):
    u_min, u_max = line.get_u_bounds()
    p1 = tuple(line.evaluate(u_min))
    p2 = tuple(line.evaluate(u_max))
    p1 = Base.Vector(*p1)
    p2 = Base.Vector(*p2)
    fc_line = Part.LineSegment(p1, p2)
    return [fc_line]

curve_converters[SvLine] = line_to_freecad

def circle_to_freecad(circle):
    center = tuple(circle.center)
    normal = tuple(circle.normal)
    #vectorx = tuple(circle.vectorx / np.linalg.norm(circle.vectorx))
    radius = circle.get_actual_radius()
    u_min, u_max = circle.get_u_bounds()
    vectorx = circle.evaluate(0) - circle.center
    vectorx /= np.linalg.norm(vectorx)
    vectorx = tuple(vectorx)

    fc_circle = Part.Circle(Base.Vector(*center), Base.Vector(*normal), radius)
    if u_min != 0 or u_max != 2*math.pi:
        fc_circle.XAxis = Base.Vector(*vectorx)
        fc_arc = fc_circle.trim(u_min, u_max)
        return [fc_arc]
    else:
        return [fc_circle]

curve_converters[SvCircle] = circle_to_freecad

def biarc_to_freecad(biarc):
    arc1 = circle_to_freecad(biarc.arc1)
    arc2 = circle_to_freecad(biarc.arc2)
    return arc1 + arc2

curve_converters[SvBiArc] = biarc_to_freecad

def curve_to_freecad_nurbs(sv_curve):
    """
    Convert SvCurve to FreeCAD's NURBS curve.
    Raise an exception if it is not possible.

    input: SvCurve
    output: SvFreeCadNurbsCurve
    """
    nurbs = SvNurbsCurve.to_nurbs(sv_curve)
    if nurbs is None:
        raise TypeError(f"{sv_curve} is not a NURBS curve")
    fc_curve = SvNurbsMaths.build_curve(SvNurbsMaths.FREECAD,
                nurbs.get_degree(),
                nurbs.get_knotvector(),
                nurbs.get_control_points(),
                nurbs.get_weights())
    return fc_curve

def curves_to_wire(sv_curves):
    fc_curves = [curve_to_freecad_nurbs(curve).curve for curve in sv_curves]
    shapes = [Part.Edge(curve) for curve in fc_curves]
    wire = Part.Wire(shapes)
    return wire

def make_helix(pitch, height, radius, apex_angle=0):
    # FIXME: in FreeCAD pydoc, there is also "makeLongHelix",
    # which seems to be more suitable here because it said to be "multi-edge";
    # However, in my experiments, makeLongHelix always makes
    # a helix with exactly one turn, while makeHelix makes as many
    # turns as necessary.
    wire = Part.makeHelix(pitch, height, radius, apex_angle)
    fc_edge = wire.Edges[0]
    curve = SvSolidEdgeCurve(fc_edge)
    return curve

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

    def tangent(self, t, tangent_delta=None):
        return np.array(self.edge.tangentAt(t))

    def tangent_array(self, ts, tangent_delta=None):
        tangents = []
        for t in ts:
            tangents.append(self.edge.tangentAt(t))
        return np.array(tangents)

    def get_u_bounds(self):
        return self.u_bounds

    def to_nurbs(self, implementation = SvNurbsMaths.FREECAD):
        curve = self.curve.toBSpline(*self.u_bounds)
        #curve.transform(self.edge.Matrix)
        control_points = np.array(curve.getPoles())
        weights = np.array(curve.getWeights())
        knotvector = np.array(curve.KnotSequence)
        curve = SvNurbsMaths.build_curve(implementation,
                    curve.Degree, knotvector,
                    control_points,
                    weights)
        #curve.u_bounds = self.u_bounds
        return curve

class SvFreeCadCurve(SvCurve):
    def __init__(self, curve, bounds, ndim=3):
        self.curve = curve
        self.u_bounds = bounds
        self.ndim = ndim
    
    def __repr__(self):
        return f"<FreeCAD {self.ndim}D curve, {type(self.curve).__name__}>"

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

    def tangent(self, t, tangent_delta=None):
        p = self.edge.tangentAt(t)
        return np.array(self._convert(p))

    def tangent_array(self, ts, tangent_delta=None):
        return np.vectorize(self.tangent, signature='()->(3)')(ts)

    def get_u_bounds(self):
        return self.u_bounds

    #def get_u_bounds(self):
    #    return (self.curve.FirstParameter, self.curve.LastParameter)

    def reverse(self):
        result = self.to_nurbs().reverse()
        if self.ndim == 2:
            result = result.to_2d()
        return result
        #curve = self.curve.copy()
        #curve.reverse()
        #return SvFreeCadCurve(curve, self.u_bounds, self.ndim)

    def concatenate(self, curve2, tolerance=1e-6):
        if isinstance(curve2, SvFreeCadCurve) and self.ndim == curve2.ndim == 2:
            curve1 = self.curve.toBSpline(*self.u_bounds)
            curve2 = curve2.curve.toBSpline()
            curve1.join(curve2)
            return SvFreeCadNurbsCurve(curve1, self.ndim)
        elif isinstance(curve2, SvFreeCadNurbsCurve) and self.ndim == curve2.ndim == 2:
            curve1 = self.curve.toBSpline(*self.u_bounds)
            curve2 = curve2.curve
            curve1.join(curve2)
            return SvFreeCadNurbsCurve(curve1, self.ndim)
        return self.to_nurbs().concatenate(curve2, tolerance)

    def to_nurbs(self, implementation = SvNurbsMaths.FREECAD):
        curve = self.curve.toBSpline(*self.u_bounds)

        if implementation == SvNurbsMaths.FREECAD:
            return SvFreeCadNurbsCurve(curve, self.ndim)

        #curve.transform(self.edge.Matrix)
        if self.ndim == 2:
            control_points = [(p.x, p.y, 0) for p in curve.getPoles()]
        else:
            control_points = [(p.x, p.y, p.z) for p in curve.getPoles()]
        control_points = np.array(control_points)
        weights = np.array(curve.getWeights())
        knotvector = np.array(curve.KnotSequence)

        curve = SvNurbsMaths.build_curve(implementation,
                    curve.Degree, knotvector,
                    control_points,
                    weights)
        #curve.u_bounds = self.u_bounds
        return curve

class SvFreeCadNurbsCurve(SvNurbsCurve):
    def __init__(self, curve, ndim=3):
        self.curve = curve
        self.ndim = ndim
        self.u_bounds = None # from FreeCAD data
        self.__description__ = f"FreeCAD {ndim}D NURBS (degree={curve.Degree}, pts={curve.NbPoles})"

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

    def to_2d(self):
        return SvFreeCadNurbsCurve.build_2d(self.get_degree(), self.get_knotvector(),
                    self.get_control_points(), self.get_weights())
    
    @classmethod
    def from_any_nurbs(cls, curve):
        if not isinstance(curve, SvNurbsCurve):
            raise TypeError("Invalid curve type")
        if isinstance(curve, SvFreeCadNurbsCurve):
            return curve
        return SvFreeCadNurbsCurve.build(SvNurbsMaths.FREECAD,
                    curve.get_degree(), curve.get_knotvector(),
                    curve.get_control_points(), 
                    curve.get_weights())

    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsMaths.FREECAD

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
    
    def tangent(self, t, tangent_delta=None):
        p, v = self.curve.getD1(t)
        if not isinstance(v, tuple):
            v = self._convert(v)
        return np.array(v)
    
    def tangent_array(self, ts, tangent_delta=None):
        return np.vectorize(self.tangent, signature='()->(3)')(ts)    

    def second_derivative(self, t, tangent_delta = None):
        p, v1, v = self.curve.getD2(t)
        if not isinstance(v, tuple):
            v = self._convert(v)
        return np.array(v)

    def second_derivative_array(self, ts, tangent_delta=None):
        return np.vectorize(self.second_derivative, signature='()->(3)')(ts)    

    def third_derivative(self, t, tangent_delta = None):
        p, v1, v2, v = self.curve.getD3(t)
        if not isinstance(v, tuple):
            v = self._convert(v)
        return np.array(v)

    def third_derivative_array(self, ts, tangent_delta=None):
        return np.vectorize(self.third_derivative, signature='()->(3)')(ts)    

    def derivatives_array(self, n, ts, tangent_delta=None):
        first_derivatives = []
        second_derivatives = []
        third_derivatives = []

        for t in ts:
            p, v1, v2, v3 = self.curve.getD3(t)
            first_derivatives.append(self._convert(v1))
            second_derivatives.append(self._convert(v2))
            third_derivatives.append(self._convert(v3))

        first_derivatives = np.array(first_derivatives)
        second_derivatives = np.array(second_derivatives)
        third_derivatives = np.array(third_derivatives)

        return [first_derivatives, second_derivatives, third_derivatives][:n]

    def get_u_bounds(self):
        if self.u_bounds is None:
            return (self.curve.FirstParameter, self.curve.LastParameter)
        else:
            return self.u_bounds

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

    def insert_knot(self, u, count=1):
        curve = SvFreeCadNurbsCurve(self.curve.copy(), self.ndim) # copy
        curve.curve.insertKnot(u, count)
        return curve

    def remove_knot(self, u, count=1, tolerance=1e-4, if_possible=False):
        curve = SvFreeCadNurbsCurve(self.curve.copy(), self.ndim) # copy
        ms = sv_knotvector.to_multiplicity(self.get_knotvector())
        idx = None
        M = None
        for i, (u1, m) in enumerate(ms):
            if u1 == u:
                idx = i
                if count == 'ALL':
                    M = 0
                elif count == 'ALL_BUT_ONE':
                    M = 1
                else:
                    M = m - count
                break
        if idx is not None:
            curve.curve.removeKnot(idx+1, M, tolerance)
        return curve

SvNurbsMaths.curve_classes[SvNurbsMaths.FREECAD] = SvFreeCadNurbsCurve

def curve_to_freecad(sv_curve):
    converter = curve_converters.get(type(sv_curve), None)
    if converter is not None:
        try:
            fc_curves = converter(sv_curve)
            result = []
            for fc_curve in fc_curves:
                bounds = fc_curve.FirstParameter, fc_curve.LastParameter
                sv_curve = SvFreeCadCurve(fc_curve, bounds)
                result.append(sv_curve)
            return result
        except UnsupportedCurveTypeException as e:
            info(f"Can't convert {sv_curve} to native FreeCAD curve: {e}")
            pass
    return [curve_to_freecad_nurbs(sv_curve)]

def get_curve_endpoints(fc_curve):
    if hasattr(fc_curve, 'StartPoint'):
        p1, p2 = fc_curve.StartPoint, fc_curve.EndPoint
    else:
        t1, t2 = fc_curve.FirstParameter, fc_curve.LastParameter
        if hasattr(fc_curve, 'valueAt'):
            p1, p2 = fc_curve.valueAt(t1), fc_curve.valueAt(t2)
        else:
            p1, p2 = fc_curve.value(t1), fc_curve.value(t2)
    return p1, p2

def get_edge_endpoints(fc_edge):
    t1, t2 = fc_edge.ParameterRange
    fc_curve = fc_edge.Curve
    if hasattr(fc_curve, 'valueAt'):
        p1, p2 = fc_curve.valueAt(t1), fc_curve.valueAt(t2)
    else:
        p1, p2 = fc_curve.value(t1), fc_curve.value(t2)
    return p1, p2

