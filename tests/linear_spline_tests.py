
import numpy as np 
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info
from sverchok.utils.geom import LinearSpline

class LinearSplineTests(SverchokTestCase):
    def setUp(self):
        super().setUp()
        vertices = [(-1, -1, 0), (0, 0, 0), (1, 2, 0), (2, 3, 0)]
        self.control_points = np.array(vertices)
        self.spline = LinearSpline(vertices, metric="DISTANCE")

    def test_eval(self):
        t_in = np.array([0.0, 0.1, 0.4, 0.5, 0.7, 1.0])
        result = self.spline.eval(t_in)
        expected_result = np.array(
                [[-1.0,        -1.0,         0.0 ],
                 [-0.64188612, -0.64188612,  0.0 ],
                 [ 0.27350889,  0.54701779,  0.0 ],
                 [ 0.5,         1.0,         0.0 ],
                 [ 0.95298221,  1.90596443,  0.0 ],
                 [ 2.0,         3.0,         0.0 ]])
        #info(result)
        self.assert_numpy_arrays_equal(result, expected_result, precision=8)

    def test_tangent(self):
        t_in = np.array([0.0, 0.1, 0.4, 0.5, 0.7, 1.0])
        result = self.spline.tangent(t_in)
        #info(result)
        expected_result = np.array(
                [[-1, -1,  0],
                 [-1, -1,  0],
                 [-1, -2,  0],
                 [-1, -2,  0],
                 [-1, -2,  0],
                 [-1, -1,  0]])
        self.assert_numpy_arrays_equal(result, expected_result)

    def test_control_points(self):
        points = self.spline.get_control_points()
        self.assertEquals(points.shape, (3,2,3))
        expected = np.array(list(zip(self.control_points, self.control_points[1:])))
        self.assert_numpy_arrays_equal(points, expected)

