import numpy as np
import unittest

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl.helpers import basis_functions, find_spans, find_span_linear

class Issue4469Tests(SverchokTestCase):
    @unittest.skip("not ready yet, see discussion in issue #4469")
    @requires(geomdl)
    def test_4469(self):
        knotvector = [0.0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5]
        #knotvector = [-1.25, -1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1, 1.125, 1.5, 1.175, 2, 2.25]
        sv_basis = SvNurbsBasisFunctions(knotvector)
        t = 2.6
        ts = np.array([t])
        p = 5
        n_cpts = 9
        print("Sv:", [sv_basis.derivative(i, p, 0)(ts)[0] for i in range(n_cpts)])
        spans = find_spans(p, knotvector, n_cpts, [t], find_span_linear)
        print("Geomdl spans:", spans)
        print("G2", find_span_linear(p, knotvector, n_cpts, t))
        g_basis = basis_functions(p, knotvector, spans, [t])
        print("Geomdl:", g_basis[0])
