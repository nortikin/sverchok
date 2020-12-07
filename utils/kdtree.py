# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from mathutils import kdtree

from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial import cKDTree

class SvKdTree(object):
    SCIPY = 'SCIPY'
    BLENDER = 'BLENDER'

    @staticmethod
    def new(implementation, points):
        if implementation == SvKdTree.SCIPY:
            return SvSciPyKdTree(points)
        elif implementation == SvKdTree.BLENDER:
            return SvBlenderKdTree(points)

    @staticmethod
    def best_available_implementation():
        if scipy is not None:
            return SvKdTree.SCIPY
        else:
            return SvKdTree.BLENDER

    def __init__(self, points):
        pass

    def query(self, needle, count=1):
        raise Exception("Not implemented")

    def query_array(self, needle, count=1):
        raise Exception("Not implemented")

class SvBlenderKdTree(SvKdTree):
    def __init__(self, points):
        self.kdtree = kdtree.KDTree(len(points))
        for i, v in enumerate(points):
            self.kdtree.insert(v, i)
        self.kdtree.balance()

    def query(self, needle, count=1, **kwargs):
        if count == 1:
            loc, idx, distance = self.kdtree.find(needle)
            if loc is None:
                return None
            else:
                return np.array(loc), idx, distance
        else:
            res = self.kdtree.find_n(needle, count)
            locs = np.array([np.array(loc) for loc, idx, distance in res])
            idxs = np.array([idx for loc, idx, distance in res])
            distances = np.array([distance for loc, idx, distance in res])

            return locs, idxs, distances

    def query_array(self, needle, count=1, **kwargs):
        res = [self.query(item, count) for item in needle]
        locs = [loc for loc, idx, distance in res]
        idxs = [idx for loc, idx, distance in res]
        distances = [distance for loc, idx, distance in res]

        return np.array(locs), np.array(idxs), np.array(distances)

class SvSciPyKdTree(SvKdTree):
    def __init__(self, points):
        self.points = np.asarray(points)
        self.kdtree = cKDTree(self.points)

    def query(self, needle, count=1, **kwargs):
        distance, idx = self.kdtree.query(needle, k=count, **kwargs)
        loc = self.points[idx]
        return loc, idx, distance

    def query_array(self, needle, count=1, **kwargs):
        distances, idxs = self.kdtree.query(needle, k=count, **kwargs)
        locs = self.points[idxs]
        return locs, idxs, distances

