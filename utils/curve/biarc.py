# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, acos
from cmath import exp as cexp, phase as arg

from mathutils import Vector, Matrix

from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve.algorithms import SvConcatCurve, concatenate_curves

class SvBiArc(SvConcatCurve):
    def __init__(self, arc1, arc2):
        super().__init__([arc1, arc2])
        self.arc1 = arc1
        self.arc2 = arc2

    def __repr__(self):
        return f"<BiArc C1={self.arc1.center} R1={self.arc1.radius} C2={self.arc2.center} R2={self.arc2.radius}>"

    @staticmethod
    def calc(point_a, point_b, tangent_a, tangent_b, p, planar_tolerance=1e-6):
        xx = point_b - point_a
        xx /= np.linalg.norm(xx)
        tangent_normal = np.cross(tangent_a, tangent_b)
        volume = np.dot(xx, tangent_normal)
        if abs(volume) > planar_tolerance:
            raise Exception(f"Provided tangents are not coplanar, volume={volume}")

        zz_a = np.cross(tangent_a, xx)
        zz_b = np.cross(tangent_b, xx)
        zz = (zz_a + zz_b)
        zz /= np.linalg.norm(zz)
        yy = np.cross(zz, xx)

        c = np.linalg.norm(point_b - point_a) * 0.5
        
        tangent_a /= np.linalg.norm(tangent_a)
        tangent_b /= np.linalg.norm(tangent_b)

        to_center_a = np.cross(zz, tangent_a)
        to_center_b = - np.cross(zz, tangent_b)

        matrix_inv = np.stack((xx, yy, zz))
        matrix = np.linalg.inv(matrix_inv)

        # TODO: sin(arccos(...)) = ...
        alpha = acos(np.dot(tangent_a, xx))
        beta = acos(np.dot(tangent_b, xx))
        if np.dot(tangent_a, yy) > 0:
            alpha = - alpha
        if np.dot(tangent_b, yy) > 0:
            beta = - beta
        #print("A", alpha, "B", beta)

        omega = (alpha + beta) * 0.5
        r1 = c/(sin(alpha) + sin(omega) / p)
        r2 = c/(sin(beta) + p * sin(omega))
        #print("R1", r1, "R2", r2)
        theta1 = 2 * arg(cexp(-1j * alpha) + cexp(-1j*omega)/p)
        theta2 = 2 * arg(cexp(1j*beta) + p*cexp(1j*omega))
        #print("T1", theta1, "T2", theta2)

        vectorx_a = r1 * to_center_a
        center1 = point_a + vectorx_a
        center2 = point_b + r2 * to_center_b

        arc1 = SvCircle(#radius = r1,
                    center = center1,
                    normal = -zz, vectorx = point_a - center1)
        if theta1 > 0:
            arc1.u_bounds = (0.0, theta1)
        else:
            theta1 = -theta1
            arc1.u_bounds = (0.0, theta1)
            arc1.set_normal(-arc1.normal)

        junction = arc1.evaluate(theta1)
        #print("J", junction)

        arc2 = SvCircle(#radius = r2,
                    center = center2,
                    normal = -zz, vectorx = junction - center2)
        if theta2 > 0:
            arc2.u_bounds = (0.0, theta2)
        else:
            theta2 = -theta2
            arc2.u_bounds = (0.0, theta2)
            arc2.set_normal(-arc2.normal)

        curve = SvBiArc(arc1, arc2)
        curve.p = p
        curve.junction = junction

        return curve

    def to_nurbs(self, implementation=None):
        return concatenate_curves([self.arc1.to_nurbs(), self.arc2.to_nurbs()], allow_generic=False)

    def make_revolution_surface(self, point, direction, v_min, v_max, global_origin):
        return self.to_nurbs().make_revolution_surface(point, direction, v_min, v_max, global_origin)
    
    def extrude_along_vector(self, vector):
        return self.to_nurbs().extrude_along_vector(vector)

    def make_ruled_surface(self, curve2, vmin, vmax):
        return self.to_nurbs().make_ruled_surface(curve2, vmin, vmax)

    def extrude_to_point(self, point):
        return self.to_nurbs().extrude_to_point(point)

    def lerp_to(self, curve2, coefficient):
        if isinstance(curve2, SvBezierCurve) and curve2.degree == self.degree:
            points = (1.0 - coefficient) * self.points + coefficient * curve2.points
            return SvBezierCurve(points)
        return self.to_nurbs().lerp_to(curve2, coefficient)
    
    def split_at(self, t):
        return self.to_nurbs().split_at(t)

    def cut_segment(self, new_t_min, new_t_max, rescale=False):
        return self.to_nurbs().cut_segment(new_t_min, new_t_max, rescale=rescale)

