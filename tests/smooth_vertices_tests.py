# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later

from copy import deepcopy
from itertools import product
import unittest
from unittest.mock import patch

import bmesh
import numpy as np

from sverchok.core.socket_data import sv_set_socket
from sverchok.dependencies import numba
from sverchok.utils.mesh import smooth as smooth_module
from sverchok.utils.mesh.smooth import smooth_vertices
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.testing import SverchokTestCase


def bmesh_reference(vertices, edges, faces, *, mask=(1,), axes=(True, True, True),
                    clip=(False, False, False), clip_dist=0.0001, factor=0.5,
                    iterations=1, laplacian=False, border_factor=0.5,
                    preserve_volume=False):
    """Evaluate the original node's BMesh algorithm as an independent reference."""
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    try:
        mask = list(mask[:len(vertices)])
        if mask:
            mask.extend([mask[-1]] * (len(vertices) - len(mask)))
        selected = [vertex for vertex, enabled in zip(bm.verts, mask) if enabled]
        for _ in range(iterations):
            if laplacian:
                for face in bm.faces:
                    face.select = True
                bmesh.ops.smooth_laplacian_vert(
                    bm, verts=selected, lambda_factor=factor, lambda_border=border_factor,
                    use_x=axes[0], use_y=axes[1], use_z=axes[2],
                    preserve_volume=preserve_volume)
            else:
                bmesh.ops.smooth_vert(
                    bm, verts=selected, factor=factor, clip_dist=clip_dist,
                    mirror_clip_x=clip[0], mirror_clip_y=clip[1], mirror_clip_z=clip[2],
                    use_axis_x=axes[0], use_axis_y=axes[1], use_axis_z=axes[2])
        return pydata_from_bmesh(bm)
    finally:
        bm.free()


def closed_mesh():
    """An asymmetric closed octahedron with consistently oriented triangles."""
    vertices = [
        [0, 0, 2], [0, 0, -1.5], [2, 0, 0],
        [0, 1, 0], [-1, 0, 0], [0, -2, 0],
    ]
    faces = [
        [0, 2, 3], [0, 3, 4], [0, 4, 5], [0, 5, 2],
        [1, 3, 2], [1, 4, 3], [1, 5, 4], [1, 2, 5],
    ]
    return vertices, faces


