# This file is part of project Sverchok.
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
"""Additional geometric constraints for Pulga Physics.

Boundary forces project particle positions and remove velocity/force components
normal to the constraint. All heavy static data is built once in __init__.
Fast curve/surface methods do not need SciPy; Precise methods require SciPy.
Solid constraints remain in Sverchok's existing modular core.
"""

import numpy as np


_EPS = 1.0e-12


def _unit(vectors):
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return np.divide(vectors, lengths, out=np.zeros_like(vectors), where=lengths > _EPS)


def _apply_curve_constraint(ps, locations, tangents):
    """Constrain particles to a 1D geometry; preserve tangential motion."""
    directions = _unit(np.asarray(tangents, dtype=np.float64))
    ps.verts[:] = locations
    ps.vel[:] = directions * np.sum(ps.vel * directions, axis=1)[:, None]
    ps.force_resultant[:] = directions * np.sum(ps.force_resultant * directions, axis=1)[:, None]


def _apply_surface_constraint(ps, locations, normals):
    """Constrain particles to a 2D geometry; preserve tangential motion."""
    directions = _unit(np.nan_to_num(np.asarray(normals, dtype=np.float64)))
    ps.verts[:] = locations
    ps.vel[:] -= directions * np.sum(ps.vel * directions, axis=1)[:, None]
    ps.force_resultant[:] -= directions * np.sum(ps.force_resultant * directions, axis=1)[:, None]


def nearest_on_segments(points, starts, ends, point_chunk=256, edge_chunk=256):
    """Exact nearest point on a segment set; bounded temporary memory.

    Returns closest points and the tangent of the chosen segment. Zero-length
    segments are discarded by the caller.
    """
    points = np.asarray(points, dtype=np.float64).reshape((-1, 3))
    starts = np.asarray(starts, dtype=np.float64).reshape((-1, 3))
    ends = np.asarray(ends, dtype=np.float64).reshape((-1, 3))
    if len(starts) == 0:
        raise ValueError('Boundary requires at least one nondegenerate edge')
    if len(starts) != len(ends):
        raise ValueError('Edge start/end point counts differ')

    segment = ends - starts
    lengths2 = np.einsum('ij,ij->i', segment, segment)
    valid = lengths2 > _EPS
    if not valid.any():
        raise ValueError('Boundary requires at least one nondegenerate edge')
    starts, segment, lengths2 = starts[valid], segment[valid], lengths2[valid]
    closest = np.empty_like(points)
    tangent = np.empty_like(points)
    for i in range(0, len(points), point_chunk):
        p = points[i:i + point_chunk]
        best_d2 = np.full(len(p), np.inf)
        best_p = np.zeros_like(p)
        best_t = np.zeros_like(p)
        rows = np.arange(len(p))
        for j in range(0, len(starts), edge_chunk):
            a = starts[j:j + edge_chunk]
            ab = segment[j:j + edge_chunk]
            sq = lengths2[j:j + edge_chunk]
            t = np.einsum('nmk,mk->nm', p[:, None, :] - a[None, :, :], ab)
            t = np.clip(t / sq[None, :], 0.0, 1.0)
            candidate = a[None, :, :] + t[:, :, None] * ab[None, :, :]
            d2 = np.einsum('nmk,nmk->nm', candidate - p[:, None, :], candidate - p[:, None, :])
            idx = np.argmin(d2, axis=1)
            selected = d2[rows, idx] < best_d2
            best_d2[selected] = d2[rows, idx][selected]
            best_p[selected] = candidate[rows, idx][selected]
            best_t[selected] = ab[idx][selected]
        closest[i:i + len(p)] = best_p
        tangent[i:i + len(p)] = best_t
    return closest, _unit(tangent)


