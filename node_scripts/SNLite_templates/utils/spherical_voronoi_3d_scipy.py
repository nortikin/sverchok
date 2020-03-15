"""
in in_points v
in in_center v
in in_radius s
out out_verts v
out out_faces s
"""

import numpy as np
import sys

from sverchok.utils.logging import exception, info
from sverchok.data_structure import zip_long_repeat
from sverchok.utils.math import to_spherical, from_spherical

try:
    import scipy
    from scipy.spatial import SphericalVoronoi
except ImportError as e:
    info("SciPy module is not available. Please refer to https://github.com/nortikin/sverchok/wiki/Non-standard-Python-modules-installation for how to install it.")
    raise e

def to_radius(r, v, c):
    x,y,z = v
    x0,y0,z0 = c
    v = x-x0, y-y0, z-z0
    rho, phi, theta = to_spherical(v, "radians")
    x,y,z = from_spherical(r, phi, theta, "radians")
    return x+x0, y+y0, z+z0

out_verts = []
out_edges = []
out_faces = []

for points, center, radius in zip_long_repeat(in_points, in_center, in_radius):
    if isinstance(radius, (list, tuple)):
        radius = radius[0]
    center = center[0]
    #info("Center: %s, radius: %s", center, radius)
    points = np.array([to_radius(radius, v, center) for v in points])

    vor = SphericalVoronoi(points, radius=radius, center=np.array(center))
    vor.sort_vertices_of_regions()

    new_verts = vor.vertices.tolist()
    new_faces = vor.regions

    out_verts.append(new_verts)
    out_faces.append(new_faces)

