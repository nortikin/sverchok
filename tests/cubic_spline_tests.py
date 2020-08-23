
import numpy as np 
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info
from sverchok.utils.geom import CubicSpline
from sverchok.utils.curve.bezier import SvBezierCurve
from sverchok.utils.curve.algorithms import concatenate_curves, reparametrize_curve

class CubicSplineTests(SverchokTestCase):
    def setUp(self):
        super().setUp()
        vertices = [(-1, -1, 0), (0, 0, 0), (1, 2, 0), (2, 3, 0)]
        self.control_points = np.array(vertices)
        self.spline = CubicSpline(vertices, metric="DISTANCE")

    def test_eval(self):
        t_in = np.array([0.0, 0.1, 0.4, 0.5, 0.7, 1.0])
        result = self.spline.eval(t_in)
        #info(result)
        expected_result = np.array(
                [[-1.0,        -1.0,         0.0 ],
                 [-0.60984526, -0.66497986,  0.0 ],
                 [ 0.29660356,  0.5303721,   0.0 ],
                 [ 0.5,         1.0,         0.0 ],
                 [ 0.94256655,  1.91347161,  0.0 ],
                 [ 2.0,         3.0,         0.0 ]])
        self.assert_numpy_arrays_equal(result, expected_result, precision=8)

    def test_tangent(self):
        t_in = np.array([0.0, 0.1, 0.4, 0.5, 0.7, 1.0])
        result = self.spline.tangent(t_in)
        expected_result = np.array(
             [[7.89735717, 6.63246233, 0.        ],
             [7.61454151, 6.83630432, 0.        ],
             [4.30643188, 9.22065484, 0.        ],
             [3.94869522, 9.47849683, 0.        ],
             [5.37964186, 8.44712885, 0.        ],
             [7.89735717, 6.63246233, 0.        ]]
        )
        self.assert_numpy_arrays_equal(result, expected_result, precision=8)

    def test_control_points_1(self):
        #index = np.array([0,1,2])
        points = self.spline.get_control_points()
        self.assertEquals(points.shape, (3, 4, 3))
        #print(points)
        for i in range(3):
            with self.subTest(segmentNum=i):
                p0 = points[i][0]
                p3 = points[i][3]
                expected_p0 = self.control_points[i]
                expected_p3 = self.control_points[i+1]
                self.assert_numpy_arrays_equal(p0, expected_p0, precision=8)
                self.assert_numpy_arrays_equal(p3, expected_p3, precision=8)

                bezier = SvBezierCurve([points[i][k] for k in range(4)])
                t_min_spline = self.spline.tknots[i]
                t_max_spline = self.spline.tknots[i+1]
                #print(f"Spline #{i}: {t_min_spline}, {t_max_spline}")
                t_spline = np.linspace(t_min_spline, t_max_spline, num=10)
                t_bezier = np.linspace(0, 1, num=10)
                pts_spline = self.spline.eval(t_spline)
                pts_bezier = bezier.evaluate_array(t_bezier)
                self.assert_numpy_arrays_equal(pts_bezier, pts_spline, precision=6)

