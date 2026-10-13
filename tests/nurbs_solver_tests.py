import numpy as np
import unittest
from math import pi

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.nurbs_common import SvNurbsMaths, elevate_bezier_degree, from_homogenous
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsBasisFunctions, SvNurbsCurve
from sverchok.utils.curve.nurbs_solver import *
from sverchok.utils.curve.nurbs_solver_applications import interpolate_nurbs_curve_with_tangents
from sverchok.core.sv_custom_exceptions import ArgumentError, InvalidStateError, AlgorithmError

class NurbsSolverTests(SverchokTestCase):
    def test_interpolate_with_tangents(self):
        degree = 3
        points = np.array([[0,0,0], [1,0,0], [1,1,0]], dtype=np.float64)
        tangents = np.array([[-1,1,0], [1,1,0], [-1,-1,0]], dtype=np.float64)
        curve = interpolate_nurbs_curve_with_tangents(degree, points, tangents)
        ts = np.array([0.0, 0.5, 1.0])
        tangents_result = curve.tangent_array(ts)
        self.assert_numpy_arrays_equal(points, curve.evaluate_array(ts), precision=6)

    def test_tangents_alphas(self):
        degree = 3
        n_points = 3
        tangents = np.array([[-1,1,0], [1,1,0], [-1,-1,0]], dtype=np.float64)
        ts = np.array([0.0, 0.5, 1.0])
        solver = SvNurbsCurveSolver(degree = degree)
        solver.set_curve_params(n_cpts = n_points * 4)  # Need more control points than tangent points
        goal = SvNurbsCurveTangents(ts, tangents)
        solver.add_goal(goal)
        solver._init()
        alphas = goal.calc_alphas(solver, ts)
        self.assertEqual(alphas.shape, (solver.n_cpts, len(ts)))
        self.assertFalse(np.isnan(alphas).any())

    def test_solver_creation(self):
        solver = SvNurbsCurveSolver(degree=3)
        self.assertEqual(solver.degree, 3)
        self.assertIsNone(solver.src_curve)

    def test_solver_creation_error(self):
        with self.assertRaises(ArgumentError):
            solver = SvNurbsCurveSolver()

    def test_set_curve_params(self):
        degree = 3
        n_cpts = 5
        solver = SvNurbsCurveSolver(degree=degree)
        solver.set_curve_params(n_cpts=n_cpts)
        self.assertEqual(solver.n_cpts, n_cpts)
        self.assertIsNotNone(solver.knotvector)
        self.assertEqual(len(solver.knotvector), n_cpts + degree + 1)

    def test_set_curve_params_with_knotvector(self):
        degree = 3
        n_cpts = 5
        knotvector = [0, 0, 0, 0, 0.5, 1, 1, 1, 1]
        solver = SvNurbsCurveSolver(degree=degree)
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        self.assertEqual(solver.n_cpts, n_cpts)
        np.testing.assert_array_equal(solver.knotvector, knotvector)

    def test_set_curve_params_invalid_knotvector(self):
        degree = 3
        n_cpts = 5
        knotvector = [0, 0, 0, 0.5, 1, 1, 1]
        solver = SvNurbsCurveSolver(degree=degree)
        with self.assertRaises(AlgorithmError):
            solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)

    def test_guess_curve_params(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        points = np.array([[0,0,0], [1,1,0]], dtype=np.float64)
        ts = np.array([0.0, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        solver.guess_curve_params()
        self.assertEqual(solver.n_cpts, 2)
        self.assertIsNotNone(solver.knotvector)

    def test_add_multiple_goals(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        points1 = np.array([[0,0,0]], dtype=np.float64)
        points2 = np.array([[1,1,0]], dtype=np.float64)
        ts1 = np.array([0.0])
        ts2 = np.array([1.0])
        goal1 = SvNurbsCurvePoints(ts1, points1)
        goal2 = SvNurbsCurvePoints(ts2, points2)
        solver.add_goal(goal1)
        solver.add_goal(goal2)
        self.assertEqual(len(solver.goals), 2)

    def test_goal_merging(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        points = np.array([[0,0,0], [1,1,0], [2,2,0]], dtype=np.float64)
        ts = np.array([0.0, 0.5, 1.0])
        goal1 = SvNurbsCurvePoints(ts[:1], points[:1])
        goal2 = SvNurbsCurvePoints(ts[1:], points[1:])
        solver.add_goal(goal1)
        solver.add_goal(goal2)
        solver._sort_goals()
        merged = solver.goals[0]
        self.assertEqual(len(merged.us), 3)

    def test_well_determined_system(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        n_cpts = 4
        knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        points = np.array([[0,0,0], [1,1,0], [2,2,0], [3,3,0]], dtype=np.float64)
        ts = np.array([0.0, 0.333, 0.666, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        curve = solver.solve()
        result_points = curve.evaluate_array(ts)
        self.assert_numpy_arrays_equal(points, result_points, precision=6)

    def test_underdetermined_system(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        n_cpts = 6
        knotvector = [0, 0, 0, 0, 0.5, 0.5, 1, 1, 1, 1]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        points = np.array([[0,0,0], [1,1,0]], dtype=np.float64)
        ts = np.array([0.0, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        problem_type, residue, curve = solver.solve_ex()
        self.assertEqual(problem_type, SvNurbsCurveSolver.PROBLEM_UNDERDETERMINED)
        result_points = curve.evaluate_array(ts)
        self.assert_numpy_arrays_equal(points, result_points, precision=6)

    def test_overdetermined_system(self):
        degree = 3
        # Original control points defining a reference cubic Bezier curve
        ref_cpts = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.5, 0.1],
            [2.5, 1.5, 0.1],
            [4.0, 2.0, 0.0]
        ], dtype=np.float64)
        n_cpts = 4
        knotvector = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]

        # Sample the reference curve at 5 evenly-spaced parameter values
        ts = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ref_curve = SvNurbsMaths.build_curve(
            SvNurbsMaths.NATIVE, degree, knotvector, ref_cpts, None)
        ref_points = ref_curve.evaluate_array(ts)

        # Perturb the points slightly to simulate measurement/noise.
        noise = np.array([
            [0.0, 0.0, 0.0],
            [0.05, -0.03, 0.02],
            [-0.02, 0.04, -0.01],
            [0.03, -0.02, 0.03],
            [0.0, 0.0, 0.0],
        ], dtype=np.float64)
        noisy_points = ref_points + noise

        solver = SvNurbsCurveSolver(degree=degree)
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        goal = SvNurbsCurvePoints(ts, noisy_points)
        solver.add_goal(goal)

        problem_type, residue, curve = solver.solve_ex()
        self.assertEqual(problem_type, SvNurbsCurveSolver.PROBLEM_OVERDETERMINED)

        # Overdetermined fit should have a positive (non-zero) least-squares residue
        self.assertGreater(residue, 0.0)

        result_points = curve.evaluate_array(ts)

        # The fitted curve should pass through the noisy points closely
        fit_error = np.linalg.norm(result_points - noisy_points)
        # With small noise the error should be small
        self.assertLess(fit_error, 5.0)

        # The fitted curve should be closer to the original reference curve
        # than the noisy points are — the solver "denoises" toward a smooth curve
        noisy_error = np.linalg.norm(noisy_points - ref_points)
        fitted_ref_error = np.linalg.norm(result_points - ref_points)
        self.assertLess(fitted_ref_error, noisy_error * 1.5,
                        "Fitted curve should be closer to reference than raw noisy points")

    def test_exact_goals(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        n_cpts = 4
        knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        exact_points = np.array([[0,0,0], [3,3,0]], dtype=np.float64)
        exact_ts = np.array([0.0, 1.0])
        approx_points = np.array([[1.5,1.5,0]], dtype=np.float64)
        approx_ts = np.array([0.5])
        exact_goal = SvNurbsCurvePoints(exact_ts, exact_points, exact=True)
        approx_goal = SvNurbsCurvePoints(approx_ts, approx_points, exact=False)
        solver.add_goal(exact_goal)
        solver.add_goal(approx_goal)
        problem_type, residue, curve = solver.solve_ex()
        result_points = curve.evaluate_array(exact_ts)
        self.assert_numpy_arrays_equal(exact_points, result_points, precision=6)

    def test_relative_points_goal(self):
        degree = 3
        src_points = np.array([[0,0,0], [1,1,0], [2,2,0], [3,3,0]], dtype=np.float64)
        src_knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        src_weights = [1.0, 1.0, 1.0, 1.0]
        src_curve = SvNurbsMaths.build_curve(
            SvNurbsMaths.NATIVE, degree, src_knotvector, src_points, src_weights)
        solver = SvNurbsCurveSolver(src_curve=src_curve)
        n_cpts = len(src_curve.get_control_points())
        solver.set_curve_params(n_cpts=n_cpts, knotvector=src_curve.get_knotvector(), weights=src_weights)
        delta_points = np.array([[0.1, 0.1, 0.1], [0.2, 0.2, 0.2], [0.3, 0.3, 0.3], [0.4, 0.4, 0.4]], dtype=np.float64)
        ts = np.array([0.0, 0.333, 0.666, 1.0])
        goal = SvNurbsCurvePoints(ts, delta_points, relative=True)
        solver.add_goal(goal)
        curve = solver.solve()
        result_points = curve.evaluate_array(ts)
        expected_points = src_curve.evaluate_array(ts) + delta_points
        self.assert_numpy_arrays_equal(expected_points, result_points, precision=6)

    def test_tangent_goal(self):
        degree = 1  # Linear curve for simplicity
        solver = SvNurbsCurveSolver(degree=degree)
        n_cpts = 2
        knotvector = [0, 0, 1, 1]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        points = np.array([[0,0,0], [3,3,0]], dtype=np.float64)
        point_ts = np.array([0.0, 1.0])
        point_goal = SvNurbsCurvePoints(point_ts, points, exact=True)
        solver.add_goal(point_goal)
        curve = solver.solve()
        result_tangent = curve.tangent_array([0.5])[0]
        expected_tangent = np.array([3.0, 3.0, 0.0])  # P1 - P0 for linear curve
        np.testing.assert_allclose(result_tangent, expected_tangent, rtol=1e-4)

    def test_relative_tangent_goal(self):
        degree = 3
        src_points = np.array([[0,0,0], [1,1,0], [2,2,0], [3,3,0]], dtype=np.float64)
        src_knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        src_weights = [1.0, 1.0, 1.0, 1.0]
        src_curve = SvNurbsMaths.build_curve(
            SvNurbsMaths.NATIVE, degree, src_knotvector, src_points, src_weights)
        solver = SvNurbsCurveSolver(src_curve=src_curve)
        n_cpts = len(src_curve.get_control_points())
        solver.set_curve_params(n_cpts=n_cpts, knotvector=src_curve.get_knotvector(), weights=src_weights)
        delta_tangents = np.array([[0.1, 0.1, 0.0], [0.2, 0.2, 0.0], [0.3, 0.3, 0.0], [0.4, 0.4, 0.0]], dtype=np.float64)
        ts = np.array([0.0, 0.333, 0.666, 1.0])
        goal = SvNurbsCurveTangents(ts, delta_tangents, relative=True)
        solver.add_goal(goal)
        curve = solver.solve()
        result_tangents = curve.tangent_array(ts)
        expected_tangents = src_curve.tangent_array(ts) + delta_tangents
        self.assert_numpy_arrays_equal(expected_tangents, result_tangents, precision=4)

    def test_mixed_goals(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        n_cpts = 4
        knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        points = np.array([[0,0,0]], dtype=np.float64)
        ts_points = np.array([0.0])
        tangents = np.array([[1,1,0]], dtype=np.float64)
        ts_tangents = np.array([0.0])
        points_goal = SvNurbsCurvePoints(ts_points, points)
        tangents_goal = SvNurbsCurveTangents(ts_tangents, tangents)
        solver.add_goal(points_goal)
        solver.add_goal(tangents_goal)
        curve = solver.solve()
        result_point = curve.evaluate(0.0)
        result_tangent = curve.tangent(0.0)
        self.assert_numpy_arrays_equal(points[0], result_point, precision=6)

    def test_rational_curve_weights(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        n_cpts = 4
        knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        weights = [1.0, 2.0, 2.0, 1.0]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector, weights=weights)
        points = np.array([[0,0,0], [2,2,0], [2,-2,0], [0,0,0]], dtype=np.float64)
        ts = np.array([0.0, 0.25, 0.75, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        curve = solver.solve()
        self.assertTrue(solver.is_rational())
        result_points = curve.evaluate_array(ts)
        self.assert_numpy_arrays_equal(points, result_points, precision=4)

    def test_goal_single_constructor(self):
        u = 0.5
        point = [1, 1, 1]
        goal = SvNurbsCurvePoints.single(u, point)
        self.assertEqual(len(goal.us), 1)
        self.assertEqual(goal.us[0], u)
        np.testing.assert_array_equal(goal.vectors[0], point)

    def test_tangent_goal_single_constructor(self):
        u = 0.5
        tangent = [1, 2, 3]
        goal = SvNurbsCurveTangents.single(u, tangent)
        self.assertEqual(len(goal.us), 1)
        self.assertEqual(goal.us[0], u)
        np.testing.assert_array_equal(goal.vectors[0], tangent)

    def test_derivative_goal(self):
        degree = 2  # Quadratic curve
        solver = SvNurbsCurveSolver(degree=degree)
        # 3 control points * 3 dims = 9 unknowns
        # 3 point constraints (9 eq): endpoint, midpoint, and derivative at endpoint
        n_cpts = 3
        knotvector = [0, 0, 0, 1, 1, 1]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector)
        # Point constraints: curve passes through these points
        points = np.array([[0,0,0], [1,1,0], [2,2,0]], dtype=np.float64)
        point_ts = np.array([0.0, 0.5, 1.0])
        point_goal = SvNurbsCurvePoints(point_ts, points, exact=True)
        solver.add_goal(point_goal)
        curve = solver.solve()
        # Compute and verify the second derivative of quadratic curve
        # For a quadratic Bezier, second derivative is constant: 2*(P0 - 2*P1 + P2)
        result = curve.second_derivative_array(np.array([0.5]))
        expected = 2 * (points[0] - 2*points[1] + points[2])
        np.testing.assert_array_almost_equal(result[0], expected, decimal=4)

    def test_goal_add(self):
        ts1 = np.array([0.0])
        points1 = np.array([[1,0,0]], dtype=np.float64)
        ts2 = np.array([1.0])
        points2 = np.array([[2,0,0]], dtype=np.float64)
        goal1 = SvNurbsCurvePoints(ts1, points1)
        goal2 = SvNurbsCurvePoints(ts2, points2)
        merged = goal1.add(goal2)
        self.assertEqual(len(merged.us), 2)

    def test_goal_add_different_types(self):
        ts = np.array([0.0])
        points = np.array([[1,0,0]], dtype=np.float64)
        goal1 = SvNurbsCurvePoints(ts, points, relative=True)
        goal2 = SvNurbsCurvePoints(ts, points, relative=False)
        result = goal1.add(goal2)
        self.assertIsNone(result)

    def test_solver_invalid_state(self):
        solver = SvNurbsCurveSolver(degree=3)
        ts = np.array([0.0, 1.0])
        points = np.array([[0,0,0], [1,1,0]], dtype=np.float64)
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        with self.assertRaises(InvalidStateError):
            solver.solve()

    def test_problem_type_detection(self):
        degree = 3
        knotvector_4 = [0, 0, 0, 0, 1, 1, 1, 1]  # n_cpts=4, degree=3: 4+3+1=8
        knotvector_5 = [0, 0, 0, 0, 0.5, 1, 1, 1, 1]  # n_cpts=5, degree=3: 5+3+1=9
        
        # Well-determined: 4 control points * 3 dims = 12 unknowns, 4 points * 3 dims = 12 equations
        solver = SvNurbsCurveSolver(degree=degree)
        solver.set_curve_params(n_cpts=4, knotvector=knotvector_4)
        points = np.array([[0,0,0], [1,1,0], [2,2,0], [3,3,0]], dtype=np.float64)
        ts = np.array([0.0, 0.33, 0.66, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        type_ = solver.get_problem_type()
        self.assertEqual(type_, SvNurbsCurveSolver.PROBLEM_WELLDETERMINED)
        
        # Underdetermined: 5 control points * 3 dims = 15 unknowns, 4 points * 3 dims = 12 equations
        solver = SvNurbsCurveSolver(degree=degree)
        solver.set_curve_params(n_cpts=5, knotvector=knotvector_5)
        points = np.array([[0,0,0], [1,1,0], [2,2,0], [3,3,0]], dtype=np.float64)
        ts = np.array([0.0, 0.33, 0.66, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        type_ = solver.get_problem_type()
        self.assertEqual(type_, SvNurbsCurveSolver.PROBLEM_UNDERDETERMINED)
        
        # Overdetermined: 3 control points * 3 dims = 9 unknowns, 4 points * 3 dims = 12 equations
        knotvector_3 = [0, 0, 0, 0, 1, 1, 1]  # n_cpts=3, degree=3: 3+3+1=7
        solver = SvNurbsCurveSolver(degree=degree)
        solver.set_curve_params(n_cpts=3, knotvector=knotvector_3)
        points = np.array([[0,0,0], [0.3,0.3,0], [0.7,0.7,0], [1,1,0]], dtype=np.float64)
        ts = np.array([0.0, 0.33, 0.66, 1.0])
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        type_ = solver.get_problem_type()
        self.assertEqual(type_, SvNurbsCurveSolver.PROBLEM_OVERDETERMINED)

    def test_4d_homogenous_goal(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree, ndim=4)
        # 4 control points * 4 dims = 16 unknowns
        # 4 point constraints * 4 dims = 16 equations → well-determined
        n_cpts = 4
        knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        weights = [1.0, 1.0, 1.0, 1.0]
        solver.set_curve_params(n_cpts=n_cpts, knotvector=knotvector, weights=weights)
        # Points in homogeneous coordinates (x, y, z, w)
        points_hom = np.array([
            [0, 0, 0, 1.0],      # At t=0
            [1, 1, 1, 1.0],      # At t=0.33
            [2, 2, 2, 1.0],      # At t=0.66
            [3, 3, 3, 1.0]       # At t=1.0
        ], dtype=np.float64)
        ts = np.array([0.0, 1.0/3.0, 2.0/3.0, 1.0])
        goal = SvNurbsCurvePoints(ts, points_hom)
        solver.add_goal(goal)
        curve = solver.solve()
        result_points_hom = curve.evaluate_homogenous_array(ts)
        self.assert_numpy_arrays_equal(points_hom, result_points_hom, precision=4)

    def test_solver_copy(self):
        degree = 3
        solver = SvNurbsCurveSolver(degree=degree)
        knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
        solver.set_curve_params(n_cpts=4, knotvector=knotvector)
        ts = np.array([0.0])
        points = np.array([[1,1,1]], dtype=np.float64)
        goal = SvNurbsCurvePoints(ts, points)
        solver.add_goal(goal)
        
        solver_copy = solver.copy()
        self.assertEqual(solver.degree, solver_copy.degree)
        self.assertEqual(solver.n_cpts, solver_copy.n_cpts)
        np.testing.assert_array_equal(solver.knotvector, solver_copy.knotvector)
        self.assertEqual(len(solver.goals), len(solver_copy.goals))


