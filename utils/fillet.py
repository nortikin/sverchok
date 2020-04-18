
import numpy as np
from math import tan, sin, pi

from mathutils import Vector, Matrix

from sverchok.utils.curve import SvCircle

class ArcFilletData(object):
    def __init__(self, center, matrix, normal, radius, p1, p2, angle):
        self.center = center
        self.normal = normal
        self.radius = radius
        self.p1 = p1
        self.p2 = p2
        self.angle = angle
        self.matrix = matrix

    def get_curve(self):
        circle = SvCircle(self.matrix, self.radius)
        circle.u_bounds = (0.0, self.angle)
        #circle.u_bounds = (-self.angle, 0.0)
        return circle

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

    return ArcFilletData(center, matrix, normal, radius, p1, p2, big_angle)

