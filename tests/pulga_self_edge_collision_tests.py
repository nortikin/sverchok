# SPDX-License-Identifier: GPL-3.0-or-later
"""Numerical tests independent of Blender. Run: python -m unittest tests.test_pulga_self_edge_collision"""
import unittest
import numpy as np

from sverchok.utils.pulga_self_edge_collision import (
    HAS_NUMBA, contact_forces, SvSelfEdgeCollisionForce)


class SelfEdgeCollisionTests(unittest.TestCase):
    def calculate(self, verts, edges, radii, engine='NUMPY', strength=1.0,
                  edge_radius=0.0, damping=0.0, velocity=None):
        verts = np.asarray(verts, dtype=float)
        if velocity is None:
            velocity = np.zeros_like(verts)
        return contact_forces(verts, velocity, radii, edges, [strength],
                              [edge_radius], [damping], engine)

    def test_incident_edges_ignored(self):
        out = self.calculate([[0, 0, 0], [1, 0, 0]], [[0, 1]], [.5, .5])
        np.testing.assert_array_equal(out, 0)

    def test_collision_pushes_particle_and_both_endpoints(self):
        out = self.calculate([[0, 0, 0], [2, 0, 0], [.5, .1, 0]],
                             [[0, 1]], [0, 0, .5])
        np.testing.assert_allclose(out[:, 1], [-.3, -.1, .4], atol=1e-12)
        np.testing.assert_allclose(out.sum(axis=0), 0, atol=1e-12)

    def test_far_edge_no_collision(self):
        out = self.calculate([[0, 0, 0], [2, 0, 0], [.5, 1, 0]],
                             [[0, 1]], [0, 0, .2])
        np.testing.assert_array_equal(out, 0)

    def test_multiple_edges_both_contribute(self):
        pts = [[-1, 0, 0], [1, 0, 0], [0, -.3, 0],
               [-1, .3, 0], [1, .3, 0]]
        out = self.calculate(pts, [[0, 1], [3, 4]], [0, 0, .5, 0, 0])
        self.assertGreater(np.linalg.norm(out[2]), 0)
        np.testing.assert_allclose(out.sum(axis=0), 0, atol=1e-12)

    def test_per_vertex_strength(self):
        pts = [[0, 0, 0], [1, 0, 0], [.5, .1, 0]]
        a = contact_forces(pts, np.zeros((3,3)), [0,0,.5], [[0,1]], [1,1,1], [0], [0], 'NUMPY')
        b = contact_forces(pts, np.zeros((3,3)), [0,0,.5], [[0,1]], [1,1,2], [0], [0], 'NUMPY')
        np.testing.assert_allclose(b, a*2, atol=1e-12)

    def test_exact_overlap_is_finite(self):
        out = self.calculate([[0, 0, 0], [2, 0, 0], [1, 0, 0]],
                             [[0, 1]], [0, 0, .5])
        self.assertTrue(np.isfinite(out).all())
        self.assertGreater(np.linalg.norm(out[2]), 0)
        np.testing.assert_allclose(out.sum(axis=0), 0, atol=1e-12)

    def test_invalid_indices(self):
        with self.assertRaises(ValueError):
            self.calculate([[0, 0, 0]], [[0, 7]], [.5])

    def test_empty_edges(self):
        out = self.calculate([[0, 0, 0]], [], [.5])
        np.testing.assert_array_equal(out, 0)

    def test_numba_matches_numpy(self):
        if not HAS_NUMBA:
            self.skipTest('Numba not installed')
        pts = [[0, 0, 0], [2, 0, 0], [1, .1, 0],
               [.8, 0, 0], [1.4, .4, 0], [0, 0, 2]]
        e = [[0,1], [0,5], [1,5]]
        a = self.calculate(pts, e, [.1, .1, .5, .4, .6, .3], 'NUMPY', damping=.2)
        b = self.calculate(pts, e, [.1, .1, .5, .4, .6, .3], 'NUMBA', damping=.2)
        np.testing.assert_allclose(a, b, atol=1e-10)

    def test_pulga_force_contract(self):
        class PS:
            verts = np.array([[0,0,0], [2,0,0], [.5,.1,0]], dtype=float)
            vel = np.zeros_like(verts)
            rads = np.array([0,0,.5], dtype=float)
            v_len = len(verts)
            force_resultant = np.zeros_like(verts)
        ps = PS()
        obj = SvSelfEdgeCollisionForce([[0,1]], [1.0], [0.0], [0.0])
        obj.setup(ps)
        obj.add(ps)
        self.assertGreater(ps.force_resultant[2,1], 0)


if __name__ == '__main__':
    unittest.main()
