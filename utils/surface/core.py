# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, cos, sin, atan, sqrt
from collections import defaultdict

from sverchok.utils.logging import info, exception
from sverchok.utils.surface.data import *

class UnsupportedSurfaceTypeException(TypeError):
    pass

class SvSurface(object):
    def __repr__(self):
        if hasattr(self, '__description__'):
            description = self.__description__
        else:
            description = self.__class__.__name__
        return "<{} surface>".format(description)

    def evaluate(self, u, v):
        raise Exception("not implemented!")

    def evaluate_array(self, us, vs):
        raise Exception("not implemented!")

    def normal(self, u, v):
        h = self.normal_delta
        p = self.evaluate(u, v)
        p_u = self.evaluate(u+h, v)
        p_v = self.evaluate(u, v+h)
        du = (p_u - p) / h
        dv = (p_v - p) / h
        normal = np.cross(du, dv)
        n = np.linalg.norm(normal)
        normal = normal / n
        return normal

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

    def derivatives_data_array(self, us, vs):
        if hasattr(self, 'normal_delta'):
            h = self.normal_delta
        else:
            h = 0.0001
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + h, vs)
        v_plus = self.evaluate_array(us, vs + h)
        du = (u_plus - surf_vertices) / h
        dv = (v_plus - surf_vertices) / h
        return SurfaceDerivativesData(surf_vertices, du, dv)

    def curvature_calculator(self, us, vs, order=True):
        if hasattr(self, 'normal_delta'):
            h = self.normal_delta
        else:
            h = 0.0001
        h2 = h*h

        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + h, vs)
        v_plus = self.evaluate_array(us, vs + h)
        u_minus = self.evaluate_array(us - h, vs)
        v_minus = self.evaluate_array(us, vs - h)
        uv_plus = self.evaluate_array(us + h, vs + h)
        uv_minus = self.evaluate_array(us - h, vs - h)

        fu = (u_plus - surf_vertices)/h
        fv = (v_plus - surf_vertices)/h
        normal = np.cross(fu, fv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        normal = normal / norm

        fuu = (u_plus - 2*surf_vertices + u_minus) / h2
        fvv = (v_plus - 2*surf_vertices + v_minus) / h2
        fuv = (uv_plus - u_plus - v_plus + surf_vertices) / h2

        nuu = (fuu * normal).sum(axis=1)
        nvv = (fvv * normal).sum(axis=1)
        nuv = (fuv * normal).sum(axis=1)

        duu = np.linalg.norm(fu, axis=1) **2
        dvv = np.linalg.norm(fv, axis=1) **2
        duv = (fu * fv).sum(axis=1)

        calc = SurfaceCurvatureCalculator(us, vs, order=order)
        calc.set(surf_vertices, normal, fu, fv, duu, dvv, duv, nuu, nvv, nuv)
        return calc

    def gauss_curvature_array(self, us, vs):
        calc = self.curvature_calculator(us, vs)
        return calc.gauss()

    def mean_curvature_array(self, us, vs):
        calc = self.curvature_calculator(us, vs)
        return calc.mean()

    def principal_curvature_values_array(self, us, vs, order=True):
        calc = self.curvature_calculator(us, vs, order=order)
        return calc.values()

    def principal_curvatures_array(self, us, vs):
        calc = self.curvature_calculator(us, vs)
        return calc.values_and_directions()

    def get_coord_mode(self):
        return 'UV'

    @property
    def has_input_matrix(self):
        return False

    def get_input_matrix(self):
        return None

    def get_input_orientation(self):
        return None

    def get_u_min(self):
        return 0.0

    def get_u_max(self):
        return 1.0

    def get_v_min(self):
        return 0.0

    def get_v_max(self):
        return 1.0

    @property
    def u_size(self):
        m,M = self.get_u_min(), self.get_u_max()
        return M - m

    @property
    def v_size(self):
        m,M = self.get_v_min(), self.get_v_max()
        return M - m

class SvSurfaceSubdomain(SvSurface):
    def __init__(self, surface, u_bounds, v_bounds):
        self.surface = surface
        self.u_bounds = u_bounds
        self.v_bounds = v_bounds
        if hasattr(surface, "normal_delta"):
            self.normal_delta = surface.normal_delta
        else:
            self.normal_delta = 0.001
        self.__description__ = "{}[{} .. {}][{} .. {}]".format(surface, u_bounds[0], u_bounds[1], v_bounds[0], v_bounds[1])

    def evaluate(self, u, v):
        return self.surface.evaluate(u, v)

    def evaluate_array(self, us, vs):
        return self.surface.evaluate_array(us, vs)

    def normal(self, u, v):
        return self.surface.normal(u, v)

    def normal_array(self, us, vs):
        return self.surface.normal_array(us, vs)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

class SvFlipSurface(SvSurface):
    def __init__(self, surface, flip_u, flip_v):
        self.surface = surface
        self.flip_u = flip_u
        self.flip_v = flip_v
        if hasattr(surface, "normal_delta"):
            self.normal_delta = surface.normal_delta
        else:
            self.normal_delta = 0.001
        self.__description__ = "Flipped {}".format(surface)

    def get_u_min(self):
        return self.surface.get_u_min()

    def get_v_min(self):
        return self.surface.get_v_min()

    def get_u_max(self):
        return self.surface.get_u_max()

    def get_v_max(self):
        return self.surface.get_v_max()

    def flip(self, u, v):
        min_u, max_u = self.get_u_min(), self.get_u_max()
        min_v, max_v = self.get_v_min(), self.get_v_max()

        if self.flip_u:
            u = max_u - u + min_u
        if self.flip_v:
            v = max_v - v + max_v
        return u, v

    def evaluate(self, u, v):
        u, v = self.flip(u, v)
        return self.surface.evaluate(u, v)
    
    def evaluate_array(self, us, vs):
        us, vs = self.flip(us, vs)
        return self.surface.evaluate_array(us, vs)

    def normal(self, u, v):
        u, v = self.flip(u, v)
        return self.surface.normal(u, v)

    def normal_array(self, us, vs):
        us, vs = self.flip(us, vs)
        return self.surface.normal_array(us, vs)

class SvSwapSurface(SvSurface):
    def __init__(self, surface):
        self.surface = surface
        if hasattr(surface, "normal_delta"):
            self.normal_delta = surface.normal_delta
        else:
            self.normal_delta = 0.001
        self.__description__ = "Swapped {}".format(surface)

    @staticmethod
    def build(surface):
        if hasattr(surface, 'swap_uv'):
            return surface.swap_uv()
        return SvSwapSurface(surface)

    def get_u_min(self):
        return self.surface.get_v_min()

    def get_v_min(self):
        return self.surface.get_u_min()

    def get_u_max(self):
        return self.surface.get_v_max()

    def get_v_max(self):
        return self.surface.get_u_max()

    def evaluate(self, u, v):
        return self.surface.evaluate(v, u)
    
    def evaluate_array(self, us, vs):
        return self.surface.evaluate_array(vs, us)

    def normal(self, u, v):
        return self.surface.normal(v, u)

    def normal_array(self, us, vs):
        return self.surface.normal_array(vs, us)

class SvReparametrizedSurface(SvSurface):
    def __init__(self, surface, new_u_min, new_u_max, new_v_min, new_v_max):
        self.surface = surface
        self.new_u_min = new_u_min
        self.new_u_max = new_u_max
        self.new_v_min = new_v_min
        self.new_v_max = new_v_max
        if hasattr(surface, "normal_delta"):
            self.normal_delta = surface.normal_delta
        else:
            self.normal_delta = 0.001

    def get_u_min(self):
        return self.new_u_min

    def get_v_min(self):
        return self.new_v_min

    def get_u_max(self):
        return self.new_u_max

    def get_v_max(self):
        return self.new_v_max

    def map_uv(self, u, v):
        new_u_min, new_u_max = self.new_u_min, self.new_u_max
        new_v_min, new_v_max = self.new_v_min, self.new_v_max

        u_min, u_max = self.surface.get_u_min(), self.surface.get_u_max()
        v_min, v_max = self.surface.get_v_min(), self.surface.get_v_max()

        u = (u_max - u_min) * (u - new_u_min) / (new_u_max - new_u_min) + u_min
        v = (v_max - v_min) * (v - new_v_min) / (new_v_max - new_v_min) + v_min

        return u, v

    def scale_u(self):
        new_u_min, new_u_max = self.new_u_min, self.new_u_max
        u_min, u_max = self.surface.get_u_min(), self.surface.get_u_max()
        return (u_max - u_min) / (new_u_max - new_u_min)

    def scale_v(self):
        new_v_min, new_v_max = self.new_v_min, self.new_v_max
        v_min, v_max = self.surface.get_v_min(), self.surface.get_v_max()
        return (v_max - v_min) / (new_v_max - new_v_min)

    def evaluate(self, u, v):
        u, v = self.map_uv(u, v)
        return self.surface.evaluate(u, v)

    def evaluate_array(self, us, vs):
        us, vs = self.map_uv(us, vs)
        return self.surface.evaluate_array(us, vs)

    def normal(self, u, v):
        u, v = self.map_uv(u, v)
        return self.surface.normal(u, v)

    def normal_array(self, us, vs):
        us, vs = self.map_uv(us, vs)
        return self.surface.normal_array(us, vs)

    def derivatives_data_array(self, us, vs):
        us, vs = self.map_uv(us, vs)
        data = self.surface.derivatives_data_array(us, vs)
        data.du *= self.scale_u()
        data.dv *= self.scale_v()
        return data


class SvLambdaSurface(SvSurface):
    __description__ = "Formula"

    def __init__(self, function, function_numpy = None):
        self.function = function
        self.function_numpy = function_numpy
        self.u_bounds = (0.0, 1.0)
        self.v_bounds = (0.0, 1.0)
        self.normal_delta = 0.001

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
        return self.function(u, v)

    def evaluate_array(self, us, vs):
        if self.function_numpy is None:
            return np.vectorize(self.function, signature='(),()->(3)')(us, vs)
        else:
            return self.function_numpy(us, vs)

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

