# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Module containing primitive curve types: straight lines, circles, ellipses.
"""

import numpy as np
from math import sin, cos, pi, radians, sqrt

from mathutils import Vector, Matrix

from sverchok.utils.geom import LineEquation, CircleEquation2D, CircleEquation3D, Ellipse3D, rotate_vector_around_vector_np, rotate_vector_around_vector
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve, UnsupportedCurveTypeException
from sverchok.utils.surface.primitives import SvPlane
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve.algorithms import curve_segment

class SvLine(SvCurve):
    """
    Straight line segment curve.
    """

    def __init__(self, point, direction, u_bounds=None):
        """
        Args:
            point: a point on a line.
            direction: directing vector of a line.
        """
        self.point = np.array(point)
        self.direction = np.array(direction)
        if u_bounds is None:
            u_bounds = (0.0, 1.0)
        self.u_bounds = u_bounds

    def __repr__(self):
        return f"<{self.point} - {self.point+self.direction}>"

    @classmethod
    def from_two_points(cls, point1, point2):
        """
        Generate straight line segment from two points.
        """
        direction = np.array(point2) - np.array(point1)
        return SvLine(point1, direction)
    
    def copy(self, u_bounds=None):
        if u_bounds is None:
            u_bounds = self.u_bounds
        return SvLine(self.point, self.direction, u_bounds=u_bounds)

    def get_degree(self):
        return 1

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.point + t * self.direction

    def evaluate_array(self, ts):
        ts = ts[np.newaxis].T
        return self.point + ts * self.direction

    def tangent(self, t, tangent_delta=None):
        tg = self.direction
        n = np.linalg.norm(tg)
        return tg / n

    def tangent_array(self, ts, tangent_delta=None):
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

    def split_at(self, t):
        t_min, t_max = self.get_u_bounds()
        curve1 = self.copy(u_bounds=(t_min, t))
        curve2 = self.copy(u_bounds=(t, t_max))
        return curve1, curve2

    def reverse(self):
        t_min, t_max = self.get_u_bounds()
        p1, p2 = self.evaluate(t_min), self.evaluate(t_max)
        return SvLine.from_two_points(p2, p1)

    def to_nurbs(self, implementation=SvNurbsMaths.NATIVE):
        u_min, u_max = self.get_u_bounds()
        knotvector = sv_knotvector.generate(1, 2)
        knotvector = sv_knotvector.rescale(knotvector, u_min, u_max)
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

    def concatenate(self, curve2, tolerance=1e-6, remove_knots=False):
        return self.to_nurbs().concatenate(curve2, tolerance=tolerance, remove_knots=remove_knots)

    def reparametrize(self, new_t_min, new_t_max):
        t_min, t_max = self.get_u_bounds()
        scale = (t_max - t_min) / (new_t_max - new_t_min)
        new_direction = self.direction * scale
        new_point = self.point + self.direction * (t_min - scale * new_t_min)
        return SvLine(new_point, new_direction, u_bounds = (new_t_min, new_t_max))

    def is_polyline(self):
        return True

    def get_polyline_vertices(self):
        return np.array(self.get_end_points())

    def is_closed(self, *args):
        return False

    def extrude_along_vector(self, vector):
        return self.to_nurbs().extrude_along_vector(vector)

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)
    
    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)

    def lerp_to(self, curve2, coefficient):
        return self.to_nurbs().lerp_to(curve2, coefficient)

class SvPointCurve(SvCurve):
    __description__ = "Single-Point"

    def __init__(self, point):
        self.point = np.asarray(point)

    def evaluate(self, t):
        return self.point

    def evaluate_array(self, ts):
        points = np.empty((len(ts),3))
        points[:] = self.point
        return points
    
    def get_u_bounds(self):
        return (0.0, 1.0)

    def get_degree(self):
        return 1

    def to_bezier(self):
        u_min, u_max = self.get_u_bounds()
        p1 = self.evaluate(u_min)
        p2 = self.evaluate(u_max)
        return SvBezierCurve([p1, p2])

    def to_bezier_segments(self):
        return [self.to_bezier()]

    def is_closed(self, *args):
        return False

    def concatenate(self, curve2, *args):
        return curve2

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        return self.to_bezier().to_nurbs()

    def reverse(self):
        return SvPointCurve(self.point)


def rotate_radius(radius, normal, thetas):
    """Internal method"""
    ct = np.cos(thetas)[np.newaxis].T
    st = np.sin(thetas)[np.newaxis].T

    normal /= np.linalg.norm(normal)
    
    binormal = np.cross(normal, radius)
    vx = radius * ct
    vy = binormal * st

    return vx + vy

class SvCircle(SvCurve):
    """
    Circle (or circular arc) curve.
    """

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

    def get_mu_matrix(self):
        m = Matrix(self.matrix).to_4x4()
        m.translation = Vector(self.center)
        return m

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

    def tangent(self, t, tangent_delta=None):
        x = - self.radius * sin(t)
        y = self.radius * cos(t)
        z = 0
        return self.matrix @ np.array([x, y, z])

    def tangent_array(self, ts, tangent_delta=None):
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

    def to_nurbs_arc(self, n=4, t_min=None, t_max=None, implementation = SvNurbsMaths.NATIVE):
        if t_min is None:
            t_min = 0.0
        if t_max is None:
            t_max = 2*pi

        if t_max < t_min:
            return self.to_nurbs_arc(n=n, t_max=t_min, t_min=t_max, implementation=implementation).reverse()

        omega = t_max - t_min
        alpha = pi / n
        n_full_arcs = round(omega // (2*alpha))
        small_arc_angle = omega % (2*alpha)

        idxs_full = np.array(range(2*n_full_arcs+1), dtype=np.float64)
        ts_full = pi * idxs_full / n + t_min
        rs_full = np.where(idxs_full % 2 == 0, 1.0, 1.0 / cos(alpha))

        xs_full = rs_full * np.cos(ts_full)
        ys_full = rs_full * np.sin(ts_full)
        zs_full = np.zeros_like(xs_full)

        weights_full = np.where(idxs_full % 2 == 0, 1.0, cos(alpha))

        knots_full = np.array(range(n_full_arcs+1), dtype=np.float64)
        knots_full = 2*pi * knots_full / n + t_min
        knots_full = np.repeat(knots_full, 2)

        if small_arc_angle > 1e-6:
            t_mid_small_arc = ts_full[-1] + small_arc_angle / 2.0
            r_mid_small_arc = 1.0 / cos(small_arc_angle / 2.0)
            x_mid_small_arc = r_mid_small_arc * cos(t_mid_small_arc)
            y_mid_small_arc = r_mid_small_arc * sin(t_mid_small_arc)
            z_mid_small_arc = 0.0

            x_end = cos(t_max)
            y_end = sin(t_max)
            z_end = 0.0

            xs = np.concatenate((xs_full, [x_mid_small_arc, x_end]))
            ys = np.concatenate((ys_full, [y_mid_small_arc, y_end]))
            zs = np.concatenate((zs_full, [z_mid_small_arc, z_end]))

            weight_mid_small_arc = cos(small_arc_angle / 2.0)
            weight_end = 1.0
            weights = np.concatenate((weights_full, [weight_mid_small_arc, weight_end]))

            knots = np.concatenate((knots_full, [t_max, t_max]))
        else:
            xs = xs_full
            ys = ys_full
            zs = zs_full

            weights = weights_full
            knots = knots_full

        knots = np.concatenate(([knots[0]], knots, [knots[-1]]))

        control_points = np.stack((xs, ys, zs)).T
        control_points = self.radius * control_points
        control_points = np.apply_along_axis(lambda v: self.matrix @ v, 1, control_points)
        control_points = self.center + control_points

        degree = 2
        curve = SvNurbsMaths.build_curve(implementation,
                    degree, knots,
                    control_points, weights)
        return curve

    def to_nurbs_quadric(self, n=3, t_min=None, t_max=None, parametrization = 'C2', implementation = SvNurbsMaths.NATIVE):
        """
        Convert the circle to NURBS curve with 4-degree parametrization.

        This implements the algorithm described in the paper:
        Carole Blanc, Christophe Schlick.
        More Accurate Representation of Conics by NURBS.
        Technical Report, LaBRI, 1995.

        Args:
            n: number of subdivisions, usually 3, 4 or 6.
            t_min, t_max: indicate the arc to be converted.
            parametrization: 'C2' for parametrization with continuous 2nd
                derivative; 'QIDEAL' for quasi-ideal parametrization, i.e. for
                parametrization which is almost identical to trigonometric
                parametrization.
            implementation: implementation of Nurbs mathematics.

        Returns:
            an instance of SvNurbsCurve.
        """
        if parametrization not in {'C2', 'QIDEAL'}:
            raise Exception("Unsupported parametrization type")

        if t_min is None:
            t_min = 0.0
        if t_max is None:
            t_max = 2*pi

        if t_max < t_min:
            return self.to_nurbs_quadric(n=n, t_max=t_min, t_min=t_max, implementation=implementation).reverse()

        def make_quad_arc(t1, t2):
            p1 = [cos(t1), sin(t1), 0.0]
            alpha = (t2 - t1)/2.0
            r_mid = 1.0 / cos(alpha)
            t_mid = (t1 + t2)/2.0
            p_mid = [r_mid*cos(t_mid), r_mid*sin(t_mid), 0.0]
            p2 = [cos(t2), sin(t2), 0.0]
            points = np.array([p1, p_mid, p2])

            w = cos(alpha)
            return points, w

        def make_quadric_arc(t1, t2):
            ps, w = make_quad_arc(t1, t2)

            if parametrization == 'C2':
                p = (1.0 + sqrt(5.0 + 4.0*w)) / (2*(1.0 + w))
            else:
                phi = (t2 - t1) / 2.0
                cosphi = cos(phi / 5.0)
                p = (4 - 2*cosphi**3 + cosphi) / (-1 + 8*cosphi**3 - 4*cosphi)

            q0 = ps[0]
            q1 = (ps[0] + w*ps[1])/(1.0 + w)
            q2 = (p*p*ps[0] + 2*w*(1+p*p)*ps[1] + p*p*ps[2]) / (2*(p*p + p*p*w + w))
            q3 = (ps[2] + w*ps[1]) / (1.0 + w)
            q4 = ps[2]

            w0 = 1.0
            w1 = p*(1.0 + w)/2.0
            w2 = (p*p + p*p*w + w)/3.0
            w3 = w1
            w4 = w0

            degree = 4
            knots = (t2 - t1) * sv_knotvector.generate(degree, 5)
            control_points = np.array([q0, q1, q2, q3, q4])
            weights = np.array([w0, w1, w2, w3, w4])
            return SvNurbsMaths.build_curve(implementation,
                        degree, knots,
                        control_points, weights)

        omega = t_max - t_min
        alpha = pi / n
        full_arc_angle = 2*alpha
        n_full_arcs = round(omega // full_arc_angle)
        small_arc_angle = omega % full_arc_angle
        ts_full = [t_min + full_arc_angle*i for i in range(n_full_arcs+1)]
        full_arcs = [make_quadric_arc(t1, t2) for t1,t2 in zip(ts_full, ts_full[1:])]
        if small_arc_angle > 1e-6:
            small_arc = make_quadric_arc(ts_full[-1], t_max)
            small_arcs = [small_arc]
        else:
            small_arcs = []

        all_arcs = full_arcs + small_arcs
        unit_arc = all_arcs[0]
        for arc in all_arcs[1:]:
            unit_arc = unit_arc.concatenate(arc)

        control_points = unit_arc.get_control_points()
        control_points = self.radius * control_points
        control_points = np.apply_along_axis(lambda v: self.matrix @ v, 1, control_points)
        control_points = self.center + control_points

        curve = unit_arc.copy(control_points = control_points)
        return curve

    def to_nurbs_full(self, n=4, parametrization = 'SIMPLE', implementation = SvNurbsMaths.NATIVE):
        """
        Convert fulll circle to a NURBS curve.

        Args:
            n: number of subdivisions, usually 3, 4 or 6.
            paramerization: 'SIMPLE' for traditional (2-degree) circle
                parametrization; 'C2' for 4-degree parametrization with continuous
                2nd derivative; 'QIDEAL' for quasi-ideal parametrization, i.e. for
                4-degree parametrization which is almost identical to trigonometric
                parametrization.
            implementation: implementation of Nurbs mathematics.

        Returns:
            an instance of SvNurbsCurve.
        """
        if parametrization == 'SIMPLE':
            return self.to_nurbs_arc(n=n, implementation=implementation)
        elif parametrization in {'C2', 'QIDEAL'}:
            return self.to_nurbs_quadric(n=n, parametrization=parametrization, implementation=implementation)
        else:
            raise Exception("Unsupported parametrization type")

    def reverse(self):
        circle = self.copy()
        u1, u2 = self.u_bounds
        circle.u_bounds = (2*pi - u2, 2*pi - u1)
        circle.normal = - circle.normal
        return circle

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

    def elevate_degree(self, delta=None, target=None):
        return self.to_nurbs().elevate_degree(delta=delta, target=target)

#     def concatenate(self, curve2, tolerance=1e-6, remove_knots=False):
#         t_min, t_max = self.get_u_bounds()
#         return self.to_nurbs_arc(t_min=t_min, t_max=t_max).concatenate(curve2, tolerance=tolerance, remove_knots=remove_knots)

class SvEllipse(SvCurve):
    """
    Ellipse curve.
    """
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
        Build an instance of SvEllipse from `sverchok.utils.geom.Ellipse3D`.
        """
        return SvEllipse(eq.get_matrix(), eq.a, eq.b)

    def to_equation(self):
        """
        Convert an instance of SvEllipse to `sverchok.utils.geom.Ellipse3D`.
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
        """
        Calculate ellipse focal points.

        Returns:
            list of two points.
        """
        df = self.matrix @ np.array([self.c, 0, 0])
        f1 = self.center + df
        f2 = self.center - df
        return [f1, f2]

    def get_center(self):
        """
        Calculate ellipse center.
        """
        if self.center_type == SvEllipse.CENTER:
            return self.center
        elif self.center_type == SvEllipse.F1:
            df = self.matrix @ np.array([self.c, 0, 0])
            return self.center - df
        else: # F2
            df = self.matrix @ np.array([self.c, 0, 0])
            return self.center + df

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

    def tangent(self, t, tangent_delta=None):
        return self.tangent_array(np.array([t]))[0]

    def tangent_array(self, ts, tangent_delta=None):
        xs = - self.a * np.sin(ts)
        ys = self.b * np.cos(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        return vs

    def second_derivative(self, t, tangent_delta=None):
        return self.second_derivative_array(np.array([t]))[0]

    def second_derivative_array(self, ts, tangent_delta=None):
        xs = - self.a * np.cos(ts)
        ys = - self.b * np.sin(ts)
        zs = np.zeros_like(xs)
        vs = np.array((xs, ys, zs)).T
        vs = np.apply_along_axis(lambda v : self.matrix @ v, 1, vs)
        return vs

    def to_nurbs(self, implementation=SvNurbsMaths.NATIVE):
        """
        Convert the ellipse to SvNurbsCurve.
        """
        if self.a == 0 and self.b == 0:
            coef_x = 0
            coef_y = 0
            radius = 0
        elif self.a == 0:
            coef_x = 0
            coef_y = 1
            radius = self.b
        elif self.b == 0:
            coef_x = 1
            coef_y = 0
            radius = self.a
        else:
            coef_x = 1
            coef_y = self.b/self.a
            radius = self.a
        scale = Matrix([[coef_x,0,0], [0, coef_y, 0], [0, 0, 1]]).to_4x4()
        matrix = Matrix(self.matrix).to_4x4()
        matrix.translation = Vector(self.get_center())
        circle = SvCircle(matrix = matrix @ scale, radius = radius,
                    center = self.get_center())
        return circle.to_nurbs(implementation)

    def concatenate(self, curve2, tolerance=1e-6, remove_knots=False):
        return self.to_nurbs().concatenate(curve2, tolerance=tolerance, remove_knots=remove_knots)

