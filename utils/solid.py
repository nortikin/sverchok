# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import math
from collections import defaultdict
import numpy as np

from mathutils.kdtree import KDTree

from sverchok.data_structure import match_long_repeat as mlr
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:

    import Part
    import Mesh
    import MeshPart
    from FreeCAD import Base
    from sverchok.nodes.solid.mesh_to_solid import ensure_triangles

    class SvSolidTopology(object):
        class Item(object):
            def __init__(self, item):
                self.item = item

            def __hash__(self):
                return self.item.hashCode()

            def __eq__(self, other):
                return self.item.isSame(other.item)

            def __repr__(self):
                return f"<Item: {type(self.item)} #{self.item.hashCode()}>"

        def __init__(self, solid):
            self.solid = solid
            self._init()

        def __repr__(self):
            v = len(self.solid.Vertexes)
            e = len(self.solid.Edges)
            f = len(self.solid.Faces)
            return f"<Solid topology: {v} vertices, {e} edges, {f} faces>"

        def _init(self):
            self._faces_by_vertex = defaultdict(set)
            self._faces_by_edge = defaultdict(set)
            self._edges_by_vertex = defaultdict(set)

            for face in self.solid.Faces:
                for vertex in face.Vertexes:
                    self._faces_by_vertex[SvSolidTopology.Item(vertex)].add(SvSolidTopology.Item(face))
                for edge in face.Edges:
                    self._faces_by_edge[SvSolidTopology.Item(edge)].add(SvSolidTopology.Item(face))
            
            for edge in self.solid.Edges:
                for vertex in edge.Vertexes:
                    self._edges_by_vertex[SvSolidTopology.Item(vertex)].add(SvSolidTopology.Item(edge))

            self._tree = KDTree(len(self.solid.Vertexes))
            for i, vertex in enumerate(self.solid.Vertexes):
                co = (vertex.X, vertex.Y, vertex.Z)
                self._tree.insert(co, i)
            self._tree.balance()

        def tessellate(self, precision):
            self._points_by_edge = defaultdict(list)
            self._points_by_face = defaultdict(list)

            for edge in self.solid.Edges:
                points = edge.discretize(Deflection=precision)
                i_edge = SvSolidTopology.Item(edge)
                for pt in points:
                    self._points_by_edge[i_edge].append((pt.x, pt.y, pt.z))

            for face in self.solid.Faces:
                data = face.tessellate(precision)
                i_face = SvSolidTopology.Item(face)
                for pt in data[0]:
                    self._points_by_face[i_face].append((pt.x, pt.y, pt.z))

        def calc_normals(self):
            self._normals_by_face = dict()
            for face in self.solid.Faces:
                #face.tessellate(precision)
                #u_min, u_max, v_min, v_max = face.ParameterRange
                sum_normal = Base.Vector(0,0,0)
                for u, v in face.getUVNodes():
                    normal = face.normalAt(u,v)
                    sum_normal = sum_normal + normal
                sum_normal = np.array([sum_normal.x, sum_normal.y, sum_normal.z])
                sum_normal = sum_normal / np.linalg.norm(sum_normal)
                self._normals_by_face[SvSolidTopology.Item(face)] = sum_normal

        def get_normal_by_face(self, face):
            return self._normals_by_face[SvSolidTopology.Item(face)]

        def get_vertices_by_location(self, condition):
            to_tuple = lambda v : (v.X, v.Y, v.Z)
            return [to_tuple(v) for v in self.solid.Vertexes if condition(to_tuple(v))]

        def get_vertices_by_location_mask(self, condition):
            to_tuple = lambda v : (v.X, v.Y, v.Z)
            return [condition(to_tuple(v)) for v in self.solid.Vertexes]

        def get_points_by_edge(self, edge):
            return self._points_by_edge[SvSolidTopology.Item(edge)]

        def get_points_by_face(self, face):
            return self._points_by_face[SvSolidTopology.Item(face)]

        def get_edges_by_location_mask(self, condition, include_partial):
            # condition is vectorized
            check = any if include_partial else all
            mask = []
            for edge in self.solid.Edges:
                test = condition(np.array(self._points_by_edge[SvSolidTopology.Item(edge)]))
                mask.append(check(test))
            return mask

        def get_faces_by_location_mask(self, condition, include_partial):
            # condition is vectorized
            check = any if include_partial else all
            mask = []
            for face in self.solid.Faces:
                test = condition(np.array(self._points_by_face[SvSolidTopology.Item(face)]))
                mask.append(check(test))
            return mask

        def get_faces_by_vertex(self, vertex):
            return [i.item for i in self._faces_by_vertex[SvSolidTopology.Item(vertex)]]

        def get_faces_by_vertices_mask(self, vertices, include_partial=True):
            if include_partial:
                good = set()
                for vertex in vertices:
                    new = self._faces_by_vertex[SvSolidTopology.Item(vertex)]
                    good.update(new)
                return [SvSolidTopology.Item(face) in good for face in self.solid.Faces]
            else:
                vertices = set([SvSolidTopology.Item(v) for v in vertices])
                mask = []
                for face in self.solid.Faces:
                    ok = all(SvSolidTopology.Item(v) in vertices for v in face.Vertexes)
                    mask.append(ok)
                return mask

        def get_faces_by_edge(self, edge):
            return [i.item for i in self._faces_by_edge[SvSolidTopology.Item(edge)]]

        def get_faces_by_edges_mask(self, edges, include_partial=True):
            if include_partial:
                good = set()
                for edge in edges:
                    new = self._faces_by_edge[SvSolidTopology.Item(edge)]
                    good.update(new)
                return [SvSolidTopology.Item(face) in good for face in self.solid.Faces]
            else:
                edges = set([SvSolidTopology.Item(e) for e in edges])
                mask = []
                for face in self.solid.Faces:
                    ok = all(SvSolidTopology.Item(e) in edges for e in face.Edges)
                    mask.append(ok)
                return mask

        def get_edges_by_vertex(self, vertex):
            return [i.item for i in self._edges_by_vertex[SvSolidTopology.Item(vertex)]]

        def get_edges_by_vertices_mask(self, vertices, include_partial=True):
            if include_partial:
                good = set()
                for vertex in vertices:
                    new = self._edges_by_vertex[SvSolidTopology.Item(vertex)]
                    good.update(new)
                return [SvSolidTopology.Item(edge) in good for edge in self.solid.Edges]
            else:
                vertices = set([SvSolidTopology.Item(v) for v in vertices])
                mask = []
                for edge in self.solid.Edges:
                    ok = all(SvSolidTopology.Item(v) in vertices for v in edge.Vertexes)
                    mask.append(ok)
                return mask

        def get_edges_by_faces_mask(self, faces):
            good = set()
            for face in faces:
                new = set([SvSolidTopology.Item(e) for e in face.Edges])
                good.update(new)
            return [SvSolidTopology.Item(edge) in good for edge in self.solid.Edges]

        def get_vertices_by_faces_mask(self, faces):
            good = set()
            for face in faces:
                new = set([SvSolidTopology.Item(v) for v in face.Vertexes])
                good.update(new)
            return [SvSolidTopology.Item(vertex) in good for vertex in self.solid.Vertexes]

        def get_vertices_by_edges_mask(self, edges):
            good = set()
            for edge in edges:
                new = set([SvSolidTopology.Item(v) for v in edge.Vertexes])
                good.update(new)
            return [SvSolidTopology.Item(vertex) in good for vertex in self.solid.Vertexes]

        def get_vertices_within_range(self, origin, distance):
            found = self._tree.find_range(tuple(origin), distance)
            idxs = [item[1] for item in found]
            vertices = [self.solid.Vertexes[i] for i in idxs]
            return vertices

        def get_vertices_within_range_mask(self, origin, distance):
            found = self._tree.find_range(tuple(origin), distance)
            idxs = set([item[1] for item in found])
            return [i in idxs for i in range(len(self.solid.Vertexes))]

    def basic_mesher(solids, precisions):
        verts = []
        faces = []
        for solid, precision in zip(*mlr([solids, precisions])):
            rawdata = solid.tessellate(precision)
            b_verts = []
            b_faces = []
            for v in rawdata[0]:
                b_verts.append((v.x, v.y, v.z))
            for f in rawdata[1]:
                b_faces.append(f)
            verts.append(b_verts)
            faces.append(b_faces)

        return verts, faces

    def standard_mesher(solids, surface_deviation, angle_deviation, relative_surface_deviation):
        verts = []
        faces = []
        for solid, s_dev, ang_dev in zip(*mlr([solids, surface_deviation, angle_deviation])):
            mesh = MeshPart.meshFromShape(
                Shape=solid,
                LinearDeflection=s_dev,
                AngularDeflection=math.radians(ang_dev),
                Relative=relative_surface_deviation)

            verts.append([v[:] for v in mesh.Topology[0]])
            faces.append(mesh.Topology[1])

        return verts, faces

    def mefisto_mesher(solids, max_edge_length):

        verts = []
        faces = []
        for solid, max_edge in zip(*mlr([solids, max_edge_length])):
            mesh = MeshPart.meshFromShape(
                Shape=solid,
                MaxLength=max_edge
                )

            verts.append([v[:] for v in mesh.Topology[0]])
            faces.append(mesh.Topology[1])

        return verts, faces


    def svmesh_to_solid(verts, faces, precision, remove_splitter=True):
        """
        input:
            verts: list of 3element iterables, [vector, vector...]
            faces: list of lists of face indices
            precision: a conversion factor defined in makeShapeFromMesh (FreeCAD)
            remove_splitter: default True, removes duplicate geometry (edges)
        output:
            a FreeCAD solid

        """
        tri_faces = ensure_triangles(verts, faces, True)
        faces_t = [[verts[c] for c in f] for f in tri_faces]
        mesh = Mesh.Mesh(faces_t)
        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh.Topology, precision)

        if remove_splitter:
            # may slow it down, or be totally necessary
            shape = shape.removeSplitter() 

        return Part.makeSolid(shape)
