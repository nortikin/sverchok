
import numpy as np

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.utils.curve import SvCubicBezierCurve, SvBezierCurve

def cubic_control_points():
    return [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [2.0, 1.0, 0.0],
            [3.0, 2.0, 0.0]
        ]

class BezierTests(SverchokTestCase):
    def test_cubic_equals_generic(self):
        ts = np.linspace(0.0, 1.0, num=10)
        points = cubic_control_points()
        cubic = SvCubicBezierCurve(*points)
        generic = SvBezierCurve(points)
        cubic_points = cubic.evaluate_array(ts)
        generic_points = generic.evaluate_array(ts)
        self.assert_numpy_arrays_equal(cubic_points, generic_points)

    def test_tangents_equal(self):
        ts = np.linspace(0.0, 1.0, num=10)
        points = cubic_control_points()
        cubic = SvCubicBezierCurve(*points)
        generic = SvBezierCurve(points)
        cubic_points = cubic.tangent_array(ts)
        generic_points = generic.tangent_array(ts)
        self.assert_numpy_arrays_equal(cubic_points, generic_points, precision=6)

    def test_normals_equal(self):
        ts = np.linspace(0.0, 1.0, num=10)
        points = cubic_control_points()
        cubic = SvCubicBezierCurve(*points)
        generic = SvBezierCurve(points)
        cubic_points = cubic.main_normal_array(ts)
        generic_points = generic.main_normal_array(ts)
        self.assert_numpy_arrays_equal(cubic_points, generic_points, precision=6)

    def test_second_derivs_equal(self):
        ts = np.linspace(0.0, 1.0, num=10)
        points = cubic_control_points()
        cubic = SvCubicBezierCurve(*points)
        generic = SvBezierCurve(points)
        cubic_points = cubic.second_derivative_array(ts)
        generic_points = generic.second_derivative_array(ts)
        self.assert_numpy_arrays_equal(cubic_points, generic_points, precision=6)

    def test_third_derivs_equal(self):
        ts = np.linspace(0.0, 1.0, num=10)
        points = cubic_control_points()
        cubic = SvCubicBezierCurve(*points)
        generic = SvBezierCurve(points)
        cubic_points = cubic.third_derivative_array(ts)
        generic_points = generic.third_derivative_array(ts)
        self.assert_numpy_arrays_equal(cubic_points, generic_points, precision=6)

