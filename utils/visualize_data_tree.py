# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, sin, cos

from mathutils import Matrix

from sverchok.data_structure import get_max_data_nesting_level, NUMERIC_DATA_TYPES
from sverchok.core.sockets import (
        SvMatrixSocket,
        SvStringsSocket, SvCurveSocket,
        SvSurfaceSocket, SvObjectSocket,
        SvScalarFieldSocket, SvVectorFieldSocket
    )
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.field.vector import SvVectorField
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.core.sockets import STANDARD_TYPES

class Line:
    def __init__(self, curve, skip=False):
        self.curve = curve
        self.skip = skip

class Item:
    def __init__(self, value, point):
        self.color = Item.get_color(value)
        self.point = point

    @staticmethod
    def get_color(value):
        if isinstance(value, NUMERIC_DATA_TYPES):
            return SvStringsSocket.color
        elif isinstance(value, str):
            return SvStringsSocket.color
        elif isinstance(value, Matrix):
            return SvMatrixSocket.color
        elif isinstance(value, SvCurve):
            return SvCurveSocket.color
        elif isinstance(value, SvSurface):
            return SvSurfaceSocket.color
        elif isinstance(value, SvScalarField):
            return SvScalarFieldSocket.color
        elif isinstance(value, SvVectorField):
            return SvVectorFieldSocket.color
        else:
            return SvObjectSocket.color

def mk_line(r1, r2, phi1, phi2, skip=False):
    phi1 += pi/2
    phi2 += pi/2
    delta_r = (r2 - r1) / 3.0
    p1 = np.array([r1*cos(phi1), r1*sin(phi1), 0])
    dphi = phi2 - phi1
    dr1 = r1 * dphi# / 2.0
    p2 = p1 + np.array([-dr1*sin(phi1), dr1*cos(phi1), 0])
    p4 = np.array([r2*cos(phi2), r2*sin(phi2), 0])
    p3 = p4 - np.array([delta_r*cos(phi2), delta_r*sin(phi2), 0])
    return Line(SvCubicBezierCurve(p1, p2, p3, p4), skip)

PADDING = pi/120
MIN_SPACING = 0.12

def draw_level(r1, delta_r, phi_start, phi_min, phi_max, data, allow_skip=True):
    if data is None:
        return []
    if not isinstance(data, (list, tuple, np.ndarray)):
        pt = [r1*cos(phi_start+pi/2), r1*sin(phi_start+pi/2), 0]
        return 0, [Item(data, pt)]
    r2 = r1+delta_r
    N = len(data)
    if N == 1:
        level, lines = draw_level(r2, delta_r, phi_start, phi_min, phi_max, data[0], allow_skip=allow_skip)
        print(f"Single: return {level+1}")
        return (level+1), [mk_line(r1, r2, phi_start, phi_start)] + lines

    phi_range = phi_max - phi_min

    def calc_phis(num):
        #print(f"calc_phis({num})")
        phis = np.linspace(phi_min, phi_max, num=num, endpoint=False)
        delta_phi = phis[1] - phis[0]
        phis += delta_phi*0.5
        return delta_phi, phis

    delta_phi, phis = calc_phis(N)
    #spacing = r2 * delta_phi
    draw_max = N
    idxs = np.arange(N)
    #print(f"N {N}, Delta {phi_range}, Dphi {delta_phi}, ms {MIN_SPACING}")
    if allow_skip and N > 3 and r2*phi_range > MIN_SPACING and r2*delta_phi < MIN_SPACING:
        min_angle = MIN_SPACING / r2
        fixed_N = int((phi_max - phi_min) / min_angle)
        draw_max = max(fixed_N // 2, 1)
        fixed_N = draw_max * 2 + 1
        delta_phi, phis = calc_phis(min(N, fixed_N))
        idxs = np.concatenate((idxs[:draw_max], [-1], idxs[-draw_max:]))

    result = []
    max_level = 0
    for i, phi in zip(idxs, phis):
        p1 = phi - 0.45*delta_phi# + PADDING
        p2 = phi + 0.45*delta_phi# - PADDING
        skip = i < 0
        line = mk_line(r1, r2, phi_start, phi, skip=skip)
        result.append(line)
        if not skip:
            level, lines = draw_level(r2, delta_r, phi, p1, p2, data[i], allow_skip=allow_skip)
            max_level = max(level, max_level)
            result.extend(lines)
    return max_level+1, result

def data_tree_lines(delta_r, data, allow_skip=True):
    return draw_level(0.0, delta_r, 0.0, -pi, pi, data, allow_skip=allow_skip)

def data_tree_curves(delta_r, data, allow_skip=True):
    lines = draw_level(0.0, delta_r, 0.0, -pi, pi, data, allow_skip=allow_skip)[1]
    return [line.curve for line in lines if isinstance(line, Line)]

def nesting_circles(delta_r, nesting):
    radiuses = delta_r * np.arange(1, nesting+1)
    m = Matrix.Rotation(-pi/2, 4, 'Z')
    def mk_circle(radius):
        circle = SvCircle(m, radius)
        circle.u_bounds = (0.1, 2*pi-0.1)
        return circle
    circles = [mk_circle(radius) for radius in radiuses]
    return circles

def data_nesting_circles(delta_r, data):
    nesting = get_max_data_nesting_level(data, STANDARD_TYPES)
    return nesting_circles(delta_r, nesting)

