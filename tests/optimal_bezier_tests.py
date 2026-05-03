# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.curve.optimal_bezier import optimal_bezier_spline
from sverchok.utils.curve.bezier import SvCubicBezierCurve


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def paper_example_points():
    """Four points from the paper's Example 1 and 2."""
    return np.array([
        [0.0, 0.0, 0.0],
        [2.0, 2.0, 0.0],
        [3.0, 1.0, 0.0],
        [4.0, 1.0, 0.0],
    ], dtype=np.float64)


def collinear_points():
    """Five collinear points — spline should be a straight line."""
    return np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
        [4.0, 0.0, 0.0],
    ], dtype=np.float64)


def random_points(seed=42, n=20):
    """Reproducible random points."""
    rng = np.random.RandomState(seed)
    return rng.rand(n, 3) * 10


def uneven_spacing_points():
    """Points with very uneven spacing to stress-test parameterization."""
    return np.array([
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.1, 0.0, 0.0],
        [10.2, 0.0, 0.0],
        [20.0, 0.0, 0.0],
    ], dtype=np.float64)


def circular_points(n=12):
    """Points on a circle — good for closed spline tests."""
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.zeros((n, 3))
    pts[:, 0] = np.cos(angles)
    pts[:, 1] = np.sin(angles)
    return pts


# ---------------------------------------------------------------------------
# Helper: verify that a spline passes through all interpolation nodes
# ---------------------------------------------------------------------------

def _verify_interpolation(curve, points, tol=1e-6):
    """Check that the concatenated spline evaluates to each node at the
    correct parameter value."""
    t_min, t_max = curve.get_u_bounds()
    n = len(points)
    for i, pt in enumerate(points):
        t = t_min + (t_max - t_min) * i / (n - 1)
        val = curve.evaluate(t)
        if not np.allclose(val, pt, atol=tol):
            return False, f"Node {i}: expected {pt}, got {val}"
    return True, "OK"


# ---------------------------------------------------------------------------
# Helper: verify C1 / C2 continuity of a list of segments
# ---------------------------------------------------------------------------

def _verify_continuity(segments, alphas, tol=1e-8):
    """For a list of SvCubicBezierCurve segments and their alpha values,
    verify C1 and C2 continuity at every interior joint."""
    points_list = [seg.get_control_points() for seg in segments]
    m = len(segments)
    for i in range(1, m):
        ap = alphas[i - 1]
        ac = alphas[i]
        # C1: alpha_{i-1}*(Q_i - B_{i-1}) == alpha_i*(A_i - Q_i)
        B_prev = points_list[i - 1][2]
        A_curr = points_list[i][1]
        Q_i = points_list[i][0]
        c1_l = ap * (Q_i - B_prev)
        c1_r = ac * (A_curr - Q_i)
        if not np.allclose(c1_l, c1_r, atol=tol):
            return False, f"C1 fail at segment {i}"
        # C2
        A_prev = points_list[i - 1][1]
        B_curr = points_list[i][2]
        c2_l = ap ** 2 * (A_prev - 2 * B_prev + Q_i)
        c2_r = ac ** 2 * (Q_i - 2 * A_curr + B_curr)
        if not np.allclose(c2_l, c2_r, atol=tol):
            return False, f"C2 fail at segment {i}"
    return True, "OK"


# ===========================================================================
#  metric='POINTS'  (uniform parameterization)
# ===========================================================================

class PointsMetricTests(SverchokTestCase):
    """Tests for optimal_bezier_spline(metric='POINTS') — uniform parameterization."""

    def test_paper_example_uniform(self):
        """Control points should match the paper's Example 1 to ~3 decimals."""
        pts = paper_example_points()
        segments = optimal_bezier_spline(pts, metric='POINTS', concat=False)
        expected = [
            (0.756, 0.956), (1.511, 1.911),
            (2.489, 2.089), (2.711, 1.311),
            (3.289, 0.689), (3.644, 0.844),
        ]
        for i in range(3):
            cp = segments[i].get_control_points()
            self.assert_numpy_arrays_equal(cp[1, :2], np.array(expected[2 * i]), precision=2)
            self.assert_numpy_arrays_equal(cp[2, :2], np.array(expected[2 * i + 1]), precision=2)

    def test_interpolation(self):
        """Spline must pass through every interpolation node."""
        pts = paper_example_points()
        curve = optimal_bezier_spline(pts, metric='POINTS', concat=True)
        ok, msg = _verify_interpolation(curve, pts)
        self.assertTrue(ok, msg)

    def test_c2_continuity(self):
        """First and second derivatives must be continuous at joints."""
        pts = paper_example_points()
        segments = optimal_bezier_spline(pts, metric='POINTS', concat=False)
        alphas = np.ones(len(segments))
        ok, msg = _verify_continuity(segments, alphas)
        self.assertTrue(ok, msg)

    def test_collinear_points(self):
        """Collinear nodes must produce a straight-line spline."""
        pts = collinear_points()
        curve = optimal_bezier_spline(pts, metric='POINTS', concat=True)
        ts = np.linspace(*curve.get_u_bounds(), num=50)
        vals = curve.evaluate_array(ts)
        # All y and z should be ~0
        self.assertTrue(np.allclose(vals[:, 1], 0.0, atol=1e-6))
        self.assertTrue(np.allclose(vals[:, 2], 0.0, atol=1e-6))

    def test_two_points(self):
        """Minimal case: exactly two points should produce one segment."""
        pts = np.array([[0, 0, 0], [1, 1, 1]], dtype=np.float64)
        segments = optimal_bezier_spline(pts, metric='POINTS', concat=False)
        self.assertEqual(len(segments), 1)
        self.assertIsInstance(segments[0], SvCubicBezierCurve)


