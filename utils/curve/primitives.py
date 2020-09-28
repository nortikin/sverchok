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
from sverchok.utils.geom import LineEquation, CircleEquation2D, CircleEquation3D, Ellipse3D, rotate_vector_around_vector_np, rotate_vector_around_vector
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.surface.primitives import SvPlane
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve.algorithms import curve_segment

class SvLine(SvCurve):

    def __init__(self, point, direction):
        self.point = np.array(point)
        self.direction = np.array(direction)
        self.u_bounds = (0.0, 1.0)

    def __repr__(self):
        return f"<{self.point} - {self.point+self.direction}>"

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

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)
    
    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)

    def lerp_to(self, curve2, coefficient):
        return self.to_nurbs().lerp_to(curve2, coefficient)

    def reverse(self):
        t_min, t_max = self.get_u_bounds()
        p1, p2 = self.evaluate(t_min), self.evaluate(t_max)
        return SvLine.from_two_points(p2, p1)

    def to_nurbs(self, implementation=SvNurbsMaths.NATIVE):
        knotvector = sv_knotvector.generate(1, 2)
        u_min, u_max = self.get_u_bounds()
        p1 = self.evaluate(u_min)
        p2 = self.evaluate(u_max)
        control_points = np.array([p1, p2])
        return SvNurbsMaths.build_curve(implementation,
                degree=1, knotvector=knotvector,
                control_points = control_points)

    def to_bezier(self):
        u_min, u_max = self.get_u_bounds()
        p1 = self.evaluate(u_min)
        p2 = self.evaluate(u_max)
        return SvBezierCurve([p1, p2])

    def to_bezier_segments(self):
        return [self.to_bezier()]

def rotate_radius(radius, normal, thetas):
    ct = np.cos(thetas)[np.newaxis].T
    st = np.sin(thetas)[np.newaxis].T

    normal /= np.linalg.norm(normal)
    
    binormal = np.cross(normal, radius)
    vx = radius * ct
    vy = binormal * st

    return vx + vy

