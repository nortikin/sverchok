# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.core import SvSurface, UnsupportedSurfaceTypeException
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve, curve_to_freecad, curve_to_freecad_nurbs, curves_to_wire

from sverchok.dependencies import FreeCAD
if FreeCAD is not None:
    from FreeCAD import Base
    import Part

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

def curves_to_face(sv_curves, planar=True, force_nurbs=True):
    """
    Make a Part.Face from a list of SvCurve.
    Curves must have NURBS representation, must form a closed loop, and it must
    be planar, otherwise an exception will be raised.
    
    input:
        * list of SvCurve.
        * planar: True to make a flat face; in this case, all curves
            must lie exactly in one plane
        * force_nurbs: True if you want NURBS surface as output even when
            curves are not NURBS
    output:
    * SvSolidFaceSurface for face's surface;
        SvFreeCadNurbsSurface if force_nurbs == True.
    """
    # Check
    sv_curves = [curve_to_freecad(curve) for curve in sv_curves]
    all_nurbs = all(isinstance(curve, SvFreeCadNurbsCurve) for curve in sv_curves)
    edges = [Part.Edge(curve.curve) for curve in sv_curves]
    try:
        wire = Part.Wire(edges)
    except Part.OCCError as e:
        fc_curves = [edge.Curve for edge in edges]
        raise Exception(f"Can't build a Wire out of edges: {fc_curves}: {e}")
    if not wire.isClosed():
        last_point = None
        distance = None
        for i, edge in enumerate(wire.Edges):
            p1, p2 = get_edge_endpoints(edge)
            if last_point is not None:
                distance = last_point.distanceToPoint(p1)
                print(f"#{i-1}-{i}: distance={distance}: ({last_point.x}, {last_point.y}, {last_point.z}) - ({p1.x}, {p1.y}, {p1.z})")
            last_point = p2
        p1 = get_edge_endpoints(wire.Edges[-1])[1]
        p2 = get_edge_endpoints(wire.Edges[0])[0]
        distance = p1.distanceToPoint(p2)
        print(f"Last - first distance = {distance}")
        raise Exception(f"The wire is not closed: {sv_curves}")

    if planar:
        try:
            fc_face = Part.Face(wire)
        except Part.OCCError as e:
            raise Exception(f"Can't create a Face from {sv_curves}: {e}\nProbably these curves are not all lying in the same plane?")
        surface = SvSolidFaceSurface(fc_face)
    else:
        fc_face = Part.makeFilledFace(edges)
        surface = SvSolidFaceSurface(fc_face)

    if all_nurbs or force_nurbs:
        surface = surface.to_nurbs()

    return surface

def surface_to_freecad(sv_surface, make_face=False):
    """
    Convert SvSurface into FreeCAD's Surface.
    The surface must be presentable as NURBS.

    input:
      * sv_surface: SvSurface
      * make_face: if True, create a Part.Face out of the surface and assign it
        to the `face` property of the resulting surface
    output: SvFreeCadNurbsSurface
    """
    nurbs = SvNurbsSurface.get(sv_surface)
    if nurbs is None:
        raise Exception("not a NURBS surface")
    sv_fc_nurbs = SvNurbsMaths.build_surface(SvNurbsMaths.FREECAD,
                nurbs.get_degree_u(),
                nurbs.get_degree_v(),
                nurbs.get_knotvector_u(),
                nurbs.get_knotvector_v(),
                nurbs.get_control_points(),
                nurbs.get_weights())
    if make_face:
        sv_fc_nurbs.face = Part.Face(sv_fc_nurbs.surface)
    return sv_fc_nurbs

class SvSolidFaceSurface(SvSurface):
    __description__ = "Solid Face"
    def __init__(self, solid_face):
        self.face = solid_face
        self.surface = solid_face.Surface
        self.u_bounds = solid_face.ParameterRange[:2]
        self.v_bounds = solid_face.ParameterRange[2:]

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        return np.array(self.surface.value(u, v))

    def evaluate_array(self, us, vs):
        v_out = []
        for u, v in zip(us, vs):
            v_out.append(self.surface.value(u, v))
        return np.array(v_out)

    def gauss_curvature_array(self, us, vs):
        v_out = []
        for u, v in zip(us, vs):
            v_out.append(self.surface.curvature(u, v, "Gauss"))
        return np.array(v_out)

    def mean_curvature_array(self, us, vs):
        v_out = []
        for u,v in zip(us, vs):
            v_out.append(self.surface.curvature(u, v, "Mean"))
        return np.array(v_out)

    def normal(self, u, v):
        return np.array(self.surface.normal(u, v))

    def normal_array(self, us, vs):
        v_out = []
        for u,v in zip(us, vs):
            v_out.append(self.surface.normal(u, v))
        return np.array(v_out)

    def to_nurbs(self, implementation = SvNurbsMaths.FREECAD):
        faces = self.face.toNurbs().Faces
        nurbs = faces[0].Surface
        return SvFreeCadNurbsSurface(nurbs, face=faces[0])

    def get_min_continuity(self):
        s = self.surface.Continuity[1]
        if s == 'N':
            return -1
        else:
            return int(s)

