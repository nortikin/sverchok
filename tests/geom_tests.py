
import unittest
from mathutils import Vector

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.utils.geom import *

class GeometryTests(SverchokTestCase):

    def test_center_trivial(self):
        input = [(0, 0, 0)]
        output = center(input)
        expected_output = input[0]
        self.assertEquals(output, expected_output)

    def test_center_quad(self):
        inputs = [(-1, 0, 0), (0, -1, 0), (0, 1, 0), (1, 0, 0)]
        output = center(inputs)
        expected_output = (0, 0, 0)
        self.assertEquals(output, expected_output)

    def test_normal_quad(self):
        inputs = [(-1, 0, 0), (0, -1, 0), (1, 0, 0), (0, 1, 0)]
        output = calc_normal(inputs)
        expected_output = Vector((0, 0, 1))
        self.assertEquals(output, expected_output)

