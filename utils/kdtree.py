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
    def new(implementation, points, power=2):
        if implementation == SvKdTree.SCIPY:
            return SvSciPyKdTree(points, power=power)
        elif implementation == SvKdTree.BLENDER:
            if power == 2:
                return SvBlenderKdTree(points)
            else:
                return SvBruteforceKdTree(points, power=power)

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

    def query_range(self, needle, radius, **kwargs):
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

    def query_range(self, needle, radius, **kwargs):
        res = self.kdtree.find_range(needle, radius)
        idxs = [r[1] for r in res]
        res = [tuple(r[0]) for r in res]
        return  idxs, np.array(res)

class SvSciPyKdTree(SvKdTree):
    def __init__(self, points, power=2):
        self.points = np.asarray(points)
        self.kdtree = cKDTree(self.points)
        self.power = power

    def query(self, needle, count=1, **kwargs):
        distance, idx = self.kdtree.query(needle, k=count, p=self.power, **kwargs)
        loc = self.points[idx]
        return loc, idx, distance

    def query_array(self, needle, count=1, **kwargs):
        distances, idxs = self.kdtree.query(needle, k=count, p=self.power, **kwargs)
        locs = self.points[idxs]
        return locs, idxs, distances

    def query_range(self, needle, radius, **kwargs):
        idxs = self.kdtree.query_ball_point(needle, radius, p=self.power, **kwargs)
        return idxs, self.points[idxs]

class SvBruteforceKdTree(SvKdTree):
    def __init__(self, points, power=2):
        self.points = np.asarray(points)
        self.power = power

    def query(self, needle, count=1):
        dvs = self.points - needle
        distances = np.linalg.norm(dvs, axis=1, ord=self.power)
        if count == 1:
            idx = np.argmin(distances)
            loc = self.points[idx]
            distance = distances[idx]
            return loc, idx, distance
        else:
            idxs = np.argsort(distances)[:count]
            locs = self.points[idxs]
            distances = distances[idxs]
            return locs, idxs, distances

    def query_array(self, needle, count=1):
        if count == 1:
            return np.vectorize(self.query, signature='(3)->(3),(),()')(needle)
        else:
            qry = lambda p: self.query(p, count=count)
            return np.vectorize(qry, signature='(n,3)->(k,3),(k),(k)')(needle)

