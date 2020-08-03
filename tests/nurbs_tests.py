import numpy as np
import unittest

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.curve.nurbs import SvGeomdlCurve, SvNativeNurbsCurve, SvNurbsBasisFunctions
from sverchok.utils.surface.nurbs import SvGeomdlSurface, SvNativeNurbsSurface
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl.helpers import basis_function_one, basis_function_ders_one

#@unittest.skip
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

class NurbsSurfaceTests(SverchokTestCase):
    def setUp(self):
        super().setUp()
        self.degree_u = 3
        self.degree_v = 3
        self.knotvector_u = [0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0]
        self.knotvector_v = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
        self.control_points = [[[-4.970711899389312, -4.87088638787232, 0.47476678569065944],
                  [-1.6397367584736762, -5.04580711766634, 0.6740307856716949],
                  [1.6292189956563377, -4.764936213541646, 2.1421219004527634],
                  [4.930064915463923, -4.824964987583302, 0.13349452595165756]],
                 [[-4.959173265777104, -2.244642032244925, -1.9818133620347351],
                  [-1.9143890720803352, -2.7878689443774776, 1.536703648366153],
                  [1.8335607072889166, -2.277992724284574, 2.2112166863418476],
                  [5.17949512783129, -2.5231123812706358, 1.2960447623394078]],
                 [[-5.229035330827069, 0.08395260779254865, -1.6477077713552284],
                  [-1.399865332339516, 0.013108992268686115, -0.39426182747761507],
                  [1.5254000423495906, 0.16454020385316903, -0.20258546014134948],
                  [5.0410603668738005, -0.2887261025287691, 0.5434759830282379]],
                 [[-4.932742570375402, 2.5701603939429685, 2.0501160719546263],
                  [-1.557574493706977, 2.4157047453686604, -0.29091236624092165],
                  [1.7852453771551835, 2.2361352987051246, 0.7704622062740487],
                  [5.10238271566841, 2.3262295470018315, -1.7143604623685627]],
                 [[-5.110742982844693, 4.9182264674396565, 0.324309071297221],
                  [-1.7035057563934934, 5.293024285369926, -1.8385529288017533],
                  [1.4919927307349463, 4.796785722843513, 0.7073604461282836],
                  [4.851974970346849, 4.979786464918605, -1.1807537357044255]]]
        self.weights = [[1.0 for i in row] for row in self.control_points]

        us = np.linspace(0.0, 1.0, num=3)
        vs = np.linspace(0.0, 1.0, num=4)
        us, vs = np.meshgrid(us, vs)
        self.us = us.flatten()
        self.vs = vs.flatten()

    @requires(geomdl)
    #@unittest.skip
    def test_eval(self):
        geomdl_surface = SvGeomdlSurface.build(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        vs1 = geomdl_surface.evaluate_array(self.us, self.vs)
        vs2 = native_surface.evaluate_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8)

    @requires(geomdl)
    #@unittest.skip
    def test_eval_2(self):
        weights = [[1,1,1,1], [1,2,3,1], [1,3,4,1], [1,4,5,1], [1,1,1,1]]

        geomdl_surface = SvGeomdlSurface.build(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
        vs1 = geomdl_surface.evaluate_array(self.us, self.vs)
        vs2 = native_surface.evaluate_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8, fail_fast=False)

    @requires(geomdl)
    #@unittest.skip
    def test_normal(self):
        geomdl_surface = SvGeomdlSurface.build(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        vs1 = geomdl_surface.normal_array(self.us, self.vs)
        vs2 = native_surface.normal_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8)

    @requires(geomdl)
    #@unittest.skip
    def test_gauss_curvature(self):
        geomdl_surface = SvGeomdlSurface.build(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        vs1 = geomdl_surface.gauss_curvature_array(self.us, self.vs)
        vs2 = native_surface.gauss_curvature_array(self.us, self.vs)
        self.assert_sverchok_data_equal(vs1, vs2, precision=8)

    @requires(geomdl)
    #@unittest.skip
    def test_gauss_curvature_2(self):
        weights = [[1,1,1,1], [1,2,3,1], [1,3,4,1], [1,4,5,1], [1,1,1,1]]
        #us, vs = self.us, self.vs

        us = np.linspace(0.0, 1.0, num=10)
        vs = np.linspace(0.0, 1.0, num=20)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()

        geomdl_surface = SvGeomdlSurface.build(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
        c1 = geomdl_surface.curvature_calculator(us, vs)
        c2 = native_surface.curvature_calculator(us, vs)
        self.assert_numpy_arrays_equal(c1.fu, c2.fu, precision=8)
        self.assert_numpy_arrays_equal(c1.fv, c2.fv, precision=8)
        self.assert_numpy_arrays_equal(c1.duu, c2.duu, precision=8)
        self.assert_numpy_arrays_equal(c1.dvv, c2.dvv, precision=8)
        self.assert_numpy_arrays_equal(c1.duv, c2.duv, precision=8)
        self.assert_numpy_arrays_equal(c1.nuu, c2.nuu, precision=8, fail_fast=False)
        self.assert_numpy_arrays_equal(c1.nvv, c2.nvv, precision=8)
        self.assert_numpy_arrays_equal(c1.nuv, c2.nuv, precision=8)
        vs1 = geomdl_surface.gauss_curvature_array(self.us, self.vs)
        vs2 = native_surface.gauss_curvature_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8, fail_fast=False)

