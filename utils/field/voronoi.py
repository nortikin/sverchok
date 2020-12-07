# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.kdtree import SvKdTree

class SvVoronoiFieldData(object):
    def __init__(self, sites, metric='DISTANCE', power=None):
        self.sites = np.asarray(sites)
        self.metric = metric

        if metric == 'DISTANCE':
            self.power = 2
        elif metric == 'MANHATTAN':
            self.power = 1
        elif metric == 'CHEBYSHEV':
            self.power = np.inf
        elif metric == 'CUSTOM':
            self.power = power
        else:
            raise Exception("Unsupported metric")

        self.implementation = SvKdTree.best_available_implementation()
        self.kdtree = SvKdTree.new(self.implementation, sites, power=self.power)

    def query(self, point):
        if self.implementation == SvKdTree.SCIPY or self.metric == 'DISTANCE':
            locs, idxs, distances = self.kdtree.query(point, count=2)
            distance1 = distances[0]
            distance2 = distances[1]
            v1 = (locs[0] - point)
            v1 /= np.linalg.norm(v1)
            delta = abs(distance1 - distance2)
            return delta, delta * v1
        else:
            dvs = self.sites - point
            distances = np.linalg.norm(dvs, axis=1, ord=self.power)
            idx1, idx2 = np.argsort(distances)[:2]
            v1 = (self.sites[idx1] - point)
            v1 /= np.linalg.norm(v1)
            distance1, distance2 = distances[idx1], distances[idx2]
            delta = abs(distance1 - distance2)
            return delta, delta * v1

    def query_array(self, points):
        if self.implementation == SvKdTree.SCIPY or self.metric == 'DISTANCE':
            locs, idxs, distances = self.kdtree.query_array(points, count=2)
            distances1 = distances[:,0]
            distances2 = distances[:,1]
            v1s = locs[:,0] - points
            v1s /= np.linalg.norm(v1s, axis=1, keepdims=True)
            deltas = np.abs(distances1 - distances2)
            return deltas, deltas[np.newaxis].T * v1s
        else:
            return np.vectorize(self.query, signature='(3)->(),(3)')(points)

