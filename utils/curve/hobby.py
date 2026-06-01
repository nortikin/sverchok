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

    # segment lengths
    if cyclic:
        d = np.array([np.linalg.norm(points[(k + 1) % m] - points[k])
                       for k in range(m)])
    else:
        d = np.array([np.linalg.norm(points[k + 1] - points[k])
                       for k in range(m - 1)])

    normals = np.zeros((m, 3))
    psi = np.zeros(m)
    has_normal = np.zeros(m, dtype=bool)

    for k in range(m):
        if not cyclic and (k == 0 or k == m - 1):
            continue

        v_in = points[k] - points[(k - 1) % m]
        v_out = points[(k + 1) % m] - points[k]

        n_in = np.linalg.norm(v_in)
        n_out = np.linalg.norm(v_out)
        if n_in < 1e-15 or n_out < 1e-15:
            continue

        n = np.cross(v_in, v_out)
        n_mag = np.linalg.norm(n)

        cos_psi = np.dot(v_in, v_out) / (n_in * n_out)
        psi[k] = np.arccos(np.clip(cos_psi, -1.0, 1.0))

        if n_mag > _EPS:
            normals[k] = n
            has_normal[k] = True

    # consistent orientation -> signed psi
    _make_normals_consistent(normals, psi, has_normal, m, cyclic)
    # fill gaps
    _fill_fallback_normals(normals, has_normal, m, cyclic)

    return d, psi, normals


def _make_normals_consistent(normals, psi, has_normal, m, cyclic):
    """Walk through knots; flip n[k] and psi[k] if dot(n[k], n[prev]) < 0."""
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
    """Borrow normals from nearest non-zero neighbor."""
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

def _mp_curl_ratio(gamma, a_tension, b_tension):
    alpha = 1.0 / a_tension
    beta = 1.0 / b_tension
    g = float(gamma)

    if alpha <= beta:
        ff = (alpha / beta) ** 2
        g = g * ff
        denom = g * alpha + 3.0
    else:
        ff = (beta / alpha) ** 2
        arg1 = beta * ff
        beta = arg1
        denom = g * alpha + ff / 3.0

    denom -= beta
    num = g * (3.0 - alpha) + beta

    if num >= 4.0 * denom:
        return 4.0
    return num / denom


# ─── Hobby system solvers ────────────────────────────────────────────────────

def _solve_hobby_open(d, psi, n, m, tension=1.0, curl_start=1.0, curl_end=1.0):
    """Solve open-curve Hobby system (Thomas algorithm, Robin BCs)."""
    tau = max(tension, 0.75)

    if abs(tau - 1.0) < 1e-15:
        aa = 0.5
    else:
        aa = 1.0 / (3.0 * tau - 1.0)
    bb = aa

    uu0 = _mp_curl_ratio(curl_start, tau, tau)
    ff_end = _mp_curl_ratio(curl_end, tau, tau)

    uu = np.zeros(m)
    vv = np.zeros(m)

    # Start BC: theta[0] = vv[0] - uu[0]*theta[1], vv[0] = -psi[1]*uu[0]
    uu[0] = uu0
    vv[0] = -psi[1] * uu0

    # Forward elimination
    for k in range(1, n):
        if abs(tau - 1.0) < 1e-15:
            dd = 2.0 * d[k]
            ee = 2.0 * d[k - 1]
        else:
            dd = d[k] * (3.0 - 1.0 / tau)
            ee = d[k - 1] * (3.0 - 1.0 / tau)

        cc_val = 1.0 - uu[k - 1] * aa
        ff = ee / (dd * cc_val + ee)
        uu[k] = ff * bb

        acc = -psi[k + 1] * uu[k]
        ff_new = (1.0 - ff) / cc_val
        acc -= psi[k] * ff_new
        ff_new2 = ff_new * aa
        vv[k] = acc - vv[k - 1] * ff_new2

    # End BC
    denom_end = 1.0 - ff_end * uu[n - 1]
    theta_n = 0.0 if abs(denom_end) < 1e-15 else -(vv[n - 1] * ff_end) / denom_end

    # Back-substitution
    theta = np.zeros(m)
    theta[m - 1] = theta_n
    for k in range(m - 2, -1, -1):
        theta[k] = vv[k] - theta[k + 1] * uu[k]

    return theta


def _solve_hobby_cyclic(d, psi, m, tension=1.0):
    """Solve cyclic Hobby system."""
    tau = max(tension, 0.75)
    factor = 3.0 * tau - 1.0

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

    try:
        return np.linalg.solve(A, rhs)
    except np.linalg.LinAlgError:
        return np.zeros(m)


# ─── Bezier control points (3D, Rodrigues) ───────────────────────────────────

def _compute_bezier_segments_full(points, theta, psi, normals, n_segments=None,
                                   tension=1.0):
    """
    Compute Bezier control points using Rodrigues rotation in 3D.

    For segment k (p[k] -> p[k+1]):
        p1 = p[k] + R(seg, n[k], theta[k]) * rho
        p2 = p[k+1] - R(seg, n[k+1], -phi[k]) * sigma

    where R(v, n, a) = v*cos(a) + (n_hat x v)*sin(a)  (Rodrigues, n perp v)
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

        theta_k = theta[ki]
        phi_k = -theta[ki1] - psi[ki1]

        st = np.sin(theta_k)
        ct = np.cos(theta_k)
        sf = np.sin(phi_k)
        cf = np.cos(phi_k)

        rho = _velocity(st, ct, sf, cf, tau=tension)
        sigma = _velocity(sf, cf, st, ct, tau=tension)

        # p1: rotate seg by theta_k around n[ki] (CCW by right-hand rule)
        n_k = normals[ki]
        n_k_mag = np.linalg.norm(n_k)
        if n_k_mag > _EPS:
            n_k_hat = n_k / n_k_mag
            tangent_start = seg * ct + np.cross(n_k_hat, seg) * st
        else:
            tangent_start = seg.copy()
        p1 = pk + tangent_start * rho

        # p2: rotate seg by phi_k around n[ki1] (CW = opposite direction)
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
