"""
in p_in s
in q_in s
in t_in s
out field_out VF
"""

import numpy as np
import math

from sverchok.data_structure import zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.vector import SvVectorField

class Rotate4dField(SvVectorField):
    __description__ = "4D Rotation"
    def __init__(self, p, q, t):
        self.p = p
        self.q = q
        self.t = t

    def evaluate(self, x, y, z):
        p, q, t = self.p, self.q, self.t

        cos_pt = math.cos(p*t)
        sin_pt = math.sin(p*t)
        cos_qt = math.cos(q*t)
        sin_qt = math.sin(q*t)

        # reverse stereographically project to Riemann hypersphere
        xb = 2 * x / (1 + x * x + y * y + z * z)
        yb = 2 * y / (1 + x * x + y * y + z * z)
        zb = 2 * z / (1 + x * x + y * y + z * z)
        wb = (-1 + x * x + y * y + z * z) / (1 + x * x + y * y + z * z)

        # now rotate the hypersphere (use p = q = 1 for isoclinic rotations)
        # and vary t between 0 and 2*PI
        xc = +xb * cos_pt + yb * sin_pt
        yc = -xb * sin_pt + yb * cos_pt
        zc = +zb * cos_qt - wb * sin_qt
        wc = +zb * sin_qt + wb * cos_qt

        # then project stereographically back to flat 3D
        xd = xc / (1 - wc)
        yd = yc / (1 - wc)
        zd = zc / (1 - wc)

        result = np.array([xd, yd, zd])
        return result - np.array([x,y,z])

    def evaluate_grid(self, xs, ys, zs):
        p, q, t = self.p, self.q, self.t

        cos_pt = math.cos(p*t)
        sin_pt = math.sin(p*t)
        cos_qt = math.cos(q*t)
        sin_qt = math.sin(q*t)

        # reverse stereographically project to Riemann hypersphere
        xb = 2 * xs / (1 + xs * xs + ys * ys + zs * zs)
        yb = 2 * ys / (1 + xs * xs + ys * ys + zs * zs)
        zb = 2 * zs / (1 + xs * xs + ys * ys + zs * zs)
        wb = (-1 + xs * xs + ys * ys + zs * zs) / (1 + xs * xs + ys * ys + zs * zs)

        # now rotate the hypersphere (use p = q = 1 for isoclinic rotations)
        # and vary t between 0 and 2*PI
        xc = +xb * cos_pt + yb * sin_pt
        yc = -xb * sin_pt + yb * cos_pt
        zc = +zb * cos_qt - wb * sin_qt
        wc = +zb * sin_qt + wb * cos_qt

        # then project stereographically back to flat 3D
        xd = xc / (1 - wc)
        yd = yc / (1 - wc)
        zd = zc / (1 - wc)

        return xd - xs, yd - ys, zd - zs

field_out = []

for ps, qs, ts in zip_long_repeat(p_in, q_in, t_in):
    for p, q, t in zip_long_repeat(ps, qs, ts):
        field = Rotate4dField(p, q, t)
        field_out.append(field)

