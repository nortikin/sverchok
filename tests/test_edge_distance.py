# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the Blender-independent edge_distance utility."""

import importlib.util
import sys
from pathlib import Path
import unittest
from unittest import mock

import numpy as np

MODULE_PATH = Path(__file__).resolve().parents[1] / 'utils' / 'edge_distance.py'
spec = importlib.util.spec_from_file_location('tested_edge_distance', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class TestEdgeDistance(unittest.TestCase):
    def query(self, points, verts, edges, engine='NUMPY', **kwargs):
        return mod.distance_to_edges(points, verts, edges, engine=engine, **kwargs)

    def test_interior_and_endpoints(self):
        d, q, idx, f = self.query([[0.25, 2, 0], [2, 1, 0]],
                                   [[0, 0, 0], [1, 0, 0]], [[0, 1]])
        np.testing.assert_allclose(d, [2, 2**.5])
        np.testing.assert_allclose(q, [[0.25, 0, 0], [1, 0, 0]])
        np.testing.assert_array_equal(idx, [0, 0])
        np.testing.assert_allclose(f, [0.25, 1.])

    def test_edge_index_and_ties(self):
        d, q, i, t = self.query([[0, 1, 0]],
                                 [[-1, 0, 0], [1, 0, 0], [-1, 2, 0], [1, 2, 0]],
                                 [[0, 1], [2, 3]])
        self.assertEqual(int(i[0]), 0)
        self.assertAlmostEqual(d[0], 1)
        self.assertAlmostEqual(t[0], 0.5)

    def test_loose_vertices_and_zero_length(self):
        verts = [[0, 0, 0], [0, 0, 0], [3, 0, 0]]
        d, q, i, t = self.query([[2.9, 0, 0], [0, 2, 0]], verts, [[0, 1]])
        np.testing.assert_allclose(d, [0.1, 2.0])
        np.testing.assert_array_equal(i, [-1, 0])
        np.testing.assert_allclose(t, [-1, 0])
        d2, _, _, _ = self.query([[2.9, 0, 0]], verts, [[0, 1]],
                                  include_loose=False)
        np.testing.assert_allclose(d2, [2.9])

    def test_no_edges_and_no_targets(self):
        d, q, i, t = self.query([[1, 0, 0]], [[2, 0, 0]], [])
        np.testing.assert_allclose(d, [1])
        np.testing.assert_array_equal(i, [-1])
        np.testing.assert_allclose(t, [-1])
        d, q, i, t = self.query([[1, 0, 0]], [], [])
        self.assertTrue(np.isinf(d[0]))
        self.assertTrue(np.isnan(q).all())
        np.testing.assert_array_equal(i, [-1])

    def test_tiny_distances_not_treated_as_ties(self):
        p = [[0., 0., 0.]]
        verts = [[0, 2.e-9, 0], [1.e-9, 2.e-9, 0],
                 [0, 1.e-9, 0], [1.e-9, 1.e-9, 0]]
        edges = [[0, 1], [2, 3]]
        for engine in (['NUMPY', 'NUMBA'] if mod.HAS_NUMBA else ['NUMPY']):
            d, q, idx, t = self.query(p, verts, edges, engine)
            self.assertEqual(int(idx[0]), 1)
            np.testing.assert_allclose(d, [1.e-9], rtol=1.e-12)

    def test_reject_invalid_indices(self):
        with self.assertRaises(ValueError):
            self.query([[0, 0, 0]], [[0, 0, 0]], [[0, 3]])
        with self.assertRaises(ValueError):
            self.query([[0, 0, 0]], [[0, 0, 0]], [[-1, 0]])

    def test_budget_and_random_bruteforce(self):
        rng = np.random.default_rng(10)
        points = rng.normal(size=(22, 3))
        verts = rng.normal(size=(31, 3))
        edges = np.stack([np.arange(30), np.arange(1, 31)], axis=1)
        outputs = [self.query(points, verts, edges, pair_budget=b)
                   for b in (1, 100, 65536)]
        for r in outputs[1:]:
            for a, b in zip(outputs[0], r):
                np.testing.assert_allclose(a, b)

    def test_recursive_matching_broadcast(self):
        p = [[[[0.5, 2, 0]], [[2, 2, 0]]]]
        v = [[[0, 0, 0], [1, 0, 0]]]
        e = [[[0, 1]]]
        result = mod.recursive_distance_to_edges(p, v, e)
        self.assertEqual(result[0], [[[2.0], [5 ** 0.5]]])
        self.assertEqual(result[2], [[[0], [0]]])

    def test_recursive_two_targets(self):
        p = [[[0, 0, 0]], [[10, 0, 0]]]
        v = [[[1, 0, 0]], [[11, 0, 0]]]
        e = [[], []]
        result = mod.recursive_distance_to_edges(p, v, e)
        self.assertEqual(result[0], [[1.0], [1.0]])
        self.assertEqual(result[2], [[-1], [-1]])

    def test_auto_uses_numpy_without_numba(self):
        points = [[0, 0, 0]]
        verts = [[0, 2, 0], [1, 2, 0]]
        edges = [[0, 1]]
        with mock.patch.object(mod, 'HAS_NUMBA', False):
            auto_result = self.query(points, verts, edges, engine='AUTO')
            numpy_result = self.query(points, verts, edges, engine='NUMPY')
            for a, b in zip(auto_result, numpy_result):
                np.testing.assert_allclose(a, b)
            with self.assertRaises(RuntimeError):
                self.query(points, verts, edges, engine='NUMBA')

    @unittest.skipUnless(mod.HAS_NUMBA, 'Numba is not installed')
    def test_auto_uses_numba_even_for_one_pair(self):
        points = [[0, 0, 0]]
        verts = [[0, 2, 0], [1, 2, 0]]
        edges = [[0, 1]]
        with mock.patch.object(mod, '_numba_query', wraps=mod._numba_query) as jit:
            auto_result = self.query(points, verts, edges, engine='AUTO')
            jit.assert_called_once()
            np.testing.assert_allclose(auto_result[0], [2.0])
            self.query(points, verts, edges, engine='NUMPY')
            jit.assert_called_once()  # Explicit NumPy bypasses Numba.

    @unittest.skipUnless(mod.HAS_NUMBA, 'Numba is not installed')
    def test_numba_matches_numpy(self):
        rng = np.random.default_rng(2)
        p = rng.standard_normal((18, 3))
        verts = rng.standard_normal((12, 3))
        edges = [[i, i+1] for i in range(9)] + [[9, 9]]
        a = self.query(p, verts, edges, 'NUMPY')
        b = self.query(p, verts, edges, 'NUMBA')
        for av, bv in zip(a, b):
            np.testing.assert_allclose(av, bv, rtol=1.e-12, atol=1.e-12)


class TestEdgeDistanceMulti(unittest.TestCase):
    def query(self, points, verts, edges, engine='NUMPY', **kwargs):
        return mod.distance_to_edges(points, verts, edges, engine=engine, **kwargs)

    def test_nearest_n_sorted_and_limited(self):
        v = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 2, 0],
             [0, 4, 0], [2, 4, 0]]
        edges = [[0, 1], [2, 3], [4, 5]]
        d, pos, idx, t = self.query([[1, 1.5, 0], [1, 4, 0]], v, edges,
                                    mode='NEAREST_N', count=2)
        np.testing.assert_allclose(d[0], [0.5, 1.5])
        np.testing.assert_array_equal(idx[0], [1, 0])
        np.testing.assert_allclose(d[1], [0, 2])
        np.testing.assert_array_equal(idx[1], [2, 1])
        np.testing.assert_allclose(t[0], [0.5, 0.5])
        self.assertEqual(len(pos[0]), 2)

    def test_nearest_n_more_than_available(self):
        d, _, idx, _ = self.query([[0, 1, 0]],
                                   [[0, 0, 0], [1, 0, 0]], [[0, 1]],
                                   mode='NEAREST_N', count=100)
        self.assertEqual(len(d[0]), 1)
        np.testing.assert_array_equal(idx[0], [0])

    def test_range_inclusive_empty_zero(self):
        v = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 2, 0]]
        e = [[0, 1], [2, 3]]
        d, loc, idx, t = self.query([[1, 0, 0], [1, 1, 0]], v, e,
                                    mode='RANGE', max_distance=0)
        np.testing.assert_allclose(d[0], [0])
        self.assertEqual(len(d[1]), 0)
        self.assertEqual(loc[1].shape, (0, 3))
        np.testing.assert_array_equal(idx[0], [0])
        d2, _, idx2, _ = self.query([[1, 1, 0]], v, e,
                                    mode='RANGE', max_distance=1)
        np.testing.assert_allclose(d2[0], [1, 1])
        np.testing.assert_array_equal(idx2[0], [0, 1])

    def test_duplicate_projected_positions_still_two_edges(self):
        v = [[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0]]
        e = [[0, 1], [2, 3]]
        for mode in ('RANGE', 'NEAREST_N'):
            d, loc, idx, _ = self.query([[0, 0, 0]], v, e,
                                         mode=mode, max_distance=0, count=2)
            np.testing.assert_allclose(d[0], [0, 0])
            np.testing.assert_array_equal(idx[0], [0, 1])
            np.testing.assert_allclose(loc[0], [[0,0,0], [0,0,0]])

    def test_loose_vertices_and_degenerate_edges(self):
        v = [[0, 0, 0], [0, 0, 0], [3, 0, 0]]
        e = [[0, 1]]
        d, loc, idx, factor = self.query([[2.9, 0, 0]], v, e,
                                         mode='NEAREST_N', count=4)
        np.testing.assert_allclose(d[0], [0.1, 2.9])
        np.testing.assert_array_equal(idx[0], [-1, 0])
        np.testing.assert_array_equal(factor[0], [-1, 0])
        self.assertEqual(len(loc[0]), 2)
        d2, _, idx2, _ = self.query([[2.9, 0, 0]], v, e,
                                    mode='RANGE', max_distance=1)
        self.assertEqual(len(d2[0]), 1)
        np.testing.assert_array_equal(idx2[0], [-1])

    def test_empty_geometry_multiple_points(self):
        for mode in ('RANGE', 'NEAREST_N'):
            results = self.query([[0, 0, 0], [1, 2, 3]], [], [], mode=mode)
            for part in results:
                self.assertEqual(len(part), 2)
                for r in part:
                    self.assertEqual(len(r), 0)
            self.assertEqual(results[1][0].shape, (0, 3))

    def test_recursive_nesting_preserved(self):
        points = [[[[0, 1, 0]], [[0, 6, 0]]]]
        verts = [[[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 2, 0]]]
        edges = [[[0, 1], [2, 3]]]
        d, loc, ids, t = mod.recursive_distance_to_edges(
            points, verts, edges, mode='RANGE', max_distance=1)
        self.assertEqual(d, [[[[1.0, 1.0]], [[]]]])
        self.assertEqual(ids, [[[[0, 1]], [[]]]])
        self.assertEqual(len(loc[0][0][0]), 2)
        as_np = mod.recursive_distance_to_edges(
            points, verts, edges, mode='RANGE', max_distance=1,
            output_numpy=True)
        self.assertIsInstance(as_np[0][0][0][0], np.ndarray)

    def test_validation(self):
        for kwargs in ({'mode':'INVALID'}, {'mode':'RANGE','max_distance':-1},
                       {'mode':'NEAREST_N','count':-1}):
            with self.assertRaises(ValueError):
                self.query([[0, 0, 0]], [[0, 0, 0]], [], **kwargs)

    @unittest.skipUnless(mod.HAS_NUMBA, 'Numba is not installed')
    def test_engines_match_for_multiple_modes(self):
        rng = np.random.default_rng(34)
        points = rng.normal(size=(15,3))
        verts = rng.normal(size=(20,3))
        edges = [[i, i+1] for i in range(17)] + [[18,18]]
        for mode, kwargs in [('NEAREST_N', {'count':5}),
                             ('NEAREST_N', {'count':100}),
                             ('RANGE', {'max_distance':1.5}),
                             ('RANGE', {'max_distance':0.2})]:
            a = self.query(points, verts, edges, mode=mode,
                           engine='NUMPY', pair_budget=11, **kwargs)
            b = self.query(points, verts, edges, mode=mode,
                           engine='NUMBA', **kwargs)
            for query_idx in range(len(points)):
                for channel in range(4):
                    np.testing.assert_allclose(a[channel][query_idx],
                                               b[channel][query_idx],
                                               rtol=1e-12, atol=1e-12,
                                               err_msg=f'{mode} {query_idx} {channel}')

    @unittest.skipUnless(mod.HAS_NUMBA, 'Numba is not installed')
    def test_auto_uses_numba_for_multiple_modes(self):
        for mode in ('NEAREST_N', 'RANGE'):
            with mock.patch.object(mod, '_numba_query_many',
                                   wraps=mod._numba_query_many) as jit:
                self.query([[0, 1, 0]], [[0, 0, 0], [1, 0, 0]], [[0, 1]],
                           engine='AUTO', mode=mode)
                jit.assert_called_once()


    def test_multi_without_numba(self):
        for mode in ('RANGE', 'NEAREST_N'):
            with mock.patch.object(mod, 'HAS_NUMBA', False):
                a = self.query([[0, 1, 0]], [[0, 0, 0], [1, 0, 0]],
                               [[0, 1]], engine='AUTO', mode=mode)
                b = self.query([[0, 1, 0]], [[0, 0, 0], [1, 0, 0]],
                               [[0, 1]], engine='NUMPY', mode=mode)
                for channel in range(4):
                    np.testing.assert_allclose(a[channel][0], b[channel][0])

    def test_zero_query_points(self):
        for mode in ('RANGE', 'NEAREST_N'):
            result = self.query([], [[0, 0, 0], [1, 0, 0]], [[0, 1]],
                                engine='AUTO', mode=mode)
            self.assertTrue(all(len(channel) == 0 for channel in result))

