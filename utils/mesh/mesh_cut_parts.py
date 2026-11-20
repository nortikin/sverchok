# SPDX-License-Identifier: GPL-3.0-or-later
"""Blender-free separation and region selection for Mesh Cut results.

The cut edge mask defines seams. Components are connected through other face
edges only. Each returned piece has its own local vertex indices and never
shares vertices with another piece. This module deliberately keeps the old
`cut_mesh` API untouched.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import numpy as np

try:
    from .mesh_cut import cut_mesh, _edges_from_faces, _edge_key, CutResult
    from .mesh_intersections import _as_vertices, triangulate_faces
except ImportError:
    from mesh_cut import cut_mesh, _edges_from_faces, _edge_key, CutResult
    from mesh_intersections import _as_vertices, triangulate_faces


@dataclass
class MeshPiece:
    vertices: np.ndarray
    edges: np.ndarray
    faces: list[list[int]]
    cut_edge_mask: np.ndarray
    cut_vertex_mask: np.ndarray
    face_origins: np.ndarray
    original_face_indices: np.ndarray
    area: float
    index: int


@dataclass
class PiecesResult:
    pieces: list[MeshPiece]
    all_pieces_count: int
    selected_indices: list[int]
    intersection_vertices: np.ndarray
    intersection_edges: np.ndarray
    acceleration: str
    numba_used: bool


def _surface_area(verts, faces):
    """Surface area of polygonal faces, including concave planar n-gons.

    The vector area (Newell/edge-cross formulation) handles concave loops
    without the overlapping triangles produced by a fan rooted at vertex 0.
    Nonplanar n-gons have a projected vector-area approximation, as in common
    polygon normal computation; cut nonplanar faces remain triangulated.
    """
    if not faces:
        return 0.0
    if len(faces) == 1:
        # Avoid array setup overhead for an unchanged single polygon.
        return _surface_area_slow(verts, faces)
    lengths = np.fromiter((len(face) for face in faces), dtype=np.intp,
                          count=len(faces))
    if np.any(lengths < 3):
        # Keep the previous behavior for malformed input that can contain
        # empty or degenerate faces; normal mesh processing uses valid faces.
        return _surface_area_slow(verts, faces)
    offsets = np.empty(len(lengths) + 1, dtype=np.intp)
    offsets[0] = 0
    np.cumsum(lengths, out=offsets[1:])
    indices = np.fromiter((int(i) for face in faces for i in face),
                          dtype=np.intp, count=int(offsets[-1]))
    following = np.roll(indices, -1)
    following[offsets[1:] - 1] = indices[offsets[:-1]]
    edge_cross = np.cross(verts[indices], verts[following])
    area_vectors = np.add.reduceat(edge_cross, offsets[:-1], axis=0)
    return 0.5 * float(np.linalg.norm(area_vectors, axis=1).sum())


def _surface_area_slow(verts, faces):
    total = 0.0
    for face in faces:
        xyz = verts[np.asarray(face, dtype=np.int64)]
        if len(xyz) < 3:
            continue
        vector_area = np.sum(np.cross(xyz, np.roll(xyz, -1, axis=0)), axis=0)
        total += float(np.linalg.norm(vector_area)) * .5
    return total


def partition_cut(cut: CutResult):
    """Separate mesh faces across every marked cut edge.

    Also separates originally disconnected components, never merges them.
    Sort components by decreasing area, then first output face index to keep
    the selection deterministic. Requires manifold seams or open boundary edges.
    """
    faces = cut.faces
    count = len(faces)
    if count == 0:
        return []
    parent = list(range(count))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a,b)] = min(a,b)

    seam = {tuple(map(int, ed)) for ed, mask in zip(cut.edges, cut.cut_edge_mask) if mask}
    incident = defaultdict(list)
    for i, face in enumerate(faces):
        for j in range(len(face)):
            incident[_edge_key(face[j], face[(j+1) % len(face)])].append(i)
    nonseam_by_vertex = defaultdict(list)
    for edge, touching in incident.items():
        if edge not in seam and len(touching) == 2:
            nonseam_by_vertex[edge[0]].append(tuple(touching))
            nonseam_by_vertex[edge[1]].append(tuple(touching))
        if len(touching) > 2:
            raise ValueError('Non-manifold output edge: cannot separate pieces unambiguously')
        if edge not in seam and len(touching) == 2:
            union(touching[0], touching[1])

    groups = defaultdict(list)
    for i in range(count):
        groups[find(i)].append(i)
    # Evaluate each component area only once. The local vertex remapping
    # below preserves coordinates and polygon order, so its area is identical.
    sized_groups = [(ids, _surface_area(cut.vertices, [faces[i] for i in ids]))
                    for ids in groups.values()]
    sized_groups.sort(key=lambda item: (-item[1], min(item[0])))
    pieces = []
    for index, (group, area) in enumerate(sized_groups):
        # Disconnection is local to a vertex fan, not just to face components.
        # A finite slit with both ends in the interior does not create two
        # connected *components*, but still needs duplicate seam vertices.
        # For each original vertex, connect its incident faces only across
        # edges NOT marked as seams, then give each fan a distinct output ID.
        group_set = set(group)
        fans = defaultdict(list)
        for fid in group:
            for v in faces[fid]:
                fans[int(v)].append(fid)
        fan_keys = {}
        for v, incident_faces in fans.items():
            adjacency = {f: f for f in incident_faces}

            def find_f(f):
                while adjacency[f] != f:
                    adjacency[f] = adjacency[adjacency[f]]
                    f = adjacency[f]
                return f

            for a, b in nonseam_by_vertex.get(v, ()):
                if a not in group_set or b not in group_set:
                    continue
                a, b = find_f(a), find_f(b)
                if a != b:
                    adjacency[max(a,b)] = min(a,b)
            for fid in incident_faces:
                fan_keys[(fid, v)] = (v, find_f(fid))

        local_index = {}
        originals = []
        new_faces = []
        for fid in group:
            new_face = []
            for v in faces[fid]:
                key = fan_keys[(fid, int(v))]
                if key not in local_index:
                    local_index[key] = len(originals)
                    originals.append(int(v))
                new_face.append(local_index[key])
            new_faces.append(new_face)
        new_vertices = cut.vertices[originals].copy()
        new_edges = _edges_from_faces(new_faces)
        new_cut_edge_mask = np.array([
            _edge_key(originals[int(e[0])], originals[int(e[1])]) in seam for e in new_edges
        ], dtype=bool)
        new_cut_vertex_mask = np.asarray(cut.cut_vertex_mask[originals], dtype=bool).copy()
        areas = area
        pieces.append(MeshPiece(new_vertices, new_edges, new_faces,
                                new_cut_edge_mask, new_cut_vertex_mask,
                                np.asarray(cut.face_origins[group]).copy(),
                                np.asarray(group, dtype=np.int64), areas, index))
    return pieces


def _planar_cutter(vertices_b, faces_b, tolerance):
    vb = _as_vertices(vertices_b, 'vertices_b')
    faces = [list(map(int, face)) for face in faces_b]
    if not faces:
        raise ValueError('Positive/Negative requires at least one cutter face')
    first_normal = None
    point = None
    for face in faces:
        if len(face) < 3:
            continue
        # Newell normal works for convex/concave planar faces.
        xyz = vb[face]
        n = np.sum(np.cross(xyz, np.roll(xyz, -1, axis=0)), axis=0)
        length = float(np.linalg.norm(n))
        if length <= tolerance * tolerance:
            continue
        n /= length
        if first_normal is None:
            first_normal, point = n, xyz[0]
        elif np.dot(first_normal, n) < 1 - 1e-5:
            raise ValueError('Positive/Negative requires consistently oriented planar cutter faces')
    if first_normal is None:
        raise ValueError('Degenerate cutter faces')
    distances = (vb - point) @ first_normal
    extent = max(float(np.ptp(vb,axis=0).max()), 1.)
    if np.max(np.abs(distances)) > max(tolerance * 4, extent * 1e-8):
        raise ValueError('Positive/Negative is only defined for a planar cutter; use Keep by Index or Largest/Smallest')
    return point, first_normal


def _closed_cutter_triangles(vertices_b, faces_b, tolerance):
    vb = _as_vertices(vertices_b, 'vertices_b')
    faces = [list(map(int, face)) for face in faces_b]
    if not faces:
        raise ValueError('Inside/Outside requires a closed cutter mesh')
    # Edges must occur exactly twice in opposite directions (closed orientable manifold).
    counts = defaultdict(list)
    for f in faces:
        for i, a in enumerate(f):
            b = f[(i+1) % len(f)]
            counts[_edge_key(a,b)].append((a,b))
    if any(len(pair) != 2 or pair[0] != pair[1][::-1] for pair in counts.values()):
        raise ValueError('Inside/Outside requires a closed consistently oriented manifold cutter B')
    tri, _ = triangulate_faces(vb, faces, tolerance)
    if not len(tri):
        raise ValueError('Cutter has no triangles')
    return vb[tri]


def _winding_inside(p, triangles, tolerance):
    """Solid-angle winding. Orientation-independent on closed consistent shells."""
    a, b, c = triangles[:,0] - p, triangles[:,1] - p, triangles[:,2] - p
    la = np.linalg.norm(a,axis=1)
    lb = np.linalg.norm(b,axis=1)
    lc = np.linalg.norm(c,axis=1)
    if min(float(la.min()),float(lb.min()),float(lc.min())) <= tolerance:
        raise ValueError('Piece sample touches cutter boundary; Inside/Outside is ambiguous')
    numerator = np.einsum('ij,ij->i', a, np.cross(b,c))
    denominator = la*lb*lc + np.einsum('ij,ij->i',a,b)*lc + np.einsum('ij,ij->i',b,c)*la + np.einsum('ij,ij->i',c,a)*lb
    winding = np.sum(2*np.arctan2(numerator, denominator))/(4*np.pi)
    return abs(winding) > .5


def _samples(piece):
    # Evaluate *every* output face to avoid silently keeping/dropping a region
    # when a short/incomplete cutter fails to disconnect both sides. This may
    # be expensive in Inside/Outside mode for large closed cutter meshes.
    return np.asarray([np.mean(piece.vertices[f], axis=0) for f in piece.faces],
                      dtype=float).reshape(-1, 3)


def select_pieces(pieces, vertices_b, faces_b, *, keep='ALL', piece_index=0, tolerance=1e-6):
    """Selection uses original piece index before filtering (area-descending).

    For planar cut normals, POSITIVE and NEGATIVE correspond to B's oriented
    face normal. For closed cutters INSIDE/OUTSIDE uses solid-angle winding.
    Ambiguous, incompletely split pieces raise instead of silently dropping faces.
    """
    if keep == 'ALL':
        return list(range(len(pieces)))
    if not pieces:
        return []
    if keep == 'LARGEST':
        return [0]
    if keep == 'SMALLEST':
        return [len(pieces)-1]
    if keep == 'INDEX':
        if piece_index < 0 or piece_index >= len(pieces):
            return []
        return [piece_index]
    if keep in ('POSITIVE','NEGATIVE'):
        origin, normal = _planar_cutter(vertices_b, faces_b, tolerance)
        chosen = []
        for piece in pieces:
            distances = (_samples(piece) - origin) @ normal
            nonzero = distances[np.abs(distances) > tolerance * 2]
            if len(nonzero) == 0:
                raise ValueError('Piece lies on cutter plane: Positive/Negative side is ambiguous')
            if nonzero.min() < 0 and nonzero.max() > 0:
                raise ValueError('Cutter does not completely separate this piece; use Split/Index instead')
            if (nonzero.mean() > 0) == (keep == 'POSITIVE'):
                chosen.append(piece.index)
        return chosen
    if keep in ('INSIDE','OUTSIDE'):
        triangles = _closed_cutter_triangles(vertices_b, faces_b, tolerance)
        chosen = []
        for piece in pieces:
            samples = _samples(piece)
            statuses = [_winding_inside(s,triangles,tolerance) for s in samples]
            if len(set(statuses)) != 1:
                raise ValueError('Cutter does not completely separate this piece into Inside/Outside')
            if statuses[0] == (keep == 'INSIDE'):
                chosen.append(piece.index)
        return chosen
    raise ValueError(f'Unknown Keep mode: {keep}')


def join_pieces(pieces):
    """Combine independent pieces as loose parts; no vertices shared between pieces."""
    verts, faces, edges, edge_masks, vert_masks, origins = [], [], [], [], [], []
    offset = 0
    for piece in pieces:
        verts.append(piece.vertices)
        faces.extend([[v+offset for v in f] for f in piece.faces])
        edges.append(piece.edges + offset)
        edge_masks.append(piece.cut_edge_mask)
        vert_masks.append(piece.cut_vertex_mask)
        origins.append(piece.face_origins)
        offset += len(piece.vertices)
    return MeshPiece(
        np.concatenate(verts) if verts else np.empty((0,3),dtype=float),
        np.concatenate(edges) if edges else np.empty((0,2),dtype=np.int64),
        faces,
        np.concatenate(edge_masks) if edge_masks else np.empty((0,),dtype=bool),
        np.concatenate(vert_masks) if vert_masks else np.empty((0,),dtype=bool),
        np.concatenate(origins) if origins else np.empty((0,),dtype=np.int64),
        np.arange(len(faces),dtype=np.int64),
        sum(p.area for p in pieces), -1,
    )


def cut_mesh_parts(vertices_a, faces_a, vertices_b, faces_b, *,
                   mode='CUT', keep='ALL', piece_index=0,
                   tolerance=1e-6, acceleration='auto', use_numba=None,
                   include_coplanar=True, preserve_polygons=True):
    """Returns a PiecesResult with one piece per output SV object in SEPARATE.

    CUT preserves original joined topology. SPLIT returns one loose-parts
    object; SEPARATE returns one SV object per topologically connected region.
    Keep filters are supported in SPLIT/SEPARATE only.
    """
    if mode not in ('CUT','SPLIT','SEPARATE'):
        raise ValueError('Unknown mode')
    if mode == 'CUT' and keep != 'ALL':
        raise ValueError('Keep filtering requires Split or Separate mode')
    base = cut_mesh(vertices_a, faces_a, vertices_b, faces_b,
                    tolerance=tolerance, acceleration=acceleration,
                    use_numba=use_numba, include_coplanar=include_coplanar,
                    preserve_polygons=preserve_polygons)
    if mode == 'CUT':
        item = MeshPiece(base.vertices, base.edges, base.faces, base.cut_edge_mask,
                         base.cut_vertex_mask, base.face_origins,
                         np.arange(len(base.faces),dtype=np.int64),
                         _surface_area(base.vertices, base.faces), 0)
        return PiecesResult([item], 1, [0], base.intersection_vertices,
                            base.intersection_edges, base.acceleration, base.numba_used)
    pieces = partition_cut(base)
    chosen = select_pieces(pieces, vertices_b, faces_b, keep=keep,
                           piece_index=piece_index, tolerance=tolerance)
    selected = [pieces[i] for i in chosen]
    if mode == 'SPLIT':
        selected = [join_pieces(selected)]
    return PiecesResult(selected, len(pieces), chosen, base.intersection_vertices,
                        base.intersection_edges, base.acceleration, base.numba_used)


__all__ = ['MeshPiece','PiecesResult','partition_cut','select_pieces','join_pieces','cut_mesh_parts']
