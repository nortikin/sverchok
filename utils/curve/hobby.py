# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Hobby interpolating splines.

Implementation based on:
    John D. Hobby, "Smooth, Easy to Compute Interpolating Splines",
    Stanford University, Report No. STAN-CS-85-1047, January 1985.

The Hobby spline is a cubic Bezier spline with approximate G2 continuity
achieved by equalizing "mock curvature" at knots. It produces aesthetically
pleasing curves that are invariant under scaling, rotation, and reflection.
Effects of local perturbations fall off exponentially.
"""

import numpy as np

from sverchok.utils.curve.bezier import SvCubicBezierCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves


# ---------------------------------------------------------------------------
# Velocity magnitude functions
# ---------------------------------------------------------------------------

def _hobby_velocity(theta, phi, tension=1.0):
    """
    Compute velocity magnitude factor using the METAFONT approximation
    (Hobby 1986 paper, equation 11; Hobby 1985 preprint, equation 10).

    This function rho(theta, phi) determines the magnitude of the tangent
    vector at a knot, scaled by the chord length.

    Args:
        theta: angle from chord to start tangent (radians).
        phi:   angle from end tangent to chord (radians).
        tension: tension parameter; tension=1 gives default behavior.
                 As tension -> inf, the curve approaches the chord.

    Returns:
        Velocity magnitude factor (positive scalar).
    """
    a = 1.597
    b = 0.07
    c = 2.0 / 3.0

    sum_angle = theta + phi
    alpha = (a *
             (np.sin(theta) - b * np.sin(sum_angle)) *
             (np.sin(phi) - b * np.sin(sum_angle)) *
             (np.cos(b * sum_angle) - np.cos(sum_angle)))

    numerator = 2.0 + (3.0 - c) * alpha
    denominator = 1.0 + (1.0 - c) * np.cos(theta) + c * np.cos(phi)

    return numerator / (denominator * tension)


def _hobby_velocity_accurate(theta, phi, tension=1.0):
    """
    Compute velocity magnitude using the more accurate Hobby approximation
    (Hobby 1986 paper, equation 10; Hobby 1985 preprint, equation 9).

    The velocity function is:
        ρ(θ, φ) = f(θ, φ) + ½·γ(φ)·sin(φ - θ)
        σ(θ, φ) = f(θ, φ) - ½·γ(φ)·sin(φ - θ)

    where γ(φ) = ½φ - 0.15·sin(2φ) depends ONLY on φ.
    """
    a = 0.2678306
    c_coeff = 0.2638750
    d = 1.402539
    e = 0.7539063

    # γ(φ) = ½φ - 0.15·sin(2φ) — depends only on φ, not on θ
    gamma_phi = 0.5 * phi - 0.15 * np.sin(2.0 * phi)

    x = gamma_phi
    f_val = (d * x + e) / (2.0 + a + 2.0 * c_coeff +
                            a * x * ((3.0 / 2.0 - 4.0 / np.pi) * x +
                                     9.0 / 5.0 - 4.0 / np.pi))

    rho = f_val + 0.5 * (theta - phi) / (2.0 + a + 2.0 * c_coeff)
    return rho / tension


# ---------------------------------------------------------------------------
# Linear system solvers
# ---------------------------------------------------------------------------

def _solve_tridiagonal(a_diag, b_diag, c_diag, rhs):
    """
    Solve a tridiagonal system using the Thomas algorithm.

    a[i]*x[i-1] + b[i]*x[i] + c[i]*x[i+1] = rhs[i]

    Args:
        a_diag: sub-diagonal (lower), length n. a[0] is unused.
        b_diag: main diagonal, length n.
        c_diag: super-diagonal (upper), length n. c[n-1] is unused.
        rhs: right-hand side, length n.

    Returns:
        x: solution vector, length n.
    """
    n = len(rhs)
    if n == 0:
        return np.array([])
    if n == 1:
        return rhs / b_diag

    c_diag = c_diag.copy()
    rhs = rhs.copy()

    # Forward elimination
    for i in range(1, n):
        m = a_diag[i] / b_diag[i - 1]
        b_diag[i] -= m * c_diag[i - 1]
        rhs[i] -= m * rhs[i - 1]

    # Back substitution
    x = np.zeros(n)
    x[-1] = rhs[-1] / b_diag[-1]
    for i in range(n - 2, -1, -1):
        x[i] = (rhs[i] - c_diag[i] * x[i + 1]) / b_diag[i]

    return x


def _solve_cyclic_tridiagonal(diag, lower, upper, rhs):
    """
    Solve a cyclic (periodic) tridiagonal system using direct numpy solve.
    """
    n = len(rhs)
    if n == 0:
        return np.array([])
    if n == 1:
        return rhs / diag[0]

    A = np.diag(diag) + np.diag(upper[:-1], 1) + np.diag(lower[1:], -1)
    A[0, -1] = lower[0]
    A[-1, 0] = upper[-1]
    return np.linalg.solve(A, rhs)


# ---------------------------------------------------------------------------
# Vector rotation
# ---------------------------------------------------------------------------

def _rotate_toward(v, toward, angle):
    """
    Rotate vector v by `angle` radians toward vector `toward`.

    Uses Rodrigues' rotation formula. The rotation axis is
    cross(v, toward), and a positive angle rotates v toward `toward`.

    Args:
        v: vector to rotate, shape (3,).
        toward: target direction to rotate toward, shape (3,).
        angle: rotation angle in radians (positive).

    Returns:
        Rotated vector, shape (3,).
    """
    v = np.asarray(v, dtype=np.float64)
    toward = np.asarray(toward, dtype=np.float64)

    if abs(angle) < 1e-15:
        return v.copy()

    # Normalize
    v_norm = np.linalg.norm(v)
    if v_norm < 1e-15:
        return toward.copy()
    v = v / v_norm

    toward_norm = np.linalg.norm(toward)
    if toward_norm < 1e-15:
        return v.copy()
    toward = toward / toward_norm

    # Rotation axis: cross(v, toward)
    axis = np.cross(v, toward)
    axis_norm = np.linalg.norm(axis)

    if axis_norm < 1e-15:
        # v and toward are collinear
        dot = np.dot(v, toward)
        if dot > 0:
            return v  # already pointing same direction
        else:
            return -v  # need to flip 180 degrees

    axis = axis / axis_norm

    # Rodrigues' formula with NEGATED angle to rotate TOWARD the reference
    # (cross(v, toward) as axis with positive angle rotates v AWAY from toward)
    cos_a = np.cos(-angle)
    sin_a = np.sin(-angle)
    v_dot_k = np.dot(v, axis)

    rotated = (v * cos_a +
               axis * v_dot_k * (1.0 - cos_a) +
               np.cross(axis, v) * sin_a)

    return rotated


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def hobby_curve(points, cyclic=False, tension=1.0,
                curl_start=1.0, curl_end=1.0,
                concat=False, accurate_velocity=False):
    """
    Build a Hobby interpolating spline through the given points.

    The Hobby spline produces smooth, aesthetically pleasing curves with
    approximate G2 continuity. It uses a linear "mock curvature" constraint
    to determine tangent directions at knots, solved via a tridiagonal
    linear system.

    Key properties (from Hobby, 1985):
    * Invariant under scaling, rotation, and reflection
    * Effects of local perturbations fall off exponentially (~factor of 2 per knot)
    * No iterative approximation needed — solved in linear time
    * Handles unequally spaced and widely separated knots well

    Args:
        points: list or np.array of shape (n, 2) or (n, 3) — points to
                interpolate. At least 2 points for open curves, 3 for cyclic.
        cyclic: if True, build a closed curve (last point connects to first).
        tension: global tension parameter (default 1.0). Higher values pull
                 the curve closer to the chord. As tension -> inf, curve
                 approaches the polyline.
        curl_start: curl parameter at the start endpoint (default 1.0).
                    Controls how the curve leaves the first point.
        curl_end: curl parameter at the end endpoint (default 1.0).
                  Controls how the curve approaches the last point.
        concat: if True, concatenate all Bezier segments into a single
                NURBS curve. If False, return a list of SvCubicBezierCurve.
        accurate_velocity: if True, use the more accurate Hobby velocity
                           formula (eq. 9) instead of the METAFONT
                           approximation (eq. 10).

    Returns:
        If concat=False: list of SvCubicBezierCurve, one per segment.
        If concat=True:  a single concatenated NURBS curve (SvNurbsCurve).

    Raises:
        ValueError: if fewer than 2 points are given (or 3 for cyclic).
    """
    points = np.asarray(points, dtype=np.float64)

    # Ensure 3D points
    if points.ndim == 1:
        points = points.reshape(1, -1)
    if points.shape[1] == 2:
        padded = np.zeros((len(points), 3), dtype=np.float64)
        padded[:, :2] = points
        points = padded

    n = len(points)

    # Edge cases
    if cyclic:
        if n < 3:
            raise ValueError("At least 3 points are required for a cyclic Hobby spline")
    else:
        if n < 2:
            raise ValueError("At least 2 points are required for a Hobby spline")

    if np.linalg.norm(points[1:] - points[:-1]).max() < 1e-12:
        if n >= 2:
            return [SvCubicBezierCurve(points[0], points[0], points[0], points[0])]
        raise ValueError("At least 2 points are required")

    # --- Step 1: Chord vectors and lengths ---
    if cyclic:
        chords = np.zeros_like(points)
        chords[:-1] = points[1:] - points[:-1]
        chords[-1] = points[0] - points[-1]
    else:
        chords = points[1:] - points[:-1]

    d = np.linalg.norm(chords, axis=1)
    num_segments = len(chords)

    # --- Step 2: Turning angles at knots (SIGNED) ---
    # The signed turning angle is essential for the MetaPost interior equation.
    # ψ = angle from incoming chord to outgoing chord.
    # Positive ψ means counter-clockwise turn, negative means clockwise.
    #
    # For 3D curves, we project the chords onto a reference plane and compute
    # the signed angle in that plane. The reference plane normal is determined
    # by the cross product of the first two non-collinear chords.

    # Compute reference plane normal
    ref_normal = np.array([0.0, 0.0, 1.0])  # default: xy-plane
    if num_segments >= 2:
        candidate = np.cross(chords[0], chords[1])
        if np.linalg.norm(candidate) > 1e-12:
            ref_normal = candidate / np.linalg.norm(candidate)
    
    # Project chords onto reference plane.
    # Choose the projection plane based on the reference normal.
    # We want to project onto the plane where the curve has the most variation.
    chords_2d = np.zeros((num_segments, 2))
    if abs(ref_normal[2]) >= abs(ref_normal[0]) and abs(ref_normal[2]) >= abs(ref_normal[1]):
        # Normal is close to z-axis: project onto xy-plane
        chords_2d = chords[:, :2]
    elif abs(ref_normal[1]) >= abs(ref_normal[0]):
        # Normal is close to y-axis: project onto xz-plane
        chords_2d = chords[:, [0, 2]]
    else:
        # Normal is close to x-axis: project onto yz-plane
        chords_2d = chords[:, 1:3]

    if cyclic:
        psi = np.zeros(n)
        for j in range(n):
            ci = chords_2d[(j - 1) % n]
            co = chords_2d[j]
            dot_val = ci[0] * co[0] + ci[1] * co[1]
            cross_z = ci[0] * co[1] - ci[1] * co[0]
            psi[j] = np.arctan2(cross_z, dot_val)
    else:
        num_interior = n - 2
        psi = np.zeros(num_interior)
        for j in range(num_interior):
            ci = chords_2d[j]
            co = chords_2d[j + 1]
            dot_val = ci[0] * co[0] + ci[1] * co[1]
            cross_z = ci[0] * co[1] - ci[1] * co[0]
            psi[j] = np.arctan2(cross_z, dot_val)

    # --- Step 3: Solve mock curvature continuity system ---
    #
    # From Hobby paper, Section 3:
    # The mock curvature continuity at knot i gives:
    #   (theta_{i-1} - 6*phi_i) / d_{i-1} = (phi_{i+1} - 6*theta_i) / d_i
    #
    # Substituting phi_i = psi_i - theta_i and rearranging:
    #   -2*d_i*theta_{i-1} + (d_i + 7*d_{i-1})*theta_i - d_{i-1}*theta_{i+1}
    #     = (5*d_i + d_{i-1})*psi_i
    #
    # In our indexing (0-based segments):
    #   For interior knot j (corresponding to segment j-1 -> j):
    #   -2*d[j]*theta[j-1] + (d[j] + 7*d[j-1])*theta[j] - d[j-1]*theta[j+1]
    #     = (5*d[j] + d[j-1])*psi[j-1]

    if cyclic:
        # Cyclic system: n equations for n knots.
        # Paper derivation (Hobby §3, Knuth §276):
        #   -2*d[j]·θ[j-1] + (d[j]+7*d[j-1])·θ[j] - d[j-1]·θ[j+1]
        #     = (5*d[j]+d[j-1])·ψ[j]
        diag = np.zeros(n)
        lower = np.zeros(n)
        upper = np.zeros(n)
        rhs = np.zeros(n)
        for j in range(n):
            j_prev = (j - 1) % n
            diag[j] = d[j] + 7.0 * d[j_prev]
            lower[j] = -2.0 * d[j]
            upper[j] = -d[j_prev]
            rhs[j] = (5.0 * d[j] + d[j_prev]) * psi[j]

        theta = _solve_cyclic_tridiagonal(diag, lower, upper, rhs)

    else:
        if n == 2:
            # Two points: tangent directions follow the single chord.
            # With only one segment, curl constraints give θ[0]=θ[1]=0.
            theta = np.array([0.0, 0.0])
        else:
            # Open curve: curl constraints per MetaPost source (mp.w).
            #
            # MetaPost's curl constraint (verified against MetaPost 2.11):
            #   θ[0]   = +(γ₀+½)/(γ₀+2) · ψ[0]
            #   θ[n-1] = -(γₙ+½)/(γₙ+2) · ψ[n-2]
            # where γ = curl parameter, ψ[0] is the turning angle at the
            # first interior knot, ψ[n-2] at the last interior knot.
            # For n=3, both refer to the same turning angle.
            #
            # The opposite signs ensure mirror symmetry for symmetric inputs.
            #
            # Interior mock curvature continuity (MetaPost mp.w, line 7888):
            #   A_k·θ[k-1] + (B_k+C_k)·θ[k] + D_k·θ[k+1] = -B_k·ψ[k] - D_k·ψ[k+1]
            # where A_k = α_{k-1}/(β_k²·d[k-1]),
            #       B_k = (3-α_{k-1})/(β_k²·d[k-1]),
            #       C_k = (3-β_k)/(α_k²·d[k]),
            #       D_k = β_k/(α_k²·d[k]).
            # For uniform tension (α=β=1) and equal chord lengths:
            #   θ[k-1] + 4·θ[k] + θ[k+1] = -2·(ψ[k] + ψ[k+1])
            # For unequal chord lengths with uniform tension:
            #   d[k]·θ[k-1] + (2·d[k]+2·d[k-1])·θ[k] + d[k-1]·θ[k+1]
            #     = -2·d[k]·ψ[k] - 2·d[k-1]·ψ[k+1]
            #
            # ψ[k] is the turning angle at knot k (angle from chord[k-1] to chord[k]).
            # ψ[n-1] = 0 (no turning angle at last knot).
            #
            # We use Dirichlet BCs for endpoints and solve the interior
            # (n-2)×(n-2) system for θ[1]..θ[n-2].

            chi0 = curl_start
            chie = curl_end

            # Curl constraint coefficients (verified against MetaPost 2.11).
            # The curl constraint uses ψ_hobby = angle from outgoing chord to
            # incoming chord, which is the NEGATIVE of our turning angle psi.
            #   θ[0]   = +(γ₀+½)/(γ₀+2) · ψ_hobby[0] = -(γ₀+½)/(γ₀+2) · psi[0]
            #   θ[n-1] = -(γₙ+½)/(γₙ+2) · ψ_hobby[n-2] = +(γₙ+½)/(γₙ+2) · psi[-1]
            c0 = (chi0 + 0.5) / (chi0 + 2.0)
            ce = (chie + 0.5) / (chie + 2.0)

            # Endpoint theta values (Dirichlet boundary conditions)
            theta_0 = -c0 * psi[0]
            theta_n1 = +ce * psi[-1]

            # Extend psi with ψ[n-1]=0 for the last knot.
            # psi has n-1 elements (turning angles at knots 1..n-2).
            # We need psi[n-2] for the last interior equation.
            psi_ext = np.append(psi, 0.0)  # ψ[n-1] = 0

            num_interior = n - 2
            if num_interior == 1:
                # Single interior knot (n=3): solve directly.
                # MetaPost interior equation at knot 1 (uniform tension):
                #   d[1]·θ[0] + (2·d[1]+2·d[0])·θ[1] + d[0]·θ[2]
                #     = -2·d[1]·ψ[0] - 2·d[0]·ψ[1]
                # where ψ[0] = psi[0] (turning at knot 1), ψ[1] = 0 (end knot)
                theta_int = (-2.0 * d[1] * psi[0] - 2.0 * d[0] * psi_ext[1]
                             - d[1] * theta_0
                             - d[0] * theta_n1
                             ) / (2.0 * d[1] + 2.0 * d[0])
                theta = np.array([theta_0, theta_int, theta_n1])
            else:
                # Build (n-2)×(n-2) tridiagonal system for interior knots.
                a_diag = np.zeros(num_interior)
                b_diag = np.zeros(num_interior)
                c_diag = np.zeros(num_interior)
                rhs = np.zeros(num_interior)

                for i in range(num_interior):
                    j = i + 1  # knot index (1..n-2)
                    d_in = d[j - 1]
                    d_out = d[j]
                    # ψ at knot j is psi[j-1], ψ at knot j+1 is psi[j]
                    psi_j = psi_ext[j - 1]
                    psi_j1 = psi_ext[j]

                    # MetaPost equation (uniform tension, unequal chords):
                    #   d_out·θ[j-1] + (2·d_out+2·d_in)·θ[j] + d_in·θ[j+1]
                    #     = -2·d_out·ψ[j] - 2·d_in·ψ[j+1]
                    a_diag[i] = d_out
                    b_diag[i] = 2.0 * d_out + 2.0 * d_in
                    c_diag[i] = d_in
                    rhs[i] = -2.0 * d_out * psi_j - 2.0 * d_in * psi_j1

                # Incorporate Dirichlet BC into first/last RHS
                rhs[0] -= a_diag[0] * theta_0
                rhs[-1] -= c_diag[-1] * theta_n1

                theta_int = _solve_tridiagonal(a_diag, b_diag, c_diag, rhs)
                theta = np.zeros(n)
                theta[0] = theta_0
                theta[1:-1] = theta_int
                theta[-1] = theta_n1

    # --- Step 4: Compute phi at each knot ---
    # Relation (Hobby paper): θ[j] + φ[j] + ψ_at_knot_j = 0
    # where ψ is the turning angle (our psi). So φ[j] = -θ[j] - ψ[j].
    # For boundaries: ψ is undefined, so φ = -θ (tangent symmetric to chord).
    if cyclic:
        # ψ[j] is the turning angle at knot j (psi has n elements)
        phi = -theta - psi
    else:
        phi = np.zeros(n)
        # Boundary knots: φ = -θ
        phi[0] = -theta[0]
        phi[n - 1] = -theta[n - 1]
        # Interior knots j=1..n-2: ψ at knot j is psi[j-1]
        for j in range(1, n - 1):
            phi[j] = -theta[j] - psi[j - 1]

    # --- Step 5: Compute velocity magnitudes ---
    if isinstance(tension, (list, np.ndarray)):
        tensions = np.asarray(tension, dtype=np.float64)
    else:
        tensions = np.full(n, tension, dtype=np.float64)

    vel_func = _hobby_velocity_accurate if accurate_velocity else _hobby_velocity

    alpha = np.zeros(num_segments)
    beta = np.zeros(num_segments)

    for j in range(num_segments):
        knot_start = j
        knot_end = (j + 1) % n if cyclic else j + 1

        # Velocity at knot_start (alpha) uses theta and phi at knot_start.
        # Velocity at knot_end (beta) uses phi at knot_start and theta at knot_end.
        # This is per Hobby paper: beta[k] = d[k] · f(φ[k], θ[k+1]) / tension[k+1]
        rho_val = vel_func(theta[knot_start], phi[knot_start], tensions[knot_start])
        sigma_val = vel_func(phi[knot_start], theta[knot_end], tensions[knot_end])

        alpha[j] = d[j] * rho_val
        beta[j] = d[j] * sigma_val

    # --- Step 6: Compute tangent direction at each knot ---
    #
    # The tangent direction w[j] at knot j is unique and shared by both
    # the end of segment j-1 and the start of segment j.
    #
    # θ[j] is the signed angle from the chord to the tangent.
    # For interior knots: the rotation plane is defined by the incoming
    # and outgoing chords. Positive θ rotates away from the incoming chord.
    # For endpoints: only one chord exists, so we use a perpendicular
    # direction in the chord's plane to define the rotation.
    #
    # This guarantees G1 continuity because the same direction is used
    # on both sides of each interior knot.

    tangent_dirs = np.zeros((n, 3))

    for j in range(n):
        # Outgoing chord at knot j
        out_idx = j if cyclic else min(j, num_segments - 1)
        out_dir = chords[out_idx] / d[out_idx] if d[out_idx] > 1e-15 else np.array([1.0, 0.0, 0.0])

        # Incoming chord at knot j
        in_idx = (j - 1) % num_segments
        in_len = np.linalg.norm(chords[in_idx])
        in_dir = chords[in_idx] / in_len if in_len > 1e-15 else out_dir

        if abs(theta[j]) < 1e-15:
            # θ ≈ 0: tangent aligns with the chord
            tangent_dirs[j] = out_dir.copy()
        elif not cyclic and (j == 0 or j == n - 1):
            # Endpoint: only one chord, need a perpendicular for rotation.
            # Use cross product with an arbitrary reference (z-axis preferred,
            # falling back to x-axis if the chord is parallel to z).
            ref = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(out_dir, ref)) > 0.9999:
                ref = np.array([1.0, 0.0, 0.0])
            perp = np.cross(out_dir, ref)
            perp = perp / np.linalg.norm(perp)
            # θ[j] is the signed angle from chord to tangent.
            # Positive θ: rotate counterclockwise from chord (toward +perp).
            # Negative θ: rotate clockwise from chord (toward -perp).
            if theta[j] >= 0:
                tangent_dirs[j] = _rotate_toward(out_dir, perp, theta[j])
            else:
                tangent_dirs[j] = _rotate_toward(out_dir, -perp, abs(theta[j]))
        else:
            # Interior knot (or cyclic): rotation plane defined by in/out chords.
            # Positive θ → away from incoming chord (toward -in_dir).
            # Negative θ → toward incoming chord.
            if theta[j] > 0:
                tangent_dirs[j] = _rotate_toward(out_dir, -in_dir, theta[j])
            else:
                tangent_dirs[j] = _rotate_toward(out_dir, in_dir, -theta[j])

    # --- Step 7: Build cubic Bezier segments ---
    segments = []
    for j in range(num_segments):
        knot_start = j
        knot_end = (j + 1) % n if cyclic else j + 1

        p0 = points[knot_start]
        p3 = points[knot_end]

        # Tangent vectors (shared direction, segment-specific magnitude)
        t0 = alpha[j] * tangent_dirs[knot_start]
        t1 = beta[j] * tangent_dirs[knot_end]

        # Bezier control points
        b0 = p0
        b1 = p0 + t0 / 3.0
        b2 = p3 - t1 / 3.0
        b3 = p3

        segments.append(SvCubicBezierCurve(b0, b1, b2, b3))

    if concat:
        return concatenate_nurbs_curves(segments)
    return segments


def hobby_interpolate(points, cyclic=False, tension=1.0,
                      curl_start=1.0, curl_end=1.0,
                      concat=False, accurate_velocity=False):
    """Alias for hobby_curve."""
    return hobby_curve(
        points, cyclic=cyclic, tension=tension,
        curl_start=curl_start, curl_end=curl_end,
        concat=concat, accurate_velocity=accurate_velocity
    )