class TestPointwiseControls(unittest.TestCase):
    VERTS = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 2, 0],
             [0, 4, 0], [2, 4, 0]]
    EDGES = [[0, 1], [2, 3], [4, 5]]
    POINTS = [[1, 0.5, 0], [1, 1.4, 0], [1, 3.1, 0]]

    def query(self, mode, engine='NUMPY', **kwargs):
        return mod.distance_to_edges(self.POINTS, self.VERTS,
                                     self.EDGES, mode=mode, engine=engine,
                                     **kwargs)

    def test_different_radii_per_point(self):
        distances, coords, indices, factors = self.query(
            'RANGE', max_distance=[0.6, 1.5, 0.0])
        self.assertEqual([len(row) for row in distances], [1, 2, 0])
        np.testing.assert_array_equal(indices[0], [0])
        np.testing.assert_array_equal(indices[1], [1, 0])
        self.assertEqual(coords[2].shape, (0, 3))
        self.assertEqual(len(factors[2]), 0)

    def test_different_counts_per_point_including_zero(self):
        distances, coords, indices, factors = self.query(
            'NEAREST_N', count=[1, 2.9, 0])
        self.assertEqual([len(row) for row in distances], [1, 2, 0])
        np.testing.assert_array_equal(indices[0], [0])
        np.testing.assert_array_equal(indices[1], [1, 0])
        self.assertEqual(coords[2].shape, (0, 3))
        self.assertEqual(len(factors[2]), 0)

    def test_repeat_cycle_short_at_point_level(self):
        expected = {'REPEAT': [1, 2, 2], 'CYCLE': [1, 2, 1], 'SHORT': [1, 2]}
        for match, counts in expected.items():
            d, _, _, _ = self.query('NEAREST_N', count=[1, 2],
                                     point_match=match)
            self.assertEqual([len(x) for x in d], counts)
        d, _, _, _ = self.query('NEAREST_N', count=1,
                                 point_match='SHORT')
        self.assertEqual([len(x) for x in d], [1, 1, 1])

    def test_per_point_control_uses_nesting_at_object_level(self):
        points = [self.POINTS[:2], self.POINTS[2:]]
        # A distinct Count list for each independent point set.
        control = [[1, 2], [0]]
        d, loc, idx, fac = mod.recursive_distance_to_edges(
            points, [self.VERTS], [self.EDGES], mode='NEAREST_N',
            count=control, engine='NUMPY')
        self.assertEqual([[len(x) for x in obj] for obj in d], [[1, 2], [0]])
        self.assertEqual(len(loc[1][0]), 0)
        self.assertEqual(len(idx[0][1]), 2)
        self.assertEqual(len(fac[1][0]), 0)

    def test_socket_data_typical_shape(self):
        points = [self.POINTS]
        control = [[0.6, 1.5, 0.0]]
        d, _, _, _ = mod.recursive_distance_to_edges(
            points, [self.VERTS], [self.EDGES], mode='RANGE',
            max_distance=control, engine='NUMPY')
        self.assertEqual([len(x) for x in d[0]], [1, 2, 0])

    def test_deep_broadcast_and_numpy_output(self):
        points = [[self.POINTS[:2], self.POINTS[2:]]]
        control = [[[1, 2], [0]]]
        d, _, _, _ = mod.recursive_distance_to_edges(
            points, [self.VERTS], [self.EDGES], mode='NEAREST_N',
            count=control, output_numpy=True, engine='NUMPY')
        self.assertEqual([len(x) for x in d[0][0]], [1, 2])
        self.assertEqual(len(d[0][1][0]), 0)
        self.assertIsInstance(d[0][0][0], np.ndarray)

    def test_inactive_input_is_not_validated(self):
        # Non-active controls do not affect the query.
        for mode, kwargs in [('NEAREST', {'count':-1}),
                             ('RANGE', {'count':-1, 'max_distance':1}),
                             ('NEAREST_N', {'max_distance':-1, 'count':1})]:
            result = self.query(mode, **kwargs)
            self.assertTrue(len(result[0]) > 0)

    def test_validation_of_active_values(self):
        for mode, control in [('RANGE', {'max_distance':[1,-1,2]}),
                              ('RANGE', {'max_distance':[1,float('nan')]}),
                              ('NEAREST_N', {'count':[1, -2]}),
                              ('NEAREST_N', {'count':[]})]:
            with self.assertRaises(ValueError):
                self.query(mode, **control)

    @unittest.skipUnless(mod.HAS_NUMBA, 'Numba is not installed')
    def test_numba_matches_numpy_with_per_point_controls(self):
        for mode, kw in [('RANGE', {'max_distance':[0.6, 1.0, 0.0]}),
                         ('NEAREST_N', {'count':[1, 2, 0]}),
                         ('NEAREST_N', {'count':[3, 0, 1]})]:
            a = self.query(mode, engine='NUMPY', **kw)
            b = self.query(mode, engine='NUMBA', **kw)
            for channel in range(4):
                for row in range(len(a[channel])):
                    np.testing.assert_allclose(a[channel][row], b[channel][row],
                                               atol=1e-12, rtol=1e-12,
                                               err_msg=f'{mode} ch={channel} row={row}')


if __name__ == '__main__':
    unittest.main()
