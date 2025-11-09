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
from sverchok.utils.geom import diameter, PlaneEquation
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.solid_conversion import to_solid, to_solid_recursive
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.primitives import SvPlane

if FreeCAD is not None:

    import Mesh
    import MeshPart
    import Part
    from FreeCAD import Base

    from sverchok.nodes.solid.mesh_to_solid import ensure_triangles
    from sverchok.utils.curve.freecad import curve_to_freecad
    from sverchok.utils.surface.freecad import is_solid_face_surface, surface_to_freecad

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

    def calc_face_centers(self):
        self._centers_by_face = dict()
        for face in self.solid.Faces:
            sum_points = np.array([0.0,0.0,0.0])
            for u,v in face.getUVNodes():
                p = face.valueAt(u,v)
                sum_points += np.array([p.x, p.y, p.z])
            mean = sum_points / len(sum_points)
            self._centers_by_face[SvSolidTopology.Item(face)] = mean

    def get_normal_by_face(self, face):
        return self._normals_by_face[SvSolidTopology.Item(face)]

    def get_center_by_face(self, face):
        return self._centers_by_face[SvSolidTopology.Item(face)]

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
            if refine:
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
    Utility function to apply mathutils.Matrix to a Solid object.
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

FCMESH = 'FCMESH'
BMESH = 'BMESH'

def svmesh_to_solid(verts, faces, precision=1e-6, remove_splitter=True, method=FCMESH):
    """
    input:
        verts: list of 3element iterables, [vector, vector...]
        faces: list of lists of face indices
        precision: a conversion factor defined in makeShapeFromMesh (FreeCAD)
        remove_splitter: default True, removes duplicate geometry (edges)
    output:
        a FreeCAD solid

    """
    if method == FCMESH:
        tri_faces = ensure_triangles(verts, faces, True)
        faces_t = [[verts[c] for c in f] for f in tri_faces]
        mesh = Mesh.Mesh(faces_t)
        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh.Topology, precision)

        if remove_splitter:
            # may slow it down, or be totally necessary
            shape = shape.removeSplitter() 

        return Part.makeSolid(shape)
    elif method == BMESH:
        fc_faces = []
        for face in faces:
            face_i = list(face) + [face[0]]
            face_verts = [Base.Vector(verts[i]) for i in face_i]
            wire = Part.makePolygon(face_verts)
            wire.fixTolerance(precision)
            try:
                fc_face = Part.Face(wire)
                #fc_face = Part.makeFilledFace(wire.Edges)
            except Exception as e:
                print(f"Face idxs: {face_i}, verts: {face_verts}")
                raise Exception("Maybe face is not planar?") from e
            fc_faces.append(fc_face)
        shell = Part.makeShell(fc_faces)
        solid = Part.makeSolid(shell)
        if remove_splitter:
            solid = solid.removeSplitter()
        return solid
    else:
        raise Exception("Unsupported method")

def mesh_from_solid_faces(solid):
    verts = [(v.X, v.Y, v.Z) for v in solid.Vertexes]

    all_fc_verts = {SvSolidTopology.Item(v) : i for i, v in enumerate(solid.Vertexes)}
    def find_vertex(v):
        #for i, fc_vert in enumerate(solid.Vertexes):
        #    if v.isSame(fc_vert):
        #        return i
        #return None
        return all_fc_verts[SvSolidTopology.Item(v)]

    edges = []
    for fc_edge in solid.Edges:
        edge = [find_vertex(v) for v in fc_edge.Vertexes]
        if len(edge) == 2:
            edges.append(edge)

    faces = []
    for fc_face in solid.Faces:
        incident_verts = defaultdict(set)
        for fc_edge in fc_face.Edges:
            edge = [find_vertex(v) for v in fc_edge.Vertexes]
            if len(edge) == 2:
                i, j = edge
                incident_verts[i].add(j)
                incident_verts[j].add(i)

        face = [find_vertex(v) for v in fc_face.Vertexes]

        vert_idx = face[0]
        correct_face = [vert_idx]

        for i in range(len(face)):
            incident = list(incident_verts[vert_idx])
            other_verts = [i for i in incident if i not in correct_face]
            if not other_verts:
                break
            other_vert_idx = other_verts[0]
            correct_face.append(other_vert_idx)
            vert_idx = other_vert_idx

        if len(correct_face) > 2:
            faces.append(correct_face)

    return verts, edges, faces

