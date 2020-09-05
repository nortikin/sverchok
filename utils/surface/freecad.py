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
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve, curve_to_freecad_nurbs, curves_to_wire

from sverchok.dependencies import FreeCAD
if FreeCAD is not None:
    from FreeCAD import Base
    import Part

def curves_to_face(sv_curves, planar=True):
    """
    Make a Part.Face from a list of SvCurve.
    Curves must have NURBS representation, must form a closed loop, and it must
    be planar, otherwise an exception will be raised.
    
    input:
        * list of SvCurve.
        * planar: True to make a flat face; in this case, all curves
            must lie exactly in one plane
    output: tuple:
    * Part.Face
    * List of SvFreeCadNurbsCurve for outer wire of the face
    * SvFreeCadNurbsSurface for face's surface.
    """
    # Check
    sv_curves = [curve_to_freecad_nurbs(curve) for curve in sv_curves]
    edges = [Part.Edge(curve.curve) for curve in sv_curves]
    wire = Part.Wire(edges)
    if not wire.isClosed():
        for i, edge in enumerate(wire.Edges):
            print(f"#{i}: {edge.Curve.StartPoint} - {edge.Curve.EndPoint}")
        raise Exception(f"The wire is not closed: {sv_curves}")

    if planar:
        try:
            fc_face = Part.Face(wire)
        except Part.OCCError as e:
            raise Exception(f"Can't create a Face from {sv_curves}: {e}\nProbably these curves are not all lying in the same plane?")
        surface = SvSolidFaceSurface(fc_face).to_nurbs()
    else:
        fc_face = Part.makeFilledFace(edges)
        surface = SvSolidFaceSurface(fc_face).to_nurbs()

    wire_curves = []
    for wire_edge in fc_face.OuterWire.Edges:
        pair = fc_face.curveOnSurface(wire_edge)
        fc_curve, t_min, t_max = pair
        curve = SvFreeCadNurbsCurve(fc_curve, ndim=2)
        wire_curves.append(curve)
    return fc_face, wire_curves, surface

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

class SvFreeCadNurbsSurface(SvNurbsSurface):
    def __init__(self, surface, face=None):
        self.surface = surface
        self.face = face

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        m,n,_ = control_points.shape
        if weights is None:
            weights = np.ones((m,n))
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

#     def to_nurbs(self, **kwargs):
#         return self

def is_solid_face_surface(surface):
    if not isinstance(surface, SvFreeCadNurbsSurface):
        return False
    if not hasattr(surface, 'face') or surface.face is None:
        return False
    return True

SvNurbsMaths.surface_classes[SvNurbsMaths.FREECAD] = SvFreeCadNurbsSurface

