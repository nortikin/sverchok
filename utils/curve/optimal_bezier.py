# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Optimal Bezier spline construction.

Implements the algorithm from V.V. Borisenko,
"Построение оптимального сплайна Безье" (Construction of Optimal Bezier Spline), 2017.

Given interpolation nodes Q_0, ..., Q_{n-1}, the algorithm builds a C2-continuous
cubic Bezier spline. Three construction methods are provided:

    1. build_c2_bezier_spline()       — uniform parameterization (all segments equal time)
    2. build_c2_bezier_spline_chord() — chord-length parameterization
    3. build_optimal_bezier_spline()  — minimizes integral of |B''(t)|² (bending energy)

All methods produce C2-continuous splines (continuous first and second derivatives).
The optimal method typically reduces bending energy by 5-15% compared to chord-length.
"""

import numpy as np

from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.utils.curve.algorithms import concatenate_curves


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_linear_system(points, alphas):
    """
    Build the linear system for C2 Bezier spline control points.

    For n interpolation nodes Q_0, ..., Q_{n-1} there are m = n - 1 segments.
    Unknowns: A_0, B_0, ..., A_{m-1}, B_{m-1} (2m control points).

    Equation ordering:
        Row 0:  2·A₀ − B₀ = Q₀                              (left boundary)
        For i = 1, ..., m-1:
            C₂: α_{i-1}²·A_{i-1} − 2α_{i-1}²·B_{i-1}
                 + 2α_i²·A_i − α_i²·B_i
                 = (α_i² − α_{i-1}²) · Q_i
            C₁: α_{i-1}·B_{i-1} + α_i·A_i
                 = (α_{i-1} + α_i) · Q_i
        Last:  −A_{m-1} + 2·B_{m-1} = Q_{n-1}               (right boundary)

    Args:
        points: np.array (n, 3) — interpolation nodes.
        alphas: np.array (m,)  — α_i = 1 / t_i.

    Returns:
        (A, b) — coefficient matrix (2m, 2m) and RHS (2m, 3).
    """
    n = len(points)
    m = n - 1
    size = 2 * m

    A = np.zeros((size, size))
    b = np.zeros((size, 3))

    # Left boundary: 2·A₀ − B₀ = Q₀
    A[0, 0] = 2.0
    A[0, 1] = -1.0
    b[0] = points[0]

    # Interior nodes
    row = 1
    for i in range(1, m):
        ap = alphas[i - 1]
        ac = alphas[i]
        ap2 = ap * ap
        ac2 = ac * ac

        ia_p = 2 * (i - 1)
        ib_p = ia_p + 1
        ia_c = 2 * i
        ib_c = ia_c + 1

        # C₂ continuity (second derivative match)
        A[row, ia_p] = ap2
        A[row, ib_p] = -2.0 * ap2
        A[row, ia_c] = 2.0 * ac2
        A[row, ib_c] = -ac2
        b[row] = (ac2 - ap2) * points[i]
        row += 1

        # C₁ continuity (first derivative match)
        A[row, ib_p] = ap
        A[row, ia_c] = ac
        b[row] = (ap + ac) * points[i]
        row += 1

    # Right boundary: −A_{m-1} + 2·B_{m-1} = Q_{n-1}
    ia_last = 2 * (m - 1)
    ib_last = ia_last + 1
    A[row, ia_last] = -1.0
    A[row, ib_last] = 2.0
    b[row] = points[n - 1]

    return A, b


def _compute_control_points(points, alphas):
    """
    Solve for Bezier control points given nodes and parameterization.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).

    Returns:
        np.array (m, 4, 3) — each row [Q_i, A_i, B_i, Q_{i+1}].
    """
    m = len(alphas)
    A, b = _build_linear_system(points, alphas)
    solution = np.linalg.solve(A, b)

    segments = np.empty((m, 4, 3))
    for i in range(m):
        segments[i, 0] = points[i]
        segments[i, 1] = solution[2 * i]
        segments[i, 2] = solution[2 * i + 1]
        segments[i, 3] = points[i + 1]
    return segments


def _bending_energy(points, alphas):
    """
    Compute ∫|B''(t)|² dt for the C2 spline (analytical formula, eq. 21).

    Generalized from the paper's 2D formula to 3D using dot products.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).

    Returns:
        float — total bending energy.
    """
    m = len(alphas)
    segments = _compute_control_points(points, alphas)

    total = 0.0
    for i in range(m):
        alpha = alphas[i]
        Qi = points[i]
        Qip1 = points[i + 1]
        Ai = segments[i, 1]
        Bi = segments[i, 2]

        total += 12.0 * (alpha ** 3) * (
            np.dot(Qi, Qi)
            + 3.0 * (np.dot(Ai, Ai) + np.dot(Bi, Bi))
            + np.dot(Qip1, Qip1)
            + np.dot(Qi, Qip1)
            - 3.0 * (np.dot(Qi, Ai) + np.dot(Ai, Bi) + np.dot(Bi, Qip1))
        )
    return total


def _hill_descent(points, epsilon, max_iterations, delta, acceleration):
    """
    Find optimal segment times t_i by minimizing bending energy.

    Searches over the hyperplane Σ t_i = 1, t_i > 0 using the
    hill-descent (valley-sliding) algorithm from the paper.

    Args:
        points: np.array (n, 3).
        epsilon: convergence tolerance.
        max_iterations: maximum iterations.
        delta: initial step parameter.
        acceleration: step size acceleration factor.

    Returns:
        np.array (m,) — optimal times t_i.
    """
    n = len(points)
    m = n - 1

    # Initial: chord-length proportional
    lengths = np.linalg.norm(points[1:] - points[:-1], axis=1)
    lengths = np.maximum(lengths, 1e-10)
    t = lengths / lengths.sum()

    # Search directions in the hyperplane Σ t_i = 1
    h = 1.0 / (m - 1) if m > 1 else 0.0
    delta_v = -h * np.ones((m, m))
    np.fill_diagonal(delta_v, 1.0)

    step_sizes = np.full(m, delta / m)
    Acc = acceleration

    alphas = 1.0 / np.maximum(t, 1e-15)
    current_energy = _bending_energy(points, alphas)

    for _ in range(max_iterations):
        moved = False

        for i in range(m):
            a0 = Acc
            a1 = 1.0 / Acc
            coeffs = [a0, a1, -a0, -a1]

            best_energy = current_energy
            best_k = -1

            for k, a in enumerate(coeffs):
                candidate = t + a * step_sizes[i] * delta_v[i]
                if (candidate <= 0).any():
                    continue
                candidate_alphas = 1.0 / np.maximum(candidate, 1e-15)
                energy = _bending_energy(points, candidate_alphas)
                if energy < best_energy:
                    best_energy = energy
                    best_k = k

            if best_k >= 0 and best_energy < current_energy:
                t = t + coeffs[best_k] * step_sizes[i] * delta_v[i]
                current_energy = best_energy
                step_sizes[i] *= abs(coeffs[best_k])
                moved = True
            else:
                step_sizes[i] /= Acc

        if not moved and np.all(step_sizes <= epsilon):
            break
        if moved and step_sizes.max() <= epsilon:
            break

    return t


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_c2_bezier_spline(points, concat=True):
    """
    Build a C2-continuous cubic Bezier spline with uniform parameterization.

    All segments receive equal time (t_i = 1/m). Works well when distances
    between consecutive nodes are approximately equal.

    Args:
        points: list or np.array of shape (n, 3). At least 2 points.
        concat: if True, return a single concatenated curve.

    Returns:
        Concatenated curve (if concat=True) or list of SvCubicBezierCurve.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim == 1:
        points = points.reshape(1, 3)
    m = len(points) - 1
    if m < 1:
        raise ValueError("At least two points are required")

    segments = _compute_control_points(points, np.ones(m))
    curves = [SvCubicBezierCurve(*seg) for seg in segments]
    return concatenate_curves(curves) if concat else curves


