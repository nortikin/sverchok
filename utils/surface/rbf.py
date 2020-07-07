
import numpy as np

from mathutils import Matrix, Vector

from sverchok.utils.surface import SvSurface, SurfaceCurvatureCalculator, SurfaceDerivativesData
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import operations

##################
#                #
#  Surfaces      #
#                #
##################

class SvRbfSurface(SvSurface):
    def __init__(self, rbf, coord_mode, input_orientation, input_matrix):
        self.rbf = rbf
        self.coord_mode = coord_mode
        self.input_orientation = input_orientation
        self.input_matrix = input_matrix
        self.u_bounds = (0, 0)
        self.v_bounds = (0, 0)
        self.normal_delta = 0.0001

    def get_input_orientation(self):
        return self.input_orientation

    def get_coord_mode(self):
        return self.coord_mode

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
        return self.coord_mode == 'XY' and self.input_matrix is not None and self.input_matrix != Matrix()

    def get_input_matrix(self):
        return self.input_matrix

    def evaluate(self, u, v):
        z = self.rbf(u, v)
        if self.coord_mode == 'XY':
            z = np.array([u, v, z])
        return z

    def evaluate_array(self, us, vs):
        surf_vertices = np.array( self.rbf(us, vs) )
        if self.coord_mode == 'XY':
            surf_vertices = np.stack((us, vs, surf_vertices)).T
        return surf_vertices 

    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + self.normal_delta, vs)
        v_plus = self.evaluate_array(us, vs + self.normal_delta)
        du = u_plus - surf_vertices
        dv = v_plus - surf_vertices
        #self.info("Du: %s", du)
        #self.info("Dv: %s", dv)
        normal = np.cross(du, dv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        #if norm != 0:
        normal = normal / norm
        #self.info("Normals: %s", normal)
        return normal

