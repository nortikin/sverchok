"""
in radius1_in s
in radius2_in s
in teeth_count_in s
in tangent_k_in s
out curves_out C
"""

import numpy as np
from math import pi

from mathutils import Matrix
from sverchok.data_structure import zip_long_repeat
from sverchok.utils.curve.core import SvCircle
from sverchok.utils.curve.bezier import SvBezierCurve

def interweave(a, b):
    w,h = a.shape
    c = np.empty((w*2, h), dtype=a.dtype)
    c[0::2] = a
    c[1::2] = b
    return c

curves_out = []
for radius1s, radius2s, teeth_counts, tangent_ks in zip_long_repeat(radius1_in, radius2_in, teeth_count_in, tangent_k_in):
    for radius1, radius2, teeth_count, tangent_k in zip_long_repeat(radius1s, radius2s, teeth_counts, tangent_ks):
        circle1 = SvCircle(Matrix(), radius1)
        circle2 = SvCircle(Matrix(), radius2)

        t_min, t_max = circle1.get_u_bounds()
        t1s = np.linspace(t_min, t_max, num=teeth_count, endpoint=False)
        dt = (t_max - t_min) / teeth_count / 2
        t2s = np.linspace(t_min + dt, t_max - dt, num = teeth_count)

        points1 = circle1.evaluate_array(t1s)
        tangents1 = circle1.tangent_array(t1s)
        points2 = circle2.evaluate_array(t2s)
        tangents2 = circle2.tangent_array(t2s)
        
        tangents1 *= tangent_k
        tangents2 *= tangent_k

        points = interweave(points1, points2)
        tangents = interweave(tangents1, tangents2)

        _, new_curves = SvBezierCurve.build_tangent_curve(points, tangents, cyclic=True, concat=True)
        curves_out.append(new_curves[0])

