# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import sqrt, copysign, pi
import numpy as np

from mathutils import Vector
from mathutils import bvhtree
from mathutils import noise
from sverchok.utils.curve import SvCurveLengthSolver, SvNormalTrack, MathutilsRotationCalculator
from sverchok.utils.geom import LineEquation, CircleEquation3D, rotate_around_vector_matrix
from sverchok.utils.math import (
            from_cylindrical, from_spherical,
            from_cylindrical_np, to_cylindrical_np,
            from_spherical_np, to_spherical_np,
            np_dot, np_multiply_matrices_vectors)
from sverchok.utils.kdtree import SvKdTree
from sverchok.utils.field.voronoi import SvVoronoiFieldData

##################
#                #
#  Vector Fields #
#                #
##################

class SvVectorField(object):
    def __repr__(self):
        if hasattr(self, '__description__'):
            description = self.__description__
        else:
            description = self.__class__.__name__
        return "<{} vector field>".format(description)

    def evaluate(self, x, y, z):
        rxs, rys, rzs = self.evaluate_grid([x], [y], [z])
        return rxs[0], rys[0], rzs[0]

    def evaluate_grid(self, xs, ys, zs):
        raise Exception("not implemented")

    def evaluate_array(self, points):
        xs = points[:,0]
        ys = points[:,1]
        zs = points[:,2]
        return self.evaluate_grid(xs, ys, zs)
    
    def to_relative(self):
        return SvRelativeVectorField(self)

    def to_absolute(self):
        return SvAbsoluteVectorField(self)

class SvAbsoluteVectorField(SvVectorField):
    def __init__(self, field):
        self.field = field
        self.__description__ = "Absolute({})".format(field)

    def evaluate(self, x, y, z):
        r = self.field.evaluate(x, y, z)
        return r + np.array([x, y, z])

    def evaluate_grid(self, xs, ys, zs):
        rxs, rys, rzs = self.field.evaluate_grid(xs, ys, zs)
        return rxs + xs, rys + ys, rzs + zs

class SvRelativeVectorField(SvVectorField):
    def __init__(self, field):
        self.field = field
        self.__description__ = "Relative({})".format(field)

    def evaluate(self, x, y, z):
        r = self.field.evaluate(x, y, z)
        return r - np.array([x, y, z])

    def evaluate_grid(self, xs, ys, zs):
        rxs, rys, rzs = self.field.evaluate_grid(xs, ys, zs)
        return rxs - xs, rys - ys, rzs - zs

class SvMatrixVectorField(SvVectorField):

    def __init__(self, matrix):
        self.matrix = matrix
        self.__description__ = "Matrix"

    def evaluate(self, x, y, z):
        v = Vector((x, y, z))
        v = (self.matrix @ v) - v
        return np.array(v)

    def evaluate_grid(self, xs, ys, zs):
        matrix = np.array(self.matrix.to_3x3())
        translation = np.array(self.matrix.translation)
        points = np.stack((xs, ys, zs)).T
        R = np.apply_along_axis(lambda v : matrix @ v + translation - v, 1, points).T
        return R[0], R[1], R[2]

class SvConstantVectorField(SvVectorField):

    def __init__(self, vector):
        self.vector = np.array(vector)
        self.__description__ = "Constant = {}".format(vector)

    def evaluate(self, x, y, z):
        return self.vector

    def evaluate_grid(self, xs, ys, zs):
        x, y, z = self.vector
        rx = np.full_like(xs, x)
        ry = np.full_like(ys, y)
        rz = np.full_like(zs, z)
        return rx, ry, rz

class SvVectorFieldLambda(SvVectorField):

    __description__ = "Formula"

    def __init__(self, function, variables, in_field, function_numpy = None):
        self.function = function
        self.function_numpy = function_numpy
        self.variables = variables
        self.in_field = in_field

    def evaluate_grid(self, xs, ys, zs):
        if self.in_field is None:
            Vs = np.zeros(xs.shape[0])
        else:
            vx, vy, vz = self.in_field.evaluate_grid(xs, ys, zs)
            Vs = np.stack((vx, vy, vz)).T
        if self.function_numpy is None:
            return np.vectorize(self.function,
                        signature = "(),(),(),(3)->(),(),()")(xs, ys, zs, Vs)
        else:
            Vs = Vs.T
            return self.function_numpy(xs, ys, zs, Vs)

    def evaluate(self, x, y, z):
        if self.in_field is None:
            V = None
        else:
            V = self.in_field.evaluate(x, y, z)
        return np.array(self.function(x, y, z, V))

