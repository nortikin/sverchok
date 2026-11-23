# SPDX-License-Identifier: GPL-3.0-or-later
"""CI regressions for the portable Merge by Distance node.

Discovered by Sverchok's ``run_tests.sh`` (tests/*_tests.py) in Blender.
Also runnable as ``python3 tests/merge_by_distance_tests.py`` without Blender.
The reference BMesh backend is intentionally not used as a geometry oracle:
GRID keeps independent grouping and ordering semantics.
"""

from pathlib import Path
import sys
import unittest

import numpy as np

try:
    import bpy
except ImportError:
    bpy = None

if bpy is not None:
    from sverchok.utils.mesh.sv_mesh_core.merge import merge_by_distance
    from sverchok.utils.mesh.sv_mesh_core.nesting import map_mesh_tree
    from sverchok.utils.mesh.sv_mesh_core.optional import has_scipy, numba
else:
    # Standalone execution outside Blender; no Sverchok add-on import.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'utils' / 'mesh'))
    from sv_mesh_core.merge import merge_by_distance
    from sv_mesh_core.nesting import map_mesh_tree
    from sv_mesh_core.optional import has_scipy, numba


QUAD = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
WITH_DOUBLE = QUAD + [[0, 0, 0]]


def _normalized(out):
    """Convert the six output types to comparable Python structures."""
    return tuple(item.to_list() if hasattr(item, 'to_list') else
                 item.tolist() if isinstance(item, np.ndarray) else item
                 for item in out)


def _engines():
    result = [('GRID_PY', False)]
    if has_scipy():
        result.append(('GRID_SCIPY', False))
    if numba is not None:
        result.append(('AUTO', True))
    return result


def _merge(vertices, elements, distance=0.001, **kwargs):
    return merge_by_distance(vertices, elements, distance, backend='GRID_PY',
                             use_numba=False, **kwargs)