def build_c2_bezier_spline_chord(points, concat=True):
    """
    Build a C2-continuous cubic Bezier spline with chord-length parameterization.

    Segment times are proportional to distances between nodes (t_i ∝ |Q_i Q_{i+1}|).
    Produces smoother curves than uniform parameterization when node spacing varies.

    Args:
        points: list or np.array of shape (n, 3). At least 2 points.
        concat: if True, return a single concatenated curve.

    Returns:
        Concatenated curve (if concat=True) or list of SvCubicBezierCurve.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim == 1:
        points = points.reshape(1, 3)
    m = len(points) - 1
    if m < 1:
        raise ValueError("At least two points are required")

    lengths = np.linalg.norm(points[1:] - points[:-1], axis=1)
    lengths = np.maximum(lengths, 1e-10)
    alphas = 1.0 / lengths

    segments = _compute_control_points(points, alphas)
    curves = [SvCubicBezierCurve(*seg) for seg in segments]
    return concatenate_curves(curves) if concat else curves


def build_optimal_bezier_spline(points, concat=True, epsilon=1e-8,
                                 max_iterations=1000, delta=0.01,
                                 acceleration=1.2):
    """
    Build an optimal C2-continuous cubic Bezier spline minimizing bending energy.

    Minimizes ∫|B''(t)|² dt over all parameterizations with Σ t_i = 1, t_i > 0.
    Uses hill-descent optimization; typically converges in 65-85 iterations.

    Args:
        points: list or np.array of shape (n, 3). At least 2 points.
        concat: if True, return a single concatenated curve.
        epsilon: convergence tolerance (default 1e-8).
        max_iterations: maximum iterations (default 1000).
        delta: initial step parameter (default 0.01).
        acceleration: step size acceleration factor (default 1.2).

    Returns:
        Concatenated curve (if concat=True) or list of SvCubicBezierCurve.

    Note:
        Complexity is O(n²) — the number of iterations is roughly independent
        of n, and each iteration solves a linear system in O(n).
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim == 1:
        points = points.reshape(1, 3)
    m = len(points) - 1
    if m < 1:
        raise ValueError("At least two points are required")

    t = _hill_descent(points, epsilon, max_iterations, delta, acceleration)
    alphas = 1.0 / np.maximum(t, 1e-15)
    segments = _compute_control_points(points, alphas)

    curves = [SvCubicBezierCurve(*seg) for seg in segments]
    return concatenate_curves(curves) if concat else curves


