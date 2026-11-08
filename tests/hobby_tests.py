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


class HobbyMetaPostReferenceTests(SverchokTestCase):
    """
    Verify exact control point coordinates against MetaPost 2.11 output.
    All values from mpost-generated SVG with 6 decimal places.
    """

    def test_1b_four_points(self):
        """Test 1b: 4 points, standard params.

        Input: [(0,0), (1,1), (2,0), (3,1)]
        Expected: 3 Bezier segments with exact control points.
        """
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 1.0, 0.0],
        ])
        segments = hobby_curve(points, cyclic=False, concat=False)
        self.assertEqual(len(segments), 3)

        # Seg0: P0=(0,0), P1=(-0.260941, 0.629960), P2=(0.370040, 1.260941), P3=(1,1)
        s0 = segments[0]
        self.assert_numpy_arrays_equal(
            s0.p0[:2], np.array([0.0, 0.0]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-0.260941, 0.629960]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([0.370040, 1.260941]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p3[:2], np.array([1.0, 1.0]), precision=5, fail_fast=True
        )

        # Seg1: P0=(0,0), P1=(1.452758, 0.812470), P2=(1.547242, 0.187530), P3=(2,0)
        s1 = segments[1]
        self.assert_numpy_arrays_equal(
            s1.p1[:2], np.array([1.452758, 0.812470]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1.p2[:2], np.array([1.547242, 0.187530]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1.p3[:2], np.array([2.0, 0.0]), precision=5, fail_fast=True
        )

        # Seg2: P0=(0,0), P1=(2.629960, -0.260941), P2=(3.260941, 0.370040), P3=(3,1)
        s2 = segments[2]
        self.assert_numpy_arrays_equal(
            s2.p1[:2], np.array([2.629960, -0.260941]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s2.p2[:2], np.array([3.260941, 0.370040]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s2.p3[:2], np.array([3.0, 1.0]), precision=5, fail_fast=True
        )

    def test_2a_cyclic_four_points(self):
        """Test 2a: cyclic 4 points (diamond).

        Input: [(-1,0), (0,1), (1,0), (0,-1)]
        Expected: 4 Bezier segments.
        """
        points = np.array([
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 1.0, 0.0, 0.0],
            [ 0.0,-1.0, 0.0],
        ])
        segments = hobby_curve(points, cyclic=True, concat=False)
        self.assertEqual(len(segments), 4)

        # Seg0: P0=(-1,0), P1=(-1, 0.552292), P2=(-0.552292, 1), P3=(0,1)
        s0 = segments[0]
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.0, 0.552292]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.552292, 1.0]), precision=5, fail_fast=True
        )

        # Seg2: P0=(-1,0), P1=(1, -0.552292), P2=(0.552292, -1), P3=(0,-1)
        s2 = segments[2]
        self.assert_numpy_arrays_equal(
            s2.p1[:2], np.array([1.0, -0.552292]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s2.p2[:2], np.array([0.552292, -1.0]), precision=5, fail_fast=True
        )

    def test_2b_square_cyclic(self):
        """Test 2b: square cyclic [ (1,0), (0,1), (-1,0), (0,-1) ].

        Expected: 4 segments, first starts at (1,0).
        """
        points = np.array([
            [ 1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
            [ 0.0,-1.0, 0.0],
        ])
        segments = hobby_curve(points, cyclic=True, concat=False)
        self.assertEqual(len(segments), 4)

        # First segment starts at (1,0)
        s0 = segments[0]
        self.assert_numpy_arrays_equal(
            s0.p0[:2], np.array([1.0, 0.0]), precision=5, fail_fast=True
        )
        # P1=(1, 0.552292), P2=(0.552292, 1), P3=(0,1)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([1.0, 0.552292]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([0.552292, 1.0]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p3[:2], np.array([0.0, 1.0]), precision=5, fail_fast=True
        )

    def test_9a_metapost_exact_reference(self):
        """Test 9a: exact MetaPost reference for 3 symmetric points.

        Input: [(-1,0), (0,1), (1,0)]
        Expected: control points match MetaPost SVG to 5 decimal places.
        """
        points = np.array([
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 1.0, 0.0, 0.0],
        ])
        segments = hobby_curve(points, cyclic=False, concat=False)
        self.assertEqual(len(segments), 2)

        s0, s1 = segments[0], segments[1]

        # Seg0: P0=(-1,0), P1=(-1, 0.552292), P2=(-0.552292, 1), P3=(0,1)
        self.assert_numpy_arrays_equal(
            s0.p0[:2], np.array([-1.0, 0.0]), precision=6, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.0, 0.552292]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.552292, 1.0]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p3[:2], np.array([0.0, 1.0]), precision=6, fail_fast=True
        )

        # Seg1: P0=(-1,0) in segment coords = (0,1) in global
        # P1=(0.552292, 1), P2=(1, 0.552292), P3=(1,0)
        self.assert_numpy_arrays_equal(
            s1.p0[:2], np.array([0.0, 1.0]), precision=6, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1.p1[:2], np.array([0.552292, 1.0]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1.p2[:2], np.array([1.0, 0.552292]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1.p3[:2], np.array([1.0, 0.0]), precision=6, fail_fast=True
        )


class HobbyTensionTests(SverchokTestCase):
    """
    Test tension parameter effects. Higher tension = straighter curve.
    All values from MetaPost 2.11.
    """

    def _get_segments(self, tension):
        points = np.array([
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 1.0, 0.0, 0.0],
        ])
        return hobby_curve(points, cyclic=False, concat=False, tension=tension)

    def test_6a_tension_075(self):
        """Test 6a: tension=0.75 (max softness)."""
        segs = self._get_segments(0.75)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-1, 0.736374), P2=(-0.736374, 1)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.0, 0.736374]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.736374, 1.0]), precision=5, fail_fast=True
        )

    def test_6c_tension_2(self):
        """Test 6c: tension=2.0 (stiffer)."""
        segs = self._get_segments(2.0)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-1, 0.276138), P2=(-0.276138, 1)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.0, 0.276138]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.276138, 1.0]), precision=5, fail_fast=True
        )

    def test_6d_tension_5(self):
        """Test 6d: tension=5.0 (very stiff)."""
        segs = self._get_segments(5.0)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-1, 0.110458), P2=(-0.110458, 1)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.0, 0.110458]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.110458, 1.0]), precision=5, fail_fast=True
        )

    def test_6e_tension_10(self):
        """Test 6e: tension=10.0 (nearly polyline)."""
        segs = self._get_segments(10.0)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-1, 0.055222), P2=(-0.055222, 1)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.0, 0.055222]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.055222, 1.0]), precision=5, fail_fast=True
        )

    def test_tension_monotonic(self):
        """Control point distance decreases monotonically with tension."""
        tensions = [0.75, 1.0, 2.0, 5.0, 10.0]
        distances = []
        for t in tensions:
            segs = self._get_segments(t)
            # Distance of P1 from P0 (vertical, since P0=(-1,0), P1=(-1, y))
            dist = abs(segs[0].p1[1] - segs[0].p0[1])
            distances.append(dist)

        # Each successive tension should give smaller distance
        for i in range(len(distances) - 1):
            self.assertGreater(
                distances[i], distances[i + 1],
                msg=f"Tension {tensions[i]} dist={distances[i]:.6f} "
                    f"should be > tension {tensions[i+1]} dist={distances[i+1]:.6f}"
            )