def hascurves(shape):
    for e in shape.Edges:
        if not isinstance(e.Curve, (Part.Line, Part.LineSegment)):
            return True
    return False

def drop_existing_faces(faces):
    """
    this avoids the following bmesh exception:

       faces.new(verts): face already exists

    """
    faces_set = set()
    new_faces = []
    good_face = new_faces.append
    for face in faces:
        proposed_face = tuple(sorted(face))
        if proposed_face in faces_set:
            continue
        else:
            faces_set.add(proposed_face)
            good_face(face)
    return new_faces


def mesh_from_solid_faces_MOD(shape, quality=1.0, tessellate=False):
    """
    modified from yorik van havre's FreeCAD importer for Blender.
    """

    vdict = {}
    faces = []
    add_face = faces.append # alias increase speed

    # write FreeCAD faces as polygons when possible
    for face in shape.Faces:
        
        if (len(face.Wires) > 1) or (not isinstance(face.Surface, Part.Plane)) or hascurves(face) or tessellate:
            # face has holes or is curved, so we need to triangulate it
            rawdata = face.tessellate(quality)
            
            for v in rawdata[0]:
                if (v1 := (v.x, v.y, v.z)) not in vdict:
                    vdict[v1] = len(vdict)
            
            for f in rawdata[1]:
                raw = rawdata[0]
                nf = [vdict[(nv.x, nv.y, nv.z)] for nv in [raw[vi] for vi in f]]
                add_face(nf)

        else:
        
            f = []
            ov = face.OuterWire.OrderedVertexes
        
            for v in ov:

                if (vec := (v.X, v.Y, v.Z)) not in vdict:
                    vdict[vec] = len(vdict)
                    f.append(len(vdict) - 1)
                else:
                    f.append(vdict[(v.X, v.Y, v.Z)])
        
            # FreeCAD doesn't care about verts order. Make sure our loop goes clockwise
            c = face.CenterOfMass
            v1 = ov[0].Point.sub(c)
            v2 = ov[1].Point.sub(c)
            n = face.normalAt(0,0)
            if (v1.cross(v2)).getAngle(n) > 1.57:
                f.reverse() # inverting verts order if the direction is couterclockwise
            
            add_face(f)

    faces = drop_existing_faces(faces)
    verts = list(vdict.keys())
    return verts, faces

def make_plane_by_size_of_solid(solid, plane):
    box = solid.BoundBox
    bbox_pts = [box.getPoint(i) for i in range(8)]
    bbox_pts = [(p.x,p.y,p.z) for p in bbox_pts]
    diam = diameter(bbox_pts, None)
    vec1, vec2 = plane.two_vectors()
    bbox_ctr = (box.Center.x, box.Center.y, box.Center.z)
    bbox_ctr = plane.projection_of_point(bbox_ctr)
    plane_surface = SvPlane(np.array(bbox_ctr), np.array(vec1.normalized()*diam), np.array(vec2.normalized()*diam))
    plane_surface.u_bounds = (-1,1)
    plane_surface.v_bounds = (-1,1)
    return plane_surface.to_nurbs()

def bisect_solid(solid, face_surface):
    face = face_surface.face
    result, map = solid.generalFuse([face])
    solids = map[0]
    return solids

def select_solids_by_plane_side(solids, plane, sign):
    result = []
    for solid in solids:
        ctr = solid.CenterOfMass
        ctr = (ctr.x, ctr.y, ctr.z)
        if plane.side_of_point(ctr) == sign:
            result.append(solid)
    return result

def mirror_solid(solid, plane):
    origin = plane.nearest_point_to_origin()
    direction = plane.normal
    return solid.mirror(Base.Vector(origin), Base.Vector(direction))

def fuse_solids(solids):
    if len(solids) <= 1:
        return solids
    result, map = solids[0].generalFuse(solids[1:])
    parts = sum(map, [])
    return parts[0].fuse(parts[1:])

def symmetrize_solid(solid, plane, sign_from=-1):
    plane_face = make_plane_by_size_of_solid(solid, plane)
    plane_face = surface_to_freecad(plane_face, make_face=True)
    parts = bisect_solid(solid, plane_face)
    parts = select_solids_by_plane_side(parts, plane, sign_from)
    mirrored_parts = [mirror_solid(part, plane) for part in parts]
    solids = fuse_solids(parts + mirrored_parts)
    return solids