class SvBoundingEdgesForce:
    """Constrain particles to the nearest edge of a Sverchok indexed mesh."""

    def __init__(self, vertices, edges):
        vertices = np.asarray(vertices, dtype=np.float64).reshape((-1, 3))
        edges = np.asarray(edges, dtype=np.int64).reshape((-1, 2))
        if not len(vertices) or not len(edges):
            raise ValueError('Mesh (Edges) requires vertices and edges')
        if (edges < 0).any() or (edges >= len(vertices)).any():
            raise ValueError('Mesh (Edges) has an out-of-range vertex index')
        self.starts = vertices[edges[:, 0]]
        self.ends = vertices[edges[:, 1]]
        self.setup_done = False

    def setup(self, ps):
        self.setup_done = True

    def add(self, ps):
        closest, tangent = nearest_on_segments(ps.verts, self.starts, self.ends)
        _apply_curve_constraint(ps, closest, tangent)



class SvBoundingCurveForce:
    """Constrain particle positions and velocities to a stationary SvCurve.

    Fast mode projects onto pre-sampled segments. Precise mode optimizes a
    point on the original curve via Sverchok's SciPy nearest-point utility.
    """

    def __init__(self, curve, method='FAST', resolution=64, init_samples=32):
        self.curve = curve
        self.method = method
        if method not in {'FAST', 'PRECISE'}:
            raise ValueError('Unknown Curve boundary method: ' + str(method))
        if method == 'FAST':
            resolution = max(2, int(resolution))
            t_min, t_max = curve.get_u_bounds()
            ts = np.linspace(t_min, t_max, resolution)
            sampled = np.asarray(curve.evaluate_array(ts), dtype=np.float64)
            if sampled.shape != (resolution, 3) or not np.isfinite(sampled).all():
                raise ValueError('Curve sampling returned invalid points')
            self.starts, self.ends = sampled[:-1], sampled[1:]
        else:
            from sverchok.dependencies import scipy
            if scipy is None:
                raise ImportError('Curve Precise boundaries require SciPy')
            self.init_samples = max(3, int(init_samples))

    def setup(self, ps):
        pass

    def add(self, ps):
        points = np.asarray(ps.verts, dtype=np.float64)
        if not len(points):
            return
        if self.method == 'FAST':
            closest, tangents = nearest_on_segments(points, self.starts, self.ends)
        else:
            from sverchok.utils.manifolds import nearest_point_on_curve
            result = nearest_point_on_curve(
                points.tolist(), self.curve, samples=self.init_samples,
                precise=True, output_points=True, method='bounded')
            parameters = np.asarray([entry[0] for entry in result], dtype=np.float64)
            closest = np.asarray([entry[1] for entry in result], dtype=np.float64)
            tangents = np.asarray(self.curve.tangent_array(parameters.copy()), dtype=np.float64)
        if closest.shape != points.shape or tangents.shape != points.shape:
            raise ValueError('Curve nearest-point calculation returned unexpected dimensions')
        _apply_curve_constraint(ps, closest, tangents)