class SmoothVerticesTests(SverchokTestCase):
    use_numba = False

    def smooth(self, vertices, edges=(), faces=(), **options):
        defaults = dict(
            mask=(1,), axes=(True, True, True), clip=(False, False, False),
            clip_dist=0.0001, factor=0.5, iterations=1,
            use_numba=self.use_numba)
        defaults.update(options)
        return smooth_vertices(vertices, edges, faces, **defaults)

    def assert_mesh_equal(self, actual, expected, tolerance=2e-5):
        np.testing.assert_allclose(
            np.asarray(actual[0]).reshape(-1, 3),
            np.asarray(expected[0]).reshape(-1, 3), atol=tolerance, rtol=tolerance)
        np.testing.assert_array_equal(
            np.asarray(actual[1]).reshape(-1, 2), np.asarray(expected[1]).reshape(-1, 2))
        self.assertEqual(actual[2], expected[2])

    def test_classical_averages_neighbors_and_keeps_isolated_vertices(self):
        vertices = [[0, 0, 0], [2, 2, 0], [4, 0, 2], [10, 10, 10]]
        result, _, _ = self.smooth(vertices, [[0, 1], [1, 2]])
        np.testing.assert_allclose(
            result, [[1, 1, 0], [2, 1, 0.5], [3, 1, 1], [10, 10, 10]])

    def test_iterations_use_simultaneous_updates(self):
        result, _, _ = self.smooth(
            [[0, 0, 0], [2, 0, 0], [8, 0, 0]], [[0, 1], [1, 2]],
            factor=1, iterations=2)
        np.testing.assert_allclose(result, [[4, 0, 0], [2, 0, 0], [4, 0, 0]])

    def test_short_mask_repeats_last_value_and_respects_axes(self):
        vertices = [[0, 0, 0], [2, 2, 0], [4, 0, 2]]
        result, _, _ = self.smooth(
            vertices, [[0, 1], [1, 2]], mask=(0, 1), axes=(False, True, True))
        np.testing.assert_allclose(result, [[0, 0, 0], [2, 1, 0.5], [4, 1, 1]])

    def test_mirror_clip_is_inclusive_and_only_affects_connected_enabled_axes(self):
        vertices = [[0.1, 0.1, 0], [2, 2, 0], [0.1, 0.1, 0]]
        result, _, _ = self.smooth(
            vertices, [[0, 1]], factor=0, clip=(True, True, False), clip_dist=0.1,
            axes=(True, False, True))
        np.testing.assert_allclose(
            result, [[0, 0.1, 0], [2, 2, 0], [0.1, 0.1, 0]])

    def test_face_edges_are_included_and_duplicate_edges_do_not_change_weights(self):
        vertices = [[0, 0, 0], [2, 0, 0], [0, 2, 0]]
        faces = [[0, 1, 2]]
        expected = ([[1, 1, 0], [0, 1, 0], [1, 0, 0]],
                    [[2, 0], [0, 1], [1, 2]], faces)
        for edges in ([], [[1, 0], [0, 1], [2, 1]]):
            with self.subTest(edges=edges):
                self.assert_mesh_equal(self.smooth(vertices, edges, faces, factor=1), expected)

    def test_mixed_polygons_keep_winding_and_normalize_negative_indices(self):
        vertices = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 2, 0], [3, 2, 1]]
        faces = [[0, 1, 2], [2, 1, 3, -1]]
        result = self.smooth(vertices, faces=faces, iterations=0)
        self.assertEqual(result[2], [[0, 1, 2], [2, 1, 3, 4]])
        self.assertEqual(result[1], [[2, 0], [0, 1], [1, 2], [4, 2], [1, 3], [3, 4]])

    def test_noop_options_preserve_coordinates(self):
        vertices = [[0, 0, 0], [2, 2, 1], [4, 0, 0]]
        for options in (dict(iterations=0), dict(factor=0),
                        dict(mask=()), dict(mask=(0,)),
                        dict(axes=(False, False, False))):
            with self.subTest(options=options):
                result, _, _ = self.smooth(vertices, [[0, 1], [1, 2]], **options)
                np.testing.assert_array_equal(result, vertices)

    def test_output_formats_are_independent_and_support_array_inputs(self):
        vertices = np.array([[0, 0, 0], [2, 0, 0], [0, 2, 0], [1, 2, 1]], dtype=float)
        faces = [[0, 1, 2], [2, 1, 3, 0]]
        for numpy_vertices, numpy_edges in product((False, True), repeat=2):
            with self.subTest(vertices=numpy_vertices, edges=numpy_edges):
                result = self.smooth(
                    vertices, np.empty((0, 2), dtype=int), faces,
                    numpy_vertices=numpy_vertices, numpy_edges=numpy_edges)
                self.assertEqual(isinstance(result[0], np.ndarray), numpy_vertices)
                self.assertEqual(isinstance(result[1], np.ndarray), numpy_edges)
                self.assertEqual(result[2], faces)
                self.assertIsInstance(result[2], list)
                if numpy_vertices:
                    self.assertEqual(result[0].shape, (4, 3))
                    self.assertTrue(np.issubdtype(result[0].dtype, np.floating))
                if numpy_edges:
                    self.assertEqual(result[1].shape[1], 2)
                    self.assertTrue(np.issubdtype(result[1].dtype, np.integer))
                chained = self.smooth(*result)
                self.assert_mesh_equal(chained, self.smooth(
                    result[0].tolist() if numpy_vertices else result[0],
                    result[1].tolist() if numpy_edges else result[1], result[2]))

    def test_empty_numpy_outputs_have_mesh_shapes(self):
        vertices, edges, faces = self.smooth(
            [], numpy_vertices=True, numpy_edges=True)
        self.assertEqual(vertices.shape, (0, 3))
        self.assertEqual(edges.shape, (0, 2))
        self.assertEqual(faces, [])

    def test_inputs_are_not_modified_or_aliased(self):
        vertices = np.array([[0, 0, 0], [2, 1, 0], [0, 2, 1]], dtype=np.float32)
        edges = np.array([[0, 1], [1, 2]], dtype=np.int32)
        faces = [[0, 1, 2]]
        before = deepcopy((vertices, edges, faces))
        result = self.smooth(
            vertices, edges, faces, numpy_vertices=True, numpy_edges=True)
        np.testing.assert_array_equal(vertices, before[0])
        np.testing.assert_array_equal(edges, before[1])
        self.assertEqual(faces, before[2])
        self.assertFalse(np.shares_memory(result[0], vertices))
        self.assertFalse(np.shares_memory(result[1], edges))
        result[2][0][0] = 2
        self.assertEqual(faces, before[2])

    def test_disconnected_vertex_output_skips_smoothing(self):
        with patch.object(smooth_module, "_smooth_numpy") as numpy_kernel, patch.object(
                smooth_module, "_smooth_vertices_numba") as numba_kernel:
            vertices, edges, faces = self.smooth(
                [[0, 0, 0], [2, 0, 0]], [[0, 1]], output_vertices=False,
                numpy_edges=True)
        self.assertIsNone(vertices)
        np.testing.assert_array_equal(edges, [[0, 1]])
        self.assertEqual(faces, [])
        numpy_kernel.assert_not_called()
        numba_kernel.assert_not_called()

    def test_classical_matches_original_bmesh(self):
        vertices = [[0, 0, 0.2], [2, 0, 1], [0, 2, 0], [2, 2, 1], [3, 1, 0]]
        edges = [[0, 4], [4, 3]]
        faces = [[0, 1, 2], [2, 1, 3, 4]]
        options = dict(iterations=4, mask=(0, 1), axes=(True, False, True), factor=0.3)
        self.assert_mesh_equal(
            self.smooth(vertices, edges, faces, **options),
            bmesh_reference(vertices, edges, faces, **options))

    def test_laplacian_closed_mesh_matches_bmesh_with_masks_axes_and_volume(self):
        vertices, faces = closed_mesh()
        for preserve, mask, axes in product(
                (False, True), ((1,), (1, 0, 1, 1, 0, 1)),
                ((True, True, True), (True, False, True))):
            options = dict(laplacian=True, iterations=2, preserve_volume=preserve,
                           mask=mask, axes=axes, factor=0.5)
            with self.subTest(preserve=preserve, mask=mask, axes=axes):
                self.assert_mesh_equal(
                    self.smooth(vertices, faces=faces, **options),
                    bmesh_reference(vertices, [], faces, **options))

    def test_laplacian_preserves_closed_mesh_volume(self):
        vertices, faces = closed_mesh()
        triangles = np.asarray(faces, dtype=int)

        def volume(coords):
            coords = np.asarray(coords, dtype=float)[triangles]
            return abs(np.sum(coords[:, 0] * np.cross(coords[:, 1], coords[:, 2])) / 6)

        smoothed, _, _ = self.smooth(
            vertices, faces=faces, laplacian=True, iterations=3, preserve_volume=True)
        self.assertAlmostEqual(volume(smoothed) / volume(vertices), 1.0, places=5)
        uncorrected, _, _ = self.smooth(
            vertices, faces=faces, laplacian=True, iterations=3, preserve_volume=False)
        self.assertGreater(abs(volume(uncorrected) - volume(vertices)), 1e-3)

    def test_laplacian_hexagons_match_bmesh_with_border_factor(self):
        height = np.sqrt(3) / 2
        vertices = [
            [1, 0, 0.2], [0.5, height, 0.1], [-0.5, height, 0], [-1, 0, 0],
            [-0.5, -height, 0], [0.5, -height, 0.1], [2, 0, 0.3],
            [2.5, height, 0.2], [2, 2*height, 0.1], [1, 2*height, 0],
        ]
        faces = [[0, 1, 2, 3, 4, 5], [1, 0, 6, 7, 8, 9]]
        results = []
        for border_factor in (0.1, 0.35):
            options = dict(laplacian=True, preserve_volume=False,
                           border_factor=border_factor, iterations=2)
            with self.subTest(border_factor=border_factor):
                result = self.smooth(vertices, faces=faces, **options)
                self.assert_mesh_equal(
                    result, bmesh_reference(vertices, [], faces, **options))
                results.append(result[0])
        self.assertGreater(np.max(np.abs(np.asarray(results[0]) - results[1])), 0.01)

    def test_laplacian_wire_and_degenerate_geometry_remain_finite(self):
        vertices = [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]
        for faces in ([], [[0, 1, 2]]):
            with self.subTest(faces=faces):
                result, _, _ = self.smooth(
                    vertices, [[2, 3]], faces, laplacian=True, preserve_volume=False)
                np.testing.assert_array_equal(result, vertices)

    def test_requesting_numba_without_dependency_uses_numpy(self):
        with patch.object(smooth_module, "numba", None), patch.object(
                smooth_module, "_smooth_numpy", wraps=smooth_module._smooth_numpy) as kernel:
            result, _, _ = self.smooth([[0, 0, 0], [2, 0, 0]], [[0, 1]], use_numba=True)
        kernel.assert_called_once()
        np.testing.assert_allclose(result, [[1, 0, 0], [1, 0, 0]])


