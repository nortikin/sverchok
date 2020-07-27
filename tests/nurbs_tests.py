import numpy as np

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.curve.nurbs import SvGeomdlCurve, SvNativeNurbsCurve, SvNurbsBasisFunctions
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl.helpers import basis_function_one, basis_function_ders_one

class NurbsCurveTests(SverchokTestCase):
    def setUp(self):
        super().setUp()
        self.knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        self.degree = 3
        self.span = 2
        self.ts = np.linspace(0, 1.0, num=20)
        self.control_points = [[0.0, 0.0, 0.0],
              [1.7846156358718872, 2.7446157932281494, 0.0],
              [4.566154479980469, 2.8430774211883545, 0.0],
              [5.821539402008057, 0.03692317008972168, 0.0]]

        self.weights = [1.0 for i in self.control_points]

    @requires(geomdl)
    def test_basis_function(self):
        "Test basis functions values"
        v1s = []
        for t in self.ts:
            v1 = basis_function_one(self.degree, self.knotvector, self.span, t)
            v1s.append(v1)
        v1s = np.array(v1s)

        functions = SvNurbsBasisFunctions(self.knotvector)
        v2s = functions.function(self.span, self.degree)(self.ts)

        self.assert_numpy_arrays_equal(v1s, v2s, precision=8)

    def test_basis_derivative(self):
        "Test basis functions derivative"

        expected = np.array([ 0.0,          0.29085873,  0.53185596,  0.72299169,  0.86426593,  0.95567867,
                  0.99722992,  0.98891967,  0.93074792,  0.82271468,  0.66481994,  0.45706371,
                  0.19944598, -0.10803324, -0.46537396, -0.87257618, -1.32963989, -1.8365651,
                 -2.3933518,  -3.0        ])

        functions = SvNurbsBasisFunctions(self.knotvector)
        d2s = functions.derivative(self.span, self.degree, 1)(self.ts)

        self.assert_numpy_arrays_equal(expected, d2s, precision=8)

    @requires(geomdl)
    def test_curve_eval(self):
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.evaluate_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.evaluate_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_eval_2(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.evaluate_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.evaluate_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_tangent(self):
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.tangent_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.tangent_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_tangent_2(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.tangent_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.tangent_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_second(self):
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.second_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.second_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_second(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.second_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.second_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_third(self):
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.third_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.third_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_third_2(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.third_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.third_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

