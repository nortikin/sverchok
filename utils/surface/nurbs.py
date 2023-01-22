
import numpy as np
from collections import defaultdict

from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions,
        nurbs_divide, from_homogenous,
        CantRemoveKnotException, CantReduceDegreeException
    )
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs_algorithms import unify_curves, nurbs_curve_to_xoy, nurbs_curve_matrix
from sverchok.utils.curve.algorithms import unify_curves_degree, SvCurveFrameCalculator
from sverchok.utils.curve.nurbs_solver_applications import interpolate_nurbs_curve_with_tangents
from sverchok.utils.surface.core import UnsupportedSurfaceTypeException
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.utils.logging import info, getLogger
from sverchok.data_structure import repeat_last_for_length
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import operations
    from geomdl import NURBS, BSpline

##################
#                #
#  Surfaces      #
#                #
##################

class SvNurbsSurface(SvSurface):
    """
    Base abstract class for all supported implementations of NURBS surfaces.
    """
    NATIVE = SvNurbsMaths.NATIVE
    GEOMDL = SvNurbsMaths.GEOMDL

    U = 'U'
    V = 'V'

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        return SvNurbsMaths.build_surface(implementation,
                    degree_u, degree_v,
                    knotvector_u, knotvector_v,
                    control_points, weights,
                    normalize_knots)

    @classmethod
    def get(cls, surface, implementation = NATIVE):
        if isinstance(surface, SvNurbsSurface):
            return surface
        if hasattr(surface, 'to_nurbs'):
            try:
                return surface.to_nurbs(implementation=implementation)
            except UnsupportedSurfaceTypeException as e:
                info("Can't convert %s to NURBS: %s", surface, e)
        return None

    @classmethod
    def get_nurbs_implementation(cls):
        raise Exception("NURBS implementation is not defined")

    def copy(self, implementation = None, degree_u=None, degree_v = None, knotvector_u = None, knotvector_v = None, control_points = None, weights = None):
        if implementation is None:
            implementation = self.get_nurbs_implementation()
        if degree_u is None:
            degree_u = self.get_degree_u()
        if degree_v is None:
            degree_v = self.get_degree_v()
        if knotvector_u is None:
            knotvector_u = self.get_knotvector_u()
        if knotvector_v is None:
            knotvector_v = self.get_knotvector_v()
        if control_points is None:
            control_points = self.get_control_points()
        if weights is None:
            weights = self.get_weights()

        return SvNurbsSurface.build(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)

    def insert_knot(self, direction, parameter, count=1, if_possible=False):
        raise Exception("Not implemented!")

    def remove_knot(self, direction, parameter, count=1, tolerance=None, if_possible=False):
        raise Exception("Not implemented!")

    def get_degree_u(self):
        raise Exception("Not implemented!")

    def get_degree_v(self):
        raise Exception("Not implemented!")

    def get_knotvector_u(self):
        """
        returns: np.array of shape (X,)
        """
        raise Exception("Not implemented!")

    def get_knotvector_v(self):
        """
        returns: np.array of shape (X,)
        """
        raise Exception("Not implemented!")

    def get_control_points(self):
        """
        returns: np.array of shape (n_u, n_v, 3)
        """
        raise Exception("Not implemented!")

    def get_weights(self):
        """
        returns: np.array of shape (n_u, n_v)
        """
        raise Exception("Not implemented!")

    def iso_curve(self, fixed_direction, param):
        raise Exception("Not implemented")
    
    def is_rational(self, tolerance=1e-4):
        weights = self.get_weights()
        w, W = weights.min(), weights.max()
        return (W - w) > tolerance

    def calc_greville_us(self):
        n = self.get_control_points().shape[0]
        p = self.get_degree_u()
        kv = self.get_knotvector_u()
        return sv_knotvector.calc_nodes(p, n, kv)

    def calc_greville_vs(self):
        n = self.get_control_points().shape[1]
        p = self.get_degree_v()
        kv = self.get_knotvector_v()
        return sv_knotvector.calc_nodes(p, n, kv)

    def get_homogenous_control_points(self):
        """
        returns: np.array of shape (m, n, 4)
        """
        points = self.get_control_points()
        weights = np.transpose(self.get_weights()[np.newaxis], axes=(1,2,0))
        weighted = weights * points
        return np.concatenate((weighted, weights), axis=2)

    def get_min_u_continuity(self):
        """
        Return minimum continuity degree of the surface in the U direction (guaranteed by knotvector):
        0 - point-wise continuity only (C0),
        1 - tangent continuity (C1),
        2 - 2nd derivative continuity (C2), and so on.
        """
        kv = self.get_knotvector_u()
        degree = self.get_degree_u()
        return sv_knotvector.get_min_continuity(kv, degree)

    def get_min_v_continuity(self):
        """
        Return minimum continuity degree of the surface in the V direction (guaranteed by knotvector):
        0 - point-wise continuity only (C0),
        1 - tangent continuity (C1),
        2 - 2nd derivative continuity (C2), and so on.
        """
        kv = self.get_knotvector_v()
        degree = self.get_degree_v()
        return sv_knotvector.get_min_continuity(kv, degree)
    
    def get_min_continuity(self):
        """
        Return minimum continuity degree of the surface (guaranteed by knotvectors):
        0 - point-wise continuity only (C0),
        1 - tangent continuity (C1),
        2 - 2nd derivative continuity (C2), and so on.
        """
        c_u = self.get_min_u_continuity()
        c_v = self.get_min_v_continuity()
        return min(c_u, c_v)

    def swap_uv(self):
        degree_u = self.get_degree_u()
        degree_v = self.get_degree_v()
        knotvector_u = self.get_knotvector_u()
        knotvector_v = self.get_knotvector_v()

        control_points = self.get_control_points()
        weights = self.get_weights()

        control_points = np.transpose(control_points, axes=(1,0,2))
        weights = weights.T

        return SvNurbsSurface.build(self.get_nurbs_implementation(),
                degree_v, degree_u,
                knotvector_v, knotvector_u,
                control_points, weights)

    def elevate_degree(self, direction, delta=None, target=None):
        if delta is None and target is None:
            delta = 1
        if delta is not None and target is not None:
            raise Exception("Of delta and target, only one parameter can be specified")
        if direction == SvNurbsSurface.U:
            degree = self.get_degree_u()
        else:
            degree = self.get_degree_v()
        if delta is None:
            delta = target - degree
            if delta < 0:
                raise Exception(f"Surface already has degree {degree}, which is greater than target {target}")
        if delta == 0:
            return self

        implementation = self.get_nurbs_implementation()

        if direction == SvNurbsSurface.U:
            new_points = []
            new_weights = []
            new_u_degree = None
            for i in range(self.get_control_points().shape[1]):
                fixed_v_points = self.get_control_points()[:,i]
                fixed_v_weights = self.get_weights()[:,i]
                fixed_v_curve = SvNurbsMaths.build_curve(implementation,
                                    self.get_degree_u(), self.get_knotvector_u(),
                                    fixed_v_points, fixed_v_weights)
                fixed_v_curve = fixed_v_curve.elevate_degree(delta)
                fixed_v_knotvector = fixed_v_curve.get_knotvector()
                new_u_degree = fixed_v_curve.get_degree()
                fixed_v_points = fixed_v_curve.get_control_points()
                fixed_v_weights = fixed_v_curve.get_weights()
                new_points.append(fixed_v_points)
                new_weights.append(fixed_v_weights)

            new_points = np.transpose(np.array(new_points), axes=(1,0,2))
            new_weights = np.array(new_weights).T

            return SvNurbsSurface.build(self.get_nurbs_implementation(),
                    new_u_degree, self.get_degree_v(),
                    fixed_v_knotvector, self.get_knotvector_v(),
                    new_points, new_weights)

        elif direction == SvNurbsSurface.V:
            new_points = []
            new_weights = []
            new_v_degree = None
            for i in range(self.get_control_points().shape[0]):
                fixed_u_points = self.get_control_points()[i,:]
                fixed_u_weights = self.get_weights()[i,:]
                fixed_u_curve = SvNurbsMaths.build_curve(implementation,
                                    self.get_degree_v(), self.get_knotvector_v(),
                                    fixed_u_points, fixed_u_weights)
                fixed_u_curve = fixed_u_curve.elevate_degree(delta)
                fixed_u_knotvector = fixed_u_curve.get_knotvector()
                new_v_degree = fixed_u_curve.get_degree()
                fixed_u_points = fixed_u_curve.get_control_points()
                fixed_u_weights = fixed_u_curve.get_weights()
                new_points.append(fixed_u_points)
                new_weights.append(fixed_u_weights)

            new_points = np.array(new_points)
            new_weights = np.array(new_weights)

            return SvNurbsSurface.build(implementation,
                    self.get_degree_u(), new_v_degree,
                    self.get_knotvector_u(), fixed_u_knotvector,
                    new_points, new_weights)

    def reduce_degree(self, direction, delta=None, target=None, tolerance=1e-6, logger=None):
        if delta is None and target is None:
            delta = 1
        if delta is not None and target is not None:
            raise Exception("Of delta and target, only one parameter can be specified")
        if direction == SvNurbsSurface.U:
            degree = self.get_degree_u()
        else:
            degree = self.get_degree_v()
        if delta is None:
            delta = degree - target
            if delta < 0:
                raise Exception(f"Surface already has degree {degree}, which is less than target {target}")
        if delta == 0:
            return self

        if logger is None:
            logger = getLogger()

        implementation = self.get_nurbs_implementation()

        if direction == SvNurbsSurface.U:
            new_points = []
            new_weights = []
            new_u_degree = None
            remaining_tolerance = tolerance
            max_error = 0.0
            for i in range(self.get_control_points().shape[1]):
                fixed_v_points = self.get_control_points()[:,i]
                fixed_v_weights = self.get_weights()[:,i]
                fixed_v_curve = SvNurbsMaths.build_curve(implementation,
                                    self.get_degree_u(), self.get_knotvector_u(),
                                    fixed_v_points, fixed_v_weights)
                try:
                    fixed_v_curve, error = fixed_v_curve.reduce_degree(delta=delta, tolerance=remaining_tolerance, return_error=True, logger=logger)
                except CantReduceDegreeException as e:
                    raise CantReduceDegreeException(f"At parallel #{i}: {e}") from e
                max_error = max(max_error, error)
                fixed_v_knotvector = fixed_v_curve.get_knotvector()
                new_u_degree = fixed_v_curve.get_degree()
                fixed_v_points = fixed_v_curve.get_control_points()
                fixed_v_weights = fixed_v_curve.get_weights()
                new_points.append(fixed_v_points)
                new_weights.append(fixed_v_weights)

            new_points = np.transpose(np.array(new_points), axes=(1,0,2))
            new_weights = np.array(new_weights).T

            logger.debug(f"Surface degree reduction error: {max_error}")

            return SvNurbsSurface.build(self.get_nurbs_implementation(),
                    new_u_degree, self.get_degree_v(),
                    fixed_v_knotvector, self.get_knotvector_v(),
                    new_points, new_weights)

        elif direction == SvNurbsSurface.V:
            new_points = []
            new_weights = []
            new_v_degree = None
            remaining_tolerance = tolerance
            max_error = 0.0
            for i in range(self.get_control_points().shape[0]):
                fixed_u_points = self.get_control_points()[i,:]
                fixed_u_weights = self.get_weights()[i,:]
                fixed_u_curve = SvNurbsMaths.build_curve(implementation,
                                    self.get_degree_v(), self.get_knotvector_v(),
                                    fixed_u_points, fixed_u_weights)
                try:
                    fixed_u_curve, error = fixed_u_curve.reduce_degree(delta=delta, tolerance=remaining_tolerance, return_error=True, logger=logger)
                except CantReduceDegreeException as e:
                    raise CantReduceDegreeException(f"At parallel #{i}: {e}") from e
                max_error = max(max_error, error)
                fixed_u_knotvector = fixed_u_curve.get_knotvector()
                new_v_degree = fixed_u_curve.get_degree()
                fixed_u_points = fixed_u_curve.get_control_points()
                fixed_u_weights = fixed_u_curve.get_weights()
                new_points.append(fixed_u_points)
                new_weights.append(fixed_u_weights)

            new_points = np.array(new_points)
            new_weights = np.array(new_weights)

            logger.debug(f"Surface degree reduction error: {max_error}")

            return SvNurbsSurface.build(implementation,
                    self.get_degree_u(), new_v_degree,
                    self.get_knotvector_u(), fixed_u_knotvector,
                    new_points, new_weights)

    def cut_u(self, u):
        u_min, u_max = self.get_u_min(), self.get_u_max()

        if u <= u_min:
            return None, self
        if u >= u_max:
            return self, None

        knotvector = self.get_knotvector_u()
        current_multiplicity = sv_knotvector.find_multiplicity(knotvector, u)
        to_add = self.get_degree_u() - current_multiplicity
        surface = self.insert_knot('U', u, count=to_add)
        knot_span = np.searchsorted(knotvector, u)

        us = np.full((self.get_degree_u()+1,), u)
        knotvector1 = np.concatenate((surface.get_knotvector_u()[:knot_span], us))
        knotvector2 = np.insert(surface.get_knotvector_u()[knot_span:], 0, u)

        control_points_1 = surface.get_control_points()[:knot_span, :]
        control_points_2 = surface.get_control_points()[knot_span-1:, :]
        weights_1 = surface.get_weights()[:knot_span, :]
        weights_2 = surface.get_weights()[knot_span-1:, :]

        surface1 = self.copy(knotvector_u=knotvector1, weights=weights_1, control_points=control_points_1)
        surface2 = self.copy(knotvector_u=knotvector2, weights=weights_2, control_points=control_points_2)

        return surface1, surface2

    def cut_v(self, v):
        v_min, v_max = self.get_v_min(), self.get_v_max()

        if v <= v_min:
            return None, self
        if v >= v_max:
            return self, None

        current_multiplicity = sv_knotvector.find_multiplicity(self.get_knotvector_v(), v)
        to_add = self.get_degree_v() - current_multiplicity
        surface = self.insert_knot('V', v, count=to_add)
        m,n,_ = surface.get_control_points().shape
        knot_span = sv_knotvector.find_span(surface.get_knotvector_v(), n, v) - 1
        #knot_span = np.searchsorted(surface.get_knotvector_v(), v)#, side='right')-1

        vs = np.full((self.get_degree_v()+1,), v)
        knotvector1 = np.concatenate((surface.get_knotvector_v()[:knot_span], vs))
        knotvector2 = np.insert(surface.get_knotvector_v()[knot_span:], 0, v)

        control_points_1 = surface.get_control_points()[:, :knot_span]
        control_points_2 = surface.get_control_points()[:, knot_span-1:]
        weights_1 = surface.get_weights()[:, :knot_span]
        weights_2 = surface.get_weights()[:, knot_span-1:]

        surface1 = self.copy(knotvector_v=knotvector1, weights=weights_1, control_points=control_points_1)
        surface2 = self.copy(knotvector_v=knotvector2, weights=weights_2, control_points=control_points_2)

        return surface1, surface2

    def split_at(self, direction, parameter):
        if direction == SvNurbsSurface.U:
            return self.cut_u(parameter)
        elif direction == SvNurbsSurface.V:
            return self.cut_v(parameter)
        else:
            raise Exception("Unsupported direction")

    def cut_slice(self, direction, p_min, p_max):
        _, rest = self.split_at(direction, p_min)
        if rest is None:
            return None
        result, _ = rest.split_at(direction, p_max)
        return result

    def _concat_u(self, surface2, tolerance=1e-6):
        surface1 = self
        surface2 = SvNurbsSurface.get(surface2)
        if surface2 is None:
            raise UnsupportedSurfaceTypeException("second surface is not NURBS")

        if surface1.get_control_points().shape[1] != surface2.get_control_points().shape[1]:
            # TODO: try to unify knots first?
            raise UnsupportedSurfaceTypeException("number of control points along V direction does not match")

        p1, p2 = surface1.get_degree_u(), surface2.get_degree_u()
        if p1 > p2:
            surface2 = surface2.elevate_degree('U', delta = p1 - p2)
        elif p2 > p1:
            surface1 = surface1.elevate_degree('U', delta = p2 - p1)

        cps1 = surface1.get_control_points()[-1,:]
        cps2 = surface2.get_control_points()[0,:]
        dpts = np.linalg.norm(cps1 - cps2, axis=0)
        if (dpts > tolerance).any():
            raise UnsupportedSurfaceTypeException("Boundary control points do not match")

        ws1 = surface1.get_weights()[-1,:]
        ws2 = surface2.get_weights()[0,:]
        if (np.abs(ws1 - ws2) > tolerance).any():
            raise UnsupportedSurfaceTypeException("Weights at bounds do not match")

        p = surface1.get_degree_u()

        kv1 = surface1.get_knotvector_u()
        kv2 = surface2.get_knotvector_u()
        kv1_end_multiplicity = sv_knotvector.to_multiplicity(kv1)[-1][1]
        kv2_start_multiplicity = sv_knotvector.to_multiplicity(kv2)[0][1]
        if kv1_end_multiplicity != p+1:
            raise UnsupportedSurfaceTypeException(f"End knot multiplicity of the first surface ({kv1_end_multiplicity}) is not equal to degree+1 ({p+1})")
        if kv2_start_multiplicity != p+1:
            raise UnsupportedSurfaceTypeException(f"Start knot multiplicity of the second surface ({kv2_start_multiplicity}) is not equal to degree+1 ({p+1})")

        knotvector = sv_knotvector.concatenate(kv1, kv2, join_multiplicity=p)

        weights = np.concatenate((surface1.get_weights(), surface2.get_weights()[1:]))
        control_points = np.concatenate((surface1.get_control_points(), surface2.get_control_points()[1:]))

        result = surface1.copy(knotvector_u = knotvector,
                    control_points = control_points,
                    weights = weights)
        return result

    def _concat_v(self, surface2, tolerance=1e-6):
        surface1 = self
        surface2 = SvNurbsSurface.get(surface2)
        if surface2 is None:
            raise UnsupportedSurfaceTypeException("second surface is not NURBS")

        if surface1.get_control_points().shape[0] != surface2.get_control_points().shape[0]:
            # TODO: try to unify knots first?
            raise UnsupportedSurfaceTypeException("number of control points along U direction does not match")

        p1, p2 = surface1.get_degree_v(), surface2.get_degree_v()
        if p1 > p2:
            surface2 = surface2.elevate_degree('V', delta = p1 - p2)
        elif p2 > p1:
            surface1 = surface1.elevate_degree('V', delta = p2 - p1)
        cps1 = surface1.get_control_points()[:,-1]
        cps2 = surface2.get_control_points()[:,0]
        dpts = np.linalg.norm(cps1 - cps2, axis=0)
        if (dpts > tolerance).any():
            raise UnsupportedSurfaceTypeException("Boundary control points do not match")

        ws1 = surface1.get_weights()[:,-1]
        ws2 = surface2.get_weights()[:,0]
        if (np.abs(ws1 - ws2) > tolerance).any():
            raise UnsupportedSurfaceTypeException("Weights at bounds do not match")

        p = surface1.get_degree_v()

        kv1 = surface1.get_knotvector_v()
        kv2 = surface2.get_knotvector_v()
        kv1_end_multiplicity = sv_knotvector.to_multiplicity(kv1)[-1][1]
        kv2_start_multiplicity = sv_knotvector.to_multiplicity(kv2)[0][1]
        if kv1_end_multiplicity != p+1:
            raise UnsupportedSurfaceTypeException(f"End knot multiplicity of the first surface ({kv1_end_multiplicity}) is not equal to degree+1 ({p+1})")
        if kv2_start_multiplicity != p+1:
            raise UnsupportedSurfaceTypeException(f"Start knot multiplicity of the second surface ({kv2_start_multiplicity}) is not equal to degree+1 ({p+1})")

        knotvector = sv_knotvector.concatenate(kv1, kv2, join_multiplicity=p)

        weights = np.concatenate((surface1.get_weights(), surface2.get_weights()[:,1:]), axis=1)
        control_points = np.concatenate((surface1.get_control_points(), surface2.get_control_points()[:,1:]), axis=1)

        result = surface1.copy(knotvector_v = knotvector,
                    control_points = control_points,
                    weights = weights)
        return result

    def concatenate(self, direction, surface2, tolerance=1e-6):
        if direction == SvNurbsSurface.U:
            return self._concat_u(surface2, tolerance)
        elif direction == SvNurbsSurface.V:
            return self._concat_v(surface2, tolerance)
        else:
            raise Exception("Unsupported direction")

