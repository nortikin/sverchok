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
    hobby_curve(points, cyclic=False, concat=False) -> list of SvCubicBezierCurve or concatenated curve
"""

import numpy as np

from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves

# ─── Constants ───────────────────────────────────────────────────────────────

_FRACTION_MULTIPLIER = 4096.0
_SQRT2 = np.sqrt(2.0)
_SQRT5 = np.sqrt(5.0)
_GOLDEN = (_SQRT5 - 1.0) / 2.0        # ≈ 0.618034
_GOLDEN_INV = (3.0 - _SQRT5) / 2.0    # ≈ 0.381966


def _take_fraction(a, b):
    """
    Fraction arithmetic: take_fraction(a, b) = (a * b) / fraction_multiplier.
    This is MetaPost's fixed-point style multiplication.
    """
    return (a * b) / _FRACTION_MULTIPLIER


def _velocity(sin_theta, cos_theta, sin_phi, cos_phi, tau=1.0):
    """
    Compute the velocity (speed ratio) for a Bezier segment.

    Implements the standard MetaPost velocity function:
        f(θ, φ) = min( (2 + take_fraction((sinθ - sinφ/16) * (sinφ - sinθ/16) * (cosθ - cosφ), √2))
                        / (3 + take_fraction(cosθ, 3·golden) + take_fraction(cosφ, 3·golden_inv)),
                      4 )

    Parameters:
        sin_theta, cos_theta: sin and cos of θ (turning angle at start)
        sin_phi, cos_phi:     sin and cos of φ (turning angle at end)
        tau:                  tension (default 1.0)

    Returns:
        velocity ratio ρ or σ (bounded by [0, 4])
    """
    # Numerator
    acc = _take_fraction(sin_theta - sin_phi / 16.0, sin_phi - sin_theta / 16.0)
    acc = _take_fraction(acc, cos_theta - cos_phi)
    num = 2.0 + _take_fraction(acc, _SQRT2)

    # Denominator
    denom = 3.0 + _take_fraction(cos_theta, 3.0 * _GOLDEN) + _take_fraction(cos_phi, 3.0 * _GOLDEN_INV)

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
        psi: array of shape (n-1,) - turning angles ψ_k (ψ_k is the angle from
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


def _solve_hobby_open(d, psi, n, m):
    """
    Solve the open curve system using tridiagonal solver (Thomas algorithm).

    For open curves, we solve for all θ_k (k=0..n).
    The system has n-1 interior equations plus 2 boundary conditions.

    Boundary conditions (open, τ=1):
        k=0: θ_0 = 0  (natural boundary)
        k=n: θ_n = 0  (natural boundary)
    """
    # Build the tridiagonal system A · θ = b
    # For interior knots k=1..n-1:
    #   d_k · θ_{k-1} + 2·(d_k + d_{k-1}) · θ_k + d_{k-1} · θ_{k+1}
    #       = -2·d_k · ψ_k - d_{k-1} · ψ_{k+1}
    # where d_k = d[k] = distance from knot k to knot k+1
    # and d_{k-1} = d[k-1] = distance from knot k-1 to knot k

    a = np.zeros(m)  # lower diagonal
    b = np.zeros(m)  # main diagonal
    c = np.zeros(m)  # upper diagonal
    rhs = np.zeros(m)  # right-hand side

    for k in range(1, n):  # interior knots
        dk = d[k]       # d_{k,k+1}
        dk1 = d[k - 1]  # d_{k-1,k}

        a[k] = dk1
        b[k] = 2.0 * (dk + dk1)
        c[k] = dk
        rhs[k] = -2.0 * dk * psi[k] - dk1 * psi[k + 1]

    # Boundary conditions: natural (θ_0 = 0, θ_n = 0)
    # This means the first and last rows are identity
    b[0] = 1.0
    b[n] = 1.0

    # Solve using Thomas algorithm (tridiagonal solver)
    theta = np.zeros(m)

    # Forward elimination
    for k in range(1, n):
        if abs(b[k - 1]) < 1e-15:
            # Singular - use a small value
            b[k - 1] = 1e-15
        factor = a[k] / b[k - 1]
        b[k] = b[k] - factor * c[k - 1]
        rhs[k] = rhs[k] - factor * rhs[k - 1]

    # Back substitution
    if abs(b[n - 1]) < 1e-15:
        b[n - 1] = 1e-15
    theta[n - 1] = rhs[n - 1] / b[n - 1]

    for k in range(n - 2, 0, -1):
        if abs(b[k]) < 1e-15:
            b[k] = 1e-15
        theta[k] = (rhs[k] - c[k] * theta[k + 1]) / b[k]

    # θ_0 = θ_n = 0 (boundary)
    theta[0] = 0.0
    theta[n] = 0.0

    return theta


def _solve_hobby_cyclic(d, psi, m):
    """
    Solve the cyclic (closed) curve system.

    For cyclic curves with m knots (indices 0..m-1), we have m equations:
        d[k] * θ_{k-1} + 2*(d[k] + d[k-1]) * θ_k + d[k-1] * θ_{k+1}
            = -2*d[k]*ψ[k] - d[k-1]*ψ[k+1]
    where all indices are taken modulo m.

    Parameters:
        d: array of shape (m,) - segment lengths (including wrap-around)
        psi: array of shape (m,) - turning angles at each knot
        m: number of knots (= number of segments)

    Returns:
        theta: array of shape (m,) - Hobby angles θ_k for each knot
    """
    # Build the full m x m system matrix
    A = np.zeros((m, m))
    rhs = np.zeros(m)

    for k in range(m):
        prev_k = (k - 1) % m
        next_k = (k + 1) % m
        dk = d[k]
        dk1 = d[prev_k]

        A[k, prev_k] = dk1
        A[k, k] = 2.0 * (dk + dk1)
        A[k, next_k] = dk
        rhs[k] = -2.0 * dk * psi[k] - dk1 * psi[next_k]

    # Solve the full system
    try:
        theta = np.linalg.solve(A, rhs)
    except np.linalg.LinAlgError:
        # Fallback: return zeros if singular
        theta = np.zeros(m)

    return theta


def _compute_bezier_segments_full(points_2d, theta, psi, n_segments=None):
    """
    Compute Bezier control points for each segment given θ angles and ψ angles.

    Parameters:
        points_2d: array of shape (m, 2) - knot points
        theta: array of shape (m,) - Hobby angles θ_k
        psi: array of shape (m,) - turning angles ψ_k
        n_segments: if specified, number of segments (for cyclic, this equals m).
                    If None, defaults to m-1 (open curve).

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
        rho = _velocity(st, ct, sf, cf, tau=1.0)
        sigma = _velocity(sf, cf, st, ct, tau=1.0)

        # Right control point: P_k⁺
        # P_k⁺ = P_k + (dx·cos(θ_k) - dy·sin(θ_k), dy·cos(θ_k) + dx·sin(θ_k)) · ρ_k / 3
        p1x = pk[0] + (dx * ct - dy * st) * rho / 3.0
        p1y = pk[1] + (dy * ct + dx * st) * rho / 3.0

        # Left control point: P_{k+1}⁻
        # P_{k+1}⁻ = P_{k+1} - (dx·cos(φ_k) + dy·sin(φ_k), dy·cos(φ_k) - dx·sin(φ_k)) · σ_{k+1} / 3
        p2x = pk1[0] - (dx * cf + dy * sf) * sigma / 3.0
        p2y = pk1[1] - (dy * cf - dx * sf) * sigma / 3.0

        segments.append((pk, np.array([p1x, p1y]), np.array([p2x, p2y]), pk1))

    return segments


def hobby_curve(points, cyclic=False, concat=False):
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
        >>> segments = hobby_curve(points)
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
        theta = _solve_hobby_cyclic(d, psi, m)

        # Compute Bezier segments (m segments for m knots)
        segments_2d = _compute_bezier_segments_full(points_2d, theta, psi, n_segments=m)

    else:
        # Non-cyclic: m knots, m-1 segments
        d, psi = _compute_angles_and_distances(points_2d)
        n = m - 1  # number of segments
        theta = _solve_hobby_open(d, psi, n, m)

        # Compute Bezier segments (m-1 segments)
        segments_2d = _compute_bezier_segments_full(points_2d, theta, psi)

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
