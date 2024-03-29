
import numpy as np
from math import tan, sin, pi

from mathutils import Vector, Matrix

from sverchok.utils.curve.primitives import SvCircle, SvLine
from sverchok.utils.curve.bezier import SvBezierCurve

class ArcFilletData(object):
    def __init__(self, center, matrix, normal, radius, p1, p2, v2, angle):
        self.center = center
        self.normal = normal
        self.radius = radius
        self.p1 = p1
        self.p2 = p2
        self.vertex = np.array(v2)
        self.angle = angle
        self.matrix = matrix

    def get_circular_arc(self):
        center = np.array(self.center)
        normal = np.array(self.normal)
        p1 = np.array(self.p1)

        circle = SvCircle(center = center,
                    normal = -normal,
                    vectorx = p1 - center)
        circle.u_bounds = (0.0, self.angle)
        #circle.u_bounds = (-self.angle, 0.0)
        return circle

    def get_bezier_arc(self):
        cpts = np.array([self.p1, self.vertex, self.p2])
        return SvBezierCurve(cpts)

    def get_bevel(self):
        return SvLine.from_two_points(self.p1, self.p2)

def calc_fillet(v1, v2, v3, radius):
    if not isinstance(v1, Vector):
        v1 = Vector(v1)
    if not isinstance(v2, Vector):
        v2 = Vector(v2)
    if not isinstance(v3, Vector):
        v3 = Vector(v3)

    dv1 = v1 - v2
    dv2 = v3 - v2
    dv1n, dv2n = dv1.normalized(), dv2.normalized()
    angle = dv1.angle(dv2)
    if abs(angle) < 1e-6 or abs(angle-pi) < 1e-6:
        # The two edges are parallel
        return None

    angle2 = angle / 2.0
    big_angle = pi - angle

    edge_len = radius / tan(angle2)
    p1 = v2 + edge_len * dv1n
    p2 = v2 + edge_len * dv2n

    center_len = radius / sin(angle2)
    center = v2 + center_len * (dv1n + dv2n).normalized()

    normal = dv1.cross(dv2).normalized()
    to_p1 = (p1 - center).normalized()
    binormal = normal.cross(to_p1).normalized()

    matrix = Matrix([to_p1, -binormal, normal]).to_4x4().inverted()
    matrix.translation = center

    return ArcFilletData(center, matrix, normal, radius, p1, p2, v2, big_angle)

