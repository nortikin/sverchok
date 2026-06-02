# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Optimal Bezier spline construction.

Implements the algorithm from V.V. Borisenko,
"Construction of Optimal Bezier Spline" ("Построение оптимального сплайна Безье"), 2017.

Given interpolation nodes Q_0, ..., Q_{n-1}, the algorithm builds a C2-continuous
cubic Bezier spline. A single public entry point is provided:

    optimal_bezier_spline(points, cyclic=False, metric='OPTIMAL', ...)

Parameterization modes (metric):
    'POINTS'  — uniform (all segments equal time)
    'DISTANCE'— chord-length (segment times proportional to node distances)
    'OPTIMAL' — hill-descent minimization of bending energy ∫|B''(t)|²

Topology (cyclic):
    False — open spline (clamped boundary conditions)
    True  — closed spline (continuity at all nodes, last segment wraps to Q_0)
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Guard against division by zero when computing alphas from segment times.
_ALPHA_MIN = 1e-15

# Minimum segment length in chord-length parameterization.
_LENGTH_MIN = 1e-10

import numpy as np

from sverchok.core.sv_custom_exceptions import SvInvalidInputException
from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.utils.curve.algorithms import concatenate_curves


# ---------------------------------------------------------------------------
# Open spline helpers
# ---------------------------------------------------------------------------