class SvNoiseVectorField(SvVectorField):
    def __init__(self, noise_type, seed):
        self.noise_type = noise_type
        self.seed = seed
        self.__description__ = "{} noise".format(noise_type)

    def evaluate(self, x, y, z):
        noise.seed_set(self.seed)
        v = noise.noise_vector((x, y, z), noise_basis=self.noise_type)
        return np.array(v)

    def evaluate_grid(self, xs, ys, zs):
        noise.seed_set(self.seed)
        def mk_noise(v):
            r = noise.noise_vector(v, noise_basis=self.noise_type)
            return r[0], r[1], r[2]
        vectors = np.stack((xs,ys,zs)).T
        return np.vectorize(mk_noise, signature="(3)->(),(),()")(vectors)

class SvRotationVectorField(SvVectorField):

    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff
        self.__description__ = "Rotation Field"

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        dv = np.cross(to_center - projection, direction)

        if self.falloff is not None:
            norm = np.linalg.norm(dv)
            dv = self.falloff(norm) * dv / norm
        return dv

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)
        points = np.stack((xs, ys, zs)).T
        to_center = self.center[np.newaxis, :] - points
        projection = direction[np.newaxis, :] * (np_dot(to_center, direction[np.newaxis,:]) / direction2)[:, np.newaxis]
        vectors = np.cross(to_center - projection, direction)

        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            lens = self.falloff(norms)
            vectors[nonzero] = vectors[nonzero] / norms[nonzero][:, 0][np.newaxis].T
            R = (lens * vectors).T
            return R[0], R[1], R[2]
        else:
            R = vectors.T
            return R[0], R[1], R[2]

