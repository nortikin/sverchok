import numpy as np

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.mesh.inset_faces import inset_special_np


class InsetFacesTests(SverchokTestCase):
    def test_quad_fans(self):
        vertices = [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0],
                    [3, 0, 0], [5, 0, 0], [5, 2, 0], [3, 2, 0]]
        # Keep each polygon as one object for the variable-polygon path.
        faces = np.empty(2, dtype=object)
        faces[:] = [[0, 1, 2, 3], [4, 5, 6, 7]]
        triangles = [[0, 1, 8], [1, 2, 8], [2, 3, 8], [3, 0, 8],
                     [4, 5, 9], [5, 6, 9], [6, 7, 9], [7, 4, 9]]
        for distances, centers in [([0], [[1, 1, 0], [4, 1, 0]]),
                                   ([0, 0], [[1, 1, 0], [4, 1, 0]]),
                                   ([0, 2], [[1, 1, 0], [4, 1, 2]]),
                                   ([1, -2], [[1, 1, 1], [4, 1, -2]])]:
            for metadata in [False, True]:
                with self.subTest(distances=distances, metadata=metadata):
                    result = inset_special_np(
                        vertices, faces, [0], distances, [False], [True], [], [],
                        zero_mode='FAN', offset_mode='CENTER',
                        output_old_face_id=metadata, output_old_v_id=metadata,
                        output_pols_groups=metadata, output_new_verts_mask=metadata)
                    self.assert_sverchok_data_equal(result[0], vertices + centers)
                    self.assertEqual(result[1], triangles)
                    self.assertEqual(result[2], [])
                    self.assertEqual(result[3], [])
                    self.assertEqual(result[4], list(range(8)) + [0, 4] if metadata else [])
                    self.assertEqual(result[5], [[0] * 4, [1] * 4] if metadata else [])
                    self.assertEqual(result[6], [1] * 8 if metadata else [])
                    self.assertEqual(result[7], [0] * 8 + [1, 1] if metadata else [])

    def test_single_quad_fan_zero_distance(self):
        vertices = [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]]
        faces = np.empty(1, dtype=object)
        faces[:] = [[0, 1, 2, 3]]
        result = inset_special_np(
            vertices, faces, [0], [0], [False], [True], [], [],
            zero_mode='FAN', offset_mode='CENTER')
        self.assert_sverchok_data_equal(result[0], vertices + [[1, 1, 0]])
        self.assertEqual(result[1], [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]])
        self.assertEqual(result[2:], ([], [], [], [], [], []))