def _open_linear_system(points, alphas):
    """
    Build the linear system for an open C2 Bezier spline.

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


def _open_control_points(points, alphas):
    """
    Solve for Bezier control points of an open spline.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).

    Returns:
        np.array (m, 4, 3) — each row [Q_i, A_i, B_i, Q_{i+1}].
    """
    m = len(alphas)
    A, b = _open_linear_system(points, alphas)
    try:
        solution = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        raise SvInvalidInputException(
            "Cannot compute spline: interpolation nodes produce a singular "
            "linear system (e.g., collinear or duplicate points)"
        )

    segments = np.empty((m, 4, 3))
    for i in range(m):
        segments[i, 0] = points[i]
        segments[i, 1] = solution[2 * i]
        segments[i, 2] = solution[2 * i + 1]
        segments[i, 3] = points[i + 1]
    return segments


def _bending_energy_from_segments(segments, alphas):
    """
    Compute ∫|B''(t)|² dt from pre-computed Bezier segments (eq. 21).

    For each cubic Bezier segment [Q, A, B, Q'] with segment time t_i
    (alpha_i = 1 / t_i), the contribution to the bending energy is
    12 · α³ · (|Q|² + 3(|A|² + |B|²) + |Q'|² + Q·Q' - 3(Q·A + A·B + B·Q')).

    Generalized from the paper's 2D formula to 3D using dot products.

    Args:
        segments: np.array (m, 4, 3) — each row [Q_i, A_i, B_i, Q_{i+1}].
        alphas: np.array (m,) — α_i = 1 / t_i.

    Returns:
        float — total bending energy.
    """
    total = 0.0
    for i in range(len(alphas)):
        a = alphas[i]
        Qi = segments[i, 0]
        Ai = segments[i, 1]
        Bi = segments[i, 2]
        Qip1 = segments[i, 3]
        total += 12.0 * (a ** 3) * (
            np.dot(Qi, Qi)
            + 3.0 * (np.dot(Ai, Ai) + np.dot(Bi, Bi))
            + np.dot(Qip1, Qip1)
            + np.dot(Qi, Qip1)
            - 3.0 * (np.dot(Qi, Ai) + np.dot(Ai, Bi) + np.dot(Bi, Qip1))
        )
    return total


def _open_bending_energy(points, alphas):
    """
    Compute ∫|B''(t)|² dt for an open C2 spline.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).

    Returns:
        float — total bending energy.
    """
    segments = _open_control_points(points, alphas)
    return _bending_energy_from_segments(segments, alphas)


# ---------------------------------------------------------------------------
# Closed spline helpers
# ---------------------------------------------------------------------------

def _closed_linear_system(points, alphas, m):
    """
    Build the linear system for a closed C2 Bezier spline.

    For n interpolation nodes Q_0, ..., Q_{n-1} there are m = n segments
    (last segment wraps from Q_{n-1} to Q_0). No boundary conditions —
    continuity equations apply at every node.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).
        m: number of segments (= n for closed spline).

    Returns:
        (A, b) — coefficient matrix (2m, 2m) and RHS (2m, 3).
    """
    sz = 2 * m
    A = np.zeros((sz, sz))
    b = np.zeros((sz, 3))
    row = 0
    for i in range(m):
        ip = (i - 1) % m
        ap = alphas[ip]
        ac = alphas[i]
        ap2 = ap * ap
        ac2 = ac * ac
        ia_p = 2 * ip
        ib_p = ia_p + 1
        ia_c = 2 * i
        ib_c = ia_c + 1
        # C₂
        A[row, ia_p] = ap2
        A[row, ib_p] = -2.0 * ap2
        A[row, ia_c] = 2.0 * ac2
        A[row, ib_c] = -ac2
        b[row] = (ac2 - ap2) * points[i]
        row += 1
        # C₁
        A[row, ib_p] = ap
        A[row, ia_c] = ac
        b[row] = (ap + ac) * points[i]
        row += 1
    return A, b


def _closed_control_points(points, alphas, m):
    """
    Solve for Bezier control points of a closed spline.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).
        m: number of segments (= n for closed spline).

    Returns:
        np.array (m, 4, 3) — each row [Q_i, A_i, B_i, Q_{(i+1)%n}].
    """
    A, b = _closed_linear_system(points, alphas, m)
    try:
        sol = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        raise SvInvalidInputException(
            "Cannot compute closed spline: interpolation nodes produce a "
            "singular linear system (e.g., collinear or duplicate points)"
        )
    segs = np.empty((m, 4, 3))
    for i in range(m):
        segs[i, 0] = points[i]
        segs[i, 1] = sol[2 * i]
        segs[i, 2] = sol[2 * i + 1]
        segs[i, 3] = points[(i + 1) % m]
    return segs


def _closed_bending_energy(points, alphas, m):
    """
    Compute ∫|B''(t)|² dt for a closed C2 spline.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).
        m: number of segments (= n for closed spline).

    Returns:
        float — total bending energy.
    """
    segments = _closed_control_points(points, alphas, m)
    return _bending_energy_from_segments(segments, alphas)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _segment_diffs(points, cyclic):
    """
    Compute vectors from each node to the next.

    Args:
        points: np.array (n, 3).
        cyclic: if True, the last vector wraps from points[-1] to points[0].

    Returns:
        np.array (m, 3) where m = n if cyclic else n - 1.
    """
    if cyclic:
        return np.diff(points, axis=0, append=points[:1])
    return points[1:] - points[:-1]


def _chord_lengths(points, cyclic):
    """
    Compute segment lengths for chord-length parameterization.

    Args:
        points: np.array (n, 3).
        cyclic: if True, include the wrap-around segment.

    Returns:
        np.array (m,) — segment lengths, floored at _LENGTH_MIN.
    """
    diffs = _segment_diffs(points, cyclic)
    lengths = np.linalg.norm(diffs, axis=1)
    return np.maximum(lengths, _LENGTH_MIN)


# ---------------------------------------------------------------------------
# Shared hill-descent optimizer
# ---------------------------------------------------------------------------

def _compute_optimal_times(points, m, energy_fn, epsilon,
                           max_iterations, delta, acceleration):
    """
    Compute optimal segment times via hill-descent.

    This is the concrete implementation that inlines the optimization loop
    for performance (avoids closure overhead on energy_fn calls).

    Args:
        points: np.array (n, 3).
        m: number of segments.
        energy_fn: callable(points, alphas, m) -> float.
        epsilon: convergence tolerance.
        max_iterations: maximum iterations.
        delta: initial step parameter.
        acceleration: step size acceleration factor.

    Returns:
        np.array (m,) — optimal times t_i.
    """
    cyclic = m == len(points)

    # Initial: chord-length proportional
    lengths = _chord_lengths(points, cyclic)
    t = lengths / lengths.sum()

    # Search directions in the hyperplane Σ t_i = 1
    h = 1.0 / (m - 1) if m > 1 else 0.0
    delta_v = -h * np.ones((m, m))
    np.fill_diagonal(delta_v, 1.0)

    step_sizes = np.full(m, delta / m)
    Acc = acceleration

    alphas = 1.0 / np.maximum(t, _ALPHA_MIN)
    current_energy = energy_fn(points, alphas, m)

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
                candidate_alphas = 1.0 / np.maximum(candidate, _ALPHA_MIN)
                energy = energy_fn(points, candidate_alphas, m)
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
# Internal: energy wrappers that match the unified signature (pts, alphas, m)
# ---------------------------------------------------------------------------

def _open_energy_wrapper(pts, alphas, m):
    return _open_bending_energy(pts, alphas)


def _closed_energy_wrapper(pts, alphas, m):
    return _closed_bending_energy(pts, alphas, m)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def optimal_bezier_spline(
        points,
        cyclic=False,
        metric='OPTIMAL',
        concat=True,
        epsilon=1e-8,
        max_iterations=1000,
        delta=0.01,
        acceleration=1.2):
    """
    Build a C2-continuous cubic Bezier spline through interpolation nodes.

    This is the single entry point for all spline construction variants.
    The ``metric`` parameter selects the parameterization strategy;
    the ``cyclic`` parameter selects open vs. closed topology.

    Args:
        points: list or np.array of shape (n, 3).
            At least 2 points for open splines, at least 3 for closed.
        cyclic: if True, build a closed spline that wraps Q_{n-1} back to Q_0.
            Default False (open spline with clamped boundaries).
        metric: parameterization strategy. One of:

            - ``'POINTS'``  — uniform (all segments receive equal time).
              Fast; works well when node spacing is roughly even.
            - ``'DISTANCE'``— chord-length (segment times proportional to
              distances between consecutive nodes). Better for uneven spacing.
            - ``'OPTIMAL'`` — hill-descent minimization of bending energy
              ∫|B''(t)|². Typically 5-15% lower energy than chord-length.

            Default ``'OPTIMAL'``.
        concat: if True, return a single concatenated curve.
            If False, return a list of SvCubicBezierCurve segments.
        epsilon: convergence tolerance for hill-descent (default 1e-8).
        max_iterations: maximum hill-descent iterations (default 1000).
        delta: initial step parameter for hill-descent (default 0.01).
        acceleration: step-size acceleration factor (default 1.2).

    Returns:
        Concatenated curve (if concat=True) or list of SvCubicBezierCurve.

    Raises:
        ValueError: If too few points are provided.
        SvInvalidInputException: If the linear system is singular
            (e.g., all points collinear or duplicate).

    Note:
        Complexity is O(K · n³) where K is the number of hill-descent
        iterations (roughly independent of n). Each iteration evaluates
        up to 4n candidate alphas, and each evaluation solves a linear
        system in O(n³). In practice K is small (typically < 50).
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim == 1:
        points = points.reshape(1, 3)
    n = len(points)

    # --- Validate point count ---
    if cyclic:
        if n < 3:
            raise ValueError("At least 3 points are required for a closed spline")
        m = n
    else:
        if n < 2:
            raise ValueError("At least two points are required")
        m = n - 1

    # --- Compute alphas based on metric ---
    if metric == 'POINTS':
        # Uniform parameterization: all segments equal time → alphas all 1
        alphas = np.ones(m)

    elif metric == 'DISTANCE':
        # Chord-length parameterization
        lengths = _chord_lengths(points, cyclic)
        alphas = 1.0 / lengths

    elif metric == 'OPTIMAL':
        # Hill-descent optimization
        energy_fn = _closed_energy_wrapper if cyclic else _open_energy_wrapper
        t = _compute_optimal_times(
            points, m, energy_fn, epsilon, max_iterations, delta, acceleration)
        alphas = 1.0 / np.maximum(t, _ALPHA_MIN)

    else:
        raise ValueError(
            f"Unknown metric '{metric}'. "
            "Expected one of: 'POINTS', 'DISTANCE', 'OPTIMAL'")

    # --- Solve for control points ---
    if cyclic:
        segments = _closed_control_points(points, alphas, m)
    else:
        segments = _open_control_points(points, alphas)

    # --- Build curves ---
    curves = [SvCubicBezierCurve(*seg) for seg in segments]
    return concatenate_curves(curves) if concat else curves



