
import numpy as np 
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info
from sverchok.utils.geom import CubicSpline

class CubicSplineTests(SverchokTestCase):
    def setUp(self):
        super().setUp()
        vertices = [(-1, -1, 0), (0, 0, 0), (1, 2, 0), (2, 3, 0)]
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

