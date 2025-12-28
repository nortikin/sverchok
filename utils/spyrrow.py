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

from sverchok.core.sv_custom_exceptions import InvalidStateError, SvInvalidInputException
from sverchok.utils.geom import calc_polygon_area, diameter
from sverchok.dependencies import spyrrow

EPSILON_Z = 1e-4
EPSILON_AREA = 1e-4

def rotate(points, angle):
    angle = radians(angle)
    points = np.array(points)
    m = [[cos(angle), -sin(angle)], [sin(angle), cos(angle)]]
    m = np.array(m)
    return (m @ points.T).T

def translate(points, vector):
    return points + np.array(vector)

class SpyrrowSolutionItem:
    def __init__(self, placed_item, verts2d, plane = 'XY'):
        self.placed_item = placed_item
        self.verts2d = verts2d
        self.plane = plane
        if plane == 'XY':
            self.axis = 'Z'
        elif plane == 'XZ':
            self.axis = 'Y'
        else:
            self.axis = 'X'

    def to_3d(self, verts):
        if self.plane == 'XY':
            return [(v[0], v[1], 0) for v in verts]
        elif self.plane == 'XZ':
            return [(v[0], 0, v[1]) for v in verts]
        else:
            return [(0, v[0], v[1]) for v in verts]

    def get_index(self):
        return int(self.placed_item.id)

    def calc_verts(self):
        verts2d = translate(rotate(self.verts2d, self.placed_item.rotation), self.placed_item.translation)
        return self.to_3d(verts2d)
    
    def calc_matrix(self):
        rotation = Matrix.Rotation(radians(self.placed_item.rotation), 4, self.axis)
        v = self.placed_item.translation
        v = self.to_3d([v])[0]
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
    def __init__(self, config, strip_height, plane = 'XY'):
        self.instance = None
        self.config = config
        self.strip_height = strip_height
        self.solution = None
        self.items = []
        self.verts2d = dict()
        self.plane = plane

    def to_2d(self, verts):
        if self.plane == 'XY':
            if any(abs(v[2]) >= EPSILON_Z for v in verts):
                raise SvInvalidInputException("Z value for one of points is not zero")
            return [(v[0], v[1]) for v in verts]
        elif self.plane == 'XZ':
            if any(abs(v[1]) >= EPSILON_Z for v in verts):
                raise SvInvalidInputException("Y value for one of points is not zero")
            return [(v[0], v[2]) for v in verts]
        else: # YZ
            if any(abs(v[0]) >= EPSILON_Z for v in verts):
                raise SvInvalidInputException("X value for one of points is not zero")
            return [(v[1], v[2]) for v in verts]

    def add_item(self, verts, count = 1, allowed_orientations = None):
        if self.instance is not None:
            raise InvalidStateError("Spyrrow instance has already been initialized")
        # These checks are required, because currently spyrrow
        # reacts on such polygons very badly: not only raises an exception,
        # but stops to work at all.
        if calc_polygon_area(verts) <= EPSILON_AREA:
            raise SvInvalidInputException("Polygon area is too small")
        if diameter(verts, axis=None) > self.strip_height:
            raise SvInvalidInputException("Polygon is too large for this strip height")
        j = len(self.items)
        verts = self.to_2d(verts)
        # This format is required in order to
        # 1) be able to sort objects by ID properly
        # 2) recover object's ID as integer
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
        try:
            self.solution = self.instance.solve(self.config)
        except Exception as e:
            print(f"Spyrrow exception: {e}")
            raise
        print("Spyrrow solver done")
        result = SpyrrowSolution()
        for placed_item in self.solution.placed_items:
            verts = self.verts2d[placed_item.id]
            item = SpyrrowSolutionItem(placed_item, verts, plane = self.plane)
            result.add_item(item)
        return result