@unittest.skipIf(numba is None, "Numba is not installed")
class NumbaSmoothVerticesTests(SmoothVerticesTests):
    use_numba = True


class SmoothVerticesNodeTests(SverchokTestCase):
    def test_node_handles_multiple_meshes_and_independent_numpy_outputs(self):
        vertices = [[0, 0, 0], [2, 0, 0], [0, 2, 0]]
        second = [[x + 5, y, z] for x, y, z in vertices]
        faces = [[0, 1, 2]]
        with self.temporary_node_tree("SmoothVerticesUnitTests") as tree:
            source = tree.nodes.new("SvSmoothNode")
            for use_numba, numpy_vertices, numpy_edges, laplacian in product(
                    (False, True), repeat=4):
                with self.subTest(numba=use_numba, vertices=numpy_vertices,
                                  edges=numpy_edges, laplacian=laplacian):
                    node = tree.nodes.new("SvSmoothNode")
                    self.assertTrue(node.use_numba)
                    self.assertFalse(node.output_numpy_vertices)
                    self.assertFalse(node.output_numpy_edges)
                    node.use_numba = use_numba
                    node.output_numpy_vertices = numpy_vertices
                    node.output_numpy_edges = numpy_edges
                    node.laplacian = laplacian
                    node.preserve_volume = False
                    sink = tree.nodes.new("SvSmoothNode")
                    for name in ("Vertices", "Edges", "Faces"):
                        tree.links.new(source.outputs[name], node.inputs[name])
                        tree.links.new(node.outputs[name], sink.inputs[name])
                    for name, data in zip(
                            ("Vertices", "Edges", "Faces"),
                            ([vertices, second], [[]], [faces])):
                        sv_set_socket(node.inputs[name], data)
                    node.process()
                    output_vertices = node.outputs["Vertices"].sv_get(deepcopy=False)
                    output_edges = node.outputs["Edges"].sv_get(deepcopy=False)
                    output_faces = node.outputs["Faces"].sv_get(deepcopy=False)
                    self.assertEqual(len(output_vertices), 2)
                    for i, coords in enumerate((vertices, second)):
                        expected = smooth_vertices(
                            coords, [], faces, (1,), (True, True, True),
                            (False, False, False), 0.0001, 0.5, 1,
                            laplacian=laplacian, preserve_volume=False)
                        self.assertEqual(isinstance(output_vertices[i], np.ndarray), numpy_vertices)
                        self.assertEqual(isinstance(output_edges[i], np.ndarray), numpy_edges)
                        self.assertEqual(output_faces[i], faces)
                        np.testing.assert_allclose(
                            output_vertices[i], expected[0], atol=2e-5, rtol=2e-5)
                        np.testing.assert_array_equal(output_edges[i], expected[1])
                    tree.nodes.remove(sink)
                    tree.nodes.remove(node)
