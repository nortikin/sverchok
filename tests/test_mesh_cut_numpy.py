# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression tests for Sverchok Mesh Intersection and Cut by Mesh.

Run from any directory:
    python3 tests/test_mesh_cut_numpy.py

Only NumPy is required. SciPy and Numba paths are exercised if available.
No bpy, bmesh, mathutils or Blender process is required.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import math
import sys
import unittest

import numpy as np

# Import the geometric kernels directly, without importing 'sverchok' (which
# boots Blender). Works both inside a checkout and as a standalone test file.
REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "utils" / "mesh"
if not (CORE / "mesh_cut.py").is_file():
    raise RuntimeError(f"Mesh Cut kernel not found at {CORE}. Install the nodes first.")
sys.path.insert(0, str(CORE))

from mesh_intersections import HAS_NUMBA, HAS_SCIPY, intersect_meshes
from mesh_cut import cut_mesh
from mesh_cut_parts import cut_mesh_parts

CUBE_V = np.asarray([
    (-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
    (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)
], dtype=float)
CUBE_F = [[0,3,2,1], [4,5,6,7], [0,1,5,4],
          [1,2,6,5], [2,3,7,6], [3,0,4,7]]
PLANE_V = np.asarray([(-2,-2,0), (2,-2,0), (2,2,0), (-2,2,0)], dtype=float)
PLANE_F = [[0,1,2,3]]


def vector_area(vertices, faces):
    """Area of planar polygons, including concave n-gons."""
    verts = np.asarray(vertices, dtype=float)
    total = 0.0
    for f in faces:
        p = verts[np.asarray(f, dtype=int)]
        total += 0.5 * float(np.linalg.norm(np.cross(p, np.roll(p, -1, axis=0)).sum(axis=0)))
    return total


def edge_keys(edges):
    return [tuple(sorted(map(int, e))) for e in edges]


def check_topology(test, piece):
    verts = np.asarray(piece.vertices)
    edges = np.asarray(piece.edges)
    test.assertEqual(verts.ndim, 2)
    test.assertEqual(verts.shape[1], 3)
    test.assertTrue(np.isfinite(verts).all())
    test.assertEqual(len(edges), len(piece.cut_edge_mask))
    test.assertEqual(len(verts), len(piece.cut_vertex_mask))
    test.assertEqual(len(piece.faces), len(piece.face_origins))
    edge_set = set(edge_keys(edges))
    test.assertEqual(len(edge_set), len(edges), "Duplicate edges")
    incidence = Counter()
    for f in piece.faces:
        test.assertGreaterEqual(len(f), 3)
        test.assertEqual(len(set(f)), len(f), "Repeated vertex within polygon")
        for i in f:
            test.assertTrue(0 <= int(i) < len(verts))
        for k in range(len(f)):
            key = tuple(sorted((int(f[k]), int(f[(k+1) % len(f)]))))
            test.assertIn(key, edge_set)
            incidence[key] += 1
    test.assertTrue(all(count <= 2 for count in incidence.values()),
                    "Non-manifold edge (> 2 incident faces)")


def rotated_plane(degrees=45.0):
    theta = math.radians(degrees)
    c, s = math.cos(theta), math.sin(theta)
    rotation = np.asarray([[1, 0, 0], [0, c, -s], [0, s, c]])
    return np.asarray([(-1.5,-1.5,0), (1.5,-1.5,0),
                       (1.5,1.5,0), (-1.5,1.5,0)]) @ rotation.T


def octasphere(level=2):
    """An indexed triangulated approximation to a sphere, without Blender."""
    verts = [np.asarray(v, dtype=float) for v in (
        (1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1))]
    faces = [(0,2,4), (2,1,4), (1,3,4), (3,0,4),
             (2,0,5), (1,2,5), (3,1,5), (0,3,5)]
    for _ in range(level):
        cache = {}
        def middle(i, j):
            key = tuple(sorted((i,j)))
            if key not in cache:
                midpoint = verts[i] + verts[j]
                verts.append(midpoint / np.linalg.norm(midpoint))
                cache[key] = len(verts) - 1
            return cache[key]
        updated = []
        for a, b, c in faces:
            ab, bc, ca = middle(a,b), middle(b,c), middle(c,a)
            updated.extend([(a,ab,ca), (ab,b,bc), (ca,bc,c), (ab,bc,ca)])
        faces = updated
    return np.asarray(verts), faces


class MeshIntersectionTests(unittest.TestCase):
    def test_segment_and_face_provenance(self):
        va = [[0,0,0], [1,0,0], [0,1,0]]
        vb = [[.4,-1,-1], [.4,2,-1], [.4,0,1]]
        out = intersect_meshes(va, [[0,1,2]], vb, [[0,1,2]], use_numba=False)
        self.assertEqual(out.edges.shape, (1,2))
        self.assertEqual(out.edge_face_pairs.tolist(), [[0,0]])
        points = out.vertices[out.edges[0]]
        points = points[np.argsort(points[:,1])]
        np.testing.assert_allclose(points, [[.4,0,0], [.4,.6,0]], atol=1e-7)

    def test_no_intersection(self):
        shifted = PLANE_V + [0,0,4]
        out = intersect_meshes(CUBE_V, CUBE_F, shifted, PLANE_F, use_numba=False)
        self.assertEqual(len(out.vertices), 0)
        self.assertEqual(len(out.edges), 0)
        self.assertEqual(out.coplanar_polygons, [])

    def test_coplanar_overlap(self):
        va = [[0,0,0], [1,0,0], [0,1,0]]
        vb = [[.2,.2,0], [.7,.2,0], [.2,.7,0]]
        out = intersect_meshes(va, [[0,1,2]], vb, [[0,1,2]], use_numba=False)
        self.assertEqual(len(out.coplanar_polygons), 1)
        np.testing.assert_array_equal(out.coplanar_face_pairs, [[0,0]])
        self.assertAlmostEqual(vector_area(out.vertices, out.coplanar_polygons), .125, places=8)

    def test_point_contact_does_not_create_segment(self):
        va = [[0,0,0], [1,0,0], [0,1,0]]
        vb = [[0,0,0], [0,0,1], [-1,-1,1]]
        out = intersect_meshes(va, [[0,1,2]], vb, [[0,1,2]], use_numba=False)
        self.assertEqual(len(out.edges), 0)
        self.assertEqual(len(out.point_indices), 1)

    def test_backend_equivalence(self):
        va = [[0,0,0], [1,0,0], [0,1,0]]
        vb = [[.4,-1,-1], [.4,2,-1], [.4,0,1]]
        backends = ['brute', 'bvh'] + (['scipy'] if HAS_SCIPY else [])
        results = []
        for backend in backends:
            with self.subTest(backend=backend):
                res = intersect_meshes(va, [[0,1,2]], vb, [[0,1,2]],
                                       acceleration=backend, use_numba=False)
                segs = sorted(tuple(sorted(tuple(np.round(p, 8)) for p in res.vertices[e]))
                              for e in res.edges)
                results.append(segs)
        self.assertTrue(all(result == results[0] for result in results))

    def test_input_arrays_are_not_mutated(self):
        va, vb = CUBE_V.copy(), PLANE_V.copy()
        intersect_meshes(va, CUBE_F, vb, PLANE_F, use_numba=False)
        np.testing.assert_array_equal(va, CUBE_V)
        np.testing.assert_array_equal(vb, PLANE_V)

    @unittest.skipUnless(HAS_NUMBA, "Numba not installed")
    def test_numba_matches_numpy(self):
        va = [[0,0,0], [1,0,0], [0,1,0]]
        vb = [[.4,-1,-1], [.4,2,-1], [.4,0,1]]
        basic = intersect_meshes(va, [[0,1,2]], vb, [[0,1,2]], use_numba=False)
        accelerated = intersect_meshes(va, [[0,1,2]], vb, [[0,1,2]], use_numba=True)
        self.assertTrue(accelerated.numba_used)
        p = basic.vertices[basic.edges[0]]
        q = accelerated.vertices[accelerated.edges[0]]
        np.testing.assert_allclose(p[np.argsort(p[:,1])], q[np.argsort(q[:,1])], atol=1e-8)


class MeshCutTests(unittest.TestCase):
    def test_cube_12_to_10_quads_no_unnecessary_diagonals(self):
        out = cut_mesh(CUBE_V, CUBE_F, PLANE_V, PLANE_F, use_numba=False)
        check_topology(self, out)
        self.assertEqual(len(out.faces), 10)
        self.assertTrue(all(len(f) == 4 for f in out.faces))
        self.assertEqual(int(out.cut_edge_mask.sum()), 4)
        self.assertAlmostEqual(vector_area(out.vertices, out.faces), 24.0, places=8)
        self.assertEqual(set(out.face_origins.tolist()), set(range(6)))

    def test_unaffected_quads_stay_untouched(self):
        out = cut_mesh(CUBE_V, CUBE_F, PLANE_V, PLANE_F, use_numba=False)
        for original in (0,1):
            faces = [f for f, source in zip(out.faces,out.face_origins) if source == original]
            self.assertEqual(faces, [CUBE_F[original]])

    def test_triangles_only_when_preservation_is_off(self):
        out = cut_mesh(CUBE_V, CUBE_F, PLANE_V, PLANE_F,
                       use_numba=False, preserve_polygons=False)
        self.assertEqual(len(out.faces), 28)
        self.assertTrue(all(len(f) == 3 for f in out.faces))
        self.assertAlmostEqual(vector_area(out.vertices, out.faces), 24.0, places=8)

    def test_quad_becomes_two_quads(self):
        a = [[0,0,0], [2,0,0], [2,2,0], [0,2,0]]
        b = [[.7,-1,-1], [.7,3,-1], [.7,3,1], [.7,-1,1]]
        out = cut_mesh(a, [[0,1,2,3]], b, [[0,1,2,3]], use_numba=False)
        check_topology(self, out)
        self.assertEqual(len(out.faces), 2)
        self.assertTrue(all(len(f) == 4 for f in out.faces))
        self.assertEqual(int(out.cut_edge_mask.sum()), 1)
        self.assertAlmostEqual(vector_area(out.vertices,out.faces),4.,places=8)

    def test_point_contact_does_not_add_faces(self):
        a = [[0,0,0], [2,0,0], [0,2,0]]
        b = [[.4,.4,0], [.4,.4,1], [.6,.6,1]]
        out = cut_mesh(a, [[0,1,2]], b, [[0,1,2]], use_numba=False)
        self.assertEqual(out.faces, [[0,1,2]])
        self.assertEqual(len(out.vertices), 3)
        self.assertFalse(out.cut_edge_mask.any())

    def test_open_slit_conserves_area(self):
        a = [[0,0,0], [2,0,0], [0,2,0]]
        b = [[.3,.3,-1], [.8,.3,-1], [.8,.3,1], [.3,.3,1]]
        out = cut_mesh(a, [[0,1,2]], b, [[0,1,2,3]], use_numba=False)
        check_topology(self, out)
        self.assertGreater(int(out.cut_edge_mask.sum()), 0)
        self.assertAlmostEqual(vector_area(out.vertices,out.faces), 2.,places=8)

    def test_no_hit_does_not_rebuild_mesh(self):
        out = cut_mesh(CUBE_V, CUBE_F, PLANE_V + [0,0,7], PLANE_F, use_numba=False)
        self.assertEqual(out.faces, CUBE_F)
        self.assertEqual(len(out.vertices), 8)
        self.assertFalse(out.cut_edge_mask.any())

    def test_triangle_source_becomes_triangle_plus_quad(self):
        a = [[0,0,0], [2,0,0], [0,2,0]]
        b = [[.7,-1,-1], [.7,3,-1], [.7,3,1], [.7,-1,1]]
        out = cut_mesh(a, [[0,1,2]], b, [[0,1,2,3]], use_numba=False)
        self.assertEqual(sorted(map(len,out.faces)), [3,4])
        self.assertEqual(int(out.cut_edge_mask.sum()), 1)
        self.assertAlmostEqual(vector_area(out.vertices,out.faces), 2.,places=8)


class SeparationTests(unittest.TestCase):
    def test_separate_into_two_independent_meshes(self):
        res = cut_mesh_parts(CUBE_V,CUBE_F,PLANE_V,PLANE_F,
                             mode='SEPARATE', use_numba=False)
        self.assertEqual(res.all_pieces_count, 2)
        self.assertEqual(len(res.pieces), 2)
        self.assertAlmostEqual(sum(vector_area(p.vertices,p.faces) for p in res.pieces),24.,places=8)
        for p in res.pieces:
            check_topology(self,p)
            self.assertEqual(len(p.faces),5)
            self.assertTrue(all(len(f)==4 for f in p.faces))
            self.assertAlmostEqual(p.area,12.,places=8)

    def test_split_keeps_one_object_but_duplicates_seam_vertices(self):
        res = cut_mesh_parts(CUBE_V,CUBE_F,PLANE_V,PLANE_F,
                             mode='SPLIT',use_numba=False)
        self.assertEqual(res.all_pieces_count,2)
        self.assertEqual(len(res.pieces),1)
        self.assertEqual(len(res.pieces[0].vertices),16)
        self.assertEqual(int(res.pieces[0].cut_edge_mask.sum()),8)
        self.assertAlmostEqual(res.pieces[0].area,24.,places=8)

    def test_keep_positive_and_negative_remove_opposite_half(self):
        for keep, sign in [('POSITIVE',1),('NEGATIVE',-1)]:
            with self.subTest(keep=keep):
                result = cut_mesh_parts(CUBE_V,CUBE_F,PLANE_V,PLANE_F,
                                        mode='SEPARATE',keep=keep,use_numba=False)
                self.assertEqual(len(result.pieces),1)
                p = result.pieces[0]
                self.assertAlmostEqual(p.area,12.,places=8)
                centers = np.asarray([p.vertices[f].mean(axis=0) for f in p.faces])
                self.assertTrue(np.all(centers[:,2]*sign >= -1e-8))

    def test_45_degrees_marks_original_cube_edges(self):
        knife = rotated_plane(45)
        raw = cut_mesh(CUBE_V,CUBE_F,knife,PLANE_F,use_numba=False)
        self.assertEqual(int(raw.cut_edge_mask.sum()),4)
        for mode in ('SPLIT','SEPARATE'):
            for keep in ('ALL','POSITIVE','NEGATIVE'):
                with self.subTest(mode=mode,keep=keep):
                    result = cut_mesh_parts(CUBE_V,CUBE_F,knife,PLANE_F,
                                            mode=mode,keep=keep,use_numba=False)
                    self.assertEqual(result.all_pieces_count,2)
                    area = sum(vector_area(p.vertices,p.faces) for p in result.pieces)
                    self.assertAlmostEqual(area,24. if keep=='ALL' else 12.,places=8)

    def test_reversed_cutter_winding_swaps_side(self):
        pos = cut_mesh_parts(CUBE_V,CUBE_F,PLANE_V,PLANE_F,mode='SEPARATE',
                             keep='POSITIVE',use_numba=False)
        flipped = cut_mesh_parts(CUBE_V,CUBE_F,PLANE_V,[PLANE_F[0][::-1]],
                                 mode='SEPARATE',keep='POSITIVE',use_numba=False)
        za = float(pos.pieces[0].vertices[:,2].mean())
        zb = float(flipped.pieces[0].vertices[:,2].mean())
        self.assertLess(za*zb,0)

    def test_closed_cutter_inside_outside(self):
        a = [[-2,-2,0],[2,-2,0],[2,2,0],[-2,2,0]]
        inside = cut_mesh_parts(a,[[0,1,2,3]],CUBE_V,CUBE_F,mode='SEPARATE',
                                keep='INSIDE',use_numba=False)
        outside = cut_mesh_parts(a,[[0,1,2,3]],CUBE_V,CUBE_F,mode='SEPARATE',
                                 keep='OUTSIDE',use_numba=False)
        self.assertAlmostEqual(sum(p.area for p in inside.pieces),4.,places=8)
        self.assertAlmostEqual(sum(p.area for p in outside.pieces),12.,places=8)

    def test_icosphere_like_mesh_cut_by_box_no_stray_faces(self):
        sphere, faces = octasphere(level=2)
        box = np.asarray([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0),
                          (-.5,-.5,1),(.5,-.5,1),(.5,.5,1),(-.5,.5,1)],dtype=float)
        result = cut_mesh_parts(sphere,faces,box,CUBE_F,mode='SEPARATE',
                                keep='ALL',use_numba=False)
        self.assertEqual(result.all_pieces_count,2)
        self.assertEqual(len(result.pieces),2)
        original_area = vector_area(sphere,faces)
        self.assertAlmostEqual(sum(p.area for p in result.pieces),original_area,places=7)
        for p in result.pieces:
            check_topology(self,p)
            ecount=Counter(tuple(sorted((f[i],f[(i+1)%len(f)])))
                           for f in p.faces for i in range(len(f)))
            marked={tuple(sorted(map(int,e))):bool(m)
                    for e,m in zip(p.edges,p.cut_edge_mask)}
            self.assertTrue(all(marked[edge] for edge,n in ecount.items() if n==1),
                            'Boundary without cut mask')

    def test_search_backend_parity_for_45_degree_split(self):
        knife=rotated_plane(45)
        backends=['bvh','brute']+(['scipy'] if HAS_SCIPY else [])
        for backend in backends:
            with self.subTest(backend=backend):
                pieces=cut_mesh_parts(CUBE_V,CUBE_F,knife,PLANE_F,mode='SEPARATE',
                                      acceleration=backend,use_numba=False)
                self.assertEqual(len(pieces.pieces),2)
                self.assertAlmostEqual(sum(p.area for p in pieces.pieces),24.,places=8)

    def test_cut_cannot_apply_keep_filter(self):
        with self.assertRaisesRegex(ValueError,'requires Split'):
            cut_mesh_parts(CUBE_V,CUBE_F,PLANE_V,PLANE_F,mode='CUT',
                           keep='NEGATIVE',use_numba=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
