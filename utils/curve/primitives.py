# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, pi, radians, sqrt

from mathutils import Vector, Matrix

from sverchok.utils.logging import error
from sverchok.utils.geom import LineEquation, CircleEquation2D, CircleEquation3D, Ellipse3D
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.primitives import SvPlane
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.bezier import SvBezierCurve

class SvLine(SvCurve):
    __description__ = "Line"

    def __init__(self, point, direction):
        self.point = np.array(point)
        self.direction = np.array(direction)
        self.u_bounds = (0.0, 1.0)

    @classmethod
    def from_two_points(cls, point1, point2):
        direction = np.array(point2) - np.array(point1)
        return SvLine(point1, direction)

    def get_degree(self):
        return 1

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.point + t * self.direction

    def evaluate_array(self, ts):
        ts = ts[np.newaxis].T
        return self.point + ts * self.direction

    def tangent(self, t):
        tg = self.direction
        n = np.linalg.norm(tg)
        return tg / n

    def tangent_array(self, ts):
        tg = self.direction
        n = np.linalg.norm(tg)
        tangent = tg / n
        result = np.tile(tangent[np.newaxis].T, len(ts)).T
        return result

    def extrude_along_vector(self, vector):
        return SvPlane(self.point, self.direction, vector)

    def to_nurbs(self, implementation=SvNurbsCurve.NATIVE):
        knotvector = sv_knotvector.generate(1, 2)
        u_min, u_max = self.get_u_bounds()
        p1 = self.evaluate(u_min)
        p2 = self.evaluate(u_max)
        control_points = np.array([p1, p2])
        return SvNurbsCurve.build(implementation,
                degree=1, knotvector=knotvector,
                control_points = control_points)

    def to_bezier(self):
        u_min, u_max = self.get_u_bounds()
        p1 = self.evaluate(u_min)
        p2 = self.evaluate(u_max)
        return SvBezierCurve([p1, p2])

class SvCircle(SvCurve):
    __description__ = "Circle"

    def __init__(self, matrix, radius):
        self.matrix = np.array(matrix.to_3x3())
        self.center = np.array(matrix.translation)
        self.radius = radius
        self.u_bounds = (0.0, 2*pi)

    @classmethod
    def from_equation(cls, eq):
        """
        Make an instance of SvCircle from an instance of CircleEquation2D/3D.
        """
        if isinstance(eq, CircleEquation2D):
            matrix = Matrix.Translation(eq.center)
            circle = SvCircle(matrix, eq.radius)
            return circle
        elif isinstance(eq, CircleEquation3D):
            circle = SvCircle(eq.get_matrix(), eq.radius)
            if eq.arc_angle:
                circle.u_bounds = (0, eq.arc_angle)
            return circle
        else:
            raise TypeError("Unsupported argument type:" + str(eq))

    @classmethod
    def from_arc(cls, arc):
        """
        Make an instance of SvCircle from an instance of sverchok.utils.sv_curve_utils.Arc
        """
        radius = abs(arc.radius)
        radius_dx = arc.radius.real / radius
        radius_dy = arc.radius.imag / radius
        matrix = Matrix.Translation(Vector((arc.center.real, arc.center.imag, 0)))
        scale_x = Matrix.Scale(radius_dx, 4, (1,0,0))
        scale_y = Matrix.Scale(radius_dy, 4, (0,1,0))
        rotation = radians(arc.theta)
        angle = radians(abs(arc.delta))
        rot_z = Matrix.Rotation(rotation, 4, 'Z')
        matrix = matrix @ scale_x @ scale_y @ rot_z
        if arc.delta < 0:
            matrix = matrix @ Matrix.Rotation(radians(180), 4, 'X')
        circle = SvCircle(matrix, radius)
        circle.u_bounds = (0, angle)
        return circle

    def get_degree(self):
        return 2

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        r = self.radius
        x = r * cos(t)
        y = r * sin(t)
        return self.matrix @ np.array([x, y, 0]) + self.center

    def evaluate_array(self, ts):
        r = self.radius
        xs = r * np.cos(ts)
        ys = r * np.sin(ts)
        zs = np.zeros_like(xs)
        vertices = np.stack((xs, ys, zs)).T
        return np.apply_along_axis(lambda v: self.matrix @ v, 1, vertices) + self.center

    def tangent(self, t):
        x = - self.radius * sin(t)
        y = self.radius * cos(t)
        z = 0
        return self.matrix @ np.array([x, y, z])

    def tangent_array(self, ts):
        xs = - self.radius * np.sin(ts)
        ys = self.radius * np.cos(ts)
        zs = np.zeros_like(xs)
        vectors = np.stack((xs, ys, zs)).T
        result = np.apply_along_axis(lambda v: self.matrix @ v, 1, vectors)
        return result

#     def second_derivative_array(self, ts):
#         xs = - np.cos(ts)
#         ys = - np.sin(ts)
#         zs = np.zeros_like(xs)
#         vectors = np.stack((xs, ys, zs)).T
#         return np.apply_along_axis(lambda v: self.matrix @ v, 1, vectors)

class SvEllipse(SvCurve):
    __description__ = "Ellipse"

    CENTER = 'center'
    F1 = 'f1'
    F2 = 'f2'

    def __init__(self, matrix, a, b, center_type=CENTER):
        self.matrix = np.array(matrix.to_3x3())
        self.center = np.array(matrix.translation)
        self.center_type = center_type
        self.a = a
        self.b = b
        self.u_bounds = (0, 2*pi)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    @classmethod
    def from_equation(cls, eq):
        """
        input: an instance of sverchok.utils.geom.Ellipse3D
        output: an instance of SvEllipse
        """
        return SvEllipse(eq.get_matrix(), eq.a, eq.b)

    def to_equation(self):
        """
        output: an instance of sverchok.utils.geom.Ellipse3D
        """
        major_radius = self.matrix @ np.array([self.a, 0, 0])
        minor_radius = self.matrix @ np.array([0, self.b, 0])
        eq = Ellipse3D(Vector(self.center), Vector(major_radius), Vector(minor_radius))
        return eq

    @property
    def c(self):
        a, b = self.a, self.b
        return sqrt(a*a - b*b)

    def focal_points(self):
        df = self.matrix @ np.array([self.c, 0, 0])
        f1 = self.center + df
        f2 = self.center - df
        return [f1, f2]

    def get_center(self):
        if self.center_type == SvEllipse.CENTER:
            return self.center
        elif self.center_type == SvEllipse.F1:
            df = self.matrix @ np.array([self.c, 0, 0])
            return self.center + df
        else: # F2
            df = self.matrix @ np.array([self.c, 0, 0])
            return self.center - df

    def get_degree(self):
        return 2

    def evaluate(self, t):
        v = np.array([self.a * cos(t), self.b * sin(t), 0])
        center = self.get_center()
        v = center + self.matrix @ v
        return v

    def evaluate_array(self, ts):
        xs = self.a * np.cos(ts)
        ys = self.b * np.sin(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        center = self.get_center()
        return center + vs

    def tangent(self, t):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts):
        xs = - self.a * np.sin(ts)
        ys = self.b * np.cos(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        return vs

    def second_derivative(self, t):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts):
        xs = - self.a * np.cos(ts)
        ys = - self.b * np.sin(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        return vs

