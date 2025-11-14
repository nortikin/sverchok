
from sverchok.utils.testing import *
from sverchok.utils.dictionary import SvApproxDict
from sverchok.utils.curve.nurbs_algorithms import KnotvectorDict


class ApproxDictTests(SverchokTestCase):
    
    def test_repr(self):
        d = SvApproxDict([(1.0, "A"), (2.0, "B")])
        s = repr(d)
        self.assertEqual(s, "{1.0: A, 2.0: B}")

    def test_dict_1(self):
        d = SvApproxDict([(1.0, "A"), (2.0, "B")], precision=1)
        d[2.01] = "C"

        self.assertEqual(repr(d), "{1.0: A, 2.0: C}")

        self.assertEqual(d[1.0], "A")
        self.assertEqual(d[1.01], "A")
        self.assertEqual(d[0.99], "A")

        self.assertEqual(d[2.0], "C")
        self.assertEqual(d[2.01], "C")
        self.assertEqual(d[1.99], "C")

        d[2.5] = "K"

        self.assertEqual(repr(d), "{1.0: A, 2.0: C, 2.5: K}")

        self.assertEqual(d[2.5], "K")
        self.assertEqual(d[2.51], "K")
        self.assertEqual(d[2.49], "K")

        d[1.5] = "H"

        self.assertEqual(repr(d), "{1.0: A, 1.5: H, 2.0: C, 2.5: K}")

        self.assertEqual(d[1.5], "H")
        self.assertEqual(d[1.51], "H")
        self.assertEqual(d[1.49], "H")

class KnotvectorDictTests(SverchokTestCase):
    def test_dict_1(self):
        d = KnotvectorDict(tolerance=1e-3)

        curve1_kv = [0, 0.499, 0.501, 1]
        for k in curve1_kv:
            d.put(k, 1)

        curve2_kv = [0, 0.5, 1]
        for k in curve2_kv:
            d.put(k, 1)
        d.calc_averages()

        expected_items = [(0, 1), (0.4995, 1), (0.501, 1), (1, 1)]
        self.assert_sverchok_data_equal(list(d.items()), expected_items, precision=6)

    def test_dict_2(self):
        d = KnotvectorDict(tolerance=1e-3)

        curve1_kv = [(0, 4), (0.499, 3), (0.501, 3), (1, 4)]
        for k, m in curve1_kv:
            d.put(k, m)

        curve2_kv = [(0, 4), (0.5, 3), (1, 4)]
        for k, m in curve2_kv:
            d.put(k, m)
        d.calc_averages()

        expected_items = [(0.0, 4), (0.4995, 3), (0.501, 3), (1.0, 4)]
        self.assert_sverchok_data_equal(list(d.items()), expected_items, precision=6)

    def test_dict_3(self):
        d = KnotvectorDict(tolerance=1e-2)

        curve1_kv = [(0,4), (0.499, 3), (0.501, 3), (1, 4)]
        for k, m in curve1_kv:
            d.put(k, m)
        d.calc_averages()

        expected_items = [(0.0, 4), (0.5, 3), (1.0, 4)]
        self.assert_sverchok_data_equal(list(d.items()), expected_items, precision=6)

        curve2_kv = [(0,4), (0.5, 3), (1, 4)]
        for k, m in curve2_kv:
            d.put(k, m)
        d.calc_averages()

        expected_items = [(0.0, 4), (0.5, 3), (1.0, 4)]
        self.assert_sverchok_data_equal(list(d.items()), expected_items, precision=6)

