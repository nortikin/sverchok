"""
in verts_in v
out curve_out C
"""

import numpy as np

from sverchok.data_structure import zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.bezier import SvBezierCurve

curve_out = []
for verts in verts_in:
    verts = np.array(verts)
    curve = SvBezierCurve.interpolate(verts, metric='POINTS')
    curve_out.append(curve)

