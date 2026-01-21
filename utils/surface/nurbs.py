# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.core.sv_custom_exceptions import ArgumentError, SvInvalidInputException, SvUnsupportedOptionException
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions,
        nurbs_divide,
        CantRemoveKnotException, CantReduceDegreeException
    )
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.core import UnsupportedSurfaceTypeException
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.utils.sv_logging import sv_logger, get_logger
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
                sv_logger.info("Can't convert %s to NURBS: %s", surface, e)
        return None

    @classmethod
    def get_nurbs_implementation(cls):
        raise NotImplementedError("NURBS implementation is not defined")

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
        raise NotImplementedError("Not implemented!")

    def remove_knot(self, direction, parameter, count=1, tolerance=None, if_possible=False):
        raise NotImplementedError("Not implemented!")

    def get_degree_u(self):
        raise NotImplementedError("Not implemented!")

    def get_degree_v(self):
        raise NotImplementedError("Not implemented!")

    def get_knotvector_u(self):
        """
        returns: np.array of shape (X,)
        """
        raise NotImplementedError("Not implemented!")

    def get_knotvector_v(self):
        """
        returns: np.array of shape (X,)
        """
        raise NotImplementedError("Not implemented!")

    def get_control_points(self):
        """
        returns: np.array of shape (n_u, n_v, 3)
        """
        raise NotImplementedError("Not implemented!")

    def get_weights(self):
        """
        returns: np.array of shape (n_u, n_v)
        """
        raise NotImplementedError("Not implemented!")

    def iso_curve(self, fixed_direction, param):
        raise NotImplementedError("Not implemented")
    
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
            raise ArgumentError("Of delta and target, only one parameter can be specified")
        if direction == SvNurbsSurface.U:
            degree = self.get_degree_u()
        else:
            degree = self.get_degree_v()
        if delta is None:
            delta = target - degree
            if delta < 0:
                raise SvInvalidInputException(f"Surface already has degree {degree}, which is greater than target {target}")
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
            raise ArgumentError("Of delta and target, only one parameter can be specified")
        if direction == SvNurbsSurface.U:
            degree = self.get_degree_u()
        else:
            degree = self.get_degree_v()
        if delta is None:
            delta = degree - target
            if delta < 0:
                raise SvInvalidInputException(f"Surface already has degree {degree}, which is less than target {target}")
        if delta == 0:
            return self

        if logger is None:
            logger = get_logger()

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
            raise SvUnsupportedOptionException("Unsupported direction")

    def cut_slice(self, direction, p_min, p_max):
        _, rest = self.split_at(direction, p_min)
        if rest is None:
            return None
        result, _ = rest.split_at(direction, p_max)
        return result

    def get_discontinuities_u(self, order, include_endpoints=False):
        p = self.get_degree_u()
        knotvector = self.get_knotvector_u()
        ms = sv_knotvector.to_multiplicity(knotvector)
        result = [t for t, s in ms if s == p - order + 1]
        if include_endpoints:
            result = [knotvector[0]] + result + [knotvector[-1]]
        return result

    def get_discontinuities_v(self, order, include_endpoints=False):
        p = self.get_degree_v()
        knotvector = self.get_knotvector_v()
        ms = sv_knotvector.to_multiplicity(knotvector)
        result = [t for t, s in ms if s == p - order + 1]
        if include_endpoints:
            result = [knotvector[0]] + result + [knotvector[-1]]
        return result

    def get_discontinuities(self, direction, order, include_endpoints=False):
        if direction == SvNurbsSurface.U:
            return self.get_discontinuities_u(order, include_endpoints)
        else:
            return self.get_discontinuities_v(order, include_endpoints)

    def cut_slices_by_discontinuity(self, direction, order):
        ts = self.get_discontinuities(direction, order, include_endpoints=True)
        if len(ts) <= 2:
            return [self]
        result = [self.cut_slice(direction, t1, t2) for t1, t2 in zip(ts, ts[1:])]
        #print(f"Discontinuities in {direction}: {ts} => {len(result)} slices")
        return result

    def cut_slices_by_discontinuity_uv(self, order, join=True):
        slices_u = self.cut_slices_by_discontinuity(SvNurbsSurface.U, order)
        slices = [sl.cut_slices_by_discontinuity(SvNurbsSurface.V, order) for sl in slices_u]
        if join:
            slices = sum(slices, [])
        return slices

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
            print("Cpts1", cps1)
            print("Cpts2", cps2)
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
            print("Cpts1", cps1)
            print("Cpts2", cps2)
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

    def reparametrize(self, new_u_min, new_u_max, new_v_min, new_v_max):
        knotvector_u = self.get_knotvector_u()
        knotvector_v = self.get_knotvector_v()
        knotvector_u = sv_knotvector.rescale(knotvector_u, new_u_min, new_u_max)
        knotvector_v = sv_knotvector.rescale(knotvector_v, new_v_min, new_v_max)
        return self.copy(knotvector_u = knotvector_u, knotvector_v = knotvector_v)
    
    def flip(self, flip_u, flip_v):
        ctrlpts = self.get_control_points()
        weights = self.get_weights()
        knotvector_u = self.get_knotvector_u()
        knotvector_v = self.get_knotvector_v()
        if flip_u:
            ctrlpts = ctrlpts[::-1,:]
            weights = weights[::-1,:]
            knotvector_u = sv_knotvector.reverse(knotvector_u)
        if flip_v:
            ctrlpts = ctrlpts[:,::-1]
            weights = weights[:,::-1]
            knotvector_v = sv_knotvector.reverse(knotvector_v)
        return self.copy(knotvector_u = knotvector_u,
                         knotvector_v = knotvector_v,
                         control_points = ctrlpts,
                         weights = weights)

def other_direction(direction):
    if direction == SvNurbsSurface.U:
        return SvNurbsSurface.V
    else:
        return SvNurbsSurface.U

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
        normal1 = normal / norm

        fuu = derivatives[:,2,0]
        fvv = derivatives[:,0,2]
        fuv = derivatives[:,1,1]

        nuu = (fuu * normal1).sum(axis=1)
        nvv = (fvv * normal1).sum(axis=1)
        nuv = (fuv * normal1).sum(axis=1)

        duu = np.linalg.norm(fu, axis=1) **2
        dvv = np.linalg.norm(fv, axis=1) **2
        duv = (fu * fv).sum(axis=1)

        calc = SurfaceCurvatureCalculator(us, vs, order=order)
        calc.set(surf_vertices, normal, fu, fv, duu, dvv, duv, nuu, nvv, nuv)
        calc.fuu = fuu
        calc.fvv = fvv
        calc.fuv = fuv
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
                raise SvInvalidInputException(f"Shape of control_points ({c_ku}, {c_kv}) does not match to shape of weights ({w_ku}, {w_kv})")
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
            raise ArgumentError("Unsupported direction")

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
            raise ArgumentError("Unsupported direction")

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
        calc.fuu = surface_uu
        calc.fvv = surface_vv
        calc.fuv = surface_uv
        return calc

SvNurbsMaths.surface_classes[SvNurbsMaths.NATIVE] = SvNativeNurbsSurface
if geomdl is not None:
    SvNurbsMaths.surface_classes[SvNurbsMaths.GEOMDL] = SvGeomdlSurface

