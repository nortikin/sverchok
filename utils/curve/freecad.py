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
    return fc_line

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
        return fc_arc
    else:
        return fc_circle

curve_converters[SvCircle] = circle_to_freecad

def curve_to_freecad_nurbs(sv_curve):
    """
    Convert SvCurve to FreeCAD's NURBS curve.
    Raise an exception if it is not possible.

    input: SvCurve
    output: SvFreeCadNurbsCurve
    """
    nurbs = SvNurbsCurve.to_nurbs(sv_curve)
    if nurbs is None:
        raise Exception(f"{sv_curve} is not a NURBS curve")
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

    def tangent(self, t):
        return np.array(self.edge.tangentAt(t))

    def tangent_array(self, ts):
        tangents = []
        for t in ts:
            tangents.append(self.edge.tangentAt(t))
        return np.array(tangents)

    def get_u_bounds(self):
        return self.u_bounds

    def to_nurbs(self, implementation = SvNurbsMaths.FREECAD):
        curve = self.curve.toBSpline(*self.u_bounds)
        curve.transform(self.edge.Matrix)
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

class SvFreeCadNurbsCurve(SvNurbsCurve):
    def __init__(self, curve, ndim=3):
        self.curve = curve
        self.ndim = ndim
        self.u_bounds = None # from FreeCAD data
        self.__description__ = f"FreeCAD NURBS (degree={curve.Degree}, pts={curve.NbPoles})"

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
    
    def tangent(self, t):
        v = self.curve.tangent(t)
        return np.array(self._convert(v))
    
    def tangent_array(self, ts):
        return np.vectorize(self.tangent, signature='()->(3)')(ts)    

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

SvNurbsMaths.curve_classes[SvNurbsMaths.FREECAD] = SvFreeCadNurbsCurve

def curve_to_freecad(sv_curve):
    converter = curve_converters.get(type(sv_curve), None)
    if converter is not None:
        try:
            fc_curve = converter(sv_curve)
            bounds = fc_curve.FirstParameter, fc_curve.LastParameter
            return SvFreeCadCurve(fc_curve, bounds)
        except UnsupportedCurveTypeException as e:
            info(f"Can't convert {sv_curve} to native FreeCAD curve: {e}")
            pass
    return curve_to_freecad_nurbs(sv_curve)