def build_optimal_bezier_spline_closed(points, concat=True, epsilon=1e-8,
                                        max_iterations=1000, delta=0.01,
                                        acceleration=1.2):
    """
    Build an optimal C2-continuous closed cubic Bezier spline.

    The spline wraps around: the last segment connects Q_{n-1} back to Q_0.
    No boundary conditions are needed — continuity equations apply at all nodes.

    Args:
        points: list or np.array of shape (n, 3). At least 3 points.
        concat: if True, return a single concatenated curve.
        epsilon: convergence tolerance.
        max_iterations: maximum iterations.
        delta: initial step parameter.
        acceleration: acceleration factor.

    Returns:
        Concatenated curve (if concat=True) or list of SvCubicBezierCurve.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim == 1:
        points = points.reshape(1, 3)
    n = len(points)
    m = n  # closed spline: m segments for n nodes

    if m < 3:
        raise ValueError("At least 3 points are required for a closed spline")

    # --- Closed spline helpers ---
    def _closed_system(pts, alphas):
        sz = 2 * m
        A = np.zeros((sz, sz))
        b = np.zeros((sz, 3))
        row = 0
        for i in range(m):
            ip = (i - 1) % m
            ap = alphas[ip]; ac = alphas[i]
            ap2 = ap * ap; ac2 = ac * ac
            ia_p = 2 * ip; ib_p = ia_p + 1
            ia_c = 2 * i; ib_c = ia_c + 1
            # C₂
            A[row, ia_p] = ap2; A[row, ib_p] = -2.0 * ap2
            A[row, ia_c] = 2.0 * ac2; A[row, ib_c] = -ac2
            b[row] = (ac2 - ap2) * pts[i]
            row += 1
            # C₁
            A[row, ib_p] = ap; A[row, ia_c] = ac
            b[row] = (ap + ac) * pts[i]
            row += 1
        return A, b

    def _closed_control_points(pts, alphas):
        A, b = _closed_system(pts, alphas)
        sol = np.linalg.solve(A, b)
        segs = np.empty((m, 4, 3))
        for i in range(m):
            segs[i, 0] = pts[i]
            segs[i, 1] = sol[2 * i]
            segs[i, 2] = sol[2 * i + 1]
            segs[i, 3] = pts[(i + 1) % m]
        return segs

    def _closed_energy(pts, alphas):
        segs = _closed_control_points(pts, alphas)
        total = 0.0
        for i in range(m):
            a = alphas[i]
            Qi = pts[i]; Qip1 = pts[(i + 1) % m]
            Ai = segs[i, 1]; Bi = segs[i, 2]
            total += 12.0 * (a ** 3) * (
                np.dot(Qi, Qi) + 3.0 * (np.dot(Ai, Ai) + np.dot(Bi, Bi))
                + np.dot(Qip1, Qip1) + np.dot(Qi, Qip1)
                - 3.0 * (np.dot(Qi, Ai) + np.dot(Ai, Bi) + np.dot(Bi, Qip1))
            )
        return total

    # --- Hill descent (same as open spline) ---
    diffs = np.diff(points, axis=0, append=points[:1])
    lengths = np.linalg.norm(diffs, axis=1)
    lengths = np.maximum(lengths, 1e-10)
    t = lengths / lengths.sum()

    h = 1.0 / (m - 1)
    delta_v = -h * np.ones((m, m))
    np.fill_diagonal(delta_v, 1.0)
    step_sizes = np.full(m, delta / m)
    Acc = acceleration

    alphas = 1.0 / np.maximum(t, 1e-15)
    current_energy = _closed_energy(points, alphas)

    for _ in range(max_iterations):
        moved = False
        for i in range(m):
            a0 = Acc; a1 = 1.0 / Acc
            coeffs = [a0, a1, -a0, -a1]
            best_e = current_energy; best_k = -1
            for k, a in enumerate(coeffs):
                cand = t + a * step_sizes[i] * delta_v[i]
                if (cand <= 0).any():
                    continue
                e = _closed_energy(points, 1.0 / np.maximum(cand, 1e-15))
                if e < best_e:
                    best_e = e; best_k = k
            if best_k >= 0 and best_e < current_energy:
                t = t + coeffs[best_k] * step_sizes[i] * delta_v[i]
                current_energy = best_e
                step_sizes[i] *= abs(coeffs[best_k])
                moved = True
            else:
                step_sizes[i] /= Acc
        if not moved and np.all(step_sizes <= epsilon):
            break
        if moved and step_sizes.max() <= epsilon:
            break

    alphas = 1.0 / np.maximum(t, 1e-15)
    segments = _closed_control_points(points, alphas)
    curves = [SvCubicBezierCurve(*seg) for seg in segments]
    return concatenate_curves(curves) if concat else curves
