
import unittest

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.utils.dictionary import SvApproxDict
from sverchok.utils.curve.nurbs_algorithms import KnotvectorDict

class ApproxDictTests(SverchokTestCase):
    
    def test_repr(self):
        d = SvApproxDict([(1.0, "A"), (2.0, "B")])
        s = repr(d)
        self.assertEquals(s, "{1.0: A, 2.0: B}")

    def test_dict_1(self):
        d = SvApproxDict([(1.0, "A"), (2.0, "B")], precision=1)
        d[2.01] = "C"

        self.assertEquals(repr(d), "{1.0: A, 2.0: C}")

        self.assertEquals(d[1.0], "A")
        self.assertEquals(d[1.01], "A")
        self.assertEquals(d[0.99], "A")

        self.assertEquals(d[2.0], "C")
        self.assertEquals(d[2.01], "C")
        self.assertEquals(d[1.99], "C")

        d[2.5] = "K"

        self.assertEquals(repr(d), "{1.0: A, 2.0: C, 2.5: K}")

        self.assertEquals(d[2.5], "K")
        self.assertEquals(d[2.51], "K")
        self.assertEquals(d[2.49], "K")

        d[1.5] = "H"

        self.assertEquals(repr(d), "{1.0: A, 1.5: H, 2.0: C, 2.5: K}")

        self.assertEquals(d[1.5], "H")
        self.assertEquals(d[1.51], "H")
        self.assertEquals(d[1.49], "H")

class KnotvectorDictTests(SverchokTestCase):
    def test_dict_1(self):
        d = KnotvectorDict(accuracy=3)

        curve1_kv = [0, 0.499, 0.501, 1]
        for k in curve1_kv:
            d.update(1, k, 1)

        curve2_kv = [0, 0.5, 1]
        for k in curve2_kv:
            d.update(2, k, 1)

        expected_items = [(0, 1), (0.499, 1), (0.5, 1), (0.501, 1), (1, 1)]
        self.assertEquals(d.items(), expected_items)

    def test_dict_2(self):
        d = KnotvectorDict(accuracy=3)

        curve1_kv = [(0, 4), (0.499, 3), (0.501, 3), (1, 4)]
        for k, m in curve1_kv:
            d.update(1, k, m)

        curve2_kv = [(0, 4), (0.5, 3), (1, 4)]
        for k, m in curve2_kv:
            d.update(2, k, m)

        expected_items = [(0, 4), (0.499, 3), (0.5, 3), (0.501, 3), (1, 4)]
        self.assertEquals(d.items(), expected_items)

    def test_dict_3(self):
        d = KnotvectorDict(accuracy=2)

        curve1_kv = [(0,4), (0.499, 3), (0.501, 3), (1, 4)]
        for k, m in curve1_kv:
            d.update(1, k, m)

        expected_items = [(0, 4), (0.499, 3), (0.501, 3), (1, 4)]
        self.assertEquals(d.items(), expected_items)

        curve2_kv = [(0,4), (0.5, 3), (1, 4)]
        for k, m in curve2_kv:
            d.update(2, k, m)

        expected_items = [(0, 4), (0.5, 3), (0.501, 3), (1, 4)]
        self.assertEquals(d.items(), expected_items)

