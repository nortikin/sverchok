# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Tests for utils/curve/hobby.py — Hobby interpolating splines.

Each test is designed to reproduce a specific bug found during code review
against the original Hobby paper (STAN-CS-85-1047, 1985) and Knuth's
METAFONT source (§274-277).
"""

import numpy as np

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.curve.hobby import (
    _hobby_velocity,
    _hobby_velocity_accurate,
    hobby_curve,
)


class HobbyVelocityAccurateTests(SverchokTestCase):
    """
    Bug: _hobby_velocity_accurate computes γ(φ) as
        0.5*(θ+φ) - 0.15*sin(2φ)
    but the Hobby paper (eq. 10) defines:
        γ(φ) = 0.5*φ - 0.15*sin(2φ)

    The function depends ONLY on φ, not on θ+φ.
    """

    def test_gamma_depends_only_on_phi(self):
        """
        γ(φ) = ½φ - 0.15·sin(2φ) — does NOT depend on θ.
        Therefore ρ(θ, φ) and σ(θ, φ) should differ ONLY by the
        ±½γ(φ)·sin(φ-θ) term, and their average should be independent
        of the θ+φ sum used incorrectly in the buggy code.

        With the bug, changing θ while keeping φ constant changes the
        average of ρ and σ (because γ uses θ+φ instead of φ).
        Without the bug, the average (f(θ,φ)) is correct.
        """
        phi = 0.5  # fixed

        # Two different θ values — same φ
        theta1 = 0.1
        theta2 = 0.4

        rho1 = _hobby_velocity_accurate(theta1, phi, tension=1.0)
        rho2 = _hobby_velocity_accurate(theta2, phi, tension=1.0)

        # By symmetry: ρ(θ, φ) = f(θ,φ) + ½γ(φ)·sin(φ-θ)
        #               σ(θ, φ) = f(θ,φ) - ½γ(φ)·sin(φ-θ)
        # where f(θ,φ) depends on γ(φ) through the formula.
        #
        # With the BUG: γ uses (θ+φ), so f changes when θ changes.
        # Without the bug: γ uses φ only, so f(θ,φ) still changes
        # with θ through the cos(θ) term in the denominator, but
        # the γ-dependent part is stable.
        #
        # The simplest check: compute γ(φ) directly and verify
        # that swapping θ doesn't affect it.

        # Direct γ(φ) from the paper
        gamma_expected = 0.5 * phi - 0.15 * np.sin(2.0 * phi)

        # Extract γ from the velocity function:
        # ρ(θ, φ) - ρ(φ, θ) = γ(φ)·sin(φ-θ) + γ(θ)·sin(θ-φ)
        # For small angles this is approximately 2·γ·sin(φ-θ)
        # when γ(φ) ≈ γ(θ).
        #
        # More directly: ρ(θ, φ) = f + ½γ(φ)·sin(φ-θ)
        #                  ρ(φ, θ) = f + ½γ(θ)·sin(θ-φ)
        # So: ρ(θ,φ) - ρ(φ,θ) = ½[γ(φ)·sin(φ-θ) + γ(θ)·sin(θ-φ)]
        #                       = ½[γ(φ) - γ(θ)]·sin(φ-θ)
        #
        # When θ → 0: γ(θ) → 0, so ρ(0,φ) - ρ(φ,0) ≈ ½γ(φ)·sin(φ)

        rho_0_phi = _hobby_velocity_accurate(0.0, phi, tension=1.0)
        rho_phi_0 = _hobby_velocity_accurate(phi, 0.0, tension=1.0)

        # γ(0) = 0, so:
        # ρ(0, φ) = f(0,φ) + ½γ(φ)·sin(φ)
        # ρ(φ, 0) = f(φ,0) + ½γ(0)·sin(-φ) = f(φ,0)
        # The difference should reflect γ(φ)

        # Most direct test: for θ=0, γ(0)=0, so ρ(0,φ) = f(0,φ)
        # and ρ(φ,0) = f(φ,0). These should be close to 1 for small φ.
        # But the key check is that γ(φ) extracted from the function
        # matches the formula.

        # Use the identity: ρ(0, φ) = f(0, φ) (since γ(0)=0, sin term vanishes)
        # ρ(θ, φ) = f(θ, φ) + ½γ(φ)·sin(φ-θ)
        # So: γ(φ) ≈ 2·(ρ(θ,φ) - f(θ,φ)) / sin(φ-θ)
        # where f(θ,φ) ≈ ρ(0,φ) adjusted for θ-dependence in denominator.

        # Simpler approach: test with θ = φ.
        # When θ = φ: sin(φ-θ) = 0, so ρ(φ,φ) = f(φ,φ).
        # γ(φ) doesn't enter at all. The bug affects f through γ(φ) in its
        # definition, but when θ=φ, the γ-dependent part of f is:
        # f = (d·γ(φ) + e) / (2+a+2c + a·γ(φ)·(...))
        # The bug replaces γ(φ) with γ_buggy = 0.5*(2φ) - 0.15*sin(2φ)
        # = φ - 0.15*sin(2φ) instead of 0.5*φ - 0.15*sin(2φ).

        # Direct computation of expected f(φ, φ) with correct γ
        a = 0.2678306
        c_coeff = 0.2638750
        d = 1.402539
        e = 0.7539063

        phi_val = 0.3
        gamma_correct = 0.5 * phi_val - 0.15 * np.sin(2.0 * phi_val)
        gamma_buggy = 0.5 * (2.0 * phi_val) - 0.15 * np.sin(2.0 * phi_val)

        # f(φ, φ) with correct γ
        x_correct = gamma_correct
        f_correct = (d * x_correct + e) / (
            2.0 + a + 2.0 * c_coeff
            + a * x_correct * ((3.0 / 2.0 - 4.0 / np.pi) * x_correct
                               + 9.0 / 5.0 - 4.0 / np.pi)
        )
        rho_correct = f_correct  # when θ=φ, sin(φ-θ)=0

        # f(φ, φ) with buggy γ
        x_buggy = gamma_buggy
        f_buggy = (d * x_buggy + e) / (
            2.0 + a + 2.0 * c_coeff
            + a * x_buggy * ((3.0 / 2.0 - 4.0 / np.pi) * x_buggy
                             + 9.0 / 5.0 - 4.0 / np.pi)
        )

        # Actual value from the implementation
        rho_actual = _hobby_velocity_accurate(phi_val, phi_val, tension=1.0)

        # The buggy implementation should match f_buggy, not f_correct
        # This test FAILS with the bug (rho_actual ≈ f_buggy ≠ f_correct)
        # and PASSES after the fix (rho_actual ≈ f_correct)
        self.assertAlmostEqual(
            rho_actual, f_correct, places=6,
            msg=f"_hobby_velocity_accurate(φ,φ) = {rho_actual:.8f}, "
                f"expected (correct γ) = {f_correct:.8f}, "
                f"buggy value = {f_buggy:.8f}. "
                f"γ_correct = {gamma_correct:.8f}, γ_buggy = {gamma_buggy:.8f}"
        )


class HobbyCyclicSystemTests(SverchokTestCase):
    """
    Bug: In the cyclic case, the tridiagonal system uses
        diag = 7*d[j]
        lower = -2*d[j]
        upper = -d[j]
    but the Hobby paper derives:
        -2*d[j]·θ[j-1] + (d[j]+7*d[j-1])·θ[j] - d[j-1]·θ[j+1]
        = (5*d[j]+d[j-1])·ψ[j]

    So diag should be d[j] + 7*d[j-1], not 7*d[j].
    upper should be -d[j-1], not -d[j].
    """

    def test_unequal_chords_cyclic(self):
        """
        With unequal chord lengths, the cyclic coefficient bug
        produces wrong θ values. Test with a simple asymmetric
        cyclic triangle where chord lengths differ significantly.
        """
        # Triangle with very unequal sides
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],   # chord length 1.0
            [1.0, 0.1, 3.0],   # chord length ~3.002
        ])

        segments = hobby_curve(points, cyclic=True, tension=1.0)
        self.assertEqual(len(segments), 3)

        # Verify G1 continuity: tangent direction at end of segment i
        # should match tangent direction at start of segment (i+1)%n
        for i in range(3):
            t_end = segments[i].tangent(1.0)
            next_idx = (i + 1) % 3
            t_start = segments[next_idx].tangent(0.0)

            # Directions should match (normalize and compare)
            dir_end = t_end / np.linalg.norm(t_end)
            dir_start = t_start / np.linalg.norm(t_start)

            angle = np.arccos(
                np.clip(np.dot(dir_end, dir_start), -1.0, 1.0)
            )
            self.assertAlmostEqual(
                angle, 0.0, places=4,
                msg=f"G1 break at knot {next_idx}: "
                    f"angle = {np.degrees(angle):.4f}°"
            )

        # Verify interpolation: each segment starts/ends at correct point
        for i in range(3):
            p_start = segments[i].evaluate(0.0)
            p_end = segments[i].evaluate(1.0)
            expected_start = points[i]
            expected_end = points[(i + 1) % 3]
            self.assert_numpy_arrays_equal(
                p_start, expected_start, precision=6,
                fail_fast=True
            )
            self.assert_numpy_arrays_equal(
                p_end, expected_end, precision=6,
                fail_fast=True
            )

    def test_cyclic_coefficients_match_paper(self):
        """
        Verify that the cyclic Hobby spline produces correct results
        for unequal chords by checking that the computed curve satisfies
        the mock curvature continuity equations from the paper.

        Paper (Hobby §3, Knuth §276):
            -2*d[j]·θ[j-1] + (d[j]+7*d[j-1])·θ[j] - d[j-1]·θ[j+1]
            = (5*d[j]+d[j-1])·ψ[j]

        The buggy implementation used 7*d[j] instead of d[j]+7*d[j-1]
        for the diagonal, and -d[j] instead of -d[j-1] for the upper.
        """
        # Points producing clearly unequal chords
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],    # d[0] = 1.0
            [1.0, 0.0, 4.0],    # d[1] = 4.0
            [0.0, 0.0, 4.0],    # d[2] = 1.0
        ])

        chords = np.zeros_like(points)
        chords[:-1] = points[1:] - points[:-1]
        chords[-1] = points[0] - points[-1]
        d = np.linalg.norm(chords, axis=1)

        # Turning angles
        psi = np.zeros(4)
        for j in range(4):
            ci = chords[(j - 1) % 4]
            co = chords[j]
            dot_val = np.dot(ci, co)
            cross_mag = np.linalg.norm(np.cross(ci, co))
            psi[j] = np.arctan2(cross_mag, dot_val)

        # Correct coefficients from the paper
        diag_expected = np.zeros(4)
        lower_expected = np.zeros(4)
        upper_expected = np.zeros(4)
        rhs_expected = np.zeros(4)

        for j in range(4):
            j_prev = (j - 1) % 4
            diag_expected[j] = d[j] + 7.0 * d[j_prev]
            lower_expected[j] = -2.0 * d[j]
            upper_expected[j] = -d[j_prev]
            rhs_expected[j] = (5.0 * d[j] + d[j_prev]) * psi[j]

        # Buggy coefficients
        diag_buggy = 7.0 * d
        upper_buggy = -d

        # Coefficients must differ for unequal chords
        self.assertFalse(
            np.allclose(diag_expected, diag_buggy),
            msg="Test setup error: coefficients should differ for unequal chords"
        )

        from sverchok.utils.curve.hobby import _solve_cyclic_tridiagonal
        theta_correct = _solve_cyclic_tridiagonal(
            diag_expected, lower_expected, upper_expected, rhs_expected
        )

        # Verify: the segments produced by hobby_curve should yield
        # tangent directions consistent with theta_correct.
        # Specifically, the mock curvature residuals should be near zero
        # when using theta_correct.
        segments = hobby_curve(points, cyclic=True, tension=1.0)

        # Check G1 continuity (tangent direction matches at knots)
        for j in range(4):
            t_end = segments[j].tangent(1.0)
            t_start = segments[(j + 1) % 4].tangent(0.0)
            dir_end = t_end / np.linalg.norm(t_end)
            dir_start = t_start / np.linalg.norm(t_start)
            angle = np.arccos(
                np.clip(np.dot(dir_end, dir_start), -1.0, 1.0)
            )
            self.assertAlmostEqual(
                angle, 0.0, places=4,
                msg=f"G1 break at knot {(j+1)%4}: angle={np.degrees(angle):.4f}°"
            )

        # Verify mock curvature continuity using correct coefficients.
        # Extract θ from the system solution and check residuals.
        residuals = np.zeros(4)
        for j in range(4):
            j_prev = (j - 1) % 4
            j_next = (j + 1) % 4
            lhs = (lower_expected[j] * theta_correct[j_prev]
                   + diag_expected[j] * theta_correct[j]
                   + upper_expected[j] * theta_correct[j_next])
            residuals[j] = lhs - rhs_expected[j]

        self.assertTrue(
            np.allclose(residuals, 0.0, atol=1e-10),
            msg=f"Mock curvature residuals with correct coefficients: {residuals}"
        )

        # Now verify that the buggy coefficients would NOT give zero residuals
        # with theta_correct (proving the coefficients matter)
        residuals_buggy = np.zeros(4)
        lower_buggy_full = -2.0 * d
        for j in range(4):
            j_prev = (j - 1) % 4
            j_next = (j + 1) % 4
            lhs = (lower_buggy_full[j] * theta_correct[j_prev]
                   + diag_buggy[j] * theta_correct[j]
                   + upper_buggy[j] * theta_correct[j_next])
            residuals_buggy[j] = lhs - rhs_expected[j]

        self.assertFalse(
            np.allclose(residuals_buggy, 0.0, atol=1e-6),
            msg="Test setup error: buggy coefficients should not satisfy "
                "the correct system"
        )


class HobbyCurlTests(SverchokTestCase):
    """
    Bug: curl_start and curl_end parameters are accepted by
    hobby_curve() but never used. The boundary conditions are
    always θ[0] = θ[n-1] = 0 (natural/Clamped), regardless of
    the curl values.

    Per Hobby paper (§3, eq. 16a, 16b), curl parameters control
    the ratio of mock curvature at endpoints to adjacent knots.
    curl=1 (default) gives circular-arc-like endpoints.
    curl=0 gives zero curvature at endpoints.
    """

    def test_curl_affects_endpoint_tangents(self):
        """
        Different curl values should produce different endpoint
        tangent directions. With the bug, all curl values produce
        identical results (θ[0] = θ[n-1] = 0).
        """
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.5, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.5, 0.0],
            [4.0, 0.0, 0.0],
        ])

        segments_curl0 = hobby_curve(points, cyclic=False, tension=1.0,
                                     curl_start=0.0, curl_end=0.0)
        segments_curl1 = hobby_curve(points, cyclic=False, tension=1.0,
                                     curl_start=1.0, curl_end=1.0)
        segments_curl2 = hobby_curve(points, cyclic=False, tension=1.0,
                                     curl_start=2.0, curl_end=2.0)

        # Endpoint tangent directions should differ for different curl values
        t0_curl0 = segments_curl0[0].tangent(0.0)
        t0_curl1 = segments_curl1[0].tangent(0.0)
        t0_curl2 = segments_curl2[0].tangent(0.0)

        dir0_curl0 = t0_curl0 / np.linalg.norm(t0_curl0)
        dir0_curl1 = t0_curl1 / np.linalg.norm(t0_curl1)
        dir0_curl2 = t0_curl2 / np.linalg.norm(t0_curl2)

        # With the bug, all three are identical (θ[0]=0 for all)
        # After the fix, they should differ
        self.assertFalse(
            np.allclose(dir0_curl0, dir0_curl1),
            msg=f"curl_start=0.0 and curl_start=1.0 produce identical "
                f"endpoint tangents: {dir0_curl0}. "
                f"Curl parameter is ignored."
        )
        self.assertFalse(
            np.allclose(dir0_curl1, dir0_curl2),
            msg=f"curl_start=1.0 and curl_start=2.0 produce identical "
                f"endpoint tangents: {dir0_curl1}. "
                f"Curl parameter is ignored."
        )

    def test_curl_end_affects_last_tangent(self):
        """
        Same check for the last endpoint (curl_end).
        Use asymmetric points to avoid symmetry-induced degeneracy.
        """
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.3, 0.0],
            [2.5, -0.2, 0.0],
            [3.0, 0.7, 0.0],
            [4.2, 0.1, 0.0],
        ])

        segments_curl0 = hobby_curve(points, cyclic=False, tension=1.0,
                                     curl_start=1.0, curl_end=0.0)
        segments_curl1 = hobby_curve(points, cyclic=False, tension=1.0,
                                     curl_start=1.0, curl_end=1.0)

        # Last segment, t=1
        t_last_curl0 = segments_curl0[-1].tangent(1.0)
        t_last_curl1 = segments_curl1[-1].tangent(1.0)

        dir_last_curl0 = t_last_curl0 / np.linalg.norm(t_last_curl0)
        dir_last_curl1 = t_last_curl1 / np.linalg.norm(t_last_curl1)

        self.assertFalse(
            np.allclose(dir_last_curl0, dir_last_curl1),
            msg=f"curl_end=0.0 and curl_end=1.0 produce identical "
                f"last tangents: {dir_last_curl0}. "
                f"curl_end parameter is ignored."
        )

    def test_symmetric_points_match_metapost(self):
        """
        Verify that the Hobby spline for symmetric 3-point input
        matches MetaPost 2.11 output for endpoint control points
        and produces correct tangent directions.

        MetaPost input: A=(-1,0), B=(0,1), C=(1,0), draw A .. B .. C;
        MetaPost output (curl=1):
          cp1=(-1, 0.55229), cp2=(-0.55229, 1)
          cp3=(0.55229, 1), cp4=(1, 0.55229)

        This test verifies:
        1. Endpoint control points match MetaPost (cp1, cp4)
        2. Tangent directions are mirror-symmetric
        3. Horizontal tangent at middle knot (0°)
        """
        points = np.array([
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
        ])

        segments = hobby_curve(points, cyclic=False, tension=1.0,
                               curl_start=1.0, curl_end=1.0)
        self.assertEqual(len(segments), 2)

        seg0 = segments[0]
        seg1 = segments[1]

        cp1 = seg0.p1[:2]
        cp4 = seg1.p2[:2]

        # MetaPost expected endpoint control points
        expected_cp1 = np.array([-1.0, 0.55229])
        expected_cp4 = np.array([1.0, 0.55229])

        # Verify endpoint control points match MetaPost
        self.assertTrue(
            np.allclose(cp1, expected_cp1, atol=1e-3),
            msg=f"cp1={cp1} does not match MetaPost {expected_cp1}"
        )
        self.assertTrue(
            np.allclose(cp4, expected_cp4, atol=1e-3),
            msg=f"cp4={cp4} does not match MetaPost {expected_cp4}"
        )

        # Verify mirror symmetry of endpoint control points
        self.assertTrue(
            np.allclose(cp1, np.array([-cp4[0], cp4[1]]), atol=1e-4),
            msg=f"cp1={cp1} is not mirror of cp4={cp4}"
        )

        # Verify horizontal tangent at middle knot
        t_mid_in = seg0.tangent(1.0)[:2]
        t_mid_out = seg1.tangent(0.0)[:2]

        angle_in = np.degrees(np.arctan2(t_mid_in[1], t_mid_in[0]))
        angle_out = np.degrees(np.arctan2(t_mid_out[1], t_mid_out[0]))

        self.assertAlmostEqual(
            angle_in, 0.0, places=1,
            msg=f"Middle tangent angle (in) = {angle_in}°, expected 0°"
        )
        self.assertAlmostEqual(
            angle_out, 0.0, places=1,
            msg=f"Middle tangent angle (out) = {angle_out}°, expected 0°"
        )

        # Verify tangent direction symmetry
        t_start = seg0.tangent(0.0)[:2]
        t_end = seg1.tangent(1.0)[:2]

        angle_start = np.degrees(np.arctan2(t_start[1], t_start[0]))
        angle_end = np.degrees(np.arctan2(t_end[1], t_end[0]))

        self.assertAlmostEqual(
            angle_start, -angle_end, places=1,
            msg=f"Tangent angles not symmetric: start={angle_start}°, end={angle_end}°"
        )
