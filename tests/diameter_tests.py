
from math import sqrt
from mathutils import Vector

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.utils.geom import diameter

class DiameterTests(SverchokTestCase):
    def test_diameter_1(self):
        p1 = (0, 0, 0)
        p2 = (0, 1, 0)
        diam = diameter([p1, p2], None)
        expected = 1.0
        self.assert_sverchok_data_equal(diam, expected, precision=8)

    def test_diameter_2(self):
        p1 = (0, 0, 0)
        p2 = (0, 1, 0)
        p3 = (1, 0, 0)
        diam = diameter([p1, p2, p3], None)
        expected = sqrt(2)
        self.assert_sverchok_data_equal(diam, expected, precision=8)

    def test_diameter_3(self):
        p1 = (0, 0, 0)
        p2 = (0, 1, 0)
        p3 = (1, 0, 0)
        direction = (1, 0, 0)
        diam = diameter([p1, p2, p3], direction)
        expected = 1
        self.assert_sverchok_data_equal(diam, expected, precision=8)