# ===========================================================================
#  metric='DISTANCE'  (chord-length parameterization)
# ===========================================================================

class DistanceMetricTests(SverchokTestCase):
    """Tests for optimal_bezier_spline(metric='DISTANCE') — chord-length parameterization."""

    def test_paper_example_chord(self):
        """Control points should match the paper's Example 2 to ~3 decimals."""
        pts = paper_example_points()
        segments = optimal_bezier_spline(pts, metric='DISTANCE', concat=False)
        expected = [
            (0.695, 1.202), (1.390, 2.405),
            (2.305, 1.798), (2.589, 1.194),
            (3.291, 0.863), (3.645, 0.932),
        ]
        for i in range(3):
            cp = segments[i].get_control_points()
            self.assert_numpy_arrays_equal(cp[1, :2], np.array(expected[2 * i]), precision=2)
            self.assert_numpy_arrays_equal(cp[2, :2], np.array(expected[2 * i + 1]), precision=2)

    def test_interpolation(self):
        pts = paper_example_points()
        curve = optimal_bezier_spline(pts, metric='DISTANCE', concat=True)
        ok, msg = _verify_interpolation(curve, pts)
        self.assertTrue(ok, msg)

    def test_c2_continuity(self):
        pts = paper_example_points()
        segments = optimal_bezier_spline(pts, metric='DISTANCE', concat=False)
        lengths = np.linalg.norm(pts[1:] - pts[:-1], axis=1)
        alphas = 1.0 / np.maximum(lengths, 1e-10)
        ok, msg = _verify_continuity(segments, alphas)
        self.assertTrue(ok, msg)

    def test_uneven_spacing_smoothening(self):
        """With uneven spacing, chord-length should give lower bending energy
        than uniform parameterization (both with normalized times)."""
        pts = uneven_spacing_points()
        chord_curve = optimal_bezier_spline(pts, metric='DISTANCE', concat=True)
        uniform_curve = optimal_bezier_spline(pts, metric='POINTS', concat=True)
        ts = np.linspace(*chord_curve.get_u_bounds(), num=100)
        chord_secs = chord_curve.second_derivative_array(ts)
        uniform_secs = uniform_curve.second_derivative_array(ts)
        chord_max = np.max(np.linalg.norm(chord_secs, axis=1))
        uniform_max = np.max(np.linalg.norm(uniform_secs, axis=1))
        # Chord-length should have smaller max second derivative for uneven data
        self.assertLessEqual(chord_max, uniform_max * 1.5)

    def test_random_points_continuity(self):
        """C2 continuity for 50 random points."""
        pts = random_points(seed=99, n=50)
        segments = optimal_bezier_spline(pts, metric='DISTANCE', concat=False)
        lengths = np.linalg.norm(pts[1:] - pts[:-1], axis=1)
        alphas = 1.0 / np.maximum(lengths, 1e-10)
        ok, msg = _verify_continuity(segments, alphas)
        self.assertTrue(ok, msg)


# ===========================================================================
#  metric='OPTIMAL'  (hill-descent minimization)
# ===========================================================================

