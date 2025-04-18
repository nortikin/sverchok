# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.core.sv_custom_exceptions import ArgumentError, SvExternalLibraryException, SvInvalidInputException
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import UnsupportedCurveTypeException
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve, curve_to_freecad, get_edge_endpoints
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.sv_logging import get_logger

from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    from FreeCAD import Base
    import Part

def curves_to_face(sv_curves, planar=True, force_nurbs=True, tolerance=None, logger=None):
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
    if logger is None:
        logger = get_logger()
    # Check
    sv_curves = sum([curve_to_freecad(curve) for curve in sv_curves], [])
    all_nurbs = all(isinstance(curve, SvFreeCadNurbsCurve) for curve in sv_curves)
    edges = [curve.curve.toShape() for curve in sv_curves]
    fc_curves = [edge.Curve for edge in edges]
    if tolerance is not None:
        for edge in edges:
            edge.fixTolerance(tolerance)
    try:
        wire = Part.Wire(edges[0])
        for edge in edges[1:]:
            wire.add(edge)
        #wire = Part.Wire(edges)
        #for edge in edges:
        #    wire.add(edge)
    except Exception as e:
        for edge in edges:
            logger.error(f"Curve {edge.Curve}, endpoints: {get_edge_endpoints(edge)}")
        raise SvExternalLibraryException(f"Can't build a Wire out of edges: {fc_curves}: {e}")

    if len(edges) != len(wire.Edges):
        raise SvExternalLibraryException(f"Can't build a Wire out of edges: {fc_curves}: was able to add only {len(wire.Edges)} edges of {len(edges)}")

    #wire.fix(0, 0, 0)
    #wire.fixTolerance(1e-5)
    if not wire.isClosed():

        last_point = None
        distance = None
        for i, edge in enumerate(wire.Edges):
            logger.error(f"Edge #{i}, Curve {edge.Curve}, endpoints: {get_edge_endpoints(edge)}")
            p1, p2 = get_edge_endpoints(edge)
            if last_point is not None:
                distance = last_point.distanceToPoint(p1)
                logger.error(f"#{i-1}-{i}: distance={distance}: ({last_point.x}, {last_point.y}, {last_point.z}) - ({p1.x}, {p1.y}, {p1.z})")
            last_point = p2
        p1 = get_edge_endpoints(wire.Edges[-1])[1]
        p2 = get_edge_endpoints(wire.Edges[0])[0]
        distance = p1.distanceToPoint(p2)
        logger.error(f"Last - first distance = {distance}")
        raise SvInvalidInputException(f"The wire is not closed: {sv_curves}")

    if planar:
        try:
            fc_face = Part.Face(wire)
        except Exception as e:
            raise SvExternalLibraryException(f"Can't create a Face from {sv_curves}: {e}\nProbably these curves are not all lying in the same plane?")
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
        raise UnsupportedCurveTypeException(f"{sv_surface} is not a NURBS surface")
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
        return SvFreeCadNurbsSurface(nurbs, face=faces[0])#.copy(implementation=implementation)

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

    def copy(self, implementation = None, degree_u=None, degree_v = None, knotvector_u = None, knotvector_v = None, control_points = None, weights = None):
        surface = super().copy(implementation = implementation,
                             degree_u = degree_u,
                             degree_v = degree_v,
                             knotvector_u = knotvector_u,
                             knotvector_v = knotvector_v,
                             control_points = control_points,
                             weights = weights)
        surface.face = self.face
        return surface

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

    def iso_curve(self, fixed_direction, param, flip=False):
        if fixed_direction == 'U':
            fc_curve = self.surface.uIso(param)
        elif fixed_direction == 'V':
            fc_curve = self.surface.vIso(param)
        else:
            raise ArgumentError("Unsupported direction")

        return SvFreeCadNurbsCurve(fc_curve)

    def insert_knot(self, direction, parameter, count=1, if_possible=False):
        surface = SvFreeCadNurbsSurface(self.surface.copy())
        tolerance = 1e-6
        if direction == 'U':
            surface.surface.insertUKnot(parameter, count, tolerance)
        else:
            surface.surface.insertVKnot(parameter, count, tolerance)
        return surface
    
    def remove_knot(self, direction, parameter, count=1, if_possible=False, tolerance=1e-6):
        surface = SvFreeCadNurbsSurface(self.surface.copy())
        if direction == 'U':
            ms = sv_knotvector.to_multiplicity(self.get_knotvector_u())
        else:
            ms = sv_knotvector.to_multiplicity(self.get_knotvector_v())
        idx = None
        M = None
        for i, (u1, m) in enumerate(ms):
            if u1 == parameter:
                idx = i
                if count == 'ALL':
                    M = 0
                else:
                    M = m - count
                break
        if idx is not None:
            if direction == 'U':
                surface.surface.removeUKnot(idx+1, M, tolerance)
            else:
                surface.surface.removeVKnot(idx+1, M, tolerance)
        return surface

    def cut_slice(self, direction, p_min, p_max):
        if direction == SvNurbsSurface.U:
            u1, u2 = p_min, p_max
            v1, v2 = self.get_v_bounds()
        else:
            u1, u2 = self.get_v_bounds()
            v1, v2 = p_min, p_max
        surf = self.surface.copy()
        surf.segment(u1, u2, v1, v2)
        result = SvFreeCadNurbsSurface(surf, self.face)
        return result

#     def to_nurbs(self, **kwargs):
#         return self

def is_solid_face_surface(surface):
    if not isinstance(surface, (SvFreeCadNurbsSurface, SvSolidFaceSurface)):
        return False
    if not hasattr(surface, 'face') or surface.face is None:
        return False
    return True

SvNurbsMaths.surface_classes[SvNurbsMaths.FREECAD] = SvFreeCadNurbsSurface

