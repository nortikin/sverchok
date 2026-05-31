# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Hobby curve algorithm - John Hobby's algorithm for computing
Bezier control points that interpolate a sequence of 2D points
with continuous mock curvature, as implemented in MetaPost.

Reference:
    "Drawing Curves with Mock Curvature" - John Hobby, MetaPost source
    (mpmathdouble.w, mp_hobby function)

API:
    hobby_curve(points, cyclic=False, tension=1.0,
                curl_start=1.0, curl_end=1.0,
                concat=False) -> list of SvCubicBezierCurve or concatenated curve
"""

import numpy as np

from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves

# ─── Constants ───────────────────────────────────────────────────────────────

_SQRT2 = np.sqrt(2.0)
_SQRT5 = np.sqrt(5.0)
_GOLDEN = (_SQRT5 - 1.0) / 2.0        # ≈ 0.618034
_GOLDEN_INV = (3.0 - _SQRT5) / 2.0    # ≈ 0.381966


def _velocity(sin_theta, cos_theta, sin_phi, cos_phi, tau=1.0):
    """
    Compute the velocity (speed ratio) for a Bezier segment.

    Implements the MetaPost velocity function (mpmathdouble.w).
    Original uses fixed-point arithmetic (take_fraction with multiplier 4096);
    here we use native float64 with equivalent formula.

        acc = (sinθ - sinφ/16) * (sinφ - sinθ/16) * (cosθ - cosφ)
        num = 2 + acc * √2
        denom = 3 + cosθ * 3·golden + cosφ * 3·golden_inv
        velocity = min(num / denom, 4)

    The velocity scales the Bezier control point distance:
        P_k⁺ = P_k + (dx·cosθ - dy·sinθ, dy·cosθ + dx·sinθ) * ρ
        P_{k+1}⁻ = P_{k+1} - (dx·cosφ + dy·sinφ, dy·cosφ - dx·sinφ) * σ

    Parameters:
        sin_theta, cos_theta: sin and cos of θ (turning angle at start)
        sin_phi, cos_phi:     sin and cos of φ (turning angle at end)
        tau:                  tension (default 1.0)

    Returns:
        velocity ratio ρ or σ (bounded by [0, 4])
    """
    # Numerator
    acc = (sin_theta - sin_phi / 16.0) * (sin_phi - sin_theta / 16.0)
    acc = acc * (cos_theta - cos_phi) * _SQRT2
    num = 2.0 + acc

    # Denominator
    denom = 3.0 + cos_theta * (3.0 * _GOLDEN) + cos_phi * (3.0 * _GOLDEN_INV)

    # Apply tension
    if abs(tau - 1.0) > 1e-15:
        num = num / tau

    # Clamp to [0, 4]
    result = num / denom
    return min(max(result, 0.0), 4.0)


def _compute_angles_and_distances(points):
    """
    Compute segment distances and turning angles ψ_k between consecutive segments.

    Parameters:
        points: array of shape (n, 2) - 2D points

    Returns:
        d: array of shape (n-1,) - segment lengths
        psi: array of shape (n,) - turning angles ψ_k (ψ_k is the angle from
             segment k-1 to segment k, measured at knot k)
    """
    n = len(points)
    d = np.zeros(n - 1)
    for k in range(n - 1):
        dx = points[k + 1, 0] - points[k, 0]
        dy = points[k + 1, 1] - points[k, 1]
        d[k] = np.hypot(dx, dy)

    # ψ_k = angle from vector (P_k - P_{k-1}) to vector (P_{k+1} - P_k)
    # This is the exterior angle at knot k
    psi = np.zeros(n)
    for k in range(1, n - 1):
        # Vector from P_{k-1} to P_k
        v1x = points[k, 0] - points[k - 1, 0]
        v1y = points[k, 1] - points[k - 1, 1]
        # Vector from P_k to P_{k+1}
        v2x = points[k + 1, 0] - points[k, 0]
        v2y = points[k + 1, 1] - points[k, 1]

        # Angle from v1 to v2
        angle1 = np.arctan2(v1y, v1x)
        angle2 = np.arctan2(v2y, v2x)
        psi[k] = angle2 - angle1

    # Normalize psi to (-π, π]
    psi = np.mod(psi + np.pi, 2.0 * np.pi) - np.pi

    return d, psi


def _mp_curl_ratio(gamma, a_tension, b_tension):
    """
    Compute the curl ratio following MetaPost mp_curl_ratio (mp.w:8633).

    Formula (from mp.w comment):
        (3 - α)·α²·γ + β³
    ---------------------------
        α³·γ + (3 - β)·β²

    where α = 1/a_tension, β = 1/b_tension.
    Result is clamped to [0, 4].

    For a_tension == b_tension == 1 this simplifies to (2γ+1)/(γ+2).
    """
    alpha = 1.0 / a_tension
    beta = 1.0 / b_tension
    g = float(gamma)

    if alpha <= beta:
        ff = (alpha / beta) ** 2
        g = g * ff
        denom = g / alpha + 3.0
    else:
        ff = (beta / alpha) ** 2
        g = g * beta * ff
        denom = g / alpha + beta * ff - beta + 3.0

    denom = denom - beta
    num = g * (3.0 - alpha) + beta

    if num >= 4.0 * denom:
        return 4.0
    return num / denom


def _solve_hobby_open(d, psi, n, m, tension=1.0, curl_start=1.0, curl_end=1.0):
    """
    Solve the open-curve Hobby system using the Thomas algorithm,
    matching MetaPost's mp.w implementation exactly.

    The system is transformed into θ[k] = vv[k] - uu[k]·θ[k+1] via
    forward elimination, then back-substituted.

    Boundary conditions (curl) are Robin-type, not Dirichlet:
        θ[0] = vv[0] - uu[0]·θ[1]   where vv[0] = -uu[0]·ψ[1]
        θ[n] = -(vv[n-1]·ff_end) / (1 - ff_end·uu[n-1])

    Parameters:
        d: array of shape (n,) - segment lengths (n = m - 1)
        psi: array of shape (m,) - turning angles (psi[0] = psi[m-1] = 0)
        n: number of segments (= m - 1)
        m: number of knots
        tension: tension parameter (default 1.0)
        curl_start: curl at start endpoint (default 1.0)
        curl_end: curl at end endpoint (default 1.0)

    Returns:
        theta: array of shape (m,) - Hobby angles θ_k for each knot
    """
    tau = max(tension, 0.75)

    # Precompute aa, bb for uniform tension
    if abs(tau - 1.0) < 1e-15:
        aa = 0.5
    else:
        aa = 1.0 / (3.0 * tau - 1.0)
    bb = aa

    # Curl ratios (MetaPost mp.w:8550 and mp_curl_ratio)
    uu0 = _mp_curl_ratio(curl_start, tau, tau)
    ff_end = _mp_curl_ratio(curl_end, tau, tau)

    # Arrays for Thomas algorithm
    uu = np.zeros(m)   # uu[0..n-1] used
    vv = np.zeros(m)   # vv[0..n-1] used

    # ── Start boundary condition (mp.w:8561) ──
    uu[0] = uu0
    vv[0] = -psi[1] * uu0

    # ── Forward elimination (mp.w:8290–8440) ──
    for k in range(1, n):  # k = 1 .. n-1 (interior knots)
        # Compute dd, ee
        if abs(tau - 1.0) < 1e-15:
            dd = 2.0 * d[k]
            ee = 2.0 * d[k - 1]
        else:
            inv_tau = 1.0 / tau
            dd = d[k] * (3.0 - inv_tau)
            ee = d[k - 1] * (3.0 - inv_tau)

        # cc = 1 - uu[k-1] * aa  (mp.w:8340)
        cc_val = 1.0 - uu[k - 1] * aa

        # ff = ee / (dd * cc + ee)  (mp.w:8350–8400)
        ff = ee / (dd * cc_val + ee)

        # uu[k] = ff * bb
        uu[k] = ff * bb

        # vv[k] computation (mp.w:8400–8440)
        #   acc = -psi[k+1] * uu[k]
        #   ff_new = (1 - ff) / cc
        #   acc -= psi[k] * ff_new
        #   ff_new2 = ff_new * aa   (take_fraction, not division!)
        #   vv[k] = acc - vv[k-1] * ff_new2
        acc = -psi[k + 1] * uu[k]
        ff_new = (1.0 - ff) / cc_val
        acc -= psi[k] * ff_new
        ff_new2 = ff_new * aa
        vv[k] = acc - vv[k - 1] * ff_new2

    # ── End boundary condition (mp.w:8596) ──
    # theta[n] = -(vv[n-1] * ff_end) / (1 - ff_end * uu[n-1])
    denom_end = 1.0 - ff_end * uu[n - 1]
    if abs(denom_end) < 1e-15:
        theta_n = 0.0
    else:
        theta_n = -(vv[n - 1] * ff_end) / denom_end

    # ── Back-substitution (mp.w:8688) ──
    theta = np.zeros(m)
    theta[m - 1] = theta_n
    for k in range(m - 2, -1, -1):
        theta[k] = vv[k] - theta[k + 1] * uu[k]

    return theta


def _solve_hobby_cyclic(d, psi, m, tension=1.0):
    """
    Solve the cyclic (closed) curve system with tension.

    For cyclic curves with m knots (indices 0..m-1), we have m equations:
        d[k] * θ_{k-1} + (3τ-1)*(d[k] + d[k-1]) * θ_k + d[k-1] * θ_{k+1}
            = -(3τ-1)*d[k]*ψ[k] - d[k-1]*ψ[k+1]
    where all indices are taken modulo m.

    Parameters:
        d: array of shape (m,) - segment lengths (including wrap-around)
        psi: array of shape (m,) - turning angles at each knot
        m: number of knots (= number of segments)
        tension: tension parameter (default 1.0)

    Returns:
        theta: array of shape (m,) - Hobby angles θ_k for each knot
    """
    # Tension factor: (3τ - 1), equals 2 when τ = 1
    tau = max(tension, 0.75)
    factor = 3.0 * tau - 1.0

    # Build the full m x m system matrix
    A = np.zeros((m, m))
    rhs = np.zeros(m)

    for k in range(m):
        prev_k = (k - 1) % m
        next_k = (k + 1) % m
        dk = d[k]
        dk1 = d[prev_k]

        A[k, prev_k] = dk1
        A[k, k] = factor * (dk + dk1)
        A[k, next_k] = dk
        rhs[k] = -factor * dk * psi[k] - dk1 * psi[next_k]

    # Solve the full system
    try:
        theta = np.linalg.solve(A, rhs)
    except np.linalg.LinAlgError:
        # Fallback: return zeros if singular
        theta = np.zeros(m)

    return theta


def _compute_bezier_segments_full(points_2d, theta, psi, n_segments=None,
                                   tension=1.0):
    """
    Compute Bezier control points for each segment given θ angles and ψ angles.

    Parameters:
        points_2d: array of shape (m, 2) - knot points
        theta: array of shape (m,) - Hobby angles θ_k
        psi: array of shape (m,) - turning angles ψ_k
        n_segments: if specified, number of segments (for cyclic, this equals m).
                    If None, defaults to m-1 (open curve).
        tension: tension parameter (default 1.0)

    Returns:
        segments: list of (p0, p1, p2, p3) tuples, each a numpy array of shape (2,)
    """
    m = len(points_2d)
    if n_segments is None:
        n_segments = m - 1  # open curve

    segments = []

    for k in range(n_segments):
        pk = points_2d[k % m]  # for cyclic, wrap around
        pk1 = points_2d[(k + 1) % m]

        # Δx, Δy for this segment
        dx = pk1[0] - pk[0]
        dy = pk1[1] - pk[1]

        # θ_k at start, φ_k at end
        theta_k = theta[k % m]
        # φ_k = -θ_{k+1} - ψ_{k+1} (turning angle at knot k+1)
        # Relation: θ_{k+1} + φ_k + ψ_{k+1} = 0
        phi_k = -theta[(k + 1) % m] - psi[(k + 1) % m]

        # Compute sin/cos
        st = np.sin(theta_k)
        ct = np.cos(theta_k)
        sf = np.sin(phi_k)
        cf = np.cos(phi_k)

        # Compute velocities
        # ρ_k = velocity(θ_k, φ_k) for the right control point
        # σ_{k+1} = velocity(φ_k, θ_k) for the left control point
        rho = _velocity(st, ct, sf, cf, tau=tension)
        sigma = _velocity(sf, cf, st, ct, tau=tension)

        # Right control point: P_k⁺
        # P_k⁺ = P_k + (dx·cos(θ_k) - dy·sin(θ_k), dy·cos(θ_k) + dx·sin(θ_k)) · ρ_k
        p1x = pk[0] + (dx * ct - dy * st) * rho
        p1y = pk[1] + (dy * ct + dx * st) * rho

        # Left control point: P_{k+1}⁻
        # P_{k+1}⁻ = P_{k+1} - (dx·cos(φ_k) + dy·sin(φ_k), dy·cos(φ_k) - dx·sin(φ_k)) · σ_{k+1}
        p2x = pk1[0] - (dx * cf + dy * sf) * sigma
        p2y = pk1[1] - (dy * cf - dx * sf) * sigma

        segments.append((pk, np.array([p1x, p1y]), np.array([p2x, p2y]), pk1))

    return segments


def hobby_curve(points, cyclic=False, tension=1.0,
                curl_start=1.0, curl_end=1.0,
                concat=False):
    """
    Compute a Hobby curve (Bezier spline) through the given points.

    Implements John Hobby's algorithm for computing Bezier control points
    that interpolate a sequence of 2D points with continuous mock curvature,
    as used in MetaPost.

    The input points are 3D, but only the X and Y coordinates are used
    (Z is ignored and set to 0).

    Parameters:
        points: list or array of 3D points (numpy arrays or lists), shape (n, 3)
        cyclic: if True, create a closed (cyclic) curve
        tension: tension parameter (default 1.0). Higher values pull the curve
                 closer to the polyline. As tension -> inf, the curve approaches
                 the polyline.
        curl_start: curl parameter at the start endpoint (default 1.0).
                    Controls how the curve leaves the first point.
                    curl=1 gives circular-arc-like endpoints.
                    curl=0 gives zero curvature at the start (straight line).
        curl_end: curl parameter at the end endpoint (default 1.0).
                  Controls how the curve approaches the last point.
                  curl=1 gives circular-arc-like endpoints.
                  curl=0 gives zero curvature at the end (straight line).
        concat: if True, concatenate all Bezier segments into a single curve

    Returns:
        If concat=False: list of SvCubicBezierCurve segments
        If concat=True: a single concatenated SvNurbsCurve

    Example:
        >>> points = [
        ...     np.array([0.0, 0.0, 0.0]),
        ...     np.array([1.0, 0.5, 0.0]),
        ...     np.array([2.0, 0.0, 0.0]),
        ...     np.array([2.5, 1.0, 0.0]),
        ... ]
        >>> segments = hobby_curve(points, tension=1.0, curl_start=1.0, curl_end=1.0)
        >>> # Each segment is a SvCubicBezierCurve
    """
    points = np.asarray(points, dtype=np.float64)
    m = len(points)  # number of knots

    if m < 2:
        raise ValueError("At least 2 points are required for a Hobby curve")

    # Extract 2D coordinates (X, Y), ignore Z
    points_2d = points[:, :2].copy()

    if cyclic and m < 3:
        raise ValueError("At least 3 points are required for a cyclic Hobby curve")

    if cyclic and m >= 3:
        # For cyclic: m knots, m segments
        # Segment k goes from knot k to knot (k+1) % m
        # d[k] = distance from knot k to knot (k+1) % m
        d = np.zeros(m)
        for k in range(m):
            j = (k + 1) % m
            dx = points_2d[j, 0] - points_2d[k, 0]
            dy = points_2d[j, 1] - points_2d[k, 1]
            d[k] = np.hypot(dx, dy)

        # psi[k] = turning angle at knot k
        # = angle from segment (k-1) to segment k at knot k
        psi = np.zeros(m)
        for k in range(m):
            # Vector from previous knot to current knot
            prev_k = (k - 1) % m
            next_k = (k + 1) % m
            v1x = points_2d[k, 0] - points_2d[prev_k, 0]
            v1y = points_2d[k, 1] - points_2d[prev_k, 1]
            v2x = points_2d[next_k, 0] - points_2d[k, 0]
            v2y = points_2d[next_k, 1] - points_2d[k, 1]

            angle1 = np.arctan2(v1y, v1x)
            angle2 = np.arctan2(v2y, v2x)
            psi[k] = angle2 - angle1

        # Normalize psi to (-π, π]
        psi = np.mod(psi + np.pi, 2.0 * np.pi) - np.pi

        # Solve cyclic system
        theta = _solve_hobby_cyclic(d, psi, m, tension=tension)

        # Compute Bezier segments (m segments for m knots)
        segments_2d = _compute_bezier_segments_full(
            points_2d, theta, psi, n_segments=m, tension=tension
        )

    else:
        # Non-cyclic: m knots, m-1 segments
        d, psi = _compute_angles_and_distances(points_2d)
        n = m - 1  # number of segments
        theta = _solve_hobby_open(
            d, psi, n, m,
            tension=tension,
            curl_start=curl_start,
            curl_end=curl_end
        )

        # Compute Bezier segments (m-1 segments)
        segments_2d = _compute_bezier_segments_full(
            points_2d, theta, psi, tension=tension
        )

    # Convert to 3D Bezier curves
    bezier_segments = []
    for p0, p1, p2, p3 in segments_2d:
        # Convert to 3D (Z = 0)
        p0_3d = np.array([p0[0], p0[1], 0.0])
        p1_3d = np.array([p1[0], p1[1], 0.0])
        p2_3d = np.array([p2[0], p2[1], 0.0])
        p3_3d = np.array([p3[0], p3[1], 0.0])

        segment = SvCubicBezierCurve(p0_3d, p1_3d, p2_3d, p3_3d)
        bezier_segments.append(segment)

    if concat and len(bezier_segments) > 1:
        return concatenate_nurbs_curves(bezier_segments)

    return bezier_segments
