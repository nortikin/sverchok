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
import sverchok.utils.sv_mesh_utils as sv_mesh
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata, dissolve_internal_edges
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
    def __init__(self, placed_item, orig_verts, sorted_verts, edges, faces, plane = 'XY', keep_topology = False):
        self.placed_item = placed_item
        self.orig_verts = orig_verts
        self.sorted_verts = sorted_verts
        self.edges = edges
        self.faces = faces
        self.plane = plane
        if plane == 'XY':
            self.axis = 'Z'
        elif plane == 'XZ':
            self.axis = 'Y'
        else:
            self.axis = 'X'
        self.keep_topology = keep_topology

    @staticmethod
    def to_3d(plane, verts):
        if plane == 'XY':
            return [(v[0], v[1], 0) for v in verts]
        elif plane == 'XZ':
            return [(v[0], 0, v[1]) for v in verts]
        else:
            return [(0, v[0], v[1]) for v in verts]

    def get_index(self):
        return int(self.placed_item.id)

    def calc_verts(self):
        if self.keep_topology:
            verts = SpyrrowSolver.to_2d(self.plane, self.orig_verts)
        else:
            verts = self.sorted_verts
        verts2d = translate(rotate(verts, self.placed_item.rotation), self.placed_item.translation)
        return SpyrrowSolutionItem.to_3d(self.plane, verts2d)

    def calc_polygons(self):
        verts = self.calc_verts()
        edges = self.edges
        faces = self.faces
        return verts, edges, faces
    
    def calc_matrix(self):
        rotation = Matrix.Rotation(radians(self.placed_item.rotation), 4, self.axis)
        v = self.placed_item.translation
        v = SpyrrowSolutionItem.to_3d(self.plane, [v])[0]
        translation = Matrix.Translation(v)
        return translation @ rotation

class SpyrrowSolution:
    def __init__(self, instance, solution, plane):
        self._items = defaultdict(list)
        self.solution = solution
        self.instance = instance
        self.plane = plane

    def add_item(self, item):
        self._items[item.placed_item.id].append(item)

    def items(self):
        for id in sorted(self._items.keys()):
            yield from self._items[id]

    @staticmethod
    def make_faces(verts):
        face = list(range(len(verts)))
        return [face]

    @staticmethod
    def make_edges(verts):
        n_verts = len(verts)
        edges = [(i, i+1) for i in range(n_verts-1)]
        edges.append((n_verts-1, 0))
        return edges

    def make_strip(self):
        height = self.instance.strip_height
        width = self.solution.width
        verts = [[0,0], [width, 0], [width, height], [0, height]]
        verts = SpyrrowSolutionItem.to_3d(self.plane, verts)
        edges = SpyrrowSolution.make_edges(verts)
        faces = SpyrrowSolution.make_faces(verts)
        return verts, edges, faces

class SpyrrowSolver:
    def __init__(self, config, strip_height, plane = 'XY', keep_topology = False):
        self.instance = None
        self.config = config
        self.strip_height = strip_height
        self.items = []
        self.item_verts = dict()
        self.item_edges = dict()
        self.item_faces = dict()
        self.item_sorted_verts = dict()
        self.plane = plane
        self.keep_topology = keep_topology

    def sort_verts(self, verts, edges, faces):
        if self.keep_topology:
            bm = bmesh_from_pydata(verts, edges, faces, normal_update=True)
            bm = dissolve_internal_edges(bm, use_verts=False)
            verts_for_sort, edges_for_sort, faces_for_sort = pydata_from_bmesh(bm)
            bm.free()
        else:
            verts_for_sort = verts
            edges_for_sort = edges
            faces_for_sort = faces

        if faces_for_sort:
            if len(faces_for_sort) != 1:
                raise SvInvalidInputException("Each item must have exactly one face")
            face = faces_for_sort[0]
            verts = [verts_for_sort[j] for j in face]
        elif edges_for_sort:
            verts, e, idx = sv_mesh.sort_vertices_by_connections(verts_for_sort, edges_for_sort, True)

        if not self.keep_topology:
            edges = SpyrrowSolution.make_edges(verts)
            faces = SpyrrowSolution.make_faces(verts)
        return verts, edges, faces

    @staticmethod
    def to_2d(plane, verts):
        if plane == 'XY':
            if any(abs(v[2]) >= EPSILON_Z for v in verts):
                raise SvInvalidInputException("Z value for one of points is not zero")
            return [(v[0], v[1]) for v in verts]
        elif plane == 'XZ':
            if any(abs(v[1]) >= EPSILON_Z for v in verts):
                raise SvInvalidInputException("Y value for one of points is not zero")
            return [(v[0], v[2]) for v in verts]
        else: # YZ
            if any(abs(v[0]) >= EPSILON_Z for v in verts):
                raise SvInvalidInputException("X value for one of points is not zero")
            return [(v[1], v[2]) for v in verts]

    def add_item(self, verts, edges, faces, count = 1, allowed_orientations = None):
        if self.instance is not None:
            raise InvalidStateError("Spyrrow instance has already been initialized")
        sorted_verts, sorted_edges, sorted_faces = self.sort_verts(verts, edges, faces)
        edges = sorted_edges
        faces = sorted_faces
        # These checks are required, because currently spyrrow
        # reacts on such polygons very badly: not only raises an exception,
        # but stops to work at all.
        if calc_polygon_area(sorted_verts) <= EPSILON_AREA:
            raise SvInvalidInputException("Polygon area is too small")
        diam = diameter(sorted_verts, axis=None)
        if diam > self.strip_height:
            raise SvInvalidInputException(f"Polygon is too large ({diam}) for this strip height ({self.strip_height})")
        j = len(self.items)
        sorted_verts = SpyrrowSolver.to_2d(self.plane, sorted_verts)
        # This format is required in order to
        # 1) be able to sort objects by ID properly
        # 2) recover object's ID as integer
        id = f"{j:08}"
        item = spyrrow.Item(
                id, sorted_verts,
                demand = count,
                allowed_orientations = allowed_orientations)
        self.item_verts[id] = verts
        self.item_sorted_verts[id] = sorted_verts
        self.item_edges[id] = edges
        self.item_faces[id] = faces
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
            solution = self.instance.solve(self.config)
            print("Spyrrow solver done")
            result = SpyrrowSolution(self.instance, solution, plane = self.plane)
            for placed_item in solution.placed_items:
                verts = self.item_verts[placed_item.id]
                sorted_verts = self.item_sorted_verts[placed_item.id]
                edges = self.item_edges[placed_item.id]
                faces = self.item_faces[placed_item.id]
                #print(f"Object {placed_item.id}: verts {verts} => sorted {sorted_verts}")
                item = SpyrrowSolutionItem(placed_item, verts, sorted_verts, edges, faces, plane = self.plane, keep_topology = self.keep_topology)
                result.add_item(item)
            return result
        except Exception as e:
            print(f"Spyrrow exception: {e}")
            raise

