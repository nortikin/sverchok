
import numpy as np

from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import operations

##################
#                #
#  Surfaces      #
#                #
##################

class SvGeomdlSurface(SvSurface):
    def __init__(self, surface):
        self.surface = surface
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)

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
        #print(f"({u}, {v}) => {vert}")
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

