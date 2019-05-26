
import numpy as np
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info
from sverchok.utils.geom import PlaneEquation, LineEquation, linear_approximation

class PlaneTests(SverchokTestCase):
    def test_plane_from_three_points(self):
        p1 = (1, 0, 0)
        p2 = (0, 1, 0)
        p3 = (0, 0, 1)
        plane = PlaneEquation.from_three_points(p1, p2, p3)
        self.assertEquals(plane.a, 1)
        self.assertEquals(plane.b, 1)
        self.assertEquals(plane.c, 1)
        self.assertEquals(plane.d, -1)

    def test_nearest_to_origin(self):
        p1 = (1, 0, 0)
        p2 = (0, 1, 0)
        p3 = (0, 0, 1)
        plane = PlaneEquation.from_three_points(p1, p2, p3)
        p = plane.nearest_point_to_origin()
        self.assert_sverchok_data_equal(tuple(p), (0.3333, 0.3333, 0.3333), precision=4)

    def test_check_yes(self):
        plane = PlaneEquation.from_coordinate_plane('XY')
        p = (7, 8, 0)
        self.assertTrue(plane.check(p))

    def test_check_no(self):
        plane = PlaneEquation.from_coordinate_plane('XY')
        p = (7, 8, 1)
        self.assertFalse(plane.check(p))

    def test_two_vectors(self):
        p1 = (2, 0, 0)
        p2 = (0, 1, 0)
        p3 = (0, 0, 2)
        plane = PlaneEquation.from_three_points(p1, p2, p3)

        normal = plane.normal
        v1, v2 = plane.two_vectors()

        self.assertTrue(abs(normal.dot(v1)) < 1e-8)
        self.assertTrue(abs(normal.dot(v2)) < 1e-8)
        self.assertTrue(abs(v1.dot(v2)) < 1e-8)

    def test_distance_to_point(self):
        plane = PlaneEquation.from_coordinate_plane('XY')
        point = (1, 2, 3)
        distance = plane.distance_to_point(point)
        self.assertEquals(distance, 3)

    def test_distance_to_points(self):
        plane = PlaneEquation.from_coordinate_plane('XY')
        points = [(1, 2, 3), (4, 5, 6)]
        distances = plane.distance_to_points(points)
        self.assert_numpy_arrays_equal(distances, np.array([3, 6]))

    def test_intersect_with_line(self):
        plane = PlaneEquation.from_coordinate_plane('XY')
        line = LineEquation.from_direction_and_point((1, 1, 1), (1, 1, 1))
        point = plane.intersect_with_line(line)
        self.assert_sverchok_data_equal(tuple(point), (0, 0, 0))

    def test_intersect_with_plane(self):
        plane1 = PlaneEquation.from_coordinate_plane('XY')
        plane2 = PlaneEquation.from_coordinate_plane('XZ')
        line = plane1.intersect_with_plane(plane2)
        self.assert_sverchok_data_equal(tuple(line.direction.normalized()), (1, 0, 0))
        self.assert_sverchok_data_equal(tuple(line.point), (0, 0, 0))

class LineTests(SverchokTestCase):
    def test_from_two_points(self):
        p1 = (1, 1, 1)
        p2 = (3, 3, 3)
        line = LineEquation.from_two_points(p1, p2)
        self.assert_sverchok_data_equal(tuple(line.direction), (2, 2, 2))
        self.assert_sverchok_data_equal(tuple(line.point), p1)

    def test_check_yes(self):
        p1 = (1, 1, 1)
        p2 = (3, 3, 3)
        line = LineEquation.from_two_points(p1, p2)
        p3 = (5, 5, 5)
        self.assertTrue(line.check(p3))

    def test_check_no(self):
        p1 = (1, 1, 1)
        p2 = (3, 3, 3)
        line = LineEquation.from_two_points(p1, p2)
        p3 = (5, 5, 6)
        self.assertFalse(line.check(p3))
    
    def test_distance_to_point(self):
        line = LineEquation.from_coordinate_axis('Z')
        point = (0, 2, 0)
        self.assertEquals(line.distance_to_point(point), 2)

class LinearApproximationTests(SverchokTestCase):
    def test_approximate_line_1(self):
        p1 = (0, 0, 0)
        p2 = (1, 0, 0)
        p3 = (2, 0, 0)
        p4 = (3, 0, 0)
        line = linear_approximation([p1, p2, p3, p4]).most_similar_line()
        self.assert_sverchok_data_equal(tuple(line.direction.normalized()), (1, 0, 0), precision=5)
    
    def test_approximate_line_2(self):
        p1 = (0, -1, 0)
        p2 = (1, 1, 0)
        p3 = (2, -1, 0)
        p4 = (3, 1, 0)
        line = linear_approximation([p1, p2, p3, p4]).most_similar_line()
        self.assert_sverchok_data_equal(tuple(line.direction), (0.7882054448127747, 0.6154122352600098, 0.0), precision=5)

    def test_approximate_plane(self):
        p1 = (0, -1, 0)
        p2 = (1, 1, 0)
        p3 = (2, -1, 0)
        p4 = (3, 1, 0)
        plane = linear_approximation([p1, p2, p3, p4]).most_similar_plane()
        self.assert_sverchok_data_equal(tuple(plane.normal.normalized()), (0, 0, 1), precision=5)

