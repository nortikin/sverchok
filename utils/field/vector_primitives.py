# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.geom import rotate_around_vector_matrix, CubicSpline
from sverchok.utils.math import (np_dot, np_multiply_matrices_vectors)
from sverchok.utils.integrate import TrapezoidIntegral
from sverchok.utils.field.vector import SvVectorField

class SvCurveIntegral:
    def __init__(self, curve, resolution=100, x_axis=0, y_axis=1):
        self.curve = curve
        self.resolution = resolution
        self.x_axis = x_axis
        self.y_axis = y_axis
        u_min, u_max = curve.get_u_bounds()
        ts = np.linspace(u_min, u_max, num=resolution)
        pts = curve.evaluate_array(ts)
        ys = pts[:,y_axis]
        xs = pts[:,x_axis]
        self.integral = TrapezoidIntegral(xs, ts, ys)
        self.integral.calc()

    def evaluate(self, ts):
        return self.integral.evaluate_linear(ts)

class SvCurveProjection:
    def __init__(self, curve, resolution=100, x_axis=0, y_axis=1):
        self.curve = curve
        self.resolution = resolution
        self.x_axis = x_axis
        self.y_axis = y_axis
        u_min, u_max = curve.get_u_bounds()
        ts = np.linspace(u_min, u_max, num=resolution)
        pts = curve.evaluate_array(ts)
        ys = pts[:,y_axis]
        xs = pts[:,x_axis]
        #print("Xs", xs)
        #print("Ys", ys)
        self.spline = CubicSpline.from_2d_points(xs, ys)

    def evaluate(self, ts):
        u_min, u_max = self.curve.get_u_bounds()
        ts = (ts - u_min) / (u_max - u_min)
        return self.spline.eval(ts)[:,1]

class SvTwistVectorField(SvVectorField):
    def __init__(self, center, axis, angle_along_axis, angle_along_radius,
                 min_z = None, max_z = None, min_r = None, max_r = None):
        self.center = np.asarray(center)
        self.axis = np.asarray(axis)
        self.axis = self.axis / np.linalg.norm(self.axis)
        self.angle_along_axis = angle_along_axis
        self.angle_along_radius = angle_along_radius
        self.min_z = min_z
        self.max_z = max_z
        self.min_r = min_r
        self.max_r = max_r

    def _calc_angles(self, angle, ts):
        if isinstance(angle, (int,float,np.float64)):
            return angle * ts
        else:
            r = angle.evaluate(ts)
            return r

    def evaluate_grid(self, xs, ys, zs):
        pts = np.stack((xs, ys, zs)).T
        dpts = pts - self.center
        ts = np_dot(dpts, self.axis)
        rads = dpts - ts[np.newaxis].T * self.axis
        rs = np.linalg.norm(rads, axis=1)
        if self.min_z is not None or self.max_z is not None:
            ts = np.clip(ts, self.min_z, self.max_z)
        if self.min_r is not None or self.max_r is not None:
            rs = np.clip(rs, self.min_r, self.max_r)
        angles = self._calc_angles(self.angle_along_axis, ts)
        angles += self._calc_angles(self.angle_along_radius, rs)
        #angles = ts * self.angle_along_axis + rs * self.angle_along_radius
        matrices = rotate_around_vector_matrix(self.axis, angles)
        new_pts = np_multiply_matrices_vectors(matrices, dpts)
        new_pts += self.center
        vectors = (new_pts - pts).T
        return vectors[0], vectors[1], vectors[2]

    def evaluate(self, x, y, z):
        rxs, rys, rzs = self.evaluate_grid([x], [y], [z])
        return rxs[0], rys[0], rzs[0]

class SvTaperVectorField(SvVectorField):
    def __init__(self, center, axis, coefficient, min_z=None, max_z=None):
        self.center = np.asarray(center)
        self.axis = np.asarray(axis)
        self.axis = self.axis / np.linalg.norm(self.axis)
        self.coefficient = coefficient
        self.min_z = None
        self.max_z = None
        rho = 1.0 / coefficient
        if min_z is not None:
            self.max_z = rho - min_z
        if max_z is not None:
            self.min_z = rho - max_z

    @classmethod
    def from_base_point_and_vertex(cls, base_point, vertex, **kwargs):
        base_point = np.array(base_point)
        vertex = np.array(vertex)
        rho = np.linalg.norm(base_point - vertex)
        return SvTaperVectorField(vertex, base_point - vertex, 1.0/rho, **kwargs)

    @classmethod
    def from_base_point_and_vector(cls, base_point, vector, **kwargs):
        base_point = np.array(base_point)
        vector = np.array(vector)
        return SvTaperVectorField.from_base_point_and_vertex(base_point, base_point + vector, **kwargs)

    def evaluate_grid(self, xs, ys, zs):
        pts = np.stack((xs, ys, zs)).T
        dpts = pts - self.center
        ts = np_dot(dpts, self.axis)
        projections = ts[np.newaxis].T * self.axis
        rads = dpts - projections
        if self.min_z is not None or self.max_z is not None:
            ts = np.clip(ts, self.min_z, self.max_z)
        rads *= self.coefficient * ts[np.newaxis].T
        new_pts = self.center + projections + rads
        vectors = (new_pts - pts).T
        return vectors[0], vectors[1], vectors[2]

    def evaluate(self, x, y, z):
        rxs, rys, rzs = self.evaluate_grid([x], [y], [z])
        return rxs[0], rys[0], rzs[0]

