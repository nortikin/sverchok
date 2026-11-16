import numpy as np

from sverchok.utils.sv_mesh_utils import polygons_to_edges_np
from sverchok.utils.testing import SverchokTestCase


class PolygonsToEdgesTest(SverchokTestCase):
    def test_unique_edges_are_deduplicated_and_sorted(self):
        cases = (
            (
                "triangles",
                [[0, 1, 2], [2, 1, 3]],
                [[0, 1], [0, 2], [1, 2], [1, 3], [2, 3]],
            ),
            (
                "triangle and quad",
                [[0, 1, 2], [2, 1, 3, 4]],
                [[0, 1], [0, 2], [1, 2], [1, 3], [2, 4], [3, 4]],
            ),
        )

        for name, faces, expected in cases:
            with self.subTest(faces=name, output_numpy=False):
                self.assertEqual(
                    polygons_to_edges_np([faces], unique_edges=True, output_numpy=False),
                    [expected],
                )

            with self.subTest(faces=name, output_numpy=True):
                [edges] = polygons_to_edges_np([faces], unique_edges=True, output_numpy=True)
                self.assertIsInstance(edges, np.ndarray)
                self.assertEqual(edges.dtype, np.dtype(np.int32))
                np.testing.assert_array_equal(edges, expected)
