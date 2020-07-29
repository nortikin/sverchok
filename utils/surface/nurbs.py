
import numpy as np

from sverchok.utils.curve.nurbs import SvNurbsBasisFunctions
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import operations
    from geomdl import NURBS

##################
#                #
#  Surfaces      #
#                #
##################

class SvNurbsSurface(SvSurface):
    """
    Base abstract class for all supported implementations of NURBS surfaces.
    """
    NATIVE = 'NATIVE'
    GEOMDL = 'GEOMDL'

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        if implementation == SvNurbsSurface.GEOMDL:
            return SvGeomdlSurface.build(degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights, normalize_knots)
        elif implementation == SvNurbsSurface.NATIVE:
            if normalize_knots:
                knotvector_u = sv_knotvector.normalize(knotvector_u)
                knotvector_v = sv_knotvector.normalize(knotvector_v)
            return SvNativeNurbsSurface(degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights)
        else:
            raise Exception(f"Unsupported NURBS Surface implementation: {implementation}")

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

class SvGeomdlSurface(SvNurbsSurface):
    def __init__(self, surface):
        self.surface = surface
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)

    def get_degree_u(self):
        return self.surface.degree_u

    def get_degree_v(self):
        return self.surface.degree_v

    def get_knotvector_u(self):
        return self.surface.knotvector_u

    def get_knotvector_v(self):
        return self.surface.knotvector_v

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
    def build(cls, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights, normalize_knots=False):

        def convert_row(verts_row, weights_row):
            return [(x*w, y*w, z*w, w) for (x,y,z), w in zip(verts_row, weights_row)]

        if weights is None:
            surf = BSpline.Surface(normalize_kv = normalize_knots)
        else:
            surf = NURBS.Surface(normalize_kv = normalize_knots)
        surf.degree_u = degree_u
        surf.degree_v = degree_v
        ctrlpts = list(map(convert_row, control_points, weights))
        surf.ctrlpts2d = ctrlpts
        surf.knotvector_u = knotvector_u
        surf.knotvector_v = knotvector_v
        return SvGeomdlSurface(surf)

    @classmethod
    def from_any_nurbs(cls, surface):
        if not isinstance(surface, SvNurbsSurface):
            raise TypeError("Invalid surface")
        if isinstance(surface, SvGeomdlSurface):
            return surface
        return SvGeomdlSurface.build(surface.get_degree_u(), surface.get_degree_v(),
                    surface.get_knotvector_u(), surface.get_knotvector_v(),
                    surface.get_control_points(),
                    surface.get_weights())

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
        #print("Geomdl/Suu", fuu)
        #print("Geomdl/Suv:", fuv)

        nuu = (fuu * normal).sum(axis=1)
        nvv = (fvv * normal).sum(axis=1)
        nuv = (fuv * normal).sum(axis=1)
        #print("Geomdl/Nuu", nuu)
        #print("Geomdl/Nuv", nuv)

        duu = np.linalg.norm(fu, axis=1) **2
        dvv = np.linalg.norm(fv, axis=1) **2
        duv = (fu * fv).sum(axis=1)
        #print("Geomdl/Duv", duv)

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
    def __init__(self, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights):
        self.degree_u = degree_u
        self.degree_v = degree_v
        self.knotvector_u = np.array(knotvector_u)
        self.knotvector_v = np.array(knotvector_v)
        self.control_points = np.array(control_points)
        self.weights = np.array(weights)
        self.basis_u = SvNurbsBasisFunctions(knotvector_u)
        self.basis_v = SvNurbsBasisFunctions(knotvector_v)
        self.u_bounds = (self.knotvector_u.min(), self.knotvector_u.max())
        self.v_bounds = (self.knotvector_v.min(), self.knotvector_v.max())
        self.normal_delta = 0.0001

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
        return numerator / denominator

    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        N, D = self.fraction(0, 0, us, vs)
        S = N / D
        Nu, Du = self.fraction(1, 0, us, vs)
        Nv, Dv = self.fraction(0, 1, us, vs)
        Su = (Nu - S*Du) / D
        Sv = (Nv - S*Dv) / D
        normal = np.cross(Su, Sv)
        n = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = normal / n
        return normal

    def derivatives_data_array(self, us, vs):
        N, D = self.fraction(0, 0, us, vs)
        S = N / D
        Nu, Du = self.fraction(1, 0, us, vs)
        Nv, Dv = self.fraction(0, 1, us, vs)
        Su = (Nu - S*Du) / D
        Sv = (Nv - S*Dv) / D
        return SurfaceDerivativesData(S, Su, Sv)

    def curvature_calculator(self, us, vs, order=True):
    
        N, D = self.fraction(0, 0, us, vs)
        S = N / D
        Nu, Du = self.fraction(1, 0, us, vs)
        Nv, Dv = self.fraction(0, 1, us, vs)
        Su = (Nu - S*Du) / D
        Sv = (Nv - S*Dv) / D

        normal = np.cross(Su, Sv)
        n = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = normal / n

        Nuu, Duu = self.fraction(2, 0, us, vs)
        Suu = (Nuu - 2*Su*Du - S*Duu) / D
        Nvv, Dvv = self.fraction(0, 2, us, vs)
        Svv = (Nvv - 2*Sv*Dv - S*Dvv) / D
        #print("Native/Suu", Suu)

        Nuv, Duv = self.fraction(1, 1, us, vs)
        Suv = (Nuv - Sv*Du - Su*Dv - S*Duv) / D
        #print("Native/Suv:", Suv)

        nuu = (Suu * normal).sum(axis=1)
        nvv = (Svv * normal).sum(axis=1)
        nuv = (Suv * normal).sum(axis=1)
        #print("Native/Nuu", nuu)
        #print("Native/Nuv", nuv)

        duu = np.linalg.norm(Su, axis=1) **2
        dvv = np.linalg.norm(Sv, axis=1) **2
        duv = (Su * Sv).sum(axis=1)
        #print("Native/Duv", duv)

        calc = SurfaceCurvatureCalculator(us, vs, order=order)
        calc.set(S, normal, Su, Sv, duu, dvv, duv, nuu, nvv, nuv)
        return calc