class SvGeomdlSurface(SvNurbsSurface):
    def __init__(self, surface):
        self.surface = surface
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)
        self.__description__ = f"Geomdl NURBS (degree={surface.degree_u}x{surface.degree_v}, pts={len(surface.ctrlpts2d)}x{len(surface.ctrlpts2d[0])})"

    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsSurface.GEOMDL

    def insert_knot(self, direction, parameter, count=1, if_possible=False):
        if direction == SvNurbsSurface.U:
            uv = [parameter, None]
            counts = [count, 0]
        elif direction == SvNurbsSurface.V:
            uv = [None, parameter]
            counts = [0, count]
        surface = operations.insert_knot(self.surface, uv, counts)
        return SvGeomdlSurface(surface)

    def remove_knot(self, direction, parameter, count=1, if_possible=False, tolerance=None):
        if direction == SvNurbsSurface.U:
            orig_kv = self.get_knotvector_u()
            uv = [parameter, None]
            counts = [count, 0]
        elif direction == SvNurbsSurface.V:
            orig_kv = self.get_knotvector_v()
            uv = [None, parameter]
            counts = [0, count]
        orig_multiplicity = sv_knotvector.find_multiplicity(orig_kv, parameter)

        surface = operations.remove_knot(self.surface, uv, counts)

        if direction == SvNurbsSurface.U:
            new_kv = self.get_knotvector_u()
        elif direction == SvNurbsSurface.V:
            new_kv = self.get_knotvector_v()

        new_multiplicity = sv_knotvector.find_multiplicity(new_kv, parameter)

        if not if_possible and (orig_multiplicity - new_multiplicity < count):
            raise CantRemoveKnotException(f"Asked to remove knot {direction}={parameter} {count} times, but could remove it only {orig_multiplicity-new_multiplicity} times")

        return SvGeomdlSurface(surface)

    def get_degree_u(self):
        return self.surface.degree_u

    def get_degree_v(self):
        return self.surface.degree_v

    def get_knotvector_u(self):
        return np.array(self.surface.knotvector_u)

    def get_knotvector_v(self):
        return np.array(self.surface.knotvector_v)

    def get_control_points(self):
        pts = []
        for row in self.surface.ctrlpts2d:
            new_row = []
            for point in row:
                if len(point) == 4:
                    x,y,z,w = point
                    new_point = (x/w, y/w, z/w)
                else:
                    new_point = point
                new_row.append(new_point)
            pts.append(new_row)
        return np.array(pts)

    def get_weights(self):
        if isinstance(self.surface, NURBS.Surface):
            weights = [[pt[3] for pt in row] for row in self.surface.ctrlpts2d]
        else:
            weights = [[1.0 for pt in row] for row in self.surface.ctrlpts2d]
        return np.array(weights)

    @classmethod
    def build_geomdl(cls, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights, normalize_knots=False):

        def convert_row(verts_row, weights_row):
            return [(x*w, y*w, z*w, w) for (x,y,z), w in zip(verts_row, weights_row)]

        if weights is None:
            surf = BSpline.Surface(normalize_kv = normalize_knots)
        else:
            surf = NURBS.Surface(normalize_kv = normalize_knots)
        surf.degree_u = degree_u
        surf.degree_v = degree_v
        if weights is None:
            ctrlpts = control_points
        else:
            ctrlpts = list(map(convert_row, control_points, weights))
        surf.ctrlpts2d = ctrlpts
        surf.knotvector_u = knotvector_u
        surf.knotvector_v = knotvector_v

        result = SvGeomdlSurface(surf)
        result.u_bounds = surf.knotvector_u[0], surf.knotvector_u[-1]
        result.v_bounds = surf.knotvector_v[0], surf.knotvector_v[-1]
        return result

    @classmethod
    def from_any_nurbs(cls, surface):
        if not isinstance(surface, SvNurbsSurface):
            raise TypeError("Invalid surface")
        if isinstance(surface, SvGeomdlSurface):
            return surface
        return SvGeomdlSurface.build_geomdl(surface.get_degree_u(), surface.get_degree_v(),
                    surface.get_knotvector_u(), surface.get_knotvector_v(),
                    surface.get_control_points(),
                    surface.get_weights())

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        return SvGeomdlSurface.build_geomdl(degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights, normalize_knots)

    def get_input_orientation(self):
        return 'Z'

    def get_coord_mode(self):
        return 'UV'

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

    @property
    def has_input_matrix(self):
        return False

    def evaluate(self, u, v):
        vert = self.surface.evaluate_single((u, v))
        return np.array(vert)

    def evaluate_array(self, us, vs):
        uv_coords = list(zip(list(us), list(vs)))
        verts = self.surface.evaluate_list(uv_coords)
        verts = np.array(verts)
        return verts

    def iso_curve(self, fixed_direction, param, flip=False):
        if self.surface.rational:
            raise UnsupportedSurfaceTypeException("iso_curve() is not supported for rational Geomdl surfaces yet")
        controls = self.get_control_points()
        weights = self.get_weights()
        k_u,k_v = weights.shape
        if fixed_direction == SvNurbsSurface.U:
            q_curves = [SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                            self.get_degree_u(),
                            self.get_knotvector_u(),
                            controls[:,j], weights[:,j]) for j in range(k_v)]
            q_controls = [q_curve.evaluate(param) for q_curve in q_curves]
            q_weights = np.ones((k_v,))
            curve = SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                    self.get_degree_v(),
                    self.get_knotvector_v(),
                    q_controls, q_weights)
            if flip:
                return curve.reverse()
            else:
                return curve
        elif fixed_direction == SvNurbsSurface.V:
            q_curves = [SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                            self.get_degree_v(),
                            self.get_knotvector_v(),
                            controls[i,:], weights[i,:]) for i in range(k_u)]
            q_controls = [q_curve.evaluate(param) for q_curve in q_curves]
            q_weights = np.ones((k_u,))
            curve = SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                    self.get_degree_u(),
                    self.get_knotvector_u(),
                    q_controls, q_weights)
            if flip:
                return curve.reverse()
            else:
                return curve
    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        if geomdl is not None:
            uv_coords = list(zip(list(us), list(vs)))
            spline_normals = np.array( operations.normal(self.surface, uv_coords) )[:,1,:]
            return spline_normals

    def derivatives_list(self, us, vs):
        result = []
        for u, v in zip(us, vs):
            ds = self.surface.derivatives(u, v, order=2)
            result.append(ds)
        return np.array(result)

    def curvature_calculator(self, us, vs, order=True):
        surf_vertices = self.evaluate_array(us, vs)

        derivatives = self.derivatives_list(us, vs)
        # derivatives[i][j][k] = derivative w.r.t U j times, w.r.t. V k times, at i'th pair of (u, v)
        fu = derivatives[:,1,0]
        fv = derivatives[:,0,1]

        normal = np.cross(fu, fv)
        norm = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = normal / norm

        fuu = derivatives[:,2,0]
        fvv = derivatives[:,0,2]
        fuv = derivatives[:,1,1]

        nuu = (fuu * normal).sum(axis=1)
        nvv = (fvv * normal).sum(axis=1)
        nuv = (fuv * normal).sum(axis=1)

        duu = np.linalg.norm(fu, axis=1) **2
        dvv = np.linalg.norm(fv, axis=1) **2
        duv = (fu * fv).sum(axis=1)

        calc = SurfaceCurvatureCalculator(us, vs, order=order)
        calc.set(surf_vertices, normal, fu, fv, duu, dvv, duv, nuu, nvv, nuv)
        return calc

    def derivatives_data_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        derivatives = self.derivatives_list(us, vs)
        # derivatives[i][j][k] = derivative w.r.t U j times, w.r.t. V k times, at i'th pair of (u, v)
        du = derivatives[:,1,0]
        dv = derivatives[:,0,1]
        return SurfaceDerivativesData(surf_vertices, du, dv)