class SvFreeCadNurbsSurface(SvNurbsSurface):
    def __init__(self, surface, face=None):
        self.surface = surface
        self.face = face

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        control_points = np.asarray(control_points)
        m,n,_ = control_points.shape
        if weights is None:
            weights = np.ones((m,n))
        weights = np.asarray(weights)
        if normalize_knots:
            knotvector_u = sv_knotvector.normalize(knotvector_u)
            knotvector_v = sv_knotvector.normalize(knotvector_v)

        pts = [[Base.Vector(*t) for t in row] for row in control_points]

        ms_u = sv_knotvector.to_multiplicity(knotvector_u)
        knots_u = [p[0] for p in ms_u]
        mults_u = [p[1] for p in ms_u]
        ms_v = sv_knotvector.to_multiplicity(knotvector_v)
        knots_v = [p[0] for p in ms_v]
        mults_v = [p[1] for p in ms_v]

        surface = Part.BSplineSurface()
        surface.buildFromPolesMultsKnots(pts,
                    mults_u, mults_v,
                    knots_u, knots_v,
                    False, False,
                    degree_u, degree_v,
                    weights.tolist())
        return SvFreeCadNurbsSurface(surface)

    def __repr__(self):
        degree_u = self.surface.UDegree
        degree_v = self.surface.VDegree
        points = self.surface.getPoles()
        points_u = len(points)
        points_v = len(points[0])
        if self.face is None:
            word = "surface"
        else:
            word = "Face"
        return f"<FreeCAD NURBS (degree={degree_u}x{degree_v}, pts={points_u}x{points_v}) {word}>"
    
    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsMaths.FREECAD

    def get_degree_u(self):
        return self.surface.UDegree

    def get_degree_v(self):
        return self.surface.VDegree

    def get_knotvector_u(self):
        ks = self.surface.getUKnots()
        ms = self.surface.getUMultiplicities()
        pairs = zip(ks, ms)
        return sv_knotvector.from_multiplicity(pairs)

    def get_knotvector_v(self):
        ks = self.surface.getVKnots()
        ms = self.surface.getVMultiplicities()
        pairs = zip(ks, ms)
        return sv_knotvector.from_multiplicity(pairs)

    def get_control_points(self):
        poles = self.surface.getPoles()
        points = [[[pt.x, pt.y, pt.z] for pt in row] for row in poles]
        return np.array(points)

    def get_weights(self):
        weights = self.surface.getWeights()
        return np.array(weights)

    def get_u_min(self):
        return self.get_knotvector_u()[0]

    def get_u_max(self):
        return self.get_knotvector_u()[-1]

    def get_v_min(self):
        return self.get_knotvector_v()[0]

    def get_v_max(self):
        return self.get_knotvector_v()[-1]

    def _convert(self, p):
        return [p.x, p.y, p.z]

    def evaluate(self, u, v):
        pt = self.surface.value(u, v)
        return np.array(self._convert(pt))

    def evaluate_array(self, us, vs):
        return np.vectorize(self.evaluate, signature='(),()->(3)')(us, vs)

    def normal(self, u, v):
        v = self.surface.normal(u, v)
        return np.array(self._convert(v))

    def normal_array(self, us, vs):
        return np.vectorize(self.normal, signature='(),()->(3)')(us, vs)

    def iso_curve(self, fixed_axis, param, flip=False):
        if fixed_axis == 'U':
            fc_curve = self.surface.uIso(param)
        elif fixed_axis == 'V':
            fc_curve = self.surface.vIso(param)
        else:
            raise Exception("Unsupported direction")

        return SvFreeCadNurbsCurve(fc_curve)

#     def to_nurbs(self, **kwargs):
#         return self

def is_solid_face_surface(surface):
    if not isinstance(surface, (SvFreeCadNurbsSurface, SvSolidFaceSurface)):
        return False
    if not hasattr(surface, 'face') or surface.face is None:
        return False
    return True

SvNurbsMaths.surface_classes[SvNurbsMaths.FREECAD] = SvFreeCadNurbsSurface

