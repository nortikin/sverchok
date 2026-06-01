# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Hobby curve algorithm - John Hobby's algorithm for computing
Bezier control points that interpolate a sequence of 3D points
with continuous mock curvature, as implemented in MetaPost.

For 3D curves, each triple of consecutive points defines a local
plane. Signed turning angles are produced by making local plane
normal orientation consistent along the curve. Control point
tangents are obtained via Rodrigues rotation around the local
plane normal.

Reference:
    "Drawing Curves with Mock Curvature" - John Hobby, MetaPost source

API:
    hobby_curve(points, cyclic=False, tension=1.0,
                curl_start=1.0, curl_end=1.0,
                concat=False)
"""

import numpy as np

from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves

_SQRT2 = np.sqrt(2.0)
_SQRT5 = np.sqrt(5.0)
_GOLDEN = (_SQRT5 - 1.0) / 2.0
_GOLDEN_INV = (3.0 - _SQRT5) / 2.0
_EPS = 1e-10


# ─── Velocity ────────────────────────────────────────────────────────────────

def _velocity(sin_theta, cos_theta, sin_phi, cos_phi, tau=1.0):
    """
    Compute the velocity (speed ratio) for a Bezier segment endpoint.

    This determines how far the control point lies from the knot along
    the tangent direction. The ratio is bounded to [0, 4] to prevent
    excessive overshoot.

    Implements the MetaPost velocity function (mpmathdouble.w), which
    uses a heuristic based on the turning angles θ and φ at the segment
    endpoints:

        acc = (sinθ - sinφ/16) · (sinφ - sinθ/16) · (cosθ - cosφ) · √2
        num = 2 + acc
        denom = 3 + cosθ · 3φ + cosφ · 3φ⁻¹    (φ = golden ratio)
        velocity = clamp(num / (denom · τ), 0, 4)

    Parameters:
        sin_theta, cos_theta: sin and cos of θ (turning angle at start)
        sin_phi, cos_phi:     sin and cos of φ (turning angle at end)
        tau:                  tension (default 1.0)

    Returns:
        velocity ratio ρ or σ, clamped to [0, 4]
    """
    acc = (sin_theta - sin_phi / 16.0) * (sin_phi - sin_theta / 16.0)
    acc *= (cos_theta - cos_phi) * _SQRT2
    num = 2.0 + acc
    denom = 3.0 + cos_theta * (3.0 * _GOLDEN) + cos_phi * (3.0 * _GOLDEN_INV)
    if abs(tau - 1.0) > 1e-15:
        num /= tau
    return min(max(num / denom, 0.0), 4.0)


# ─── Geometry: angles, distances, normals ────────────────────────────────────

def _compute_angles_distances_normals(points, cyclic=False):
    """
    Compute segment lengths, SIGNED turning angles, and local plane normals.

    Signed psi is achieved by making consecutive normals agree in direction
    (dot(n[k], n[prev]) >= 0). If they disagree, both n[k] and psi[k] flip.
    """
    m = len(points)
    points = np.asarray(points, dtype=np.float64)

    # ── Segment lengths ──
    if cyclic:
        segs = np.roll(points, -1, axis=0) - points
        d = np.linalg.norm(segs, axis=1)
    else:
        segs = points[1:] - points[:-1]
        d = np.linalg.norm(segs, axis=1)

    normals = np.zeros((m, 3))
    psi = np.zeros(m)
    has_normal = np.zeros(m, dtype=bool)

    # ── Incoming / outgoing segment vectors at each knot ──
    # For cyclic: all knots have neighbors.
    # For open: endpoints have no local plane; use dummy vectors (zeros).
    if cyclic:
        v_in = points - np.roll(points, 1, axis=0)
        v_out = np.roll(points, -1, axis=0) - points
    else:
        v_in = np.zeros((m, 3))
        v_out = np.zeros((m, 3))
        v_in[1:-1] = points[1:-1] - points[:-2]
        v_out[1:-1] = points[2:] - points[1:-1]

    # ── Vectorized: norms, cross products, dot products ──
    n_in = np.linalg.norm(v_in, axis=1)
    n_out = np.linalg.norm(v_out, axis=1)

    # Mask out degenerate segments (coincident points or endpoints)
    valid = (n_in > 1e-15) & (n_out > 1e-15)

    # Cross products (normals) and dot products (cos psi) — only for valid knots
    n = np.cross(v_in[valid], v_out[valid])
    n_mag_valid = np.linalg.norm(n, axis=1)
    cos_psi_valid = np.sum(v_in[valid] * v_out[valid], axis=1) / (n_in[valid] * n_out[valid])

    # Store results
    psi[valid] = np.arccos(np.clip(cos_psi_valid, -1.0, 1.0))

    non_collinear_valid = n_mag_valid > _EPS
    non_collinear = np.zeros(m, dtype=bool)
    non_collinear[valid] = non_collinear_valid
    normals[non_collinear] = n[non_collinear_valid]
    has_normal[non_collinear] = True

    # consistent orientation -> signed psi
    _make_normals_consistent(normals, psi, has_normal, m, cyclic)
    # fill gaps
    _fill_fallback_normals(normals, has_normal, m, cyclic)

    return d, psi, normals


def _make_normals_consistent(normals, psi, has_normal, m, cyclic):
    """
    Ensure consistent normal orientation along the curve.

    Walk through knots in order. If the normal at knot k points in the
    opposite direction from the previous oriented normal (dot < 0), flip
    both the normal and the turning angle. This produces signed ψ values
    analogous to the 2D arctan2 convention.
    """
    if cyclic:
        start = -1
        for k in range(m):
            if has_normal[k]:
                start = k
                break
        if start < 0:
            return
        for i in range(1, m):
            k = (start + i) % m
            if not has_normal[k]:
                continue
            for j in range(1, m):
                prev = (k - j) % m
                if has_normal[prev] and np.linalg.norm(normals[prev]) > _EPS:
                    if np.dot(normals[k], normals[prev]) < 0:
                        normals[k] = -normals[k]
                        psi[k] = -psi[k]
                    break
    else:
        for k in range(1, m):
            if not has_normal[k]:
                continue
            for prev in range(k - 1, -1, -1):
                if has_normal[prev] and np.linalg.norm(normals[prev]) > _EPS:
                    if np.dot(normals[k], normals[prev]) < 0:
                        normals[k] = -normals[k]
                        psi[k] = -psi[k]
                    break


def _fill_fallback_normals(normals, has_normal, m, cyclic):
    """
    Fill zero normals by borrowing from the nearest non-zero neighbor.

    Needed for: open-curve endpoints (no local plane), collinear triples
    (cross product is zero), and degenerate cases.

    If all points are collinear, use (0, 1, 0) as a default normal.
    """
    changed = True
    while changed:
        changed = False
        for k in range(m):
            if np.linalg.norm(normals[k]) > _EPS:
                continue
            for offset in range(1, m):
                for sign in (1, -1):
                    j = k + sign * offset
                    if cyclic:
                        j = j % m
                    else:
                        if j < 0 or j >= m:
                            continue
                    if np.linalg.norm(normals[j]) > _EPS:
                        normals[k] = normals[j].copy()
                        changed = True
                        break
                if changed:
                    break

    # all collinear -> default normal
    if np.linalg.norm(normals) < _EPS:
        for k in range(m):
            normals[k] = np.array([0.0, 1.0, 0.0])


# ─── Curl ratio (MetaPost mp_curl_ratio) ─────────────────────────────────────

def _mp_curl_ratio(curl_gamma, tension_left, tension_right):
    """
    Compute the curl coefficient for a Hobby curve endpoint.

    This determines the Robin-type boundary condition used by the Thomas
    algorithm. A curl_gamma of 1 gives circular-arc-like endpoints; 0
    gives zero curvature (straight-line departure/arrival).

    Implements MetaPost's mp_curl_ratio (mp.w:8668) exactly.

    Parameters:
        curl_gamma:   curl parameter (0 = zero curvature, 1 = circular arc)
        tension_left: tension on the segment leaving the endpoint
        tension_right: tension on the neighboring segment
    """
    alpha = 1.0 / tension_left
    beta = 1.0 / tension_right
    g = float(curl_gamma)

    if alpha <= beta:
        # Tension on the left is >= tension on the right
        ff = (alpha / beta) ** 2
        g *= ff
        denom = g * alpha + 3.0
    else:
        # Tension on the left is < tension on the right
        ff = (beta / alpha) ** 2
        beta = beta * ff
        denom = g * alpha + ff / 3.0

    denom -= beta
    num = g * (3.0 - alpha) + beta

    if num >= 4.0 * denom:
        return 4.0
    return num / denom


# ─── Hobby system solvers ────────────────────────────────────────────────────

def _solve_hobby_open(d, psi, n_segments, n_knots, tension=1.0,
                       curl_start=1.0, curl_end=1.0):
    """
    Solve the open-curve Hobby linear system via the Thomas algorithm.

    The Hobby system is a tridiagonal system of equations:

        d[k-1]·θ[k-1] + factor·(d[k-1]+d[k])·θ[k] + d[k]·θ[k+1]
            = -factor·d[k]·ψ[k] - d[k-1]·ψ[k+1]

    where factor = 3·τ - 1 (equals 2 when τ = 1).

    The Thomas algorithm reduces this to a simple back-substitution form:

        θ[k] = reduced_rhs[k] - reduced_slope[k] · θ[k+1]

    Boundary conditions are Robin-type (not Dirichlet):
        θ[0] = reduced_rhs[0] - reduced_slope[0] · θ[1]
        θ[n] = -(reduced_rhs[n-1] · curl_end_ratio)
               / (1 - curl_end_ratio · reduced_slope[n-1])

    The curl parameters control how the curve leaves/arrives at endpoints:
        curl=1  → circular-arc-like endpoint
        curl=0  → zero curvature at endpoint (straight line)

    Parameters:
        d:           segment lengths, shape (n_segments,)
        psi:         signed turning angles, shape (n_knots,)
        n_segments:  number of segments (= n_knots - 1)
        n_knots:     number of knots
        tension:     tension parameter (default 1.0)
        curl_start:  curl at start endpoint (default 1.0)
        curl_end:    curl at end endpoint (default 1.0)

    Returns:
        theta: Hobby angles θ_k for each knot, shape (n_knots,)
    """
    tau = max(tension, 0.75)

    # Tension coefficient: aa = 1/(3τ-1) for τ≠1, or 0.5 for τ=1
    # This appears in the Thomas elimination as the coupling strength
    # between neighboring θ values.
    if abs(tau - 1.0) < 1e-15:
        tension_coeff = 0.5
    else:
        tension_coeff = 1.0 / (3.0 * tau - 1.0)

    # Curl coefficients: determine the Robin boundary conditions
    # at the start and end endpoints.
    curl_start_coeff = _mp_curl_ratio(curl_start, tau, tau)
    curl_end_ratio = _mp_curl_ratio(curl_end, tau, tau)

    # Thomas algorithm arrays:
    #   reduced_slope[k] = coefficient of θ[k+1] in θ[k] = reduced_rhs[k] - reduced_slope[k]·θ[k+1]
    #   reduced_rhs[k]   = constant term in the reduced equation
    reduced_slope = np.zeros(n_knots)
    reduced_rhs = np.zeros(n_knots)

    # ── Start boundary condition (Robin) ──
    # The start endpoint uses a curl-dependent boundary condition:
    #   θ[0] = reduced_rhs[0] - reduced_slope[0] · θ[1]
    # where reduced_slope[0] = curl_start_coeff and
    #       reduced_rhs[0] = -ψ[1] · curl_start_coeff
    #
    # This encodes the desired curvature behavior at the start endpoint.
    reduced_slope[0] = curl_start_coeff
    reduced_rhs[0] = -psi[1] * curl_start_coeff

    # ── Forward elimination ──
    # For each interior knot k, substitute θ[k-1] = reduced_rhs[k-1]
    # - reduced_slope[k-1]·θ[k] into the original equation, then solve
    # for θ[k] in terms of θ[k+1].
    for k in range(1, n_segments):
        # Weighted segment lengths for this knot.
        # For τ=1: weight = 2·d[k]; for τ≠1: weight = d[k]·(3 - 1/τ)
        if abs(tau - 1.0) < 1e-15:
            weight_right = 2.0 * d[k]
            weight_left = 2.0 * d[k - 1]
        else:
            weight_right = d[k] * (3.0 - 1.0 / tau)
            weight_left = d[k - 1] * (3.0 - 1.0 / tau)

        # Denominator after substituting θ[k-1]:
        #   cc = 1 - reduced_slope[k-1] · tension_coeff
        # This accounts for the coupling between θ[k-1] and θ[k].
        coupling_denom = 1.0 - reduced_slope[k - 1] * tension_coeff

        # Weight fraction: determines how much of the left segment
        # contributes to the reduced coefficient.
        weight_fraction = weight_left / (weight_right * coupling_denom + weight_left)

        # Reduced slope for this knot.
        reduced_slope[k] = weight_fraction * tension_coeff

        # Reduced RHS: combines the turning angles ψ[k], ψ[k+1] with
        # the propagated boundary term from the previous knot.
        #
        # The term ff_new = (1 - weight_fraction) / coupling_denom is the
        # propagation factor from θ[k-1] to θ[k].
        #
        # The term ff_new2 = ff_new · tension_coeff is the scaled
        # propagation factor (MetaPost's take_fraction maps to
        # multiplication in float64).
        rhs_accum = -psi[k + 1] * reduced_slope[k]
        prop_factor = (1.0 - weight_fraction) / coupling_denom
        rhs_accum -= psi[k] * prop_factor
        scaled_prop = prop_factor * tension_coeff
        reduced_rhs[k] = rhs_accum - reduced_rhs[k - 1] * scaled_prop

    # ── End boundary condition (Robin) ──
    # The end endpoint uses a curl-dependent boundary condition:
    #   θ[n] = -(reduced_rhs[n-1] · curl_end_ratio)
    #          / (1 - curl_end_ratio · reduced_slope[n-1])
    end_denom = 1.0 - curl_end_ratio * reduced_slope[n_segments - 1]
    if abs(end_denom) < 1e-15:
        theta_last = 0.0
    else:
        theta_last = -(reduced_rhs[n_segments - 1] * curl_end_ratio) / end_denom

    # ── Back-substitution ──
    # Recover θ values from the last knot to the first using:
    #   θ[k] = reduced_rhs[k] - reduced_slope[k] · θ[k+1]
    theta = np.zeros(n_knots)
    theta[n_knots - 1] = theta_last
    for k in range(n_knots - 2, -1, -1):
        theta[k] = reduced_rhs[k] - theta[k + 1] * reduced_slope[k]

    return theta


def _solve_hobby_cyclic(d, psi, n_knots, tension=1.0):
    """
    Solve the cyclic (closed) Hobby linear system.

    For a closed curve with n_knots points, the Hobby system is a full
    cyclic tridiagonal system:

        d[k-1]·θ[k-1] + factor·(d[k-1]+d[k])·θ[k] + d[k]·θ[k+1]
            = -factor·d[k]·ψ[k] - d[k-1]·ψ[k+1]

    where all indices are taken modulo n_knots, and factor = 3·τ - 1.

    Unlike the open-curve case (which uses the Thomas algorithm with
    Robin boundary conditions), the cyclic system has no endpoints and
    is solved directly as a dense linear system.

    Parameters:
        d:         segment lengths, shape (n_knots,) — includes wrap-around
        psi:       signed turning angles, shape (n_knots,)
        n_knots:   number of knots (= number of segments)
        tension:   tension parameter (default 1.0)

    Returns:
        theta: Hobby angles θ_k for each knot, shape (n_knots,)
    """
    tau = max(tension, 0.75)
    factor = 3.0 * tau - 1.0

    # Build the full n_knots × n_knots system matrix.
    # Each row k has three non-zero entries: θ[k-1], θ[k], θ[k+1]
    # (indices wrap around modulo n_knots).
    A = np.zeros((n_knots, n_knots))
    rhs = np.zeros(n_knots)

    for k in range(n_knots):
        prev_k = (k - 1) % n_knots
        next_k = (k + 1) % n_knots
        seg_len_k = d[k]         # segment leaving knot k
        seg_len_prev = d[prev_k] # segment entering knot k

        A[k, prev_k] = seg_len_prev
        A[k, k] = factor * (seg_len_k + seg_len_prev)
        A[k, next_k] = seg_len_k
        rhs[k] = -factor * seg_len_k * psi[k] - seg_len_prev * psi[next_k]

    try:
        return np.linalg.solve(A, rhs)
    except np.linalg.LinAlgError:
        # Singular system (degenerate curve): return zero angles
        return np.zeros(n_knots)


# ─── Bezier control points (3D, Rodrigues) ───────────────────────────────────

def _compute_bezier_segments_full(points, theta, psi, normals, n_segments=None,
                                   tension=1.0):
    """
    Compute Bezier control points for each segment using Rodrigues rotation.

    For each Bezier segment k (from p[k] to p[k+1]), two control points are
    computed:

        p1 = p[k] + tangent_start · ρ    (right control point, near p[k])
        p2 = p[k+1] - tangent_end · σ    (left control point, near p[k+1])

    The tangent directions are obtained by rotating the segment vector within
    the local plane at each knot:

        tangent_start = R(seg, n[k], θ[k])     (at the start of the segment)
        tangent_end   = R(seg, n[k+1], -φ[k])  (at the end of the segment)

    where R(v, n, α) = v·cos(α) + (n̂ × v)·sin(α) is the Rodrigues rotation.
    Since n̂ ⊥ v, the third Rodrigues term n̂·(n̂·v)·(1-cosα) vanishes.

    The angles θ[k] and φ[k] come from the Hobby system. The relationship
    φ[k] = -θ[k+1] - ψ[k+1] ensures G1 continuity at interior knots.

    The velocity ratios ρ and σ are computed by the Hobby velocity function,
    which depends on sin/cos of θ and φ and the tension parameter.

    Parameters:
        points:      knot points, shape (m, 3)
        theta:       Hobby angles θ_k, shape (m,)
        psi:         turning angles ψ_k, shape (m,)
        normals:     local plane normals, shape (m, 3)
        n_segments:  number of segments (default: m-1 for open curves)
        tension:     tension parameter (default 1.0)

    Returns:
        list of (p0, p1, p2, p3) tuples for each Bezier segment
    """
    m = len(points)
    if n_segments is None:
        n_segments = m - 1

    segments = []
    for k in range(n_segments):
        ki = k % m
        ki1 = (k + 1) % m

        pk = points[ki]
        pk1 = points[ki1]
        seg = pk1 - pk

        # θ_k: tangent angle at the start of segment k (at knot k)
        # φ_k: tangent angle at the end of segment k (at knot k+1)
        # The relation φ_k = -θ_{k+1} - ψ_{k+1} ensures G1 continuity.
        theta_k = theta[ki]
        phi_k = -theta[ki1] - psi[ki1]

        st = np.sin(theta_k)
        ct = np.cos(theta_k)
        sf = np.sin(phi_k)
        cf = np.cos(phi_k)

        # Velocity ratios: determine how far control points lie from knots.
        # ρ controls the start, σ controls the end.
        rho = _velocity(st, ct, sf, cf, tau=tension)
        sigma = _velocity(sf, cf, st, ct, tau=tension)

        # ── Right control point (near p[k]) ──
        # Rotate the segment vector by θ[k] around the local plane normal.
        # By the right-hand rule, positive θ rotates counterclockwise.
        n_k = normals[ki]
        n_k_mag = np.linalg.norm(n_k)
        if n_k_mag > _EPS:
            n_k_hat = n_k / n_k_mag
            tangent_start = seg * ct + np.cross(n_k_hat, seg) * st
        else:
            # Degenerate normal: no rotation, tangent = segment direction
            tangent_start = seg.copy()
        p1 = pk + tangent_start * rho

        # ── Left control point (near p[k+1]) ──
        # Rotate the segment vector by φ[k] in the opposite direction
        # (clockwise around the local plane normal at knot k+1).
        n_k1 = normals[ki1]
        n_k1_mag = np.linalg.norm(n_k1)
        if n_k1_mag > _EPS:
            n_k1_hat = n_k1 / n_k1_mag
            tangent_end = seg * cf - np.cross(n_k1_hat, seg) * sf
        else:
            tangent_end = seg.copy()
        p2 = pk1 - tangent_end * sigma

        segments.append((pk.copy(), p1, p2, pk1.copy()))

    return segments


# ─── Public API ──────────────────────────────────────────────────────────────

def hobby_curve(points, cyclic=False, tension=1.0,
                curl_start=1.0, curl_end=1.0,
                concat=False):
    """
    Compute a Hobby curve (Bezier spline) through the given 3D points.

    For 3D curves, each triple of consecutive points defines a local plane.
    Signed turning angles are produced by consistent normal orientation.
    Control point tangents use Rodrigues rotation around the local normal.

    For planar (XY) curves, results match the original 2D MetaPost algorithm.

    Parameters:
        points: list/array of 3D points, shape (n, 3)
        cyclic: if True, create a closed curve
        tension: tension parameter (default 1.0)
        curl_start: curl at start endpoint (default 1.0)
        curl_end: curl at end endpoint (default 1.0)
        concat: if True, concatenate segments into a single curve

    Returns:
        list of SvCubicBezierCurve (or single concatenated curve if concat=True)
    """
    points = np.asarray(points, dtype=np.float64)
    m = len(points)

    if m < 2:
        raise ValueError("At least 2 points required for a Hobby curve")

    if points.shape[1] == 2:
        points = np.column_stack([points, np.zeros(m)])
    elif points.shape[1] < 2 or points.shape[1] > 3:
        raise ValueError("Points must have 2 or 3 coordinates")

    if cyclic and m < 3:
        raise ValueError("At least 3 points required for a cyclic Hobby curve")

    d, psi, normals = _compute_angles_distances_normals(points, cyclic=cyclic)

    if cyclic:
        theta = _solve_hobby_cyclic(d, psi, m, tension=tension)
        segments_3d = _compute_bezier_segments_full(
            points, theta, psi, normals, n_segments=m, tension=tension)
    else:
        n = m - 1
        theta = _solve_hobby_open(d, psi, n, m, tension=tension,
                                   curl_start=curl_start, curl_end=curl_end)
        segments_3d = _compute_bezier_segments_full(
            points, theta, psi, normals, tension=tension)

    bezier_segments = [
        SvCubicBezierCurve(p0, p1, p2, p3)
        for p0, p1, p2, p3 in segments_3d
    ]

    if concat and len(bezier_segments) > 1:
        return concatenate_nurbs_curves(bezier_segments)

    return bezier_segments