class HobbyCurlTests(SverchokTestCase):
    """
    Test curl parameter effects. curl=0 → tangent along polyline.
    All values from MetaPost 2.11.
    """

    def _get_segments(self, curl_start=1.0, curl_end=1.0):
        points = np.array([
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 1.0, 0.0, 0.0],
        ])
        return hobby_curve(points, cyclic=False, concat=False,
                           curl_start=curl_start, curl_end=curl_end)

    def test_7a_curl_start_zero(self):
        """Test 7a: curl_start=0 (horizontal tangent at start)."""
        segs = self._get_segments(curl_start=0.0, curl_end=1.0)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-0.770844, 0.449753)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-0.770844, 0.449753]), precision=5, fail_fast=True
        )
        # P2=(-0.492004, 0.922074)
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.492004, 0.922074]), precision=5, fail_fast=True
        )

    def test_7b_curl_end_zero(self):
        """Test 7b: curl_end=0 (horizontal tangent at end)."""
        segs = self._get_segments(curl_start=1.0, curl_end=0.0)
        self.assertEqual(len(segs), 2)
        s1 = segs[1]
        # P1=(0.492004, 0.922074), P2=(0.770843, 0.449753)
        self.assert_numpy_arrays_equal(
            s1.p1[:2], np.array([0.492004, 0.922074]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s1.p2[:2], np.array([0.770843, 0.449753]), precision=5, fail_fast=True
        )

    def test_7c_both_curls_zero(self):
        """Test 7c: both curls=0."""
        segs = self._get_segments(curl_start=0.0, curl_end=0.0)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-0.797089, 0.489883), P2=(-0.508072, 1)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-0.797089, 0.489883]), precision=5, fail_fast=True
        )
        self.assert_numpy_arrays_equal(
            s0.p2[:2], np.array([-0.508072, 1.0]), precision=5, fail_fast=True
        )

    def test_7d_large_curl(self):
        """Test 7d: curl=10 (large curl, control points outside polyline)."""
        segs = self._get_segments(curl_start=10.0, curl_end=10.0)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-1.294174, 0.440262) — x < -1, outside the segment
        self.assertLess(
            s0.p1[0], -1.0,
            msg=f"P1.x={s0.p1[0]:.6f} should be < -1 for large curl"
        )
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-1.294174, 0.440262]), precision=5, fail_fast=True
        )

    def test_7e_small_curl(self):
        """Test 7e: curl=0.1 (very small curl, nearly straight)."""
        segs = self._get_segments(curl_start=0.1, curl_end=0.1)
        self.assertEqual(len(segs), 2)
        s0 = segs[0]
        # P1=(-0.823364, 0.504807)
        self.assert_numpy_arrays_equal(
            s0.p1[:2], np.array([-0.823364, 0.504807]), precision=5, fail_fast=True
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
        """Planar curves with constant Z offset produce identical XY results.

        In the 3D implementation, each triple of points defines a local plane.
        For planar curves (all points in the same plane), the local planes
        are identical regardless of the Z offset, so XY control points match.
        Non-planar curves (varying Z) produce different results.
        """
        points_xy = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.5, 0.0]),
            np.array([2.0, 0.0, 0.0]),
        ]
        # Same XY shape, constant Z offset (still planar)
        points_z = [
            np.array([0.0, 0.0, 5.0]),
            np.array([1.0, 0.5, 5.0]),
            np.array([2.0, 0.0, 5.0]),
        ]
        segs_xy = hobby_curve(points_xy, cyclic=False, concat=False)
        segs_z = hobby_curve(points_z, cyclic=False, concat=False)

        # XY control points should be identical for planar curves
        for i in range(len(segs_xy)):
            self.assert_numpy_arrays_equal(
                segs_xy[i].get_control_points()[:, :2],
                segs_z[i].get_control_points()[:, :2],
                precision=10,
                fail_fast=True
            )
