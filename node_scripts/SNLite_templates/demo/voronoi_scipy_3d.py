"""
in in_points v
out out_verts v
out out_faces s
"""

import numpy as np
import sys

from sverchok.utils.logging import exception, info
from sverchok.data_structure import zip_long_repeat

try:
    import scipy
    from scipy.spatial import Voronoi
except ImportError as e:
    info("SciPy module is not available. Please refer to https://github.com/nortikin/sverchok/wiki/Non-standard-Python-modules-installation for how to install it.")
    raise e

out_verts = []
out_edges = []
out_faces = []

for points in in_points:
    vor = Voronoi(points)

    new_verts = vor.vertices.tolist()
    new_faces = [e for e in vor.ridge_vertices if not -1 in e]

    out_verts.append(new_verts)
    out_faces.append(new_faces)

