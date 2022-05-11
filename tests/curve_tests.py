import numpy as np
import unittest

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.curve.core import *

class TaylorTests(SverchokTestCase):
    def test_square_1(self):
        coeffs = np.array([[4,0,0], [3,0,0], [2,0,0], [1,0,0]], dtype=np.float64)
        curve = SvTaylorCurve.from_coefficients(coeffs)

        square_coeffs = curve.square().get_coefficients()[:,0]
        expected_coeffs = np.array([16, 24, 25, 20, 10, 4, 1])
        self.assert_numpy_arrays_equal(square_coeffs, expected_coeffs, precision=6)

    def test_square_2(self):
        coeffs = np.array([[-2, 1, 0], [4, 0, 0]], dtype=np.float64)
        curve = SvTaylorCurve.from_coefficients(coeffs)
        square_coeffs = curve.square().get_coefficients()[:,0]
        expected_coeffs = np.array([5, -16, 16])
        self.assert_numpy_arrays_equal(square_coeffs, expected_coeffs, precision=6)

    def test_to_nurbs_1(self):
        coeffs = np.array([[-2, 1, 0], [4, 0, 0]], dtype=np.float64)
        curve = SvTaylorCurve.from_coefficients(coeffs)

        cpts = curve.to_nurbs().get_control_points()
        expected_cpts = np.array([[-2, 1, 0], [2, 1, 0]])

        self.assert_numpy_arrays_equal(cpts, expected_cpts, precision=6)

    def test_to_nurbs_2(self):
        coeffs = np.array([[5,0,0], [-16,0,0], [16,0,0]], dtype=np.float64)
        curve = SvTaylorCurve.from_coefficients(coeffs)

        cpts = curve.to_nurbs().get_control_points()
        expected_cpts = np.array([[5,0,0], [-3,0,0], [5,0,0]])

        self.assert_numpy_arrays_equal(cpts, expected_cpts, precision=6)