class SvNativeNurbsSurface(SvNurbsSurface):
    def __init__(self, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights, normalize_knots=False):
        self.degree_u = degree_u
        self.degree_v = degree_v
        self.knotvector_u = np.array(knotvector_u)
        self.knotvector_v = np.array(knotvector_v)
        if normalize_knots:
            self.knotvector_u = sv_knotvector.normalize(self.knotvector_u)
            self.knotvector_v = sv_knotvector.normalize(self.knotvector_v)
        self.control_points = np.array(control_points)
        c_ku, c_kv, _ = self.control_points.shape
        if weights is None:
            self.weights = weights = np.ones((c_ku, c_kv))
        else:
            self.weights = np.array(weights)
            w_ku, w_kv = self.weights.shape
            if c_ku != w_ku or c_kv != w_kv:
                raise Exception(f"Shape of control_points ({c_ku}, {c_kv}) does not match to shape of weights ({w_ku}, {w_kv})")
        self.basis_u = SvNurbsBasisFunctions(knotvector_u)
        self.basis_v = SvNurbsBasisFunctions(knotvector_v)
        self.u_bounds = (self.knotvector_u.min(), self.knotvector_u.max())
        self.v_bounds = (self.knotvector_v.min(), self.knotvector_v.max())
        self.normal_delta = 0.0001
        self.__description__ = f"Native NURBS (degree={degree_u}x{degree_v}, pts={self.control_points.shape[0]}x{self.control_points.shape[1]})"

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        return SvNativeNurbsSurface(degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights, normalize_knots)

    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsSurface.NATIVE

    def insert_knot(self, direction, parameter, count=1, if_possible=False):
        def get_common_count(curves):
            if not if_possible:
                # in this case the first curve.rinsert() call which can't insert the knot
                # requested number of times will raise an exception, so we do not have to bother
                return count
            else:
                # curve.insert_knot() calls will not raise exceptions, so we have to
                # select the minimum number of possible knot insertions among all curves
                min_count = count
                for curve in curves:
                    orig_kv = curve.get_knotvector()
                    orig_multiplicity = sv_knotvector.find_multiplicity(orig_kv, parameter)
                    if (parameter == orig_kv[0]) or (parameter == orig_kv[-1]):
                        max_multiplicity = curve.get_degree()+1
                    else:
                        max_multiplicity = curve.get_degree()
                    max_delta = max_multiplicity - orig_multiplicity
                    min_count = min(min_count, max_delta)
                return min_count

        if direction == SvNurbsSurface.U:
            new_points = []
            new_weights = []
            new_u_degree = None
            fixed_v_curves = []

            for i in range(self.get_control_points().shape[1]):
                fixed_v_points = self.get_control_points()[:,i]
                fixed_v_weights = self.get_weights()[:,i]
                fixed_v_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                                    self.degree_u, self.knotvector_u,
                                    fixed_v_points, fixed_v_weights)
                fixed_v_curves.append(fixed_v_curve)

            common_count = get_common_count(fixed_v_curves)

            for fixed_v_curve in fixed_v_curves:
                fixed_v_curve = fixed_v_curve.insert_knot(parameter, common_count, if_possible)
                fixed_v_knotvector = fixed_v_curve.get_knotvector()
                new_u_degree = fixed_v_curve.get_degree()
                fixed_v_points = fixed_v_curve.get_control_points()
                fixed_v_weights = fixed_v_curve.get_weights()
                new_points.append(fixed_v_points)
                new_weights.append(fixed_v_weights)

            new_points = np.transpose(np.array(new_points), axes=(1,0,2))
            new_weights = np.array(new_weights).T

            return SvNativeNurbsSurface(new_u_degree, self.degree_v,
                    fixed_v_knotvector, self.knotvector_v,
                    new_points, new_weights)

        elif direction == SvNurbsSurface.V:
            new_points = []
            new_weights = []
            new_v_degree = None
            fixed_u_curves = []

            for i in range(self.get_control_points().shape[0]):
                fixed_u_points = self.get_control_points()[i,:]
                fixed_u_weights = self.get_weights()[i,:]
                fixed_u_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                                    self.degree_v, self.knotvector_v,
                                    fixed_u_points, fixed_u_weights)
                fixed_u_curves.append(fixed_u_curve)

            common_count = get_common_count(fixed_u_curves)

            for fixed_u_curve in fixed_u_curves:
                fixed_u_curve = fixed_u_curve.insert_knot(parameter, common_count, if_possible)
                fixed_u_knotvector = fixed_u_curve.get_knotvector()
                new_v_degree = fixed_u_curve.get_degree()
                fixed_u_points = fixed_u_curve.get_control_points()
                fixed_u_weights = fixed_u_curve.get_weights()
                new_points.append(fixed_u_points)
                new_weights.append(fixed_u_weights)

            new_points = np.array(new_points)
            new_weights = np.array(new_weights)

            return SvNativeNurbsSurface(self.degree_u, new_v_degree,
                    self.knotvector_u, fixed_u_knotvector,
                    new_points, new_weights)
        else:
            raise Exception("Unsupported direction")

    def remove_knot(self, direction, parameter, count=1, if_possible=False, tolerance=1e-6):
        def get_common_count(curves):
            if not if_possible:
                # in this case the first curve.remove_knot() call which can't remove the knot
                # requested number of times will raise an exception, so we do not have to bother
                return count
            else:
                # curve.remove_knot() calls will not raise exceptions, so we have to
                # select the minimum number of possible knot removals among all curves
                min_count = curves[0].get_degree()+1
                for curve in curves:
                    orig_kv = curve.get_knotvector()
                    orig_multiplicity = sv_knotvector.find_multiplicity(orig_kv, parameter)
                    tmp = curve.remove_knot(parameter, count, if_possible=True, tolerance=tolerance)
                    new_kv = tmp.get_knotvector()
                    new_multiplicity = sv_knotvector.find_multiplicity(new_kv, parameter)
                    delta = orig_multiplicity - new_multiplicity
                    min_count = min(min_count, delta)
                return min_count

        if direction == SvNurbsSurface.U:
            new_points = []
            new_weights = []
            new_u_degree = None
            fixed_v_curves = []
            for i in range(self.get_control_points().shape[1]):
                fixed_v_points = self.get_control_points()[:,i]
                fixed_v_weights = self.get_weights()[:,i]
                fixed_v_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                                    self.degree_u, self.knotvector_u,
                                    fixed_v_points, fixed_v_weights)
                fixed_v_curves.append(fixed_v_curve)
            
            common_count = get_common_count(fixed_v_curves)

            for fixed_v_curve in fixed_v_curves:
                fixed_v_curve = fixed_v_curve.remove_knot(parameter, common_count, if_possible=if_possible, tolerance=tolerance)
                fixed_v_knotvector = fixed_v_curve.get_knotvector()
                new_u_degree = fixed_v_curve.get_degree()
                fixed_v_points = fixed_v_curve.get_control_points()
                fixed_v_weights = fixed_v_curve.get_weights()
                new_points.append(fixed_v_points)
                new_weights.append(fixed_v_weights)

            new_points = np.transpose(np.array(new_points), axes=(1,0,2))
            new_weights = np.array(new_weights).T

            return SvNativeNurbsSurface(new_u_degree, self.degree_v,
                    fixed_v_knotvector, self.knotvector_v,
                    new_points, new_weights)

        elif direction == SvNurbsSurface.V:
            new_points = []
            new_weights = []
            new_v_degree = None
            fixed_u_curves = []
            for i in range(self.get_control_points().shape[0]):
                fixed_u_points = self.get_control_points()[i,:]
                fixed_u_weights = self.get_weights()[i,:]
                fixed_u_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                                    self.degree_v, self.knotvector_v,
                                    fixed_u_points, fixed_u_weights)
                fixed_u_curves.append(fixed_u_curve)

            common_count = get_common_count(fixed_u_curves)

            for fixed_u_curve in fixed_u_curves:
                fixed_u_curve = fixed_u_curve.remove_knot(parameter, common_count, if_possible=if_possible, tolerance=tolerance)
                fixed_u_knotvector = fixed_u_curve.get_knotvector()
                new_v_degree = fixed_u_curve.get_degree()
                fixed_u_points = fixed_u_curve.get_control_points()
                fixed_u_weights = fixed_u_curve.get_weights()
                new_points.append(fixed_u_points)
                new_weights.append(fixed_u_weights)

            new_points = np.array(new_points)
            new_weights = np.array(new_weights)

            return SvNativeNurbsSurface(self.degree_u, new_v_degree,
                    self.knotvector_u, fixed_u_knotvector,
                    new_points, new_weights)
        else:
            raise Exception("Unsupported direction")

    def get_degree_u(self):
        return self.degree_u

    def get_degree_v(self):
        return self.degree_v

    def get_knotvector_u(self):
        return self.knotvector_u

    def get_knotvector_v(self):
        return self.knotvector_v

    def get_control_points(self):
        return self.control_points

    def get_weights(self):
        return self.weights

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    def evaluate(self, u, v):
        return self.evaluate_array(np.array([u]), np.array([v]))[0]

    def fraction(self, deriv_order_u, deriv_order_v, us, vs):
        pu = self.degree_u
        pv = self.degree_v
        ku, kv, _ = self.control_points.shape
        nsu = np.array([self.basis_u.derivative(i, pu, deriv_order_u)(us) for i in range(ku)]) # (ku, n)
        nsv = np.array([self.basis_v.derivative(i, pv, deriv_order_v)(vs) for i in range(kv)]) # (kv, n)
        nsu = np.transpose(nsu[np.newaxis], axes=(1,0,2)) # (ku, 1, n)
        nsv = nsv[np.newaxis] # (1, kv, n)
        ns = nsu * nsv # (ku, kv, n)
        weights = np.transpose(self.weights[np.newaxis], axes=(1,2,0)) # (ku, kv, 1)
        coeffs = ns * weights # (ku, kv, n)
        coeffs = np.transpose(coeffs[np.newaxis], axes=(3,1,2,0)) # (n,ku,kv,1)
        controls = self.control_points # (ku,kv,3)

        numerator = coeffs * controls # (n,ku,kv,3)
        numerator = numerator.sum(axis=1).sum(axis=1) # (n,3)
        denominator = coeffs.sum(axis=1).sum(axis=1)

        return numerator, denominator

    def evaluate_array(self, us, vs):
        numerator, denominator = self.fraction(0, 0, us, vs)
        return nurbs_divide(numerator, denominator)

    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        numerator, denominator = self.fraction(0, 0, us, vs)
        surface = nurbs_divide(numerator, denominator)
        numerator_u, denominator_u = self.fraction(1, 0, us, vs)
        numerator_v, denominator_v = self.fraction(0, 1, us, vs)
        surface_u = nurbs_divide(numerator_u - surface*denominator_u, denominator)
        surface_v = nurbs_divide(numerator_v - surface*denominator_v, denominator)
        normal = np.cross(surface_u, surface_v)
        n = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = nurbs_divide(normal, n)
        return normal

    def iso_curve(self, fixed_direction, param, flip=False):
        controls = self.get_control_points()
        weights = self.get_weights()
        k_u,k_v = weights.shape
        if fixed_direction == SvNurbsSurface.U:
            q_curves = [SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                            self.get_degree_u(),
                            self.get_knotvector_u(),
                            controls[:,j], weights[:,j]) for j in range(k_v)]
            q_controls = [q_curve.evaluate(param) for q_curve in q_curves]
            q_weights = [q_curve.fraction_single(0, param)[1] for q_curve in q_curves]
            curve = SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                    self.get_degree_v(),
                    self.get_knotvector_v(),
                    q_controls, q_weights)
            if flip:
                return curve.reverse()
            else:
                return curve
        elif fixed_direction == SvNurbsSurface.V:
            q_curves = [SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                            self.get_degree_v(),
                            self.get_knotvector_v(),
                            controls[i,:], weights[i,:]) for i in range(k_u)]
            q_controls = [q_curve.evaluate(param) for q_curve in q_curves]
            q_weights = [q_curve.fraction_single(0, param)[1] for q_curve in q_curves]
            curve = SvNurbsMaths.build_curve(self.get_nurbs_implementation(),
                    self.get_degree_u(),
                    self.get_knotvector_u(),
                    q_controls, q_weights)
            if flip:
                return curve.reverse()
            else:
                return curve

    def derivatives_data_array(self, us, vs):
        numerator, denominator = self.fraction(0, 0, us, vs)
        surface = nurbs_divide(numerator, denominator)
        numerator_u, denominator_u = self.fraction(1, 0, us, vs)
        numerator_v, denominator_v = self.fraction(0, 1, us, vs)
        surface_u = (numerator_u - surface*denominator_u) / denominator
        surface_v = (numerator_v - surface*denominator_v) / denominator
        return SurfaceDerivativesData(surface, surface_u, surface_v)

    def curvature_calculator(self, us, vs, order=True):
    
        numerator, denominator = self.fraction(0, 0, us, vs)
        surface = nurbs_divide(numerator, denominator)
        numerator_u, denominator_u = self.fraction(1, 0, us, vs)
        numerator_v, denominator_v = self.fraction(0, 1, us, vs)
        surface_u = (numerator_u - surface*denominator_u) / denominator
        surface_v = (numerator_v - surface*denominator_v) / denominator

        normal = np.cross(surface_u, surface_v)
        n = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = normal / n

        numerator_uu, denominator_uu = self.fraction(2, 0, us, vs)
        surface_uu = (numerator_uu - 2*surface_u*denominator_u - surface*denominator_uu) / denominator
        numerator_vv, denominator_vv = self.fraction(0, 2, us, vs)
        surface_vv = (numerator_vv - 2*surface_v*denominator_v - surface*denominator_vv) / denominator

        numerator_uv, denominator_uv = self.fraction(1, 1, us, vs)
        surface_uv = (numerator_uv - surface_v*denominator_u - surface_u*denominator_v - surface*denominator_uv) / denominator

        nuu = (surface_uu * normal).sum(axis=1)
        nvv = (surface_vv * normal).sum(axis=1)
        nuv = (surface_uv * normal).sum(axis=1)

        duu = np.linalg.norm(surface_u, axis=1) **2
        dvv = np.linalg.norm(surface_v, axis=1) **2
        duv = (surface_u * surface_v).sum(axis=1)

        calc = SurfaceCurvatureCalculator(us, vs, order=order)
        calc.set(surface, normal, surface_u, surface_v, duu, dvv, duv, nuu, nvv, nuv)
        return calc

