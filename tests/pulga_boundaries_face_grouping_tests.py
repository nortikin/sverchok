"""Pulga Boundaries: Solid Face socket grouping semantics (no FreeCAD required)."""
import unittest
from unittest.mock import Mock
from sverchok.nodes.pulga_physics.pulga_boundaries_force import _solid_face_group_boundaries


class _FakeFace:
    def tessellate(self, precision):
        return [], []

    def distToShape(self, shape):
        return None


class SolidFaceGroupingTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c = _FakeFace(), _FakeFace(), _FakeFace()
        self.compound = Mock(return_value='compound')

    def test_flat_list_creates_separate_forces(self):
        groups = _solid_face_group_boundaries([self.a, self.b], self.compound)
        self.assertEqual(groups, [self.a, self.b])
        self.compound.assert_not_called()

    def test_nested_list_creates_one_compound(self):
        groups = _solid_face_group_boundaries([[self.a, self.b]], self.compound)
        self.assertEqual(groups, ['compound'])
        self.compound.assert_called_once_with([self.a, self.b])

    def test_two_groups_make_two_forces(self):
        groups = _solid_face_group_boundaries([[self.a, self.b], [self.c]], self.compound)
        self.assertEqual(groups, ['compound', self.c])
        self.compound.assert_called_once_with([self.a, self.b])

    def test_mixed_flat_and_nested(self):
        groups = _solid_face_group_boundaries([self.a, [self.b, self.c]], self.compound)
        self.assertEqual(groups, [self.a, 'compound'])
        self.compound.assert_called_once_with([self.b, self.c])

    def test_face_wrapper_is_unwrapped_only_inside_compound(self):
        wrapper = type('Wrapper', (), {'face': self.b})()
        groups = _solid_face_group_boundaries([[self.a, wrapper]], self.compound)
        self.assertEqual(groups, ['compound'])
        self.compound.assert_called_once_with([self.a, self.b])

    def test_single_face_and_empty_group(self):
        self.assertEqual(_solid_face_group_boundaries(self.a, self.compound), [self.a])
        with self.assertRaises(ValueError):
            _solid_face_group_boundaries([[]], self.compound)
        with self.assertRaises(ValueError):
            _solid_face_group_boundaries([], self.compound)


if __name__ == '__main__':
    unittest.main()