class SvBoundingSurfaceForce:
    """Constrain particles to the full untrimmed domain of a SvSurface.

    Fast uses a cached triangle BVH; Precise refines a point on the original
    parametric surface with independent U/V initial search densities.
    """

    def __init__(self, surface, method='FAST', resolution_u=25, resolution_v=25,
                 init_samples_u=15, init_samples_v=15):
        self.surface = surface
        self.method = method
        if method not in {'FAST', 'PRECISE'}:
            raise ValueError('Unknown Surface boundary method: ' + str(method))
        if method == 'FAST':
            from mathutils.bvhtree import BVHTree
            nu, nv = max(2, int(resolution_u)), max(2, int(resolution_v))
            if nu * nv > 160000:
                raise ValueError('Surface boundary resolution exceeds 160000 points')
            umin, umax = surface.get_u_bounds()
            vmin, vmax = surface.get_v_bounds()
            us, vs = np.meshgrid(np.linspace(umin, umax, nu),
                                 np.linspace(vmin, vmax, nv), indexing='ij')
            vertices = np.asarray(surface.evaluate_array(us.ravel(), vs.ravel()), dtype=np.float64)
            if vertices.shape != (nu * nv, 3) or not np.isfinite(vertices).all():
                raise ValueError('Surface sampling returned invalid points')
            triangles = []
            for i in range(nu - 1):
                for j in range(nv - 1):
                    a = i * nv + j
                    b = (i + 1) * nv + j
                    triangles.extend(((a, b, b+1), (a, b+1, a+1)))
            self.bvh = BVHTree.FromPolygons(vertices.tolist(), triangles,
                                             all_triangles=True, epsilon=0.0)
        else:
            from sverchok.dependencies import scipy
            if scipy is None:
                raise ImportError('Surface Precise boundaries require SciPy')
            self.init_samples_u = max(3, int(init_samples_u))
            self.init_samples_v = max(3, int(init_samples_v))

    def setup(self, ps):
        pass

    def add(self, ps):
        points = np.asarray(ps.verts, dtype=np.float64)
        if not len(points):
            return
        if self.method == 'FAST':
            nearest = np.empty_like(points)
            normals = np.empty_like(points)
            for i, point in enumerate(points):
                hit, normal, _, _ = self.bvh.find_nearest(tuple(point))
                if hit is None or normal is None:
                    raise ValueError('Surface BVH did not return a nearest point')
                nearest[i] = hit
                normals[i] = normal
        else:
            from sverchok.utils.manifolds import nearest_point_on_surface
            # Current Sverchok branch supports (U, V) for init_samples.
            us, vs, closest = nearest_point_on_surface(
                points.tolist(), self.surface,
                init_samples=(self.init_samples_u, self.init_samples_v),
                precise=True, method='L-BFGS-B', sequential=False,
                output_points=True)
            nearest = np.asarray(closest, dtype=np.float64)
            normals = np.asarray(
                self.surface.normal_array(np.asarray(us), np.asarray(vs)),
                dtype=np.float64)
        if nearest.shape != points.shape or normals.shape != points.shape:
            raise ValueError('Surface nearest-point calculation returned unexpected dimensions')
        _apply_surface_constraint(ps, nearest, normals)


class SvBoundingSolidFastForce:
    """Fast static FreeCAD solid / solid-face constraint.

    Build one tessellation, delegate to the *existing* mesh surface/volume
    boundary force. The cached mesh and its BVH are reused every iteration.
    """

    def __init__(self, solid, volume=False, deflection=0.1):
        from sverchok.utils.pulga_physics_modular_core import SvBoundingMeshForce

        tolerance = float(deflection)
        if not np.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError('Solid boundary Deflection must be positive and finite')
        # SvSolidFaceSurface has a FreeCAD face in .face; Part.Solid is directly
        # tessellatable. Do not convert a face wrapper to its untrimmed Surface.
        shape = getattr(solid, 'face', None)
        if shape is None:
            shape = solid
        if not hasattr(shape, 'tessellate'):
            raise TypeError('Solid Fast boundary expects a FreeCAD solid/face')

        points, triangles = shape.tessellate(tolerance)
        vertices = [((float(point.x), float(point.y), float(point.z))
                     if hasattr(point, 'x') else tuple(float(c) for c in point))
                    for point in points]
        faces = [tuple(int(index) for index in tri) for tri in triangles]
        if not vertices or not faces or any(len(face) != 3 for face in faces):
            raise ValueError('FreeCAD tessellation returned an empty/invalid triangle mesh')
        nverts = len(vertices)
        if any(any(index < 0 or index >= nverts for index in tri) for tri in faces):
            raise ValueError('FreeCAD tessellation returned invalid vertex indices')
        self.mesh_force = SvBoundingMeshForce(vertices, faces, volume=bool(volume))

    def setup(self, ps):
        self.mesh_force.setup(ps)

    def add(self, ps):
        self.mesh_force.add(ps)
