
from mathutils import Vector, Matrix

from sverchok.utils.testing import *
from sverchok.utils.geom import *
from sverchok.utils.curve.primitives import SvCircle


class GeometryTests(SverchokTestCase):

    def test_center_trivial(self):
        input = [(0, 0, 0)]
        output = center(input)
        expected_output = input[0]
        self.assertEqual(output, expected_output)

    def test_center_quad(self):
        inputs = [(-1, 0, 0), (0, -1, 0), (0, 1, 0), (1, 0, 0)]
        output = center(inputs)
        expected_output = (0, 0, 0)
        self.assertEqual(output, expected_output)

    def test_normal_quad(self):
        inputs = [(-1, 0, 0), (0, -1, 0), (1, 0, 0), (0, 1, 0)]
        output = calc_normal(inputs)
        expected_output = Vector((0, 0, 1))
        self.assertEqual(output, expected_output)

    def test_circle_equal_1(self):
        circle1 = SvCircle(Matrix(), 1.0)
        x = np.array([1, 0, 0], dtype=np.float64)
        origin = np.array([0, 0, 0], dtype=np.float64)
        z = np.array([0, 0, 1], dtype=np.float64)
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
        expected_center = np.array((0.0, -13.75, 0.0))
        self.assert_numpy_arrays_equal(circle.center, expected_center, precision=6)
        res1 = circle.evaluate(0)
        self.assert_numpy_arrays_equal(res1, pt1, precision=6)
        t_max = eq.arc_angle
        res2 = circle.evaluate(t_max)
        self.assert_numpy_arrays_equal(res2, pt3, precision=6)

    def test_arc_values_2(self):
        pt1 = np.array((-4, -2, 0))
        pt2 = np.array((-5, 0, 0))
        pt3 = np.array((-4, 2, 0))
        eq = circle_by_three_points(pt1, pt2, pt3)
        circle = SvCircle.from_equation(eq)
        res1 = circle.evaluate(0)
        self.assert_numpy_arrays_equal(res1, pt1, precision=6)
        t_max = eq.arc_angle
        res2 = circle.evaluate(t_max)
        self.assert_numpy_arrays_equal(res2, pt3, precision=6)

    def test_arc_values_3(self):
        pt1 = np.array((-1, 0, 0))
        pt2 = np.array((0, 2, 0))
        pt3 = np.array((1, 0, 0))
        eq = circle_by_three_points(pt1, pt2, pt3)
        circle = SvCircle.from_equation(eq)
        res1 = circle.evaluate(0)
        self.assert_numpy_arrays_equal(res1, pt1, precision=6)
        t_max = eq.arc_angle
        res2 = circle.evaluate(t_max)
        self.assert_numpy_arrays_equal(res2, pt3, precision=6)

    def test_arc_values_4(self):
        pt1 = np.array((0, 1, 0))
        pt2 = np.array((1, 1, 0))
        pt3 = np.array((1, 0, 0))
        eq = circle_by_three_points(pt1, pt2, pt3)
        circle = SvCircle.from_equation(eq)
        res1 = circle.evaluate(0)
        self.assert_numpy_arrays_equal(res1, pt1, precision=6)
        t_max = eq.arc_angle
        res2 = circle.evaluate(t_max)
        self.assert_numpy_arrays_equal(res2, pt3, precision=6)

    def test_arc_values_5(self):
        pt1 = np.array((0, 1, 0))
        pt2 = np.array((1, 1, 0))
        pt3 = np.array((0, 0, 0))
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

    @unittest.skip
    def test_plane_uv_projection(self):
        plane = PlaneEquation.from_coordinate_plane('XY')
        point = (1,1,1)
        uv = tuple(plane.point_uv_projection(point))
        self.assertEqual(uv, (1,1))

    def test_intersect_planes_1(self):
        plane1 = PlaneEquation.from_coordinate_plane('XY')
        plane2 = PlaneEquation.from_coordinate_plane('YZ')
        line = plane1.intersect_with_plane(plane2)

        pt1 = (0, 0, 0)
        pt2 = (0, 1, 0)
        
        self.assertTrue(line.check(pt1))
        self.assertTrue(line.check(pt2))

    def test_intersect_planes_2(self):
        pt1 = (0, 2.5, 0)
        n1 = (0.25, 8, 0)
        n2 = (-0.25, 8, 0)
        plane1 = PlaneEquation.from_normal_and_point(n1, pt1)
        plane2 = PlaneEquation.from_normal_and_point(n2, pt1)
        line = plane1.intersect_with_plane(plane2)

        pt2 = (0, 2.5, 100)

        self.assertTrue(line.check(pt1))
        self.assertTrue(line.check(pt2))

    def test_intersect_planes_3(self):
        pt1 = (0, 2.5, 0)
        n1 = (-8, 0.25, 0)
        n2 = (8, 0.25, 0)
        plane1 = PlaneEquation.from_normal_and_point(n1, pt1)
        plane2 = PlaneEquation.from_normal_and_point(n2, pt1)
        line = plane1.intersect_with_plane(plane2)

        pt2 = (0, 2.5, 100)

        self.assert_sverchok_data_equal(line.distance_to_point(pt1), 0.0, precision=6)
        self.assert_sverchok_data_equal(line.distance_to_point(pt2), 0.0, precision=6)

    def test_intersect_planes_4(self):
        pt1 = (0, 2.5, 0)
        pt2 = (0, 4.5, 0)
        n1 = (4, 8, 0)
        n2 = (2, 4, 0)

        plane1 = PlaneEquation.from_normal_and_point(n1, pt1)
        plane2 = PlaneEquation.from_normal_and_point(n2, pt1)
        r = plane1.intersect_with_plane(plane2)

        self.assertTrue(r is None)