class SvBendAlongCurveField(SvVectorField):

    ZERO = 'ZERO'
    FRENET = 'FRENET'
    HOUSEHOLDER = 'householder'
    TRACK = 'track'
    DIFF = 'diff'
    TRACK_NORMAL = 'track_normal'

    def __init__(self, curve, algorithm, scale_all, axis, t_min, t_max, up_axis=None, resolution=50, length_mode='T'):
        self.curve = curve
        self.axis = axis
        self.t_min = t_min
        self.t_max = t_max
        self.algorithm = algorithm
        self.scale_all = scale_all
        self.up_axis = up_axis
        self.length_mode = length_mode
        if algorithm == SvBendAlongCurveField.ZERO:
            self.curve.pre_calc_torsion_integral(resolution)
        elif algorithm == SvBendAlongCurveField.TRACK_NORMAL:
            self.normal_tracker = SvNormalTrack(curve, resolution)
        if length_mode == 'L':
            self.length_solver = SvCurveLengthSolver(curve)
            self.length_solver.prepare('SPL', resolution)
        self.__description__ = "Bend along {}".format(curve)

    def get_matrix(self, tangent, scale):
        return MathutilsRotationCalculator.get_matrix(tangent, scale, self.axis,
                    self.algorithm, self.scale_all, self.up_axis)

    def get_matrices(self, ts, scale):
        n = len(ts)
        if self.scale_all:
            scale_matrix = np.array([
                [scale, 0, 0],
                [0, scale, 0],
                [0, 0, 1/scale]
            ])
        else:
            scale_matrix = np.array([
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1/scale]
            ])
        if self.algorithm == SvBendAlongCurveField.FRENET:
            frenet, _ , _ = self.curve.frame_array(ts)
            return frenet @ scale_matrix
        elif self.algorithm == SvBendAlongCurveField.ZERO:
            frenet, _ , _ = self.curve.frame_array(ts)
            angles = - self.curve.torsion_integral(ts)
            zeros = np.zeros((n,))
            ones = np.ones((n,))
            row1 = np.stack((np.cos(angles), np.sin(angles), zeros)).T # (n, 3)
            row2 = np.stack((-np.sin(angles), np.cos(angles), zeros)).T # (n, 3)
            row3 = np.stack((zeros, zeros, ones)).T # (n, 3)
            rotation_matrices = np.dstack((row1, row2, row3))
            return frenet @ rotation_matrices @ scale_matrix
        elif self.algorithm == SvBendAlongCurveField.TRACK_NORMAL:
            matrices = self.normal_tracker.evaluate_array(ts)
            return matrices @ scale_matrix
        else:
            raise Exception("Unsupported algorithm")

    def get_t_value(self, x, y, z):
        curve_t_min, curve_t_max = self.curve.get_u_bounds()
        t = [x, y, z][self.axis]
        if self.length_mode == 'T':
            t = (curve_t_max - curve_t_min) * (t - self.t_min) / (self.t_max - self.t_min) + curve_t_min
        else:
            t = (t - self.t_min) / (self.t_max - self.t_min) # 0 .. 1
            t = t * self.length_solver.get_total_length()
            t = self.length_solver.solve(np.array([t]))[0]
        return t

    def get_t_values(self, xs, ys, zs):
        curve_t_min, curve_t_max = self.curve.get_u_bounds()
        ts = [xs, ys, zs][self.axis]
        if self.length_mode == 'T':
            ts = (curve_t_max - curve_t_min) * (ts - self.t_min) / (self.t_max - self.t_min) + curve_t_min
        else:
            ts = (ts - self.t_min) / (self.t_max - self.t_min) # 0 .. 1
            ts = ts * self.length_solver.get_total_length()
            ts = self.length_solver.solve(ts)
        return ts

    def get_scale(self):
        if self.length_mode == 'T':
            curve_t_min, curve_t_max = self.curve.get_u_bounds()
            t_range = curve_t_max - curve_t_min
        else:
            t_range = self.length_solver.get_total_length()
        return (self.t_max - self.t_min) / t_range

    def evaluate(self, x, y, z):
        t = self.get_t_value(x, y, z)
        spline_tangent = self.curve.tangent(t)
        spline_vertex = self.curve.evaluate(t)
        scale = self.get_scale()
        if self.algorithm in {SvBendAlongCurveField.ZERO, SvBendAlongCurveField.FRENET, SvBendAlongCurveField.TRACK_NORMAL}:
            matrix = self.get_matrices(np.array([t]), scale)
        else:
            matrix = self.get_matrix(spline_tangent, scale)
        src_vector_projection = np.array([x, y, z])
        src_vector_projection[self.axis] = 0
        new_vertex = np.matmul(matrix, src_vector_projection) + spline_vertex
        vector = new_vertex - np.array([x, y, z])
        return vector

    def evaluate_grid(self, xs, ys, zs):
        def multiply(matrices, vectors):
            vectors = vectors[np.newaxis]
            vectors = np.transpose(vectors, axes=(1,2,0))
            r = matrices @ vectors
            return r[:,:,0]

        ts = self.get_t_values(xs, ys, zs).flatten()
        spline_tangents = self.curve.tangent_array(ts)
        spline_vertices = self.curve.evaluate_array(ts)
        scale = self.get_scale()
        if self.algorithm in {SvBendAlongCurveField.ZERO, SvBendAlongCurveField.FRENET, SvBendAlongCurveField.TRACK_NORMAL}:
            matrices = self.get_matrices(ts, scale)
        else:
            matrices = np.vectorize(lambda t : self.get_matrix(t, scale), signature='(3)->(3,3)')(spline_tangents)
        src_vectors = np.stack((xs, ys, zs)).T
        src_vector_projections = src_vectors.copy()
        src_vector_projections[:,self.axis] = 0
        #multiply = np.vectorize(lambda m, v: m @ v, signature='(3,3),(3)->(3)')
        new_vertices = multiply(matrices, src_vector_projections) + spline_vertices
        R = (new_vertices - src_vectors).T
        return R[0], R[1], R[2]

