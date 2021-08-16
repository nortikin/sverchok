
import unittest

from sverchok.utils.testing import *
from sverchok.utils.math import *

class MathTests(SverchokTestCase):
    def test_distribute_int_1(self):
        n = 10
        sizes = [5.0, 5.0]
        counts = distribute_int(n, sizes)
        expected_counts = [5, 5]
        self.assertEquals(counts, expected_counts)

    def test_distribute_int_2(self):
        n = 10
        sizes = [3.0, 1.0, 2.0]
        counts = distribute_int(n, sizes)
        expected_counts = [6, 1, 3]
        self.assertEquals(counts, expected_counts)

    def test_distribute_int_3(self):
        n = 10
        sizes = [3.0, 1.0, 0.0]
        counts = distribute_int(n, sizes)
        expected_counts = [8, 2, 0]
        self.assertEquals(counts, expected_counts)

    @unittest.skip
    def test_distribute_int_3(self):
        n = 1
        sizes = [5.0, 5.0]
        counts = distribute_int(n, sizes)
        expected_counts = [0, 1]
        self.assertEquals(counts, expected_counts)

