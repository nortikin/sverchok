
from sverchok.utils.testing import *
from sverchok.nodes.generator.ngon import make_verts

class NGonTests(SverchokTestCase):
    def test_ngon_verts_1(self):
        verts = make_verts(4, 1, 0, 0, 0, 1)
        expected_verts = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)]
        self.assert_sverchok_data_equal(verts, expected_verts, precision=8)

    def test_ngon_verts_2(self):
        verts = make_verts(4, 1, 0, 0, 0, 2)
        q = 0.5
        expected_verts = [(1, 0, 0), (q, q, 0),
                          (0, 1, 0), (-q, q, 0),
                          (-1, 0, 0), (-q, -q, 0),
                          (0, -1, 0), (q, -q,0)]
        self.assert_sverchok_data_equal(verts, expected_verts, precision=8)

