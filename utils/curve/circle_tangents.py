# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sqrt, acos, asin, pi

from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.primitives import SvCircle, SvLine

def make_symmetric_arc(xx, circle, bounds):
    arc = circle.copy()
    arc.vectorx = xx * arc.radius
    arc.matrix = SvCircle.calc_matrix(arc.normal, arc.vectorx)
    arc.u_bounds = bounds
    return arc

class SvTwoCircleTangentsData(object):
    def __init__(self):
        self.outer_tangent1 = None
        self.outer_tangent2 = None
        self.outer_arc1 = None
        self.outer_arc2 = None
        self.inner_tangent1 = None
        self.inner_tangent2 = None
        self.inner_arc1 = None
        self.inner_arc2 = None

def calc_two_circles_tangents(circle1, circle2, planar_tolerance=1e-6, calc_outer=True, calc_inner=True):
    dc = circle2.center - circle1.center
    d = np.linalg.norm(dc)
    xx = dc / d

    volume = np.dot(xx, np.cross(circle1.normal, circle2.normal))
    if abs(volume) > planar_tolerance:
        raise Exception(f"Provided circles are not coplanar, volume={volume}")

    result = SvTwoCircleTangentsData()

    # Outer tangents calculation

    dr = circle2.radius - circle1.radius
    if calc_outer and dr < d:
        cos_beta = dr / d
        #print("Cos b", cos_beta)
        beta = acos(-cos_beta)
        
        outer_arc1 = make_symmetric_arc(xx, circle1, (beta, 2*pi-beta))
        outer_arc2 = make_symmetric_arc(xx, circle2, (-beta, beta))
        
        c1p1 = outer_arc1.evaluate(beta)
        c2p1 = outer_arc2.evaluate(beta)
        
        c1p2 = outer_arc1.evaluate(-beta)
        c2p2 = outer_arc2.evaluate(-beta)
        
        result.outer_tangent1 = SvLine.from_two_points(c2p1, c1p1)
        result.outer_tangent2 = SvLine.from_two_points(c1p2, c2p2)
        result.outer_arc1 = outer_arc1
        result.outer_arc2 = outer_arc2

    # Inner tangents calculation 

    r_sum = circle1.radius + circle2.radius
    if calc_inner and r_sum < d:
        cos_beta = r_sum / d
        beta = acos(cos_beta)

        inner_arc1 = make_symmetric_arc(xx, circle1, (beta, 2*pi-beta))
        inner_arc2 = make_symmetric_arc(xx, circle2, (-(pi-beta), pi-beta))
        
        c1p1 = inner_arc1.evaluate(beta)
        c2p1 = inner_arc2.evaluate(pi-beta)
        
        c1p2 = inner_arc1.evaluate(-beta)
        c2p2 = inner_arc2.evaluate(-(pi-beta))
        
        result.inner_tangent1 = SvLine.from_two_points(c2p1, c1p2)
        result.inner_tangent2 = SvLine.from_two_points(c1p1, c2p2)
        result.inner_arc1 = inner_arc1
        result.inner_arc2 = inner_arc2

    return result

class SvCircleTangentData(object):
    def __init__(self):
        self.outer_arc = None
        self.inner_arc = None
        self.tangent1 = None
        self.tangent1_point = None
        self.tangent2 = None
        self.tangent2_point = None

def calc_circle_tangents(circle, point, planar_tolerance=1e-6):
    planar = np.dot(circle.normal, point)
    if abs(planar) > planar_tolerance:
        raise Exception(f"Point is not in the same plane as circle, value={planar}")

    dc = point - circle.center
    d = np.linalg.norm(dc)
    xx = dc / d

    result = SvCircleTangentData()
    if circle.radius < d:
        cos_beta = circle.radius / d
        beta = acos(cos_beta)

        result.inner_arc = make_symmetric_arc(xx, circle, (-beta, beta))
        result.outer_arc = make_symmetric_arc(xx, circle, (beta, 2*pi-beta))

        result.tangent1_point = result.inner_arc.evaluate(-beta)
        result.tangent2_point = result.inner_arc.evaluate(beta)
        result.tangent1 = SvLine.from_two_points(point, result.tangent1_point)
        result.tangent2 = SvLine.from_two_points(point, result.tangent2_point)

    return result