class MergePortableTests(unittest.TestCase):

    def test_weld_and_duplicate_coordinates(self):
        vertices, edges, faces, data, doubles, mask = _merge(
            WITH_DOUBLE, [[0, 1, 2, 3], [4, 1, 2, 3]],
            face_data=['first', 'second'])
        self.assertEqual(vertices, QUAD)
        self.assertEqual(faces, [[0, 1, 2, 3]])
        self.assertEqual(data, ['first'])
        self.assertEqual(doubles, [[0.0, 0.0, 0.0]])
        self.assertEqual(len(edges), 4)
        self.assertEqual(mask, [])

    def test_face_rotation_and_reverse_are_duplicates(self):
        out = _merge(QUAD, [[0, 1, 2, 3], [3, 2, 1, 0], [2, 3, 0, 1]],
                     distance=0, face_data=[11, 22, 33])
        self.assertEqual(out[2], [[0, 1, 2, 3]])
        self.assertEqual(out[3], [11])

    def test_quad_and_two_triangles_are_not_exact_duplicates(self):
        # A geometric overlay is not the responsibility of vertex welding.
        out = _merge(QUAD, [[0, 1, 2, 3], [0, 1, 2], [0, 2, 3]], distance=0)
        self.assertEqual(len(out[2]), 3)

    def test_mask_prevents_merging_unselected_vertices(self):
        out = _merge(WITH_DOUBLE, [[0, 1, 2, 3], [4, 1, 2, 3]],
                     mask=[1, 1, 1, 1, 0], face_data=['a', 'b'])
        self.assertEqual(len(out[0]), 5)
        self.assertEqual(len(out[2]), 2)
        self.assertEqual(out[3], ['a', 'b'])
        self.assertEqual(out[4], [])
        self.assertEqual(out[5], [1, 1, 1, 1, 0])

    def test_short_mask_repeats_last_selection(self):
        # A short mask is vertex-level data, not a list of meshes.
        out = _merge(WITH_DOUBLE, [], mask=[0, 1])
        self.assertEqual(len(out[0]), 5)
        self.assertEqual(out[5], [False, True, True, True, True])

    def test_wire_edges_only(self):
        out = _merge(WITH_DOUBLE, [[0, 1], [4, 1], [2, 3], [0, 4]])
        self.assertEqual(out[1], [[0, 1], [2, 3]])
        self.assertEqual(out[2], [])
        self.assertEqual(out[3], [])

    def test_degenerate_faces_and_nonmanifold_are_supported(self):
        verts = [[0, 0, 0], [1, 0, 0], [0, 1, 0],
                 [0, -1, 0], [0, 0, 1], [0, 0, 0]]
        faces = [[0, 1, 2], [1, 0, 3], [0, 1, 4], [5, 1, 2],
                 [0, 1, 1, 2], [0, 1, 0]]
        out = _merge(verts, faces, face_data=list(range(len(faces))))
        out_edges = {tuple(sorted(edge)) for edge in out[1]}
        self.assertEqual(len(out_edges), len(out[1]))
        for face in out[2]:
            self.assertGreaterEqual(len(face), 3)
            self.assertEqual(len(face), len(set(face)))
            for a, b in zip(face, face[1:] + face[:1]):
                self.assertIn(tuple(sorted((a, b))), out_edges)
        self.assertEqual(len(out[3]), len(out[2]))

    def test_ngon_is_not_triangulated(self):
        vertices = [[np.cos(i * np.pi/3), np.sin(i * np.pi/3), 0] for i in range(6)]
        out = _merge(vertices, [[0, 1, 2, 3, 4, 5]], distance=0)
        self.assertEqual([len(face) for face in out[2]], [6])

    def test_numpy_types_and_list_values(self):
        args = (WITH_DOUBLE, [[0, 1, 2, 3], [4, 1, 2, 3]])
        listed = _merge(*args, mask=[1], face_data=[100, 200])
        arrays = _merge(*args, mask=[1], face_data=[100, 200], output_numpy=True)
        self.assertIsInstance(arrays[0], np.ndarray)
        self.assertIsInstance(arrays[1], np.ndarray)
        self.assertIsInstance(arrays[4], np.ndarray)
        self.assertIsInstance(arrays[5], np.ndarray)
        self.assertEqual(_normalized(arrays), _normalized(listed))

    def test_unlinked_outputs_do_not_change_other_outputs(self):
        vertices = WITH_DOUBLE
        faces = [[0, 1, 2, 3], [4, 1, 2, 3]]
        options = ('output_edges', 'output_polygons', 'output_face_data',
                   'output_doubles', 'output_mask')
        base = _normalized(_merge(vertices, faces, face_data=[1, 2], mask=[1],
                                  output_numpy=True))
        for output_index, name in enumerate(options, 1):
            with self.subTest(unlinked=name):
                result = _normalized(_merge(vertices, faces, face_data=[1, 2],
                                            mask=[1], output_numpy=True, **{name: False}))
                for i in range(6):
                    if i != output_index:
                        self.assertEqual(base[i], result[i], (name, i))

    def test_invalid_distance_and_indices_rejected(self):
        for distance in (-0.1, float('nan'), float('inf')):
            with self.subTest(distance=distance), self.assertRaises(ValueError):
                _merge(QUAD, [], distance=distance)
        with self.assertRaises(IndexError):
            _merge(QUAD, [[0, 1, 9]], distance=0)

    def test_inputs_unchanged(self):
        verts = np.asarray(WITH_DOUBLE, dtype=np.float32)
        faces = [[0, 1, 2, 3], [4, 1, 2, 3]]
        before = verts.copy()
        _merge(verts, faces)
        np.testing.assert_array_equal(verts, before)
        self.assertEqual(faces[1], [4, 1, 2, 3])

    def test_backends_same_six_outputs(self):
        cases = [
            (WITH_DOUBLE, [[0, 1, 2, 3], [4, 1, 2, 3]], 0.01),
            ([[0, 0, 0], [0.2, 0, 0], [0.22, 0, 0], [1, 0, 0]],
             [[0, 1], [2, 3]], 0.15),
        ]
        for vertices, poly_edge, distance in cases:
            expected = None
            for backend, use_numba in _engines():
                with self.subTest(backend=backend, distance=distance):
                    output = _normalized(merge_by_distance(
                        vertices, poly_edge, distance, output_numpy=True,
                        backend=backend, use_numba=use_numba))
                    if expected is None:
                        expected = output
                    self.assertEqual(output, expected)


