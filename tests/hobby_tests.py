# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Tests for utils/curve/hobby.py — Hobby interpolating splines.

Tests verify the Hobby curve algorithm as implemented in MetaPost:
- Interpolation through all knot points
- G1 continuity at interior knots
- Symmetry for symmetric inputs
- Proper handling of cyclic and open curves
"""

import numpy as np

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.curve.hobby import hobby_curve


class HobbyThreePointsSymmetryTests(SverchokTestCase):
    """
    Simple test for a Hobby curve through three symmetric points:
        [-1, 0, 0], [0, 1, 0], [1, 0, 0]

    Expected properties:
    * Two Bezier segments
    * G1 continuity at the middle knot (shared tangent direction)
    * Horizontal tangent at the middle knot: [x, 0, 0], x > 0
    * Symmetric control points
    """

    def test_three_points_symmetric(self):
        points = np.array([
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 1.0, 0.0, 0.0],
        ])

        segments = hobby_curve(points, cyclic=False, concat=False)
        self.assertEqual(len(segments), 2)

        seg0 = segments[0]
        seg1 = segments[1]

        # --- 1. G1 continuity at the middle knot ---
        t_end = seg0.tangent(1.0)
        t_start = seg1.tangent(0.0)

        # Directions should match
        dir_end = t_end / np.linalg.norm(t_end)
        dir_start = t_start / np.linalg.norm(t_start)
        angle = np.arccos(np.clip(np.dot(dir_end, dir_start), -1.0, 1.0))
        self.assertAlmostEqual(
            angle, 0.0, places=10,
            msg=f"G1 break at middle knot: angle = {np.degrees(angle):.6f}°"
        )

        # --- 2. Tangent is horizontal [x, 0, 0], x > 0 ---
        self.assertGreater(
            abs(t_start[0]), 1e-10,
            msg=f"Tangent x-component is near zero: {t_start}"
        )
        self.assertAlmostEqual(
            t_start[1], 0.0, places=10,
            msg=f"Tangent y-component should be ~0: {t_start[1]}"
        )
        self.assertAlmostEqual(
            t_start[2], 0.0, places=10,
            msg=f"Tangent z-component should be ~0: {t_start[2]}"
        )
        self.assertGreater(
            t_start[0], 0.0,
            msg=f"Tangent x-component should be positive: {t_start[0]}"
        )

        # --- 3. Symmetric control points ---
        # seg0: p0=[-1,0,0], p1, p2, p3=[0,1,0]
        # seg1: p0=[0,1,0], p1, p2, p3=[1,0,0]
        # Symmetry about x=0: p1_seg1 should be mirror of p2_seg0, etc.

        # Control points
        s0_p0, s0_p1, s0_p2, s0_p3 = seg0.p0, seg0.p1, seg0.p2, seg0.p3
        s1_p0, s1_p1, s1_p2, s1_p3 = seg1.p0, seg1.p1, seg1.p2, seg1.p3

        # Mirror transform: (x, y, z) -> (-x, y, z)
        def mirror(p):
            return np.array([-p[0], p[1], p[2]])

        # Symmetry: seg1 control points should be mirror of seg0 (reversed)
        self.assert_numpy_arrays_equal(
            s1_p0, mirror(s0_p3), precision=6,
            fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1_p1, mirror(s0_p2), precision=6,
            fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1_p2, mirror(s0_p1), precision=6,
            fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1_p3, mirror(s0_p0), precision=6,
            fail_fast=True
        )

    def test_three_points_concat(self):
        """Same test but with concat=True."""
        points = np.array([
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 1.0, 0.0, 0.0],
        ])

        curve = hobby_curve(points, cyclic=False, concat=True)
        u_min, u_max = curve.get_u_bounds()

        # Evaluate at the join point (t = 0.5 * u_max)
        t_join = 0.5 * u_max
        pt_join = curve.evaluate(t_join)
        self.assert_numpy_arrays_equal(
            pt_join, np.array([0.0, 1.0, 0.0]), precision=6,
            fail_fast=True
        )

        # Tangent at join should be horizontal
        t_vec = curve.tangent(t_join)
        self.assertAlmostEqual(
            t_vec[1], 0.0, places=10,
            msg=f"Tangent y at join should be ~0: {t_vec[1]}"
        )
        self.assertGreater(
            t_vec[0], 0.0,
            msg=f"Tangent x at join should be positive: {t_vec[0]}"
        )


class HobbyInterpolationTests(SverchokTestCase):
    """
    Verify that the Hobby curve passes through all knot points.
    """

    def test_open_interpolation(self):
        """Non-cyclic curve must pass through all input points."""
        np.random.seed(42)
        points = np.random.rand(8, 3) * 2
        segments = hobby_curve(points, cyclic=False, concat=True)

        for i, pt in enumerate(points):
            t = i / (len(points) - 1) * segments.get_u_bounds()[1]
            actual = segments.evaluate(t)
            error = np.linalg.norm(actual[:2] - pt[:2])
            self.assertLess(
                error, 1e-10,
                msg=f"Knot {i} not on curve: error={error:.2e}"
            )

    def test_cyclic_interpolation(self):
        """Cyclic curve must pass through all input points."""
        np.random.seed(42)
        points = np.random.rand(8, 3) * 2
        segments = hobby_curve(points, cyclic=True, concat=True)

        for i, pt in enumerate(points):
            t = i / len(points) * segments.get_u_bounds()[1]
            actual = segments.evaluate(t)
            error = np.linalg.norm(actual[:2] - pt[:2])
            self.assertLess(
                error, 1e-10,
                msg=f"Knot {i} not on curve: error={error:.2e}"
            )


class HobbyCyclicTests(SverchokTestCase):
    """
    Verify cyclic curve properties.
    """

    def test_cyclic_segment_count(self):
        """Cyclic curve with n points produces n segments."""
        for n in [3, 4, 5, 8]:
            points = np.random.rand(n, 3) * 2
            segments = hobby_curve(points, cyclic=True, concat=False)
            self.assertEqual(
                len(segments), n,
                msg=f"Cyclic with {n} points: got {len(segments)} segments"
            )

    def test_cyclic_closed(self):
        """Concatenated cyclic curve must be closed."""
        points = np.random.rand(5, 3) * 2
        curve = hobby_curve(points, cyclic=True, concat=True)
        self.assertTrue(curve.is_closed())

    def test_cyclic_g1_continuity(self):
        """Cyclic curve must have G1 continuity at all knots."""
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.5, 0.0],
            [2.0, 0.0, 0.0],
            [2.5, 1.0, 0.0],
        ])
        segments = hobby_curve(points, cyclic=True, concat=False)

        for i in range(len(segments)):
            t_end = segments[i].tangent(1.0)
            next_idx = (i + 1) % len(segments)
            t_start = segments[next_idx].tangent(0.0)

            dir_end = t_end / np.linalg.norm(t_end)
            dir_start = t_start / np.linalg.norm(t_start)
            angle = np.arccos(np.clip(np.dot(dir_end, dir_start), -1.0, 1.0))
            self.assertLess(
                angle, 1e-6,
                msg=f"G1 break at knot {next_idx}: angle={np.degrees(angle):.6f}°"
            )


class HobbyEdgeCasesTests(SverchokTestCase):
    """
    Test edge cases and error handling.
    """

    def test_two_points(self):
        """Two points produce one segment."""
        points = [np.array([0.0, 0.0, 0.0]), np.array([1.0, 1.0, 0.0])]
        segments = hobby_curve(points, cyclic=False, concat=False)
        self.assertEqual(len(segments), 1)

    def test_one_point_raises(self):
        """One point raises ValueError."""
        with self.assertRaises(ValueError):
            hobby_curve([np.array([0.0, 0.0, 0.0])])

    def test_cyclic_two_points_raises(self):
        """Cyclic with 2 points raises ValueError."""
        points = [np.array([0.0, 0.0, 0.0]), np.array([1.0, 1.0, 0.0])]
        with self.assertRaises(ValueError):
            hobby_curve(points, cyclic=True)

    def test_z_ignored(self):
        """Z coordinate is ignored; only X and Y matter."""
        points_xy = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.5, 0.0]),
            np.array([2.0, 0.0, 0.0]),
        ]
        points_z = [
            np.array([0.0, 0.0, 5.0]),
            np.array([1.0, 0.5, 10.0]),
            np.array([2.0, 0.0, 15.0]),
        ]
        segs_xy = hobby_curve(points_xy, cyclic=False, concat=False)
        segs_z = hobby_curve(points_z, cyclic=False, concat=False)

        # XY control points should be identical
        for i in range(len(segs_xy)):
            self.assert_numpy_arrays_equal(
                segs_xy[i].get_control_points()[:, :2],
                segs_z[i].get_control_points()[:, :2],
                precision=10,
                fail_fast=True
            )