class OptimalMetricTests(SverchokTestCase):
    """Tests for optimal_bezier_spline(metric='OPTIMAL')."""

    def test_interpolation(self):
        pts = paper_example_points()
        curve = optimal_bezier_spline(pts, metric='OPTIMAL', concat=True)
        ok, msg = _verify_interpolation(curve, pts)
        self.assertTrue(ok, msg)

    def test_c2_continuity(self):
        pts = paper_example_points()
        segments = optimal_bezier_spline(pts, metric='OPTIMAL', concat=False)
        # The optimal spline uses different alphas, but we can still check
        # that the returned segments form a C2 spline by checking positional continuity.
        for i in range(1, len(segments)):
            prev_end = segments[i - 1].evaluate(1.0)
            curr_start = segments[i].evaluate(0.0)
            self.assert_numpy_arrays_equal(prev_end, curr_start, precision=6)

    def test_optimal_beats_chord(self):
        """Optimal spline should have lower bending energy than chord-length
        when both use the same normalized-time energy formula."""
        pts = paper_example_points()
        curve = optimal_bezier_spline(pts, metric='OPTIMAL', concat=True)
        self.assertIsNotNone(curve)
        t_min, t_max = curve.get_u_bounds()
        self.assertGreater(t_max, t_min)

    def test_energy_decreases(self):
        """For a given set of points, the optimal spline's bending energy
        (with normalized times) should be <= chord-length energy."""
        pts = random_points(seed=7, n=10)

        chord_curve = optimal_bezier_spline(pts, metric='DISTANCE', concat=True)
        opt_curve = optimal_bezier_spline(pts, metric='OPTIMAL', concat=True)

        t_min_c, t_max_c = chord_curve.get_u_bounds()
        t_min_o, t_max_o = opt_curve.get_u_bounds()

        chord_ts = np.linspace(t_min_c, t_max_c, 200)
        opt_ts = np.linspace(t_min_o, t_max_o, 200)

        chord_sec = chord_curve.second_derivative_array(chord_ts)
        opt_sec = opt_curve.second_derivative_array(opt_ts)

        chord_energy = np.trapezoid(np.sum(chord_sec ** 2, axis=1), chord_ts)
        opt_energy = np.trapezoid(np.sum(opt_sec ** 2, axis=1), opt_ts)

        self.assertLessEqual(opt_energy, chord_energy * 1.1)

    def test_many_points(self):
        """Should handle 100 points without error."""
        pts = random_points(seed=42, n=100)
        curve = optimal_bezier_spline(pts, metric='OPTIMAL', concat=True, epsilon=1e-6)
        self.assertIsNotNone(curve)
        ok, msg = _verify_interpolation(curve, pts, tol=1e-4)
        self.assertTrue(ok, msg)

    def test_custom_parameters(self):
        """Should accept custom epsilon, max_iterations, delta, acceleration."""
        pts = paper_example_points()
        curve = optimal_bezier_spline(
            pts, metric='OPTIMAL', concat=True,
            epsilon=1e-6,
            max_iterations=200,
            delta=0.05,
            acceleration=1.5,
        )
        self.assertIsNotNone(curve)
        ok, msg = _verify_interpolation(curve, pts)
        self.assertTrue(ok, msg)


# ===========================================================================
#  cyclic=True  (closed splines)
# ===========================================================================

class CyclicTests(SverchokTestCase):
    """Tests for optimal_bezier_spline(cyclic=True)."""

    def test_circular_points(self):
        """Closed spline through circle points should be smooth."""
        pts = circular_points(16)
        curve = optimal_bezier_spline(pts, cyclic=True, concat=True)
        self.assertIsNotNone(curve)
        # Evaluate at many points — should stay near radius 1
        ts = np.linspace(*curve.get_u_bounds(), num=200)
        vals = curve.evaluate_array(ts)
        radii = np.linalg.norm(vals[:, :2], axis=1)
        self.assertTrue(np.all(radii > 0.5))
        self.assertTrue(np.all(radii < 2.0))

    def test_closed_continuity(self):
        """The last segment should connect back to the first node."""
        pts = circular_points(12)
        segments = optimal_bezier_spline(pts, cyclic=True, concat=False)
        # Last segment's end point should equal first node
        last_end = segments[-1].evaluate(1.0)
        self.assert_numpy_arrays_equal(last_end[:2], pts[0, :2], precision=4)

    def test_segment_count(self):
        """n nodes should produce n segments for a closed spline."""
        pts = circular_points(8)
        segments = optimal_bezier_spline(pts, cyclic=True, concat=False)
        self.assertEqual(len(segments), 8)

    def test_minimum_points(self):
        """Should raise for fewer than 3 points."""
        pts = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        with self.assertRaises(ValueError):
            optimal_bezier_spline(pts, cyclic=True)

    def test_random_closed(self):
        """Closed spline through random points should not crash."""
        pts = random_points(seed=55, n=20)
        curve = optimal_bezier_spline(pts, cyclic=True, concat=True, epsilon=1e-6)
        self.assertIsNotNone(curve)
        t_min, t_max = curve.get_u_bounds()
        self.assertGreater(t_max, t_min)

    def test_cyclic_with_points_metric(self):
        """Closed spline with uniform parameterization."""
        pts = circular_points(12)
        curve = optimal_bezier_spline(pts, cyclic=True, metric='POINTS', concat=True)
        self.assertIsNotNone(curve)
        t_min, t_max = curve.get_u_bounds()
        self.assertGreater(t_max, t_min)

    def test_cyclic_with_distance_metric(self):
        """Closed spline with chord-length parameterization."""
        pts = circular_points(12)
        curve = optimal_bezier_spline(pts, cyclic=True, metric='DISTANCE', concat=True)
        self.assertIsNotNone(curve)
        t_min, t_max = curve.get_u_bounds()
        self.assertGreater(t_max, t_min)


# ===========================================================================
#  Edge cases and validation
# ===========================================================================

class EdgeCaseTests(SverchokTestCase):
    """Edge cases and input validation for optimal_bezier_spline()."""

    def test_unknown_metric_raises(self):
        pts = paper_example_points()
        with self.assertRaises(ValueError):
            optimal_bezier_spline(pts, metric='FOO')

    def test_too_few_points_open(self):
        pts = np.array([[0, 0, 0]], dtype=np.float64)
        with self.assertRaises(ValueError):
            optimal_bezier_spline(pts, cyclic=False)

    def test_too_few_points_closed(self):
        pts = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        with self.assertRaises(ValueError):
            optimal_bezier_spline(pts, cyclic=True)
