"""
in in_points v
out out_verts v
out out_faces s
"""
import logging

logger = logging.getLogger('sverchok')

try:
    import scipy
    from scipy.spatial import Voronoi
except ImportError as e:
    logger.info("SciPy module is not available. Please refer to https://github.com/nortikin/sverchok/wiki/Non-standard-Python-modules-installation for how to install it.")
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