def build_from_curves(curves, degree_u = None, implementation = SvNurbsSurface.NATIVE):
    curves = unify_curves(curves)
    degree_v = curves[0].get_degree()
    if degree_u is None:
        degree_u = degree_v
    control_points = [curve.get_control_points() for curve in curves]
    control_points = np.array(control_points)
    weights = np.array([curve.get_weights() for curve in curves])
    knotvector_u = sv_knotvector.generate(degree_u, len(curves))
    #knotvector_v = curves[0].get_knotvector()
    knotvector_v = sv_knotvector.average([curve.get_knotvector() for curve in curves])

    surface = SvNurbsSurface.build(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)

    return curves, surface

def simple_loft(curves, degree_v = None, knots_u = 'UNIFY', knotvector_accuracy=6, metric='DISTANCE', tknots=None, implementation=SvNurbsSurface.NATIVE, logger = None):
    """
    Loft between given NURBS curves (a.k.a skinning).

    inputs:
    * degree_v - degree of resulting surface along V parameter; by default - use the same degree as provided curves
    * knots_u - one of:
        - 'UNIFY' - unify knotvectors of given curves by inserting additional knots
        - 'AVERAGE' - average knotvectors of given curves; this will work only if all curves have the same number of control points
    * metric - metric for interpolation; most useful are 'DISTANCE' and 'CENTRIPETAL'
    * implementation - NURBS maths implementation

    output: tuple:
        * list of curves - input curves after unification
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if knots_u not in {'UNIFY', 'AVERAGE'}:
        raise Exception(f"Unsupported knots_u option: {knots_u}")
    if logger is None:
        logger = getLogger()
    curves = unify_curves_degree(curves)
    if knots_u == 'UNIFY':
        curves = unify_curves(curves, accuracy=knotvector_accuracy)
    else:
        kvs = [len(curve.get_control_points()) for curve in curves]
        max_kv, min_kv = max(kvs), min(kvs)
        if max_kv != min_kv:
            raise Exception(f"U knotvector averaging is not applicable: Curves have different number of control points: {kvs}")

    degree_u = curves[0].get_degree()
    if degree_v is None:
        degree_v = degree_u

    if degree_v > len(curves):
        raise Exception(f"V degree ({degree_v}) must be not greater than number of curves ({len(curves)}) minus 1")

    src_points = [curve.get_homogenous_control_points() for curve in curves]
    #print("P", [p.shape for p in src_points])
#     lens = [len(pts) for pts in src_points]
#     max_len, min_len = max(lens), min(lens)
#     if max_len != min_len:
#         raise Exception(f"Unify error: curves have different number of control points: {lens}")

    #print("Src:", src_points)
    src_points = np.array(src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))

    if tknots is None:
        tknots_vs = [Spline.create_knots(src_points[i,:], metric=metric) for i in range(src_points.shape[0])]
        tknots_vs = np.array(tknots_vs)
        tknots_v = np.mean(tknots_vs, axis=0)
    else:
        tknots_v = tknots

    v_curves = [SvNurbsMaths.interpolate_curve(implementation, degree_v, points, metric=metric, tknots=tknots_v, logger=logger) for points in src_points]
    control_points = [curve.get_homogenous_control_points() for curve in v_curves]
    control_points = np.array(control_points)
    #weights = [curve.get_weights() for curve in v_curves]
    #weights = np.array([curve.get_weights() for curve in curves]).T
    n,m,ndim = control_points.shape
    control_points = control_points.reshape((n*m, ndim))
    control_points, weights = from_homogenous(control_points)
    control_points = control_points.reshape((n,m,3))
    weights = weights.reshape((n,m))

    mean_v_vector = control_points.mean(axis=0)
    #tknots_v = Spline.create_knots(mean_v_vector, metric=metric)
    knotvector_v = sv_knotvector.from_tknots(degree_v, tknots_v)
    if knots_u == 'UNIFY':
        knotvector_u = curves[0].get_knotvector()
    else:
        knotvectors = np.array([curve.get_knotvector() for curve in curves])
        knotvector_u = knotvectors.mean(axis=0)
    
    surface = SvNurbsSurface.build(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    surface.u_bounds = curves[0].get_u_bounds()
    return curves, v_curves, surface

def generic_loft_with_tangents(curves, tangents_calculator, degree_v = 3,
        metric = 'DISTANCE', tknots=None,
        knotvector_accuracy = 6,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):

    if logger is None:
        logger = getLogger()

    n_curves = len(curves)
    curves = unify_curves_degree(curves)
    curves = unify_curves(curves, accuracy=knotvector_accuracy)
    degree_u = curves[0].get_degree()

    src_points = [curve.get_homogenous_control_points() for curve in curves]
    src_points = np.array(src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))

    tknots_vs = [Spline.create_knots(src_points[i,:], metric=metric) for i in range(n_curves)]
    tknots_vs = np.array(tknots_vs)
    tknots_v = np.mean(tknots_vs, axis=0)

    tangents = tangents_calculator(tknots_v, curves, src_points)

    n,m,ndim = tangents.shape
    tangents = np.concatenate((tangents, np.zeros((n,m,1))), axis=2)

    v_curves = [interpolate_nurbs_curve_with_tangents(degree_v, points, tangents, tknots=tknots_v, implementation=implementation, logger=logger) for points, tangents in zip(src_points, tangents)]
    control_points = [curve.get_homogenous_control_points() for curve in v_curves]
    control_points = np.array(control_points)
    n,m,ndim = control_points.shape
    control_points = control_points.reshape((n*m, ndim))
    control_points, weights = from_homogenous(control_points)
    control_points = control_points.reshape((n,m,3))
    weights = weights.reshape((n,m))
    
    knotvector_u = curves[0].get_knotvector()
    knotvector_v = v_curves[0].get_knotvector()
    
    surface = SvNurbsSurface.build(SvNurbsSurface.NATIVE,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights)
    return surface

def loft_by_binormals(curves, degree_v = 3,
        binormals_scale = 1.0,
        metric = 'DISTANCE', tknots=None,
        knotvector_accuracy = 6,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):

    def calc_tangents(vs, u_curves, src_points):
        greville_ts = [u_curve.calc_greville_ts() for u_curve in u_curves]
        binormals = [u_curve.binormal_array(ts) for u_curve, ts in zip(u_curves, greville_ts)]
        binormals = np.array(binormals)
        binormals = np.transpose(binormals, axes=(1,0,2))

        greville_pts = [curve.evaluate_array(ts) for curve, ts in zip(u_curves, greville_ts)]
        greville_pts = np.array(greville_pts)
        greville_dpts = greville_pts[1:] - greville_pts[:-1]
        greville_dpts_mean = np.mean(greville_dpts, axis=0)
        greville_dpts = np.concatenate((greville_dpts, [greville_dpts_mean]))
        binormal_lengths = np.linalg.norm(greville_dpts, axis=2, keepdims = True)
        binormal_lengths = np.transpose(binormal_lengths, axes=(1,0,2))
        
        cpts_mean_by_curve = np.mean(src_points, axis=0)
        cpts_direction = np.mean(cpts_mean_by_curve[1:] - cpts_mean_by_curve[:-1], axis=0)[:3]
        
        binormals *= binormal_lengths * binormals_scale / 3.0

        r = np.sum(binormals * cpts_direction, axis=2)
        bad = (r < 0)
        binormals[bad] = - binormals[bad]

        return binormals

    return generic_loft_with_tangents(curves, calc_tangents,
            degree_v = degree_v,
            metric = metric, tknots = tknots,
            knotvector_accuracy = knotvector_accuracy,
            implementation = implementation,
            logger = logger)

def loft_with_tangent_fields(curves, tangent_fields, degree_v = 3,
        metric = 'DISTANCE', tknots=None,
        knotvector_accuracy = 6,
        implementation = SvNurbsMaths.NATIVE,
        logger = None):

    def calc_tangents(vs, u_curves, src_points):
        tangents = [field.evaluate_array(curve.get_control_points()) for curve, field in zip(u_curves, tangent_fields)]
        tangents = np.array(tangents)
        tangents = np.transpose(tangents, axes=(2,0,1))
        return tangents

    return generic_loft_with_tangents(curves, calc_tangents,
            degree_v = degree_v,
            metric = metric, tknots = tknots,
            knotvector_accuracy = knotvector_accuracy,
            implementation = implementation,
            logger = logger)

def interpolate_nurbs_curves(curves, base_vs, target_vs,
        degree_v = None, knots_u = 'UNIFY',
        implementation = SvNurbsSurface.NATIVE,
        logger = None):
    """
    Interpolate many NURBS curves between a list of NURBS curves, by lofting.
    Inputs:
    * curves: list of SvNurbsCurve
    * base_vs: np.array of shape (M,) - T values corresponding to `curves'
        input. M must be equal to len(curves).
    * target_vs: np.array of shape (N,) - T values at which to calculate interpolated curves.
    * rest: arguments for simple_loft.
    Returns: list of SvNurbsCurve of length N.
    """
    min_v, max_v = min(base_vs), max(base_vs)
    # Place input curves along Z axis and loft between them
    vectors = np.array([(0,0,v) for v in base_vs])
    to_loft = [curve.transform(None, vector) for curve, vector in zip(curves, vectors)]
    #to_loft = curves
    tknots = (base_vs - min_v) / (max_v - min_v)
    _,_,lofted = simple_loft(to_loft,
                degree_v = degree_v, knots_u = knots_u,
                #metric = 'POINTS',
                tknots = tknots,
                implementation = implementation,
                logger = logger)

    rebased_vs = np.linspace(min_v, max_v, num=len(target_vs))
    iso_curves = [lofted.iso_curve(fixed_direction='V', param=v) for v in rebased_vs]
    # Calculate iso_curves of the lofted surface, and move them back along Z axis
    back_vectors = []
    for v in rebased_vs:
        back_vector = np.array([0, 0, -v])
        back_vectors.append(back_vector)

    return [curve.transform(None, back) for curve, back in zip(iso_curves, back_vectors)]

def interpolate_nurbs_surface(degree_u, degree_v, points, metric='DISTANCE', uknots=None, vknots=None, implementation = SvNurbsSurface.NATIVE, logger=None):
    points = np.asarray(points)
    n = len(points)
    m = len(points[0])

    if (uknots is None) != (vknots is None):
        raise Exception("uknots and vknots must be either both provided or both omitted")

    if logger is None:
        logger = getLogger()

    if uknots is None:
        knots = np.array([Spline.create_knots(points[i,:], metric=metric) for i in range(n)])
        uknots = knots.mean(axis=0)
    if vknots is None:
        knots = np.array([Spline.create_knots(points[:,j], metric=metric) for j in range(m)])
        vknots = knots.mean(axis=0)

    knotvector_u = sv_knotvector.from_tknots(degree_u, uknots)
    knotvector_v = sv_knotvector.from_tknots(degree_v, vknots)

    u_curves = [SvNurbsMaths.interpolate_curve(implementation, degree_u, points[i,:], tknots=uknots, logger=logger) for i in range(n)]
    u_curves_cpts = np.array([curve.get_control_points() for curve in u_curves])
    v_curves = [SvNurbsMaths.interpolate_curve(implementation, degree_v, u_curves_cpts[:,j], tknots=vknots, logger=logger) for j in range(m)]

    control_points = np.array([curve.get_control_points() for curve in v_curves])

    surface = SvNurbsSurface.build(implementation,
                degree_u, degree_v,
                knotvector_u, knotvector_v,
                control_points, weights=None)

    return surface

def nurbs_sweep_impl(path, profiles, ts, frame_calculator,
        knots_u = 'UNIFY',
        metric = 'DISTANCE',
        implementation = SvNurbsSurface.NATIVE,
        logger = None):
    """
    NURBS Sweep implementation.
    Interface of this function is not flexible, so you usually want to call `nurbs_sweep' instead.

    Inputs:
    * path: SvNurbsCurve
    * profiles: list of SvNurbsCurve
    * ts: T values along path which correspond to profiles. Number of ts must
        be equal to number of profiles.
    * frame_calculator: a function, which takes np.array((n,)) of T values and
        returns np.array((n, 3, 3)) of curve frames.
    * rest: arguments for simple_loft function.

    output: tuple:
        * list of curves - initial profile curves placed / rotated along the path curve
        * list of curves - interpolated profile curves
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if len(profiles) != len(ts):
        raise Exception(f"Number of profiles ({len(profiles)}) is not equal to number of T values ({len(ts)})")
    if len(ts) < 2:
        raise Exception("At least 2 profiles are required")

    path_points = path.evaluate_array(ts)
    frames = frame_calculator(ts)
    to_loft = []
    for profile, path_point, frame in zip(profiles, path_points, frames):
        profile = profile.transform(frame, path_point)
        #cpt = profile.evaluate(profile.get_u_bounds()[0])
        #profile = profile.transform(None, -cpt + path_point)
        to_loft.append(profile)

    unified_curves, v_curves, surface = simple_loft(to_loft, degree_v = path.get_degree(),
            knots_u = knots_u, metric = metric,
            implementation = implementation,
            logger = logger)
    return to_loft, unified_curves, v_curves, surface