class SvBendAlongSurfaceField(SvVectorField):
    def __init__(self, surface, axis, autoscale=False, flip=False, only_2D=False, legacy_version=0):
        self.surface = surface
        self.orient_axis = axis
        self.autoscale = autoscale
        self.flip = flip
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)
        self.only_2D = only_2D
        self.__description__ = "Bend along {}".format(surface)
        self.legacy_version = legacy_version

    def get_other_axes(self):
        # Select U and V to be two axes except orient_axis
        if self.orient_axis == 0:
            u_index, v_index = 1,2
        elif self.orient_axis == 1:
            u_index, v_index = 2,0
        else:
            if self.legacy_version==1:
                u_index, v_index = 1,0
            else:
                u_index, v_index = 0,1
        return u_index, v_index

    def get_uv(self, vertices):
        """
        Translate source vertices to UV space of future spline.
        vertices must be np.array of shape (n, 3).
        """
        u_index, v_index = self.get_other_axes()

        # Rescale U and V coordinates to [0, 1], drop third coordinate
        us = vertices[:,u_index].flatten()
        vs = vertices[:,v_index].flatten()
        min_u, max_u = self.u_bounds
        min_v, max_v = self.v_bounds
        size_u = max_u - min_u
        size_v = max_v - min_v

        if size_u < 0.00001:
            raise Exception("Object has too small size in U direction")
        if size_v < 0.00001:
            raise Exception("Object has too small size in V direction")

        us = self.surface.u_size * (us - min_u) / size_u + self.surface.get_u_min()
        vs = self.surface.v_size * (vs - min_v) / size_v + self.surface.get_v_min()

        return size_u, size_v, us, vs

    def _evaluate(self, vertices):
        src_size_u, src_size_v, us, vs = self.get_uv(vertices)
        if self.autoscale:
            u_index, v_index = self.get_other_axes()
            scale_u = src_size_u / self.surface.u_size
            scale_v = src_size_v / self.surface.v_size
            scale_z = sqrt(scale_u * scale_v)
        else:
            if self.orient_axis == 2:
                scale_z = -1.0
            else:
                scale_z = 1.0
        if self.flip:
            scale_z = - scale_z

        if self.only_2D:
            return self.surface.evaluate_array(us, vs)

        spline_normals, surf_vertices = self.surface.normal_vertices_array(us, vs)
        spline_normals /= np.linalg.norm(spline_normals, axis=1, keepdims=True)
        zs = vertices[:,self.orient_axis].flatten()
        zs = zs[np.newaxis].T
        v1 = zs * spline_normals
        v2 = scale_z * v1
        new_vertices = surf_vertices + v2
        return new_vertices

    def evaluate_grid(self, xs, ys, zs):
        vertices = np.stack((xs, ys, zs)).T
        new_vertices = self._evaluate(vertices)
        R = (new_vertices - vertices).T
        return R[0], R[1], R[2]

    def evaluate(self, x, y, z):
        xs, ys, zs = self.evaluate_grid(np.array([x]), np.array([y]), np.array([z]))
        return np.array([xs[0], ys[0], zs[0]])

class SvVoronoiVectorField(SvVectorField):

    def __init__(self, vertices=None, voronoi=None, metric='DISTANCE'):
        if vertices is None and voronoi is None:
            raise Exception("Either vertices or voronoi must be specified")
        if voronoi is not None:
            self.voronoi = voronoi
        else:
            self.voronoi = SvVoronoiFieldData(vertices, metric=metric)
        self.__description__ = "Voronoi"

    def evaluate(self, x, y, z):
        r = self.voronoi.query(np.array([x,y,z]))
        return r[1]

    def evaluate_grid(self, xs, ys, zs):
        vs = np.stack((xs,ys,zs)).T
        r = self.voronoi.query_array(vs)
        vs = r[1]
        return vs[:,0], vs[:,1], vs[:,2]

class SvScalarFieldCurveMap(SvVectorField):
    def __init__(self, scalar_field, curve, mode):
        self.scalar_field = scalar_field
        self.curve = curve
        self.mode = mode

    def evaluate(self, x, y, z):
        t = self.scalar_field.evaluate(x,y,z)
        if self.mode == 'VALUE':
            return self.curve.evaluate(t)
        elif self.mode == 'TANGENT':
            return self.curve.tangent(t)
        else: # NORMAL
            return self.curve.main_normal(t)

    def evaluate_grid(self, xs, ys, zs):
        ts = self.scalar_field.evaluate_grid(xs, ys, zs)
        if self.mode == 'VALUE':
            vectors = self.curve.evaluate_array(ts)
        elif self.mode == 'TANGENT':
            vectors = self.curve.tangent_array(ts)
        else: # NORMAL
            vectors = self.curve.main_normal_array(ts)
        return vectors[:,0], vectors[:,1], vectors[:,2]

