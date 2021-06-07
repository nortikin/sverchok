# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils.bvhtree import BVHTree
import numpy as np

def bvh_safe_check(verts, pols):
    len_v = len(verts)
    if isinstance(pols, np.ndarray):
        max_c = np.amax(pols)
        if max_c > len_v:
            raise Exception(f"Index {max_c} should be less than vertices length ({len_v})")
    else:
        for p in pols:
            for c in p:
                if c > len_v:
                    raise Exception(f"Index {c} should be less than vertices length ({len_v})")

def bvh_tree_from_polygons(vertices, polygons, all_triangles=False, epsilon=0.0, safe_check=True):
    if safe_check:
        bvh_safe_check(vertices, polygons)
    if isinstance(vertices, np.ndarray):
        vertices = vertices.tolist()
    if isinstance(polygons, np.ndarray):
        polygons = polygons.tolist()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=all_triangles, epsilon=epsilon)
