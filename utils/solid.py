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
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:

    import Part
    import Mesh
    import MeshPart
    from FreeCAD import Base

    from sverchok.nodes.solid.mesh_to_solid import ensure_triangles
    from sverchok.utils.curve.freecad import curve_to_freecad
    from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface

class SvSolidTopology(object):
    class Item(object):
        def __init__(self, item):
            self.item = item

        def __hash__(self):
            return self.item.hashCode()

        def __eq__(self, other):
            return self.item.isSame(other.item)

        def __repr__(self):
            return f"<Item: {type(self.item).__name__} #{self.item.hashCode()}>"

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

class SvGeneralFuse(object):
    def __init__(self, solids):
        self.solids = solids
        self.result, self.map = solids[0].generalFuse(solids[1:])
        self._per_source = defaultdict(set)
        self._per_source_idx = defaultdict(set)
        self._sources_by_part = defaultdict(set)
        self._source_idxs_by_part = defaultdict(set)
        for src_idx, (source, parts) in enumerate(zip(solids, self.map)):
            items = set(SvSolidTopology.Item(i) for i in parts)

            src_key = SvSolidTopology.Item(source)
            self._per_source[src_key] = items
            self._per_source_idx[src_idx] = items

            for item in items:
                self._sources_by_part[item].add(src_key)
                #print(f"{src_idx}: P[{item}] := {src_key}")
                self._source_idxs_by_part[item].add(src_idx)
        
        self._edge_indirect_source_idxs = defaultdict(set)
        self._edge_indirect_sources = defaultdict(set)
        self._face_indirect_source_idxs = defaultdict(set)
        self._face_indirect_sources = defaultdict(set)
        for part in self.result.Solids:
            item = SvSolidTopology.Item(part)
            sources = self._sources_by_part[item]
            src_idxs = self._source_idxs_by_part[item]
            #print(f"P? {item} => {src_idxs}")

            for edge in part.Edges:
                edge_item = SvSolidTopology.Item(edge)
                self._edge_indirect_sources[edge_item].update(sources)
                self._edge_indirect_source_idxs[edge_item].update(src_idxs)

            for face in part.Faces:
                face_item = SvSolidTopology.Item(face)
                self._face_indirect_source_idxs[face_item].update(src_idxs)
                self._face_indirect_sources[face_item].update(sources)

#         self._edge_direct_source_idxs = defaultdict(set)
#         self._edge_direct_sources = defaultdict(set)
#         for part in self.result.Solids:
#             item = SvSolidTopology.Item(part)
#             for edge in part.Edges:
#                 edge_item = SvSolidTopology.Item(edge)
#                 indirect_sources = self._edge_indirect_sources[edge_item]
#                 indirect_source_idxs = self._edge_indirect_source_idxs[edge_item]
#                 for src_idx, indirect_source in zip(indirect_source_idxs, indirect_sources):
#                     src_edges = set(SvSolidTopology.Item(e) for e in indirect_source.item.Edges)
#                     if edge_item in src_edges:
#                         self._edge_direct_sources[edge_item].add(indirect_source)
#                         self._edge_direct_source_idxs[edge_item].add(src_idx)
    
    def get_all_parts(self):
        return self.result.Solids
    
    def get_union_all(self, refine=False):
        solids = self.result.Solids
        solid = solids[0].fuse(solids[1:])
        if refine:
            solid = solid.removeSplitter()
        return solid

    def get_intersect_all(self, refine=False):
        result = None
        for source, parts in self._per_source.items():
            if result is None:
                result = parts
            else:
                result.intersection_update(parts)
        if not result:
            return None
        elif len(result) == 1:
            return list(result)[0].item
        else:
            solids = [p.item for p in result]
            solid = solids[0].fuse(solids[1:])
            if refine:
                solid = solid.removeSplitter()
            return solid
    
    def get_edge_sources(self, edge):
        return self._edge_indirect_sources[SvSolidTopology.Item(edge)]
    
    def get_edge_source_idxs(self, edge):
        return self._edge_indirect_source_idxs[SvSolidTopology.Item(edge)]

    def get_face_sources(self, face):
        return self._face_indirect_sources[SvSolidTopology.Item(face)]
    
    def get_face_source_idxs(self, face):
        return self._face_indirect_source_idxs[SvSolidTopology.Item(face)]

    def get_part_sources(self, part):
        return self._sources_by_part[SvSolidTopology.Item(part)]

    def get_part_source_idxs(self, part):
        return self._source_idxs_by_part[SvSolidTopology.Item(part)]
    
    def get_by_source(self, solid):
        return self._per_source[SvSolidTopology.Item(solid)]
    
    def get_by_source_idx(self, idx):
        return self._per_source_idx[idx]
    
    def get_intersection(self, solid_a, solid_b):
        result_a = self._per_source[SvSolidTopology.Item(solid_a)]
        result_b = self._per_source[SvSolidTopology.Item(solid_b)]
        return result_a.intersection(result_b)
    
    def get_intersection_by_idx(self, idx_a, idx_b):
        result_a = self._per_source_idx[idx_a]
        result_b = self._per_source_idx[idx_b]
        return result_a.intersection(result_b)
    
    def get_difference(self, solid_a, solid_b):
        result_a = self._per_source[SvSolidTopology.Item(solid_a)]
        result_b = self._per_source[SvSolidTopology.Item(solid_b)]
        return result_a.difference(result_b)
    
    def get_clean_part(self, solid):
        item = SvSolidTopology.Item(solid)
        result = self._per_source[item].copy()
        for source, results in self._per_source.items():
            if source != item:
                result.difference_update(results)
        return result
    
    def get_clean_part_by_idx(self, idx, refine=False):
        result = self._per_source_idx[idx].copy()
        for source_idx, results in self._per_source_idx.items():
            if source_idx != idx:
                result.difference_update(results)

        parts = [part.item for part in result]
        if not parts:
            solid = None
        elif len(parts) == 1:
            solid = parts[0]
        else:
            solid = parts[0].fuse(parts[1:])
            if do_refine:
                solid = solid.removeSplitter()
        return solid

class SvBoolResult(object):
    def __init__(self, solid, edge_mask=None, edge_map=None, face_mask=None, face_map=None, solid_map=None):
        self.solid = solid
        if edge_mask is None:
            edge_mask = []
        self.edge_mask = edge_mask
        if edge_map is None:
            edge_map = []
        self.edge_map = edge_map
        if face_mask is None:
            face_mask = []
        self.face_mask = face_mask
        if face_map is None:
            face_map = []
        self.face_map = face_map
        if solid_map is None:
            solid_map = []
        self.solid_map = solid_map

def transform_solid(matrix, solid):
    """
    Utility funciton to apply mathutils.Matrix to a Solid object.
    """
    mat = Base.Matrix(*[i for v in matrix for i in v])
    return solid.transformGeometry(mat)

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

def to_solid(ob):
    if isinstance(ob, Part.Shape):
        return ob
    elif isinstance(ob, SvCurve):
        return [c.curve.toShape() for c in curve_to_freecad(ob)]
    elif isinstance(ob, SvSurface):
        if is_solid_face_surface(ob):
            return ob.face
        else:
            return surface_to_freecad(ob, make_face=True).face
    else:
        raise Exception(f"Unknown data type in input: {ob}")

