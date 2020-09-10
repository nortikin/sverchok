
import unittest
import numpy as np
import math

from mathutils import Vector, Matrix

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.utils.geom import *
from sverchok.utils.curve.primitives import SvCircle

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

    def test_circle_equal_1(self):
        circle1 = SvCircle(Matrix(), 1.0)
        x = np.array([1, 0, 0])
        origin = np.array([0, 0, 0])
        z = np.array([0, 0, 1])
        circle2 = SvCircle(center=origin, normal=z, vectorx=x)

        ts = np.linspace(0, pi/2, num=50)

        pts1 = circle1.evaluate_array(ts)
        pts2 = circle2.evaluate_array(ts)
        self.assert_numpy_arrays_equal(pts1, pts2, precision=8)

    def test_arc_values_1(self):
        pt1 = np.array((-4, 2, 0))
        pt2 = np.array((0, 2.5, 0))
        pt3 = np.array((4, 2, 0))
        eq = circle_by_three_points(pt1, pt2, pt3)
        circle = SvCircle.from_equation(eq)
        res1 = circle.evaluate(0)
        self.assert_numpy_arrays_equal(res1, pt1, precision=6)
        t_max = eq.arc_angle
        res2 = circle.evaluate(t_max)
        self.assert_numpy_arrays_equal(res2, pt3, precision=6)

    def test_arc_derivative_1(self):
        pt1 = (-5, 0, 0)
        pt2 = (-4, 3, 0)
        pt3 = (-3, 4, 0)
        eq = circle_by_three_points(pt1, pt2, pt3)
        circle = SvCircle.from_equation(eq)
        dv = circle.tangent(0)
        expected = np.array([0, 5, 0])
        self.assert_numpy_arrays_equal(dv, expected, precision=8)

