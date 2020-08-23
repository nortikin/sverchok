import numpy as np
import unittest
from math import pi

from mathutils import Matrix

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve.nurbs import SvGeomdlCurve, SvNativeNurbsCurve, SvNurbsBasisFunctions, SvNurbsCurve
from sverchok.utils.curve.algorithms import interpolate_nurbs_curve
from sverchok.utils.nurbs_common import elevate_bezier_degree, from_homogenous
from sverchok.utils.surface.nurbs import SvGeomdlSurface, SvNativeNurbsSurface
from sverchok.utils.surface.algorithms import SvCurveLerpSurface
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

    #@unittest.skip
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

    #@unittest.skip
    @requires(geomdl)
    def test_curve_eval(self):
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.evaluate_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.evaluate_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_eval_2(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.evaluate_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.evaluate_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_tangent(self):
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.tangent_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.tangent_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_tangent_2(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.tangent_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.tangent_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_second(self):
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.second_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.second_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_second(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.second_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.second_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_third(self):
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, self.weights)
        t1s = geomdl_curve.third_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, self.weights)
        t2s = native_curve.third_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_third_2(self):
        weights = [1.0, 2.0, 3.0, 1.0]
        geomdl_curve = SvGeomdlCurve.build_geomdl(self.degree, self.knotvector, self.control_points, weights)
        t1s = geomdl_curve.third_derivative_array(self.ts)
        native_curve = SvNativeNurbsCurve(self.degree, self.knotvector, self.control_points, weights)
        t2s = native_curve.third_derivative_array(self.ts)
        self.assert_numpy_arrays_equal(t1s, t2s, precision=8)

    @requires(geomdl)
    def test_curve_3436(self):
        points = [(0.0,0.0,0.0), (0.5, 0.0, 0.5), (1.0, 0.0, 0.0)]
        ts = np.array([0, 0.5, 1, 1.61803397])
        #ts = self.ts
        degree = 2
        knotvector = [0, 0, 0, 1, 1, 1]
        weights = [1, 1, 1]
        geomdl_curve = SvNurbsCurve.build('GEOMDL', degree, knotvector, points, weights)
        native_curve = SvNurbsCurve.build('NATIVE', degree, knotvector, points, weights)
        p1s = geomdl_curve.evaluate_array(ts)
        p2s = native_curve.evaluate_array(ts)
        #print("NATIVE:", p2s)
        self.assert_numpy_arrays_equal(p1s, p2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_curve_3436_2(self):
        points = [(0,0,0), (0.5, 0, 0.5), (1, 0, 0)]
        ts = np.array([0, 0.5, 1])
        degree = 2
        knotvector = [0, 0, 0, 1, 1, 1]
        weights = [1, 1, 1]
        geomdl_curve = SvGeomdlCurve.build_geomdl(degree, knotvector, points, weights)
        native_curve = SvNativeNurbsCurve(degree, knotvector, points, weights)
        p1s = geomdl_curve.third_derivative_array(ts)
        p2s = native_curve.third_derivative_array(ts)
        self.assert_numpy_arrays_equal(p1s, p2s, precision=8)

    #@unittest.skip
    @requires(geomdl)
    def test_basis_function_3436(self):
        "Test basis functions values outside of bounds"
        v1s = []
        ts = np.array([1.61803397])
        for t in ts:
            v1 = basis_function_one(self.degree, self.knotvector, self.span, t)
            v1s.append(v1)
        v1s = np.array(v1s)

        functions = SvNurbsBasisFunctions(self.knotvector)
        v2s = functions.function(self.span, self.degree)(ts)

        self.assert_numpy_arrays_equal(v1s, v2s, precision=8)

    @unittest.skip("For now, Native implementation gives different results from Geomdl when evaluating the curve out of bounds")
    def test_curve_3436_3(self):
        knotvector =  [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        basis = SvNurbsBasisFunctions(knotvector)
        ts = np.array([1.61803397])
        ns = basis.derivative(2, 2, 0)(ts)
        expected = np.array([1])
        self.assert_numpy_arrays_equal(ns, expected, precision=8)

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
        geomdl_surface = SvGeomdlSurface.build_geomdl(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        vs1 = geomdl_surface.evaluate_array(self.us, self.vs)
        vs2 = native_surface.evaluate_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8)

    @requires(geomdl)
    #@unittest.skip
    def test_eval_2(self):
        weights = [[1,1,1,1], [1,2,3,1], [1,3,4,1], [1,4,5,1], [1,1,1,1]]

        geomdl_surface = SvGeomdlSurface.build_geomdl(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
        vs1 = geomdl_surface.evaluate_array(self.us, self.vs)
        vs2 = native_surface.evaluate_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8, fail_fast=False)

    @requires(geomdl)
    #@unittest.skip
    def test_normal(self):
        geomdl_surface = SvGeomdlSurface.build_geomdl(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        native_surface = SvNativeNurbsSurface(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
        vs1 = geomdl_surface.normal_array(self.us, self.vs)
        vs2 = native_surface.normal_array(self.us, self.vs)
        self.assert_numpy_arrays_equal(vs1, vs2, precision=8)

    @requires(geomdl)
    #@unittest.skip
    def test_gauss_curvature(self):
        geomdl_surface = SvGeomdlSurface.build_geomdl(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, self.weights)
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

        geomdl_surface = SvGeomdlSurface.build_geomdl(self.degree_u, self.degree_v, self.knotvector_u, self.knotvector_v, self.control_points, weights)
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

class OtherNurbsTests(SverchokTestCase):
    def test_ruled_surface_1(self):
        """
        Test that
        1) SvCurveLerpSurface.build gives a NURBS surface for two NURBS curves;
        2) the resulting surface is identical to generic ruled surface.
        """
        control_points1 = np.array([[0, 0, 0], [0.5, 0, 0.5], [1, 0, 0]])
        control_points2 = np.array([[0, 2, 0], [0.5, 3, 0.5], [1, 2, 0]])
        # With non-trivial weights, this test will fail,
        # because the resulting surface will have different parametrization
        # comparing to generic ruled surface; however, the shape of the surface
        # will be correct anyway.
        weights1 = [1, 1, 1]
        weights2 = [1, 1, 1]

        knotvector = sv_knotvector.generate(degree=2, num_ctrlpts=3)
        curve1 = SvNativeNurbsCurve(2, knotvector, control_points1, weights1)
        curve2 = SvNativeNurbsCurve(2, knotvector, control_points2, weights2)

        surf1 = SvCurveLerpSurface(curve1, curve2)
        surf2 = SvCurveLerpSurface.build(curve1, curve2)

        self.assertTrue(isinstance(surf2, SvNativeNurbsSurface))

        us = np.array([0, 0, 0.5, 0.5, 1, 1])
        vs = np.array([0, 0.5, 0.5, 1, 0.5, 1])

        pts1 = surf1.evaluate_array(us, vs)
        pts2 = surf2.evaluate_array(us, vs)

        self.assert_numpy_arrays_equal(pts1, pts2, precision=8, fail_fast=False)

    def test_ruled_surface_2(self):
        control_points1 = np.array([[0, 0, 0], [0.5, 0, 0.5], [0.5, 0.3, 0.5], [1, 0, 0]])
        control_points2 = np.array([[0, 2, 0], [0.5, 3, 0.5], [1, 2, 0]])
        # With non-trivial weights, this test will fail,
        # because the resulting surface will have different parametrization
        # comparing to generic ruled surface; however, the shape of the surface
        # will be correct anyway.
        weights1 = [1, 1, 1, 1]
        weights2 = [1, 1, 1]

        degree = 2
        knotvector1 = sv_knotvector.generate(degree, num_ctrlpts=len(control_points1))
        knotvector2 = sv_knotvector.generate(degree, num_ctrlpts=len(control_points2))
        curve1 = SvNativeNurbsCurve(degree, knotvector1, control_points1, weights1)
        curve2 = SvNativeNurbsCurve(degree, knotvector2, control_points2, weights2)

        surf1 = SvCurveLerpSurface(curve1, curve2)
        surf2 = SvCurveLerpSurface.build(curve1, curve2)

        self.assertTrue(isinstance(surf2, SvNativeNurbsSurface))

        us = np.array([0, 0, 0.5, 0.5, 1, 1])
        vs = np.array([0, 0.5, 0.5, 1, 0.5, 1])

        pts1 = surf1.evaluate_array(us, vs)
        pts2 = surf2.evaluate_array(us, vs)

        self.assert_numpy_arrays_equal(pts1, pts2, precision=8, fail_fast=False)

    def test_elevate_bezier_degree_1(self):
        points = np.array([[0, 0, 0], [1, 0, 0]])
        self_degree = 1
        result = elevate_bezier_degree(self_degree, points)
        expected = np.array([[0, 0, 0], [0.5, 0, 0], [1, 0, 0]])
        self.assert_numpy_arrays_equal(result, expected, fail_fast=False)

    def test_elevate_bezier_degree_2(self):
        points = np.array([[0, 0, 0], [1, 0, 0]])
        self_degree = 1
        result = elevate_bezier_degree(self_degree, points, delta=3)
        expected = np.array([[0, 0, 0], [0.25, 0, 0], [0.5, 0, 0], [0.75, 0, 0], [1, 0, 0]])
        self.assert_numpy_arrays_equal(result, expected, fail_fast=False)

    def test_from_homogenous(self):
        points = np.array([[0, 0, 1, 1], [0, 0, 4, 2], [0, 0, 9, 3]])
        result, weights = from_homogenous(points)
        expected_points = np.array([[0, 0, 1], [0, 0, 2], [0, 0, 3]])
        expected_weights = np.array([1, 2, 3])
        self.assert_numpy_arrays_equal(weights, expected_weights)
        self.assert_numpy_arrays_equal(result, expected_points)

    def test_insert_1(self):
        points = np.array([[0, 0, 0], [1, 0, 0]])
        kv = sv_knotvector.generate(1,2)
        weights = [1, 1]
        curve = SvNativeNurbsCurve(1, kv, points, weights)
        curve = curve.insert_knot(0.5)

        ts = np.array([0, 0.25, 0.5, 0.75, 1.0])
        expected = np.array([[0,0,0], [0.25,0,0], [0.5,0,0], [0.75,0,0], [1,0,0]])
        result = curve.evaluate_array(ts)
        self.assert_numpy_arrays_equal(result, expected)

    def test_insert_2(self):
        points = np.array([[0, 0, 0], [1, 1, 0], [2, 0, 0]])
        degree = 2
        kv = sv_knotvector.generate(degree,3)
        weights = [1, 1, 1]
        curve = SvNativeNurbsCurve(degree, kv, points, weights)
        inserted = curve.insert_knot(0.5, 2)
        ts = np.array([0, 0.25, 0.5, 0.75, 1.0])
        expected = curve.evaluate_array(ts)
        result = inserted.evaluate_array(ts)
        self.assert_numpy_arrays_equal(result, expected)

    def test_insert_3(self):
        points = np.array([[0, 0, 0], [1, 1, 0], [2,1,0], [3, 0, 0]])
        degree = 2
        kv = sv_knotvector.generate(degree,4)
        weights = [1, 1, 1, 1]

        #print("test_insert_3: Kv:", kv)
        curve = SvNativeNurbsCurve(degree, kv, points, weights)
        inserted = curve.insert_knot(0.5)

        #print("Ins.kv:", inserted.knotvector)
        #print("Ins.cp:", inserted.control_points)

        ts = np.array([0, 0.25, 0.5, 0.75, 1.0])
        expected = curve.evaluate_array(ts)
        result = inserted.evaluate_array(ts)
        self.assert_numpy_arrays_equal(result, expected)

    def test_split_1(self):
        points = np.array([[0, 0, 0], [1, 0, 0]])
        kv = sv_knotvector.generate(1,2)
        weights = [1, 1]
        curve = SvNativeNurbsCurve(1, kv, points, weights)

        curve1, curve2 = curve.split_at(0.5)

        expected_pts1 = np.array([[0, 0, 0], [0.5, 0, 0]])
        pts1 = curve1.get_control_points()
        self.assert_numpy_arrays_equal(pts1, expected_pts1)

        expected_pts2 = np.array([[0.5, 0, 0.0], [1, 0, 0]])
        pts2 = curve2.get_control_points()
        self.assert_numpy_arrays_equal(pts2, expected_pts2)

        expected_kv1 = np.array([0,0, 0.5,0.5])
        kv1 = curve1.get_knotvector()
        self.assert_numpy_arrays_equal(kv1, expected_kv1)

        expected_kv2 = np.array([0.5,0.5, 1,1])
        kv2 = curve2.get_knotvector()
        self.assert_numpy_arrays_equal(kv2, expected_kv2)

    #@unittest.skip
    def test_split_2(self):
        points = np.array([[0, 0, 0], [1, 1, 0], [2, 0, 0]])
        kv = sv_knotvector.generate(2,3)
        weights = [1, 1, 1]
        curve = SvNativeNurbsCurve(2, kv, points, weights)

        curve1, curve2 = curve.split_at(0.5)

        expected_kv1 = np.array([0,0,0, 0.5,0.5,0.5])
        kv1 = curve1.get_knotvector()
        self.assert_numpy_arrays_equal(kv1, expected_kv1)

        expected_kv2 = np.array([0.5,0.5,0.5, 1,1,1])
        kv2 = curve2.get_knotvector()
        self.assert_numpy_arrays_equal(kv2, expected_kv2)

        expected_pts1 = np.array([[0, 0, 0], [0.5, 0.5, 0], [1, 0.5, 0]])
        pts1 = curve1.get_control_points()
        #print("Pts1", pts1)
        self.assert_numpy_arrays_equal(pts1, expected_pts1)

        expected_pts2 = np.array([[1, 0.5, 0], [1.5, 0.5, 0], [2, 0, 0]])
        pts2 = curve2.get_control_points()
        #print("Pts2", pts2)
        self.assert_numpy_arrays_equal(pts2, expected_pts2)

    def test_split_3(self):
        points = np.array([[0, 0, 0],
                           [1, 1, 0],
                           [2, 1, 0],
                           [3, 0, 0]])
        weights = [1, 1, 1, 1]
        degree = 2
        knotvector = sv_knotvector.generate(degree, 4)
        curve = SvNativeNurbsCurve(degree, knotvector, points, weights)

        t0 = 0.5
        curve1, curve2 = curve.split_at(t0)
        #print("Kv1:", curve1.get_knotvector())
        #print("Kv2:", curve2.get_knotvector())

        pt1 = curve1.evaluate(0.25)
        expected_pt1 = curve.evaluate(0.25)
        #print(f"Split3: Pt1: {pt1}, expected: {expected_pt1}")
        self.assert_numpy_arrays_equal(pt1, expected_pt1, precision=4)

        pt2 = curve2.evaluate(0.75)
        expected_pt2 = curve.evaluate(0.75)
        self.assert_numpy_arrays_equal(pt2, expected_pt2, precision=4)

    def test_split_4(self):
        points = np.array([[0, 0, 0],
                           [1, 1, 0],
                           [2, 0, 0],
                           [3, 1, 0],
                           [4, 0, 0]])
        degree = 3
        knotvector = sv_knotvector.generate(degree, 5)
        weights = [0.25, 1, 4.9, 2.35, 1]
        #weights = [1, 1, 1, 1, 1]
        curve = SvNativeNurbsCurve(degree, knotvector, points, weights)

        curve1, curve2 = curve.split_at(0.501)
        #print("Kv1:", curve1.get_knotvector())
        #print("Kv2:", curve2.get_knotvector())

        pt1 = curve1.evaluate(0.25)
        expected_pt1 = curve.evaluate(0.25)
        #print(f"Split4: Pt1: {pt1}, expected: {expected_pt1}")
        self.assert_numpy_arrays_equal(pt1, expected_pt1, precision=4)

        pt2 = curve2.evaluate(0.75)
        expected_pt2 = curve.evaluate(0.75)
        self.assert_numpy_arrays_equal(pt2, expected_pt2, precision=4)

    def test_single_1(self):
        points = np.array([[0, 0, 0], [1, 1, 0], [2, 0, 0]])
        kv = sv_knotvector.generate(2,3)
        weights = [1, 1, 1]
        curve = SvNativeNurbsCurve(2, kv, points, weights)
        t = 0.5
        result = curve.evaluate(t)
        #print(result)
        expected = np.array([1, 0.5, 0])
        self.assert_numpy_arrays_equal(result, expected, precision=6)

    def test_circle_1(self):
        circle = SvCircle(Matrix(), 1.0)
        circle.u_bounds = (0, pi/6)
        nurbs = circle.to_nurbs()
        cpts = nurbs.get_control_points()
        expected_cpts = np.array([[1.0, 0.0, 0.0 ],
                                  [1.0, 0.26794919, 0.0 ],
                                  [0.8660254,  0.5, 0.0 ]])
        self.assert_numpy_arrays_equal(cpts, expected_cpts, precision=6)

    def test_circle_2(self):
        circle = SvCircle(Matrix(), 1.0)
        t_max = pi + 0.3
        circle.u_bounds = (0, t_max)
        nurbs = circle.to_nurbs()
        ts = np.array([0, pi/2, pi, t_max])
        points = nurbs.evaluate_array(ts)
        expected_points = circle.evaluate_array(ts)
        self.assert_numpy_arrays_equal(points, expected_points, precision=6)

class KnotvectorTests(SverchokTestCase):
    def test_to_multiplicity_1(self):
        kv = np.array([0, 0, 0, 1, 1, 1], dtype=np.float64)
        result = sv_knotvector.to_multiplicity(kv)
        expected = [(0, 3), (1, 3)]
        self.assert_sverchok_data_equal(result, expected)

    def test_to_multiplicity_2(self):
        kv = np.array([0, 0, 0, 0.3, 0.7, 1, 1, 1], dtype=np.float64)
        result = sv_knotvector.to_multiplicity(kv)
        expected = [(0, 3), (0.3, 1), (0.7, 1), (1, 3)]
        self.assert_sverchok_data_equal(result, expected)

    def test_to_multiplicity_3(self):
        kv = np.array([0, 0, 0, 0.3, 0.7, 1, 1, 1, 1.5], dtype=np.float64)
        result = sv_knotvector.to_multiplicity(kv)
        expected = [(0, 3), (0.3, 1), (0.7, 1), (1, 3), (1.5, 1)]
        self.assert_sverchok_data_equal(result, expected)

    def test_to_multiplicity_4(self):
        kv = np.array([0, 0, 0, 0.3, 0.7, 1, 1, 1, 1.5, 1.7], dtype=np.float64)
        result = sv_knotvector.to_multiplicity(kv)
        expected = [(0, 3), (0.3, 1), (0.7, 1), (1, 3), (1.5, 1), (1.7, 1)]
        self.assert_sverchok_data_equal(result, expected)

    def test_from_multiplicity_1(self):
        pairs = [(0, 3), (1, 3)]
        kv = sv_knotvector.from_multiplicity(pairs)
        expected = np.array([0, 0, 0, 1, 1, 1])
        self.assert_numpy_arrays_equal(kv, expected)

    def test_from_multiplicity_2(self):
        pairs = [(0, 3), (0.5, 1), (1, 3)]
        kv = sv_knotvector.from_multiplicity(pairs)
        expected = np.array([0, 0, 0, 0.5, 1, 1, 1])
        self.assert_numpy_arrays_equal(kv, expected)

    def test_elevate_knotvector(self):
        kv = np.array([0, 0, 0, 1, 1, 1], dtype=np.float64)
        result = sv_knotvector.elevate_degree(kv)
        expected = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        self.assert_numpy_arrays_equal(result, expected)

    def test_diff_1(self):
        kv1 = np.array([0, 1, 2])
        kv2 = np.array([0, 1, 2])
        result = sv_knotvector.difference(kv1, kv2)
        expected = []
        self.assert_sverchok_data_equal(result, expected)

    def test_diff_2(self):
        kv1 = np.array([0, 1, 2], dtype=np.float64)
        kv2 = np.array([0, 1, 1, 2], dtype=np.float64)
        result = sv_knotvector.difference(kv1, kv2)
        expected = [(1, 1)]
        self.assert_sverchok_data_equal(result, expected)

    def test_diff_3(self):
        kv1 = np.array([0, 1, 2], dtype=np.float64)
        kv2 = np.array([0, 1, 1.5, 2], dtype=np.float64)
        result = sv_knotvector.difference(kv1, kv2)
        expected = [(1.5, 1)]
        self.assert_sverchok_data_equal(result, expected)

    def test_merge_1(self):
        kv1 = np.array([0, 1, 2])
        kv2 = np.array([0, 1, 2])
        result = sv_knotvector.merge(kv1, kv2)
        expected = np.array([0, 1, 2])
        self.assert_numpy_arrays_equal(result, expected)

    def test_merge_2(self):
        kv1 = np.array([0, 0.5, 2])
        kv2 = np.array([0, 1.5, 2])
        result = sv_knotvector.merge(kv1, kv2)
        expected = np.array([0, 0.5, 1.5, 2])
        self.assert_numpy_arrays_equal(result, expected)

    def test_from_tknots(self):
        tknots = np.array([0, 5, 9, 14, 17.0]) / 17.0
        degree = 3
        knotvector = sv_knotvector.from_tknots(degree, tknots)
        u4 = 0.5490196078431373
        expected = np.array([0,0,0,0, u4, 1,1,1,1])
        self.assert_numpy_arrays_equal(knotvector, expected, precision=6)

class InterpolateTests(SverchokTestCase):
    def test_interpolate_1(self):
        "NURBS interpolation in 3D"
        points = np.array([[0,0,0], [1,0,0], [1,1,0]], dtype=np.float64)
        degree = 2
        curve = interpolate_nurbs_curve(SvNativeNurbsCurve, degree, points)
        ts = np.array([0, 0.5, 1])
        result = curve.evaluate_array(ts)
        self.assert_numpy_arrays_equal(result, points, precision=6)

        ctrlpts = curve.get_control_points()
        expected_ctrlpts = np.array([[ 0.0, 0.0,   0.0 ], [ 1.5, -0.5,  0.0 ], [ 1.0,   1.0,   0.0 ]])
        self.assert_numpy_arrays_equal(ctrlpts, expected_ctrlpts, precision=6)

    def test_interpolate_2(self):
        "NURBS Interpolation in homogenous coordinates"
        points = np.array([[0,0,0,1], [1,0,0,2], [1,1,0,1]], dtype=np.float64)
        degree = 2
        curve = interpolate_nurbs_curve(SvNativeNurbsCurve, degree, points)
        ts = np.array([0, 0.5, 1])
        result = curve.evaluate_array(ts)
        expected = np.array([[0,0,0], [0.5,0,0], [1,1,0]])
        self.assert_numpy_arrays_equal(result, expected, precision=6)

        ctrlpts = curve.get_control_points()
        expected_ctrlpts = np.array( [[ 0.0, 0.0, 0.0 ], [ 0.5, -0.16666667,  0.0 ], [ 1.0, 1.0, 0.0 ]])
        self.assert_numpy_arrays_equal(ctrlpts, expected_ctrlpts, precision=6)

        weights = curve.get_weights()
        expected_weights = np.array([1, 3, 1])
        self.assert_numpy_arrays_equal(weights, expected_weights, precision=6)

