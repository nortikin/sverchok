
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
        self.assert_numpy_arrays_equal(cubic_points, generic_points, precision=6)

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

    def test_blend_tangent(self):
        p0 = np.array([0, 0, 0])
        p1 = np.array([3, 0, 0])
        v0 = np.array([3, 3, 0])
        v1 = np.array([3, 3, 0])
        curve = SvBezierCurve.from_points_and_tangents(p0, v0, v1, p1)

        v0r = curve.tangent(0)
        v1r = curve.tangent(1)

        self.assert_numpy_arrays_equal(v0r, v0)
        self.assert_numpy_arrays_equal(v1r, v1)

    def test_blend_second(self):
        p0 = np.array([0, 0, 0])
        p1 = np.array([3, 0, 0])
        v0 = np.array([3, 3, 0])
        v1 = np.array([3, 3, 0])
        a0 = np.array([0, 0, 1])
        a1 = np.array([0, 0, 1])
        curve = SvBezierCurve.blend_second_derivatives(p0, v0, a0, p1, v1, a1)

        v0r = curve.tangent(0)
        v1r = curve.tangent(1)

        a0r = curve.second_derivative(0)
        a1r = curve.second_derivative(1)

        self.assert_numpy_arrays_equal(v0r, v0)
        self.assert_numpy_arrays_equal(v1r, v1)
        self.assert_numpy_arrays_equal(a0r, a0)
        self.assert_numpy_arrays_equal(a1r, a1, precision=8)

    def test_blend_third(self):
        p0 = np.array([0, 0, 0])
        p1 = np.array([3, 0, 0])
        v0 = np.array([3, 3, 0])
        v1 = np.array([3, 3, 0])
        a0 = np.array([0, 0, 1])
        a1 = np.array([0, 0, 1])
        k0 = np.array([1, 1, 0])
        k1 = np.array([1, 1, 0])
        curve = SvBezierCurve.blend_third_derivatives(p0, v0, a0, k0, p1, v1, a1, k1)

        v0r = curve.tangent(0)
        v1r = curve.tangent(1)

        a0r = curve.second_derivative(0)
        a1r = curve.second_derivative(1)

        k0r = curve.third_derivative_array(np.array([0]))[0]
        k1r = curve.third_derivative_array(np.array([1]))[0]

        self.assert_numpy_arrays_equal(v0r, v0, precision=6)
        self.assert_numpy_arrays_equal(v1r, v1, precision=6)
        self.assert_numpy_arrays_equal(a0r, a0, precision=6)
        self.assert_numpy_arrays_equal(a1r, a1, precision=6)
        self.assert_numpy_arrays_equal(k0r, k0, precision=6)
        self.assert_numpy_arrays_equal(k1r, k1, precision=6)

