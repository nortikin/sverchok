
import numpy as np
from collections import defaultdict

from sverchok.utils.geom import Spline
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions,
        nurbs_divide, from_homogenous
    )
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs_algorithms import interpolate_nurbs_curve, unify_curves
from sverchok.utils.curve.algorithms import unify_curves_degree, SvCurveFrameCalculator
from sverchok.utils.surface.core import UnsupportedSurfaceTypeException
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.utils.logging import info
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

    def insert_knot(self, direction, parameter, count=1):
        raise Exception("Not implemented!")

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

    def iso_curve(sefl, fixed_direction, param):
        raise Exception("Not implemented")

class SvGeomdlSurface(SvNurbsSurface):
    def __init__(self, surface):
        self.surface = surface
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)
        self.__description__ = f"Geomdl NURBS (degree={surface.degree_u}x{surface.degree_v}, pts={len(surface.ctrlpts2d)}x{len(surface.ctrlpts2d[0])})"

    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsSurface.GEOMDL

    def insert_knot(self, direction, parameter, count=1):
        if direction == SvNurbsSurface.U:
            uv = [parameter, None]
            counts = [count, 0]
        elif direction == SvNurbsSurface.V:
            uv = [None, parameter]
            counts = [0, count]
        surface = operations.insert_knot(self.surface, uv, counts)
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

    def insert_knot(self, direction, parameter, count=1):
        if direction == SvNurbsSurface.U:
            new_points = []
            new_weights = []
            new_u_degree = None
            for i in range(self.get_control_points().shape[1]):
                fixed_v_points = self.get_control_points()[:,i]
                fixed_v_weights = self.get_weights()[:,i]
                fixed_v_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                                    self.degree_u, self.knotvector_u,
                                    fixed_v_points, fixed_v_weights)
                fixed_v_curve = fixed_v_curve.insert_knot(parameter, count)
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
            for i in range(self.get_control_points().shape[0]):
                fixed_u_points = self.get_control_points()[i,:]
                fixed_u_weights = self.get_weights()[i,:]
                fixed_u_curve = SvNurbsMaths.build_curve(SvNurbsMaths.NATIVE,
                                    self.degree_v, self.knotvector_v,
                                    fixed_u_points, fixed_u_weights)
                fixed_u_curve = fixed_u_curve.insert_knot(parameter, count)
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
        surface_u = (numerator_u - surface*denominator_u) / denominator
        surface_v = (numerator_v - surface*denominator_v) / denominator
        normal = np.cross(surface_u, surface_v)
        n = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = normal / n
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

def simple_loft(curves, degree_v = None, knots_u = 'UNIFY', metric='DISTANCE', tknots=None, implementation=SvNurbsSurface.NATIVE):
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
    curve_class = type(curves[0])
    curves = unify_curves_degree(curves)
    if knots_u == 'UNIFY':
        curves = unify_curves(curves)
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
#     lens = [len(pts) for pts in src_points]
#     max_len, min_len = max(lens), min(lens)
#     if max_len != min_len:
#         raise Exception(f"Unify error: curves have different number of control points: {lens}")

    src_points = np.array(src_points)
    #print("Src:", src_points)
    src_points = np.transpose(src_points, axes=(1,0,2))

    v_curves = [interpolate_nurbs_curve(curve_class, degree_v, points, metric=metric, tknots=tknots) for points in src_points]
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
    tknots_v = Spline.create_knots(mean_v_vector, metric=metric)
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

def interpolate_nurbs_curves(curves, base_vs, target_vs,
        degree_v = None, knots_u = 'UNIFY',
        implementation = SvNurbsSurface.NATIVE):
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
                implementation = implementation)
    # Calculate iso_curves of the lofted surface, and move them back along Z axis
    back_vectors = np.array([(0,0,-v) for v in np.linspace(min_v, max_v, num=len(target_vs))])
    return [lofted.iso_curve(fixed_direction='V', param=v).transform(None, back) for v, back in zip(target_vs, back_vectors)]

def nurbs_sweep_impl(path, profiles, ts, frame_calculator, knots_u = 'UNIFY', metric = 'DISTANCE', implementation = SvNurbsSurface.NATIVE):
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
        to_loft.append(profile)

    unified_curves, v_curves, surface = simple_loft(to_loft, degree_v = path.get_degree(),
            knots_u = knots_u, metric = metric,
            implementation = implementation)
    return to_loft, unified_curves, v_curves, surface

def nurbs_sweep(path, profiles, ts, min_profiles, algorithm, knots_u = 'UNIFY', metric = 'DISTANCE', implementation = SvNurbsSurface.NATIVE, **kwargs):
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
                    implementation = implementation)
        ts = np.linspace(t_min, t_max, num=min_profiles)
    else:
        profiles = repeat_last_for_length(profiles, min_profiles)

    frame_calculator = SvCurveFrameCalculator(path, algorithm, **kwargs).get_matrices

#     for i, p in enumerate(profiles):
#         print(f"P#{i}: {p.get_control_points()}")

    return nurbs_sweep_impl(path, profiles, ts, frame_calculator,
                knots_u=knots_u, metric=metric,
                implementation=implementation)

SvNurbsMaths.surface_classes[SvNurbsMaths.NATIVE] = SvNativeNurbsSurface
if geomdl is not None:
    SvNurbsMaths.surface_classes[SvNurbsMaths.GEOMDL] = SvGeomdlSurface