class MeshNestingTests(unittest.TestCase):

    @staticmethod
    def evaluate(vertices, elements, face_data, mask, distance):
        return _merge(vertices, elements, distance, face_data=face_data, mask=mask)

    def test_scalar_distance_and_unlinked_defaults_broadcast_short(self):
        two_meshes = [WITH_DOUBLE, QUAD]
        for matching in ('REPEAT', 'CYCLE', 'SHORT'):
            with self.subTest(matching=matching):
                result = map_mesh_tree(two_meshes, [], [], [], 0.01,
                                       self.evaluate, matching=matching)
                self.assertEqual(len(result[0]), 2)
                self.assertEqual([len(v) for v in result[0]], [4, 4])

    def test_recursive_groups_preserved(self):
        meshes = [[WITH_DOUBLE, QUAD], [WITH_DOUBLE]]
        result = map_mesh_tree(meshes, [], [], [], [[0.01, 0], [0.01]],
                               self.evaluate, matching='REPEAT')
        self.assertEqual([len(group) for group in result[0]], [2, 1])
        self.assertEqual([[len(mesh) for mesh in group] for group in result[0]],
                         [[4, 4], [4]])

    def test_list_matching_short_and_cycle(self):
        meshes = [QUAD, WITH_DOUBLE, QUAD]
        distances = [0, 0.01]
        short = map_mesh_tree(meshes, [], [], [], distances,
                              self.evaluate, matching='SHORT')
        cycle = map_mesh_tree(meshes, [], [], [], distances,
                              self.evaluate, matching='CYCLE')
        self.assertEqual(len(short[0]), 2)
        self.assertEqual(len(cycle[0]), 3)

    def test_empty_mesh_and_numpy_meshes(self):
        empty = np.empty((0, 3), np.float32)
        result = map_mesh_tree([empty, np.asarray(WITH_DOUBLE, np.float32)],
                               [], [], [], 0, self.evaluate, matching='REPEAT')
        self.assertEqual([len(v) for v in result[0]], [0, 4])


@unittest.skipUnless(bpy is not None, 'Blender-only registration smoke tests')
class MergeBlenderRegistrationTests(unittest.TestCase):

    def test_both_old_and_new_node_ids_load(self):
        from sverchok import old_nodes
        from sverchok.nodes.modifier_change.merge_by_distance_numpy import SvMergeByDistanceNumpyNode
        old_nodes.register_old('SvMergeByDistanceNode')
        tree = bpy.data.node_groups.new('Merge CI registration', 'SverchCustomTreeType')
        tree.sv_process = False
        try:
            expected_counts = (
                ('SvMergeByDistanceNode', 5, 6),
                ('SvMergeByDistanceNumpyNode', 8, 11),
            )
            for node_id, num_inputs, num_outputs in expected_counts:
                with self.subTest(node_id=node_id):
                    node = tree.nodes.new(node_id)
                    self.assertEqual(len(node.inputs), num_inputs)
                    self.assertEqual(len(node.outputs), num_outputs)
            node = next(n for n in tree.nodes if n.bl_idname == 'SvMergeByDistanceNumpyNode')
            self.assertEqual(node.mode, 'FAST')
            self.assertEqual(node.list_match, 'REPEAT')
            self.assertTrue(all(not getattr(node, key) for key in
                                ('numpy_vertices', 'numpy_edges', 'numpy_face_data',
                                 'numpy_doubles', 'numpy_mask')))
            self.assertIn('Weld', SvMergeByDistanceNumpyNode.__doc__)
            self.assertIn('Doubled Verts', SvMergeByDistanceNumpyNode.__doc__)
        finally:
            bpy.data.node_groups.remove(tree)


if __name__ == '__main__':
    unittest.main()
