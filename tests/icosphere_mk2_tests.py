# SPDX-License-Identifier: GPL-3.0-or-later
"""Topology and cache regressions for the NumPy/Numba IcoSphere MK2 node."""

import unittest

import numpy as np

from sverchok.nodes.generator import icosphere as ico


class TestIcosphereMk2(unittest.TestCase):

    def test_mesh_counts_and_topology(self):
        for subdivisions in range(0, 6):
            verts, edges, faces = ico._generate_unit_icosphere(subdivisions)
            factor = 4 ** max(subdivisions - 1, 0)
            self.assertEqual(verts.shape, (10 * factor + 2, 3))
            self.assertEqual(edges.shape, (30 * factor, 2))
            self.assertEqual(faces.shape, (20 * factor, 3))

            self.assertTrue(np.all(edges >= 0))
            self.assertTrue(np.all(edges < len(verts)))
            self.assertTrue(np.all(faces >= 0))
            self.assertTrue(np.all(faces < len(verts)))
            self.assertEqual(len(np.unique(np.sort(edges, axis=1), axis=0)), len(edges))
            np.testing.assert_allclose(np.linalg.norm(verts, axis=1), 1.0,
                                       atol=1e-14, rtol=0)

    def test_cache_does_not_depend_on_connected_sockets(self):
        ico._cached_unit_icosphere.cache_clear()
        verts_only = ico._unit_icosphere(4, False, False, False, True)
        self.assertIsNone(verts_only[1])
        self.assertIsNone(verts_only[2])

        all_outputs = ico._unit_icosphere(4, False, True, True, True)
        self.assertIs(verts_only[0], all_outputs[0])
        self.assertIsNotNone(all_outputs[1])
        self.assertIsNotNone(all_outputs[2])
        self.assertEqual(ico._cached_unit_icosphere.cache_info().misses, 1)
        self.assertFalse(all_outputs[0].flags.writeable)

    def test_uncached_can_skip_unused_outputs(self):
        verts, edges, faces = ico._unit_icosphere(4, False, False, False, False)
        self.assertEqual(verts.shape, (642, 3))
        self.assertIsNone(edges)
        self.assertIsNone(faces)

    @unittest.skipIf(ico.numba is None, 'Numba is not installed')
    def test_numba_matches_numpy(self):
        for subdivisions in range(0, 6):
            np_mesh = ico._generate_unit_icosphere(subdivisions, use_numba=False)
            nb_mesh = ico._generate_unit_icosphere(subdivisions, use_numba=True)
            np.testing.assert_allclose(nb_mesh[0], np_mesh[0], atol=1e-14, rtol=0)
            np.testing.assert_array_equal(nb_mesh[1], np_mesh[1])
            np.testing.assert_array_equal(nb_mesh[2], np_mesh[2])


if __name__ == '__main__':
    unittest.main()
