# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Two-way particle/edge contacts for Pulga Physics.

Every particle is tested against every non-incident edge. The edge receives
opposite forces distributed to its endpoints by the segment interpolation
factor. Detection uses current, not initial, particle positions.
"""

import math
import numpy as np

try:
    from sverchok.dependencies import numba
except ImportError:  # Support standalone numerical tests.
    numba = None

HAS_NUMBA = numba is not None


def _fit_parameter(data, count, name):
    """Accept a scalar or a per-particle array (repeat the last element)."""
    arr = np.asarray(data, dtype=np.float64).reshape(-1)
    if count == 0:
        return np.empty(0, dtype=np.float64)
    if not len(arr):
        raise ValueError(f'{name} must not be empty')
    if not np.all(np.isfinite(arr)) or np.any(arr < 0):
        raise ValueError(f'{name} must contain finite, nonnegative values')
    if len(arr) < count:
        arr = np.pad(arr, (0, count - len(arr)), mode='edge')
    return np.ascontiguousarray(arr[:count])


def _normal_at_zero(dx, dy, dz, rvx, rvy, rvz):
    """Deterministic normal when P lies exactly on the segment.

    Prefer the negative relative velocity; otherwise use a perpendicular
    direction to the edge. A zero-length edge uses the X axis.
    """
    rr = rvx * rvx + rvy * rvy + rvz * rvz
    if rr > 1e-24:
        scale = -1.0 / math.sqrt(rr)
        return rvx * scale, rvy * scale, rvz * scale
    if abs(dx) >= abs(dy) and abs(dx) >= abs(dz):
        nx, ny, nz = -dy, dx, 0.0
    else:
        nx, ny, nz = 0.0, -dz, dy
    ll = nx * nx + ny * ny + nz * nz
    if ll <= 1e-24:
        return 1.0, 0.0, 0.0
    scale = 1.0 / math.sqrt(ll)
    return nx * scale, ny * scale, nz * scale


def _contact_loop(verts, vel, rads, edges, strengths, edge_radii, dampings):
    """Reference implementation; also JIT-compiled by Numba when available.

    Intentionally serial: endpoint forces may receive simultaneous writes from
    multiple particle-edge pairs. Using prange here would be a data race.
    """
    count = verts.shape[0]
    out = np.zeros((count, 3), dtype=np.float64)
    for i in range(count):
        px, py, pz = verts[i, 0], verts[i, 1], verts[i, 2]
        radius = rads[i] + edge_radii[i]
        if radius <= 0 or strengths[i] <= 0 and dampings[i] <= 0:
            continue
        for j in range(edges.shape[0]):
            a, b = edges[j, 0], edges[j, 1]
            if i == a or i == b or a == b:
                continue
            ax, ay, az = verts[a, 0], verts[a, 1], verts[a, 2]
            bx, by, bz = verts[b, 0], verts[b, 1], verts[b, 2]
            # Broad phase: reject outside a capsule's enclosing AABB.
            if (px < min(ax, bx) - radius or px > max(ax, bx) + radius or
                py < min(ay, by) - radius or py > max(ay, by) + radius or
                pz < min(az, bz) - radius or pz > max(az, bz) + radius):
                continue
            dx, dy, dz = bx - ax, by - ay, bz - az
            length2 = dx * dx + dy * dy + dz * dz
            if length2 <= 1e-24:
                t = 0.0
            else:
                t = ((px - ax) * dx + (py - ay) * dy + (pz - az) * dz) / length2
                t = max(0.0, min(1.0, t))
            qx, qy, qz = ax + t * dx, ay + t * dy, az + t * dz
            vx, vy, vz = px - qx, py - qy, pz - qz
            distance2 = vx * vx + vy * vy + vz * vz
            if distance2 >= radius * radius:
                continue
            w0, w1 = 1.0 - t, t
            rvx = vel[i, 0] - w0 * vel[a, 0] - w1 * vel[b, 0]
            rvy = vel[i, 1] - w0 * vel[a, 1] - w1 * vel[b, 1]
            rvz = vel[i, 2] - w0 * vel[a, 2] - w1 * vel[b, 2]
            if distance2 > 1e-24:
                distance = math.sqrt(distance2)
                nx, ny, nz = vx / distance, vy / distance, vz / distance
            else:
                distance = 0.0
                nx, ny, nz = _normal_at_zero(dx, dy, dz, rvx, rvy, rvz)
            closing = max(0.0, -(rvx * nx + rvy * ny + rvz * nz))
            force = strengths[i] * (radius - distance) + dampings[i] * closing
            fx, fy, fz = nx * force, ny * force, nz * force
            out[i, 0] += fx
            out[i, 1] += fy
            out[i, 2] += fz
            out[a, 0] -= fx * w0
            out[a, 1] -= fy * w0
            out[a, 2] -= fz * w0
            out[b, 0] -= fx * w1
            out[b, 1] -= fy * w1
            out[b, 2] -= fz * w1
    return out


if HAS_NUMBA:
    # JIT both helpers so Numba never calls Python during the inner loop.
    _normal_at_zero_numba = numba.njit(cache=True)(_normal_at_zero)

    @numba.njit(cache=True)
    def _numba_contacts(verts, vel, rads, edges, strengths, edge_radii, dampings):
        count = verts.shape[0]
        out = np.zeros((count, 3), dtype=np.float64)
        for i in range(count):
            px, py, pz = verts[i, 0], verts[i, 1], verts[i, 2]
            radius = rads[i] + edge_radii[i]
            if radius <= 0 or (strengths[i] <= 0 and dampings[i] <= 0):
                continue
            for j in range(edges.shape[0]):
                a, b = edges[j, 0], edges[j, 1]
                if i == a or i == b or a == b:
                    continue
                ax, ay, az = verts[a, 0], verts[a, 1], verts[a, 2]
                bx, by, bz = verts[b, 0], verts[b, 1], verts[b, 2]
                if (px < min(ax, bx) - radius or px > max(ax, bx) + radius or
                    py < min(ay, by) - radius or py > max(ay, by) + radius or
                    pz < min(az, bz) - radius or pz > max(az, bz) + radius):
                    continue
                dx, dy, dz = bx - ax, by - ay, bz - az
                length2 = dx * dx + dy * dy + dz * dz
                if length2 <= 1e-24:
                    t = 0.0
                else:
                    t = ((px - ax) * dx + (py - ay) * dy + (pz - az) * dz) / length2
                    t = max(0.0, min(1.0, t))
                qx, qy, qz = ax + t * dx, ay + t * dy, az + t * dz
                vx, vy, vz = px - qx, py - qy, pz - qz
                distance2 = vx * vx + vy * vy + vz * vz
                if distance2 >= radius * radius:
                    continue
                w0, w1 = 1.0 - t, t
                rvx = vel[i, 0] - w0 * vel[a, 0] - w1 * vel[b, 0]
                rvy = vel[i, 1] - w0 * vel[a, 1] - w1 * vel[b, 1]
                rvz = vel[i, 2] - w0 * vel[a, 2] - w1 * vel[b, 2]
                if distance2 > 1e-24:
                    distance = math.sqrt(distance2)
                    nx, ny, nz = vx / distance, vy / distance, vz / distance
                else:
                    distance = 0.0
                    nx, ny, nz = _normal_at_zero_numba(dx, dy, dz, rvx, rvy, rvz)
                closing = max(0.0, -(rvx * nx + rvy * ny + rvz * nz))
                force = strengths[i] * (radius - distance) + dampings[i] * closing
                fx, fy, fz = nx * force, ny * force, nz * force
                out[i, 0] += fx
                out[i, 1] += fy
                out[i, 2] += fz
                out[a, 0] -= fx * w0
                out[a, 1] -= fy * w0
                out[a, 2] -= fz * w0
                out[b, 0] -= fx * w1
                out[b, 1] -= fy * w1
                out[b, 2] -= fz * w1
        return out


def contact_forces(verts, vel, rads, edges, strengths, edge_radii, dampings,
                   engine='AUTO'):
    """Return contact forces for all particles as a (V, 3) array.

    Indices refer to the Pulga solver's *initial particle order*.
    """
    verts = np.ascontiguousarray(np.asarray(verts, dtype=np.float64).reshape(-1, 3))
    vel = np.ascontiguousarray(np.asarray(vel, dtype=np.float64).reshape(-1, 3))
    count = len(verts)
    rads = _fit_parameter(rads, count, 'Particle radius')
    strengths = _fit_parameter(strengths, count, 'Strength')
    edge_radii = _fit_parameter(edge_radii, count, 'Edge Radius')
    dampings = _fit_parameter(dampings, count, 'Damping')
    if len(vel) != count:
        raise ValueError('Velocity and particle count differ')
    edges_array = np.asarray(edges)
    if edges_array.size == 0:
        edges = np.empty((0, 2), dtype=np.int64)
    else:
        if edges_array.ndim != 2 or edges_array.shape[1] != 2:
            raise ValueError('Edges must contain pairs of vertex indices')
        edges = np.ascontiguousarray(edges_array, dtype=np.int64)
        if np.any(edges_array != edges):
            raise ValueError('Edge indices must be integers')
        if np.any(edges < 0) or np.any(edges >= count):
            raise ValueError('Edge index outside solver particle range')
    if engine not in ('AUTO', 'NUMPY', 'NUMBA'):
        raise ValueError(f'Unknown engine: {engine}')
    if engine == 'NUMBA' and not HAS_NUMBA:
        raise RuntimeError('Numba engine selected but Numba is unavailable')
    if len(edges) == 0 or count == 0:
        return np.zeros((count, 3), dtype=np.float64)
    if engine == 'NUMBA' or (engine == 'AUTO' and HAS_NUMBA):
        return _numba_contacts(verts, vel, rads, edges, strengths, edge_radii, dampings)
    return _contact_loop(verts, vel, rads, edges, strengths, edge_radii, dampings)


class SvSelfEdgeCollisionForce:
    """Pulga force API: setup(ps) + add(ps)."""

    def __init__(self, edges, strength, edge_radius, damping, engine='AUTO'):
        self.edges = edges
        self.strength = strength
        self.edge_radius = edge_radius
        self.damping = damping
        self.engine = engine

    def setup(self, ps):
        # Validate at setup; cache constant topology and per-point parameters.
        self._edges = np.asarray(self.edges, dtype=np.int64)
        if self._edges.size == 0:
            self._edges = np.empty((0, 2), dtype=np.int64)
        if self._edges.ndim != 2 or self._edges.shape[1] != 2:
            raise ValueError('Edges must contain pairs of vertex indices')
        if np.any(self._edges < 0) or np.any(self._edges >= ps.v_len):
            raise ValueError('Edge index outside Pulga particle range')
        self._strength = _fit_parameter(self.strength, ps.v_len, 'Strength')
        self._edge_radius = _fit_parameter(self.edge_radius, ps.v_len, 'Edge Radius')
        self._damping = _fit_parameter(self.damping, ps.v_len, 'Damping')

    def add(self, ps):
        if not len(self._edges):
            return
        ps.force_resultant += contact_forces(
            ps.verts, ps.vel, ps.rads, self._edges,
            self._strength, self._edge_radius, self._damping, self.engine)
