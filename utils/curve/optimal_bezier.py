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
        (matrix, rhs) — coefficient matrix (2m, 2m) and RHS (2m, 3).
    """
    num_nodes = len(points)
    num_segs = num_nodes - 1
    matrix_size = 2 * num_segs

    matrix = np.zeros((matrix_size, matrix_size))
    rhs = np.zeros((matrix_size, 3))

    # Left boundary condition: 2·A₀ − B₀ = Q₀
    matrix[0, 0] = 2.0
    matrix[0, 1] = -1.0
    rhs[0] = points[0]

    # Interior nodes: C1 and C2 continuity between adjacent segments
    row = 1
    for seg in range(1, num_segs):
        alpha_prev = alphas[seg - 1]
        alpha_curr = alphas[seg]
        alpha_prev_sq = alpha_prev * alpha_prev
        alpha_curr_sq = alpha_curr * alpha_curr

        # Column indices for the four unknown control points involved:
        #   A_{seg-1}, B_{seg-1} from the previous segment
        #   A_{seg},   B_{seg}   from the current segment
        col_A_prev = 2 * (seg - 1)
        col_B_prev = col_A_prev + 1
        col_A_curr = 2 * seg
        col_B_curr = col_A_curr + 1

        # C₂ continuity: second derivatives match at the shared node
        matrix[row, col_A_prev] = alpha_prev_sq
        matrix[row, col_B_prev] = -2.0 * alpha_prev_sq
        matrix[row, col_A_curr] = 2.0 * alpha_curr_sq
        matrix[row, col_B_curr] = -alpha_curr_sq
        rhs[row] = (alpha_curr_sq - alpha_prev_sq) * points[seg]
        row += 1

        # C₁ continuity: first derivatives match at the shared node
        matrix[row, col_B_prev] = alpha_prev
        matrix[row, col_A_curr] = alpha_curr
        rhs[row] = (alpha_prev + alpha_curr) * points[seg]
        row += 1

    # Right boundary condition: −A_{last} + 2·B_{last} = Q_{n-1}
    col_A_last = 2 * (num_segs - 1)
    col_B_last = col_A_last + 1
    matrix[row, col_A_last] = -1.0
    matrix[row, col_B_last] = 2.0
    rhs[row] = points[num_nodes - 1]

    return matrix, rhs


def _open_control_points(points, alphas):
    """
    Solve for Bezier control points of an open spline.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).

    Returns:
        np.array (m, 4, 3) — each row [Q_i, A_i, B_i, Q_{i+1}].
    """
    num_segs = len(alphas)
    matrix, rhs = _open_linear_system(points, alphas)
    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        raise SvInvalidInputException(
            "Cannot compute spline: interpolation nodes produce a singular "
            "linear system (e.g., collinear or duplicate points)"
        )

    # Pack solution into Bezier segment format: [Q_start, A, B, Q_end]
    segments = np.empty((num_segs, 4, 3))
    for seg in range(num_segs):
        segments[seg, 0] = points[seg]
        segments[seg, 1] = solution[2 * seg]       # A control point
        segments[seg, 2] = solution[2 * seg + 1]   # B control point
        segments[seg, 3] = points[seg + 1]
    return segments


def _bending_energy_from_segments(segments, alphas):
    """
    Compute ∫|B''(t)|² dt from pre-computed Bezier segments (eq. 21).

    For each cubic Bezier segment [Q_start, A, B, Q_end] with parameter
    alpha = 1 / segment_time, the energy contribution is:

        12 · α³ · (|Q_start|² + 3(|A|² + |B|²) + |Q_end|²
                   + Q_start·Q_end
                   - 3(Q_start·A + A·B + B·Q_end))

    Vectorized: all dot products computed across segments simultaneously.
    """
    q_start = segments[:, 0]
    inner_a = segments[:, 1]
    inner_b = segments[:, 2]
    q_end = segments[:, 3]

    dot = lambda x, y: np.sum(x * y, axis=1)

    # The bracketed expression from eq. (21), evaluated per-segment
    bracket = (
        dot(q_start, q_start)
        + 3.0 * (dot(inner_a, inner_a) + dot(inner_b, inner_b))
        + dot(q_end, q_end)
        + dot(q_start, q_end)
        - 3.0 * (dot(q_start, inner_a) + dot(inner_a, inner_b)
                 + dot(inner_b, q_end))
    )

    # Scale by α³ and sum across all segments
    return float(np.sum(12.0 * (alphas ** 3) * bracket))


def _open_bending_energy(points, alphas):
    """Compute ∫|B''(t)|² dt for an open C2 spline."""
    segments = _open_control_points(points, alphas)
    return _bending_energy_from_segments(segments, alphas)


# ---------------------------------------------------------------------------
# Closed spline helpers
# ---------------------------------------------------------------------------

def _closed_linear_system(points, alphas, num_segs):
    """
    Build the linear system for a closed C2 Bezier spline.

    Unlike the open spline, there are no boundary conditions — continuity
    equations apply at every node, including the wrap-around from last
    segment back to the first.

    Args:
        points: np.array (n, 3).
        alphas: np.array (m,).
        num_segs: number of segments (= n for closed spline).

    Returns:
        (matrix, rhs) — coefficient matrix (2m, 2m) and RHS (2m, 3).
    """
    matrix_size = 2 * num_segs
    matrix = np.zeros((matrix_size, matrix_size))
    rhs = np.zeros((matrix_size, 3))
    row = 0

    for seg in range(num_segs):
        prev_seg = (seg - 1) % num_segs  # wraps: segment before 0 is the last
        alpha_prev = alphas[prev_seg]
        alpha_curr = alphas[seg]
        alpha_prev_sq = alpha_prev * alpha_prev
        alpha_curr_sq = alpha_curr * alpha_curr

        col_A_prev = 2 * prev_seg
        col_B_prev = col_A_prev + 1
        col_A_curr = 2 * seg
        col_B_curr = col_A_curr + 1

        # C₂ continuity at node Q_{seg}
        matrix[row, col_A_prev] = alpha_prev_sq
        matrix[row, col_B_prev] = -2.0 * alpha_prev_sq
        matrix[row, col_A_curr] = 2.0 * alpha_curr_sq
        matrix[row, col_B_curr] = -alpha_curr_sq
        rhs[row] = (alpha_curr_sq - alpha_prev_sq) * points[seg]
        row += 1

        # C₁ continuity at node Q_{seg}
        matrix[row, col_B_prev] = alpha_prev
        matrix[row, col_A_curr] = alpha_curr
        rhs[row] = (alpha_prev + alpha_curr) * points[seg]
        row += 1

    return matrix, rhs


def _closed_control_points(points, alphas, num_segs):
    """
    Solve for Bezier control points of a closed spline.

    Returns:
        np.array (m, 4, 3) — each row [Q_i, A_i, B_i, Q_{(i+1)%n}].
    """
    matrix, rhs = _closed_linear_system(points, alphas, num_segs)
    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        raise SvInvalidInputException(
            "Cannot compute closed spline: interpolation nodes produce a "
            "singular linear system (e.g., collinear or duplicate points)"
        )

    segments = np.empty((num_segs, 4, 3))
    for seg in range(num_segs):
        segments[seg, 0] = points[seg]
        segments[seg, 1] = solution[2 * seg]
        segments[seg, 2] = solution[2 * seg + 1]
        segments[seg, 3] = points[(seg + 1) % num_segs]
    return segments


def _closed_bending_energy(points, alphas, num_segs):
    """Compute ∫|B''(t)|² dt for a closed C2 spline."""
    segments = _closed_control_points(points, alphas, num_segs)
    return _bending_energy_from_segments(segments, alphas)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _segment_diffs(points, cyclic):
    """
    Compute vectors from each node to the next.

    For cyclic splines, the last vector wraps from points[-1] to points[0].
    """
    if cyclic:
        return np.diff(points, axis=0, append=points[:1])
    return points[1:] - points[:-1]


def _chord_lengths(points, cyclic):
    """
    Compute segment lengths for chord-length parameterization.

    Lengths are floored at _LENGTH_MIN to avoid degenerate zero-length segments.
    """
    diffs = _segment_diffs(points, cyclic)
    lengths = np.linalg.norm(diffs, axis=1)
    return np.maximum(lengths, _LENGTH_MIN)


# ---------------------------------------------------------------------------
# Optimized energy evaluators
#
# These closures combine three steps into one call:
#   1. Update the linear system matrix (in-place, reusing pre-allocated arrays)
#   2. Solve for control points
#   3. Compute bending energy (vectorized)
#
# This avoids creating intermediate segment arrays and eliminates repeated
# memory allocation. The matrix has a fixed sparsity pattern — only the
# alpha-dependent coefficients change between calls.
# ---------------------------------------------------------------------------

def _make_open_energy_eval(points):
    """
    Build a closure that evaluates bending energy for an open spline.

    The closure pre-allocates the system matrix and RHS, setting the fixed
    boundary rows once. Each call only updates the interior rows that depend
    on the current alpha values, then solves and computes energy.

    Args:
        points: np.array (n, 3) — interpolation nodes.

    Returns:
        Callable: eval_energy(alphas) -> float
    """
    num_nodes = len(points)
    num_segs = num_nodes - 1
    matrix_size = 2 * num_segs

    # Pre-allocate system matrix and RHS
    matrix = np.zeros((matrix_size, matrix_size))
    rhs = np.zeros((matrix_size, 3))

    # Fixed boundary rows — set once, never change during optimization
    # Left:  2·A₀ − B₀ = Q₀
    matrix[0, 0] = 2.0
    matrix[0, 1] = -1.0
    rhs[0] = points[0]
    # Right: −A_{last} + 2·B_{last} = Q_{n-1}
    col_A_last = 2 * (num_segs - 1)
    col_B_last = col_A_last + 1
    last_row = 2 * num_segs - 1
    matrix[last_row, col_A_last] = -1.0
    matrix[last_row, col_B_last] = 2.0
    rhs[last_row] = points[num_nodes - 1]

    # Pre-compute the part of the energy bracket that depends only on
    # interpolation nodes (constant across all optimization iterations)
    q_start = points[:-1]
    q_end = points[1:]
    energy_base = (
        np.sum(q_start * q_start, axis=1)
        + np.sum(q_end * q_end, axis=1)
        + np.sum(q_start * q_end, axis=1)
    )

    def eval_energy(alphas):
        # Update only the interior rows (alpha-dependent continuity equations)
        row = 1
        for seg in range(1, num_segs):
            alpha_prev = alphas[seg - 1]
            alpha_curr = alphas[seg]
            alpha_prev_sq = alpha_prev * alpha_prev
            alpha_curr_sq = alpha_curr * alpha_curr

            col_A_prev = 2 * (seg - 1)
            col_B_prev = col_A_prev + 1
            col_A_curr = 2 * seg
            col_B_curr = col_A_curr + 1

            # C₂ row
            matrix[row, col_A_prev] = alpha_prev_sq
            matrix[row, col_B_prev] = -2.0 * alpha_prev_sq
            matrix[row, col_A_curr] = 2.0 * alpha_curr_sq
            matrix[row, col_B_curr] = -alpha_curr_sq
            rhs[row] = (alpha_curr_sq - alpha_prev_sq) * points[seg]
            row += 1
            # C₁ row
            matrix[row, col_B_prev] = alpha_prev
            matrix[row, col_A_curr] = alpha_curr
            rhs[row] = (alpha_prev + alpha_curr) * points[seg]
            row += 1

        # Solve and extract inner control points
        solution = np.linalg.solve(matrix, rhs)
        inner_a = solution[0::2]  # A_0, A_1, ..., A_{m-1}
        inner_b = solution[1::2]  # B_0, B_1, ..., B_{m-1}

        # Vectorized energy: add alpha-dependent terms to the pre-computed base
        bracket = (
            energy_base
            + 3.0 * (np.sum(inner_a * inner_a, axis=1)
                     + np.sum(inner_b * inner_b, axis=1))
            - 3.0 * (np.sum(q_start * inner_a, axis=1)
                     + np.sum(inner_a * inner_b, axis=1)
                     + np.sum(inner_b * q_end, axis=1))
        )
        return float(np.sum(12.0 * (alphas ** 3) * bracket))

    return eval_energy


def _make_closed_energy_eval(points, num_segs):
    """
    Build a closure that evaluates bending energy for a closed spline.

    Same idea as the open version, but all rows are alpha-dependent
    (no fixed boundary conditions).

    Args:
        points: np.array (n, 3).
        num_segs: number of segments (= n for closed spline).

    Returns:
        Callable: eval_energy(alphas) -> float
    """
    matrix_size = 2 * num_segs
    matrix = np.zeros((matrix_size, matrix_size))
    rhs = np.zeros((matrix_size, 3))

    # Pre-compute constant part of energy bracket
    q_start = points
    q_end = np.roll(points, -1, axis=0)  # Q_{i+1} with wrap-around
    energy_base = (
        np.sum(q_start * q_start, axis=1)
        + np.sum(q_end * q_end, axis=1)
        + np.sum(q_start * q_end, axis=1)
    )

    def eval_energy(alphas):
        row = 0
        for seg in range(num_segs):
            prev_seg = (seg - 1) % num_segs
            alpha_prev = alphas[prev_seg]
            alpha_curr = alphas[seg]
            alpha_prev_sq = alpha_prev * alpha_prev
            alpha_curr_sq = alpha_curr * alpha_curr

            col_A_prev = 2 * prev_seg
            col_B_prev = col_A_prev + 1
            col_A_curr = 2 * seg
            col_B_curr = col_A_curr + 1

            # C₂ continuity row
            matrix[row, col_A_prev] = alpha_prev_sq
            matrix[row, col_B_prev] = -2.0 * alpha_prev_sq
            matrix[row, col_A_curr] = 2.0 * alpha_curr_sq
            matrix[row, col_B_curr] = -alpha_curr_sq
            rhs[row] = (alpha_curr_sq - alpha_prev_sq) * points[seg]
            row += 1
            # C₁ continuity row
            matrix[row, col_B_prev] = alpha_prev
            matrix[row, col_A_curr] = alpha_curr
            rhs[row] = (alpha_prev + alpha_curr) * points[seg]
            row += 1

        # Solve and compute energy
        solution = np.linalg.solve(matrix, rhs)
        inner_a = solution[0::2]
        inner_b = solution[1::2]

        bracket = (
            energy_base
            + 3.0 * (np.sum(inner_a * inner_a, axis=1)
                     + np.sum(inner_b * inner_b, axis=1))
            - 3.0 * (np.sum(q_start * inner_a, axis=1)
                     + np.sum(inner_a * inner_b, axis=1)
                     + np.sum(inner_b * q_end, axis=1))
        )
        return float(np.sum(12.0 * (alphas ** 3) * bracket))

    return eval_energy


# ---------------------------------------------------------------------------
# Hill-descent optimizer
#
# Minimizes bending energy by adjusting segment times t_i subject to
# the constraint Σ t_i = 1, t_i > 0.
#
# The search space is an (m-1)-dimensional simplex. For each time t_i,
# we try four candidate moves (two directions × two step sizes) and
# accept the one that reduces energy the most. Step sizes grow when
# progress is made and shrink when stuck, enabling both exploration
# and fine convergence.
# ---------------------------------------------------------------------------

def _compute_optimal_times(points, num_segs, epsilon, max_iterations,
                            delta, acceleration, cyclic):
    """
    Find segment times that minimize the spline's bending energy.

    Args:
        points: np.array (n, 3).
        num_segs: number of spline segments.
        epsilon: step-size threshold for convergence.
        max_iterations: upper bound on outer loop iterations.
        delta: initial total step budget (divided evenly among segments).
        acceleration: factor for growing/shrinking individual step sizes.
        cyclic: True for closed spline topology.

    Returns:
        np.array (m,) — optimal normalized segment times (sum to 1).
    """
    # Build the optimized energy evaluator (pre-allocates matrices)
    if cyclic:
        energy_eval = _make_closed_energy_eval(points, num_segs)
    else:
        energy_eval = _make_open_energy_eval(points)

    # Start from chord-length parameterization — a good initial guess
    lengths = _chord_lengths(points, cyclic)
    segment_times = lengths / lengths.sum()

    # Search directions: moving along direction i increases t_i while
    # decreasing all other t_j proportionally, keeping Σ t = 1.
    # Each row of direction_matrix is a valid displacement on the simplex.
    share = 1.0 / (num_segs - 1) if num_segs > 1 else 0.0
    direction_matrix = -share * np.ones((num_segs, num_segs))
    np.fill_diagonal(direction_matrix, 1.0)

    # Per-dimension adaptive step sizes
    step_sizes = np.full(num_segs, delta / num_segs)

    # Evaluate initial energy
    current_alphas = 1.0 / np.maximum(segment_times, _ALPHA_MIN)
    best_energy = energy_eval(current_alphas)

    for _ in range(max_iterations):
        made_progress = False

        for dim in range(num_segs):
            # Try four candidates: ±acceleration × current_step
            # Larger steps explore, smaller steps refine
            scale_up = acceleration
            scale_down = 1.0 / acceleration
            candidate_scales = [scale_up, scale_down, -scale_up, -scale_down]

            local_best_energy = best_energy
            local_best_idx = -1

            for idx, scale in enumerate(candidate_scales):
                trial_times = (segment_times
                               + scale * step_sizes[dim] * direction_matrix[dim])
                # Reject if any time becomes non-positive
                if (trial_times <= 0).any():
                    continue
                trial_alphas = 1.0 / np.maximum(trial_times, _ALPHA_MIN)
                trial_energy = energy_eval(trial_alphas)
                if trial_energy < local_best_energy:
                    local_best_energy = trial_energy
                    local_best_idx = idx

            # Accept the best move if it improves energy
            if local_best_idx >= 0 and local_best_energy < best_energy:
                scale = candidate_scales[local_best_idx]
                segment_times += scale * step_sizes[dim] * direction_matrix[dim]
                best_energy = local_best_energy
                step_sizes[dim] *= abs(scale)  # grow step — momentum works
                made_progress = True
            else:
                step_sizes[dim] /= acceleration  # shrink — refine locally

        # Convergence: all step sizes fell below tolerance
        if not made_progress and np.all(step_sizes <= epsilon):
            break
        if made_progress and step_sizes.max() <= epsilon:
            break

    return segment_times


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
    num_nodes = len(points)

    # --- Validate point count ---
    if cyclic:
        if num_nodes < 3:
            raise ValueError("At least 3 points are required for a closed spline")
        num_segs = num_nodes
    else:
        if num_nodes < 2:
            raise ValueError("At least two points are required")
        num_segs = num_nodes - 1

    # --- Compute alphas (inverse segment times) based on metric ---
    if metric == 'POINTS':
        # Uniform: every segment gets equal time → all alphas equal 1
        alphas = np.ones(num_segs)

    elif metric == 'DISTANCE':
        # Chord-length: longer segments get more time
        lengths = _chord_lengths(points, cyclic)
        alphas = 1.0 / lengths

    elif metric == 'OPTIMAL':
        # Hill-descent: find times that minimize bending energy
        segment_times = _compute_optimal_times(
            points, num_segs, epsilon, max_iterations,
            delta, acceleration, cyclic)
        alphas = 1.0 / np.maximum(segment_times, _ALPHA_MIN)

    else:
        raise ValueError(
            f"Unknown metric '{metric}'. "
            "Expected one of: 'POINTS', 'DISTANCE', 'OPTIMAL'")

    # --- Solve for control points (final, non-optimized path) ---
    if cyclic:
        segments = _closed_control_points(points, alphas, num_segs)
    else:
        segments = _open_control_points(points, alphas)

    # --- Build curve objects ---
    curves = [SvCubicBezierCurve(*seg) for seg in segments]
    return concatenate_curves(curves) if concat else curves
