# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import sin, cos, radians
from collections import defaultdict

from mathutils import Matrix

from sverchok.core.sv_custom_exceptions import InvalidStateError
from sverchok.dependencies import spyrrow

def rotate(points, angle):
    angle = radians(angle)
    points = np.array(points)
    m = [[cos(angle), -sin(angle)], [sin(angle), cos(angle)]]
    m = np.array(m)
    return (m @ points.T).T

def translate(points, vector):
    return points + np.array(vector)

def to_2d(verts):
    return [(v[0], v[1]) for v in verts]

def to_3d(verts):
    return [(v[0], v[1], 0) for v in verts]

class SpyrrowSolutionItem:
    def __init__(self, placed_item, verts2d):
        self.placed_item = placed_item
        self.verts2d = verts2d

    def get_index(self):
        return int(self.placed_item.id)

    def calc_verts(self):
        verts2d = translate(rotate(self.verts2d, self.placed_item.rotation), self.placed_item.translation)
        return to_3d(verts2d)
    
    def calc_matrix(self):
        rotation = Matrix.Rotation(radians(self.placed_item.rotation), 4, 'Z')
        v = self.placed_item.translation
        v = [v[0], v[1], 0]
        translation = Matrix.Translation(v)
        return translation @ rotation

class SpyrrowSolution:
    def __init__(self):
        self._items = defaultdict(list)

    def add_item(self, item):
        self._items[item.placed_item.id].append(item)

    def items(self):
        for id in sorted(self._items.keys()):
            yield from self._items[id]

class SpyrrowSolver:
    def __init__(self, config, strip_height):
        self.instance = None
        self.config = config
        self.strip_height = strip_height
        self.solution = None
        self.items = []
        self.verts2d = dict()

    def add_item(self, verts, count = 1, allowed_orientations = None):
        if self.instance is not None:
            raise InvalidStateError("Spyrrow instance has already been initialized")
        j = len(self.items)
        verts = to_2d(verts)
        id = f"{j:08}"
        item = spyrrow.Item(
                id, verts,
                demand = count,
                allowed_orientations = allowed_orientations)
        self.verts2d[id] = verts
        self.items.append(item)

    def solve(self):
        if self.instance is not None:
            raise InvalidStateError("solve() has already been called")
        self.instance = spyrrow.StripPackingInstance(
                    "spyrrow",
                    strip_height = self.strip_height,
                    items = self.items
                )
        print("Starting Spyrrow solver")
        self.solution = self.instance.solve(self.config)
        print("Spyrrow solver done")
        result = SpyrrowSolution()
        for placed_item in self.solution.placed_items:
            verts = self.verts2d[placed_item.id]
            item = SpyrrowSolutionItem(placed_item, verts)
            result.add_item(item)
        return result