class SvCircle(SvCurve):

    def __init__(self, matrix=None, radius=None, center=None, normal=None, vectorx=None):
        if matrix is not None:
            self.matrix = np.array(matrix.to_3x3())
            self.center = np.array(matrix.translation)
        elif center is not None:
            self.center = center
        if matrix is None:
            self.matrix = SvCircle.calc_matrix(normal, vectorx)
        if radius is not None:
            self.radius = radius
        else:
            self.radius = np.linalg.norm(vectorx)
        if normal is not None:
            self.normal = normal
        elif matrix is not None:
            z = Vector([0,0,1])
            m = matrix.copy()
            m.translation = Vector()
            self.normal = np.array(m @ z)
        if vectorx is not None:
            self.vectorx = vectorx
        elif matrix is not None:
            x = Vector([radius,0,0])
            m = matrix.copy()
            m.translation = Vector()
            self.vectorx = np.array(m @ x)
        self.u_bounds = (0.0, 2*pi)

    def copy(self):
        circle = SvCircle(radius=self.radius,
                    center=self.center,
                    normal=self.normal,
                    vectorx=self.vectorx)
        circle.u_bounds = self.u_bounds
        return circle

    @staticmethod
    def calc_matrix(normal, vectorx):
        normal = normal / np.linalg.norm(normal)
        vx = vectorx / np.linalg.norm(vectorx)
        vy = np.cross(normal, vx)
        vy = vy / np.linalg.norm(vy)
        m = np.stack((vx, vy, normal))
        return np.linalg.inv(m)

    def set_normal(self, normal):
        self.normal = normal
        self.matrix = SvCircle.calc_matrix(normal, self.vectorx)

    def __repr__(self):
        try:
            r = str(self.get_actual_radius())
        except UnsupportedCurveTypeException:
            r = f"Matrix @ {self.radius}"
        return f"<Circle C={self.center}, N={self.normal}, R={r}>"

    def get_actual_radius(self, tolerance=1e-10):
        x = np.array([self.radius, 0, 0])
        y = np.array([0, self.radius, 0])
        m = self.matrix
        vx = m @ x
        vy = m @ y
        rx = np.linalg.norm(vx)
        ry = np.linalg.norm(vy)
        if abs(rx - ry) > tolerance:
            raise UnsupportedCurveTypeException(f"This SvCircle instance is not an exact circle: {rx} != {ry}")
        return (rx + ry) / 2.0

    @classmethod
    def from_equation(cls, eq):
        """
        Make an instance of SvCircle from an instance of CircleEquation2D/3D.
        """
        # isinstance() wont work properly with "reload scripts".
        if type(eq).__name__ == 'CircleEquation2D':
            matrix = Matrix.Translation(eq.center)
            circle = SvCircle(matrix, eq.radius)
            return circle
        elif type(eq).__name__ == 'CircleEquation3D':
            if eq.point1 is not None:
                circle = SvCircle(center = np.array(eq.center),
                            vectorx = np.array(eq.point1) - np.array(eq.center),
                            normal = eq.normal)
            else:
                circle = SvCircle(eq.get_matrix(), eq.radius)
            if eq.arc_angle:
                circle.u_bounds = (0, eq.arc_angle)
            return circle
        else:
            raise TypeError("Unsupported argument type:" + str(eq))

    @classmethod
    def from_arc(cls, arc, z_axis='Z'):
        """
        Make an instance of SvCircle from an instance of sverchok.utils.sv_curve_utils.Arc
        """
        if arc.radius.real == arc.radius.imag:
            radius = arc.radius.real
            radius_dx = radius_dy = 1.0
            scale_x = scale_y = Matrix.Identity(4)
        else:
            radius = abs(arc.radius)
            radius_dx = arc.radius.real / radius
            radius_dy = arc.radius.imag / radius
            scale_x = Matrix.Scale(radius_dx, 4, (1,0,0))
            scale_y = Matrix.Scale(radius_dy, 4, (0,1,0))
        matrix = Matrix.Translation(Vector((arc.center.real, arc.center.imag, 0)))
        rotation = radians(arc.theta)
        angle = radians(abs(arc.delta))
        rot_z = Matrix.Rotation(rotation, 4, 'Z')
        matrix = matrix @ scale_x @ scale_y @ rot_z
        if arc.delta < 0:
            matrix = matrix @ Matrix.Rotation(radians(180), 4, 'X')

        if z_axis == 'Y':
            matrix = Matrix.Rotation(radians(90), 4, 'X') @ matrix
        elif z_axis == 'X':
            matrix = Matrix.Rotation(radians(90), 4, 'Z') @ Matrix.Rotation(radians(90), 4, 'X') @ matrix
        circle = SvCircle(matrix=matrix, radius=radius)
        circle.u_bounds = (0, angle)
        return circle

    def get_degree(self):
        return 2

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        vx = self.vectorx
        return self.center + rotate_vector_around_vector(vx, self.normal, t)

    def evaluate_array(self, ts):
        #n = len(ts)
        #vx = np.broadcast_to(self.vectorx[np.newaxis], (n,3))
        #return self.center + rotate_vector_around_vector_np(vx, self.normal, ts)
        return self.center + rotate_radius(self.vectorx, self.normal, ts)

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

    def _arc_to_nurbs(self, t_min, t_max, implementation = SvNurbsMaths.NATIVE):
        alpha = t_max - t_min 
        p0_x = cos(t_min)
        p0_y = sin(t_min)
        p2_x = cos(t_max)
        p2_y = sin(t_max)
        t_mid = 0.5*(t_max + t_min)
        theta = 0.5*alpha
        p1_r = 1.0 / cos(theta)
        p1_x = p1_r * cos(t_mid)
        p1_y = p1_r * sin(t_mid)

        control_points = np.array([[p0_x, p0_y, 0],
                                   [p1_x, p1_y, 0],
                                   [p2_x, p2_y, 0]])
        control_points = self.radius * control_points
        control_points = np.apply_along_axis(lambda v: self.matrix @ v, 1, control_points)
        control_points = self.center + control_points

        w1 = cos(theta)
        weights = np.array([1, w1, 1])
        degree = 2
        knotvector = sv_knotvector.generate(degree, 3)
        knotvector = sv_knotvector.rescale(knotvector, t_min, t_max)

        nurbs = SvNurbsMaths.build_curve(implementation,
                    degree, knotvector,
                    control_points, weights)

        if alpha > 2*pi/3:
            nurbs = nurbs.insert_knot(t_mid)

        return nurbs

    def _half_circle_nurbs(self, t_min, implementation = SvNurbsMaths.NATIVE):
        control_points = np.array([[1, 0, 0],
                                   [1, 1, 0],
                                   [0, 1, 0],
                                   [-1, 1, 0],
                                   [-1, 0, 0]])

        ct, st = cos(t_min), sin(t_min)
        rotate = np.array([[ct, -st, 0], [st, ct, 0], [0, 0, 1]])
        control_points = np.apply_along_axis(lambda v: rotate @ v, 1, control_points)

        control_points = self.radius * control_points
        control_points = np.apply_along_axis(lambda v: self.matrix @ v, 1, control_points)
        control_points = self.center + control_points

        sqrt22 = sqrt(2.0)/2.0
        weights = np.array([1, sqrt22, 1, sqrt22, 1])
        pi2 = pi/2.0
        knotvector = np.array([0, 0, 0,
                               pi2, pi2,
                               pi, pi, pi])
        knotvector += t_min

        degree = 2
        nurbs = SvNurbsMaths.build_curve(implementation,
                    degree, knotvector,
                    control_points, weights)
        return nurbs

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        t_min, t_max = self.get_u_bounds()
        epsilon = 1e-6

        if -2*pi < t_min < 0 and 0 < t_max < 2*pi:
            arc1 = self.copy()
            arc1.u_bounds = (2*pi + t_min, 2*pi)
            arc1 = arc1.to_nurbs()
            arc2 = self.copy()
            arc2.u_bounds = (0, t_max)
            arc2 = arc2.to_nurbs()
            return arc1.concatenate(arc2)

        if t_min < 0 or t_max > 2*pi + epsilon:
            raise UnsupportedCurveTypeException(f"Can't transform a circle arc out of 0-2pi bound ({t_min} - {t_max}) to NURBS")

        #print(f"T {t_min},{t_max}, 2pi {2*pi}")
        if t_max - t_min < pi:
            return self._arc_to_nurbs(t_min, t_max, implementation)
        elif t_max - t_min < 2*pi + epsilon:
            half = self._half_circle_nurbs(t_min, implementation)
            if abs(t_max - t_min - pi) < epsilon:
                return half
            arc = self._arc_to_nurbs(t_min + pi, t_max, implementation)
            return half.concatenate(arc)

        control_points = np.array([[1, 0, 0],
                                   [1, 1, 0],
                                   [0, 1, 0],
                                   [-1, 1, 0],
                                   [-1, 0, 0],
                                   [-1, -1, 0],
                                   [0, -1, 0],
                                   [1, -1, 0],
                                   [1, 0, 0]])
        control_points = self.radius * control_points
        control_points = np.apply_along_axis(lambda v: self.matrix @ v, 1, control_points)
        control_points = self.center + control_points
        sqrt22 = sqrt(2.0)/2.0
        weights = np.array([1, sqrt22, 1, sqrt22,
                            1, sqrt22, 1, sqrt22, 1])
        pi2 = pi/2.0
        pi32 = 3*pi/2.0
        knotvector = np.array([0, 0, 0,
                               pi2, pi2,
                               pi, pi,
                               pi32, pi32,
                               2*pi, 2*pi, 2*pi])
        degree = 2
        curve = SvNurbsMaths.build_curve(implementation,
                    degree, knotvector,
                    control_points, weights)

        #if t_min != 0 or t_max != 2*pi:
            #print(f"Cut {t_min} - {t_max}")
            #curve = curve_segment(curve, t_min, t_max)
        return curve

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)
    
    def extrude_along_vector(self, vector):
        return self.to_nurbs().extrude_along_vector(vector)

    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)

    def lerp_to(self, curve2, coefficient):
        return self.to_nurbs().lerp_to(curve2, coefficient)

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

