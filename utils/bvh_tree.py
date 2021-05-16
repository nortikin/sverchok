# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils.bvhtree import BVHTree

def bvh_safe_check(verts, pols):
    len_v = len(verts)
    for p in pols:
        for c in p:
            if c > len_v:
                raise Exception(f"Index {c} should be less than vertices length ({len_v})")

def bvh_tree_from_polygons(vertices, polygons, all_triangles=False, epsilon=0.0, safe_check=True):
    if safe_check:
        bvh_safe_check(vertices, polygons)
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=all_triangles, epsilon=epsilon)