def nurbs_sweep(path, profiles, ts, min_profiles, algorithm, knots_u = 'UNIFY', metric = 'DISTANCE', implementation = SvNurbsSurface.NATIVE, logger=None, **kwargs):
    """
    NURBS Sweep surface.
    
    Inputs:
    * path: SvNurbsCurve
    * profiles: list of SvNurbsCurve
    * ts: T values along path which correspond to profiles. Number of ts must
        be equal to number of profiles. If None, the function will calculate
        appropriate values automatically.
    * min_profiles: minimal number of (copies of) profile curves to be placed
        along the path: bigger number correspond to better precision, within
        certain limits. If min_profiles > len(profiles), additional profiles
        will be generated by interpolation (by lofting).
    * algorithm: rotation calculation algorithm: one of NONE, ZERO, FRENET,
        HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL, NORMAL_DIR.
    * knots_u: 'UNIFY' or 'AVERAGE'
    * metric: interpolation metric
    * implementation: surface implementation
    * kwargs: arguments for rotation calculation algorithm

    output: tuple:
        * list of curves - initial profile curves placed / rotated along the path curve
        * list of curves - interpolated profile curves
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if logger is None:
        logger = getLogger()

    n_profiles = len(profiles)
    have_ts = ts is not None and len(ts) > 0
    if have_ts and n_profiles != len(ts):
        raise Exception(f"Number of profiles ({n_profiles}) is not equal to number of T values ({len(ts)})")

    t_min, t_max = path.get_u_bounds()
    if not have_ts:
        ts = np.linspace(t_min, t_max, num=n_profiles)

    if n_profiles == 1:
        p = profiles[0]
        ts = np.linspace(t_min, t_max, num=min_profiles)
        profiles = [p] * min_profiles
    elif n_profiles == 2 and n_profiles < min_profiles:
        coeffs = np.linspace(0.0, 1.0, num=min_profiles)
        p0, p1 = profiles
        profiles = [p0.lerp_to(p1, coeff) for coeff in coeffs]
        ts = np.linspace(t_min, t_max, num=min_profiles)
    elif n_profiles < min_profiles:
        target_vs = np.linspace(0.0, 1.0, num=min_profiles)
        max_degree = n_profiles - 1
        profiles = interpolate_nurbs_curves(profiles, ts, target_vs,
                    degree_v = min(max_degree, path.get_degree()),
                    knots_u = knots_u,
                    implementation = implementation,
                    logger = logger)
        ts = np.linspace(t_min, t_max, num=min_profiles)
    else:
        profiles = repeat_last_for_length(profiles, min_profiles)

    frame_calculator = SvCurveFrameCalculator(path, algorithm, **kwargs).get_matrices

#     for i, p in enumerate(profiles):
#         print(f"P#{i}: {p.get_control_points()}")

    return nurbs_sweep_impl(path, profiles, ts, frame_calculator,
                knots_u=knots_u, metric=metric,
                implementation=implementation,
                logger = logger)

def prepare_nurbs_birail(path1, path2, profiles,
        ts1 = None, ts2 = None,
        min_profiles = 10,
        degree_v = None,
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        logger = None):

    n_profiles = len(profiles)
    have_ts1 = ts1 is not None and len(ts1) > 0
    have_ts2 = ts2 is not None and len(ts2) > 0
    if have_ts1 and n_profiles != len(ts1):
        raise Exception(f"Number of profiles ({n_profiles}) is not equal to number of T values ({len(ts1)})")
    if have_ts2 and n_profiles != len(ts2):
        raise Exception(f"Number of profiles ({n_profiles}) is not equal to number of T values ({len(ts2)})")

    if degree_v is None:
        degree_v = path1.get_degree()

    t_min_1, t_max_1 = path1.get_u_bounds()
    t_min_2, t_max_2 = path2.get_u_bounds()
    if not have_ts1:
        ts1 = np.linspace(t_min_1, t_max_1, num=n_profiles)
    if not have_ts2:
        ts2 = np.linspace(t_min_2, t_max_2, num=n_profiles)

    if n_profiles == 1:
        p = profiles[0]
        profiles = [p] * min_profiles
        #if not have_ts1:
        ts1 = np.linspace(t_min_1, t_max_1, num=min_profiles)
        #if not have_ts2:
        ts2 = np.linspace(t_min_2, t_max_2, num=min_profiles)
    elif n_profiles == 2 and n_profiles < min_profiles:
        coeffs = np.linspace(0.0, 1.0, num=min_profiles)
        p0, p1 = profiles
        profiles = [p0.lerp_to(p1, coeff) for coeff in coeffs]
        #if not have_ts1:
        ts1 = np.linspace(t_min_1, t_max_1, num=min_profiles)
        #if not have_ts2:
        ts2 = np.linspace(t_min_2, t_max_2, num=min_profiles)
    elif n_profiles < min_profiles:
        target_vs = np.linspace(0.0, 1.0, num=min_profiles)
        max_degree = n_profiles - 1
        if not have_ts1:
            ts1 = np.linspace(t_min_1, t_max_1, num=n_profiles)
        profiles = interpolate_nurbs_curves(profiles, ts1, target_vs,
                    degree_v = min(max_degree, degree_v),
                    knots_u = knots_u,
                    implementation = implementation,
                    logger = logger)
        #if not have_ts1:
        ts1 = np.linspace(t_min_1, t_max_1, num=min_profiles)
        #if not have_ts2:
        ts2 = np.linspace(t_min_2, t_max_2, num=min_profiles)
    else:
        profiles = repeat_last_for_length(profiles, min_profiles)

    points1 = path1.evaluate_array(ts1)
    points2 = path2.evaluate_array(ts2)

    orig_profiles = profiles[:]

    if use_tangents == 'PATHS_AVG':
        tangents1 = path1.tangent_array(ts1)
        tangents2 = path2.tangent_array(ts2)
        tangents = 0.5 * (tangents1 + tangents2)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    elif use_tangents == 'FROM_PATH1':
        tangents = path1.tangent_array(ts1)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    elif use_tangents == 'FROM_PATH2':
        tangents = path2.tangent_array(ts2)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    elif use_tangents == 'FROM_PROFILE':
        tangents = []
        for profile in orig_profiles:
            matrix = nurbs_curve_matrix(profile)
            yy = matrix @ np.array([0, 0, -1])
            yy /= np.linalg.norm(yy)
            tangents.append(yy)
        tangents = np.array(tangents)

    binormals = points2 - points1
    scales = np.linalg.norm(binormals, axis=1, keepdims=True)
    if scales.min() < 1e-6:
        raise Exception("Paths go too close")
    binormals /= scales

    normals = np.cross(tangents, binormals)
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)

    tangents = np.cross(binormals, normals)
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)

    matrices = np.dstack((normals, binormals, tangents))
    matrices = np.transpose(matrices, axes=(0,2,1))
    matrices = np.linalg.inv(matrices)

    scales = scales.flatten()
    placed_profiles = []
    prev_normal = None
    for pt1, pt2, profile, tangent, scale, matrix in zip(points1, points2, profiles, tangents, scales, matrices):

        if auto_rotate:
            profile = nurbs_curve_to_xoy(profile, tangent)

        t_min, t_max = profile.get_u_bounds()
        pr_start = profile.evaluate(t_min)
        pr_end = profile.evaluate(t_max)
        pr_vector = pr_end - pr_start
        pr_length = np.linalg.norm(pr_vector)
        if pr_length < 1e-6:
            raise Exception("One of profiles is closed")
        pr_dir = pr_vector / pr_length
        pr_x, pr_y, _ = tuple(pr_dir)

        rotation = np.array([
                (pr_y, -pr_x, 0),
                (pr_x, pr_y, 0),
                (0, 0, 1)
            ])

        src_scale = scale
        scale /= pr_length
        if scale_uniform:
            scale_m = np.array([
                    (scale, 0, 0),
                    (0, scale, 0),
                    (0, 0, scale)
                ])
        else:
            scale_m = np.array([
                    (1, 0, 0),
                    (0, scale, 0),
                    (0, 0, 1)
                ])
        cpts = [matrix @ scale_m @ rotation @ (pt - pr_start) + pt1 for pt in profile.get_control_points()]
        cpts = np.array(cpts)

        profile = profile.copy(control_points = cpts)
        placed_profiles.append(profile)
    return placed_profiles

def nurbs_birail(path1, path2, profiles,
        ts1 = None, ts2 = None,
        min_profiles = 10,
        knots_u = 'UNIFY',
        degree_v = None, metric = 'DISTANCE',
        scale_uniform = True,
        auto_rotate = False,
        use_tangents = 'PATHS_AVG',
        implementation = SvNurbsSurface.NATIVE,
        logger = None):
    """
    NURBS BiRail.

    Inputs:
    * path1, path2: SvNurbsCurve.
    * profiles: list of SvNurbsCurve.
    * ts: T values along path which correspond to profiles. Number of ts must
        be equal to number of profiles. If None, the function will calculate
        appropriate values automatically.
    * min_profiles: minimal number of (copies of) profile curves to be placed
        along the path: bigger number correspond to better precision, within
        certain limits. If min_profiles > len(profiles), additional profiles
        will be generated by interpolation (by lofting).
    * knots_u: 'UNIFY' or 'AVERAGE'
    * degree_v: degree of the surface along V direction; if not specified,
        degree of the first path will be used.
    * metric: interpolation metric
    * scale_uniform: If True, profile curves will be scaled along all axes
        uniformly; if False, they will be scaled only along one axis, in order to
        fill space between two path curves.
    * auto_rotate: if False, the profile curves are supposed to lie in XOY plane.
        Otherwise, try to figure out their rotation automatically.
    * implementation: surface implementation

    output: tuple:
        * list of curves - initial profile curves placed / rotated along the path curve
        * list of curves - interpolated profile curves
        * list of NURBS curves along V direction
        * generated NURBS surface.
    """
    if logger is None:
        logger = getLogger()

    placed_profiles = prepare_nurbs_birail(path1, path2, profiles,
            ts1 = ts1, ts2 = ts2,
            min_profiles = min_profiles,
            degree_v = degree_v,
            scale_uniform = scale_uniform,
            auto_rotate = auto_rotate,
            use_tangents = use_tangents)

    unified_curves, v_curves, surface = simple_loft(placed_profiles, degree_v = degree_v,
            knots_u = knots_u, metric = metric,
            implementation = implementation,
            logger = logger)

    return placed_profiles, unified_curves, v_curves, surface

SvNurbsMaths.surface_classes[SvNurbsMaths.NATIVE] = SvNativeNurbsSurface
if geomdl is not None:
    SvNurbsMaths.surface_classes[SvNurbsMaths.GEOMDL] = SvGeomdlSurface

