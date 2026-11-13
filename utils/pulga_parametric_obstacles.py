# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve, surface and FreeCAD solid obstacles for the modular Pulga solver.

These objects are stationary during one simulation. Fast methods build the
sampled representation only once. Precise methods query the analytic geometry
at each Pulga iteration. No scene data is read from inside the physics loop.
"""

import numpy as np
from mathutils.bvhtree import BVHTree
from sverchok.dependencies import scipy, FreeCAD
from sverchok.utils.pulga_collision_domains import SvStaticPointEdgeObstacleForce


def _single_number(value, name, minimum=0.0):
    arr = np.asarray(value).reshape(-1)
    if not len(arr):
        raise ValueError('%s must contain a value' % name)
    number = float(arr[0])
    if not np.isfinite(number) or number < minimum:
        raise ValueError('%s must be at least %s' % (name, minimum))
    return number


def _surface_grid(surface, resolution_u, resolution_v):
    """Triangulate the full rectangular UV domain (not a trimmed domain)."""
    umin, umax = surface.get_u_bounds()
    vmin, vmax = surface.get_v_bounds()
    us, vs = np.meshgrid(np.linspace(umin, umax, resolution_u),
                         np.linspace(vmin, vmax, resolution_v), indexing='ij')
    vertices = np.asarray(surface.evaluate_array(us.ravel(), vs.ravel()), dtype=np.float64)
    if vertices.shape != (resolution_u * resolution_v, 3) or not np.isfinite(vertices).all():
        raise ValueError('Invalid surface sampling result')
    triangles = []
    for iu in range(resolution_u - 1):
        for iv in range(resolution_v - 1):
            a = iu * resolution_v + iv
            b = (iu + 1) * resolution_v + iv
            triangles.append((a, b, b + 1))
            triangles.append((a, b + 1, a + 1))
    return vertices, triangles


def _curve_segments(curve, resolution):
    tmin, tmax = curve.get_u_bounds()
    pts = np.asarray(curve.evaluate_array(np.linspace(tmin, tmax, resolution)), dtype=np.float64)
    if pts.shape != (resolution, 3) or not np.isfinite(pts).all():
        raise ValueError('Invalid curve sampling result')
    edges = np.column_stack((np.arange(resolution-1), np.arange(1, resolution)))
    return pts, edges


def _solid_mesh(shape, deflection):
    """FreeCAD Part.Shape.tessellate returns points and triangular facets."""
    vertices, triangles = shape.tessellate(deflection)
    points = np.asarray([tuple(v) for v in vertices], dtype=np.float64).reshape(-1, 3)
    if not np.isfinite(points).all() or not len(points) or not len(triangles):
        raise ValueError('FreeCAD did not produce a valid tessellation')
    return points, [tuple(int(i) for i in t) for t in triangles]


def _make_bvh(vertices, triangles):
    if not len(vertices) or not len(triangles):
        raise ValueError('Obstacle has no triangles')
    return BVHTree.FromPolygons(vertices.tolist(), triangles, all_triangles=True, epsilon=0.0)


def _nearest_curve_precise(curve, points, samples):
    from sverchok.utils.manifolds import nearest_point_on_curve
    results = nearest_point_on_curve([p.tolist() for p in points], curve,
                                     samples=samples, precise=True,
                                     output_points=True, method='bounded')
    nearest = np.asarray([result[1] for result in results], dtype=np.float64)
    if nearest.shape != points.shape:
        raise ValueError('Curve closest point search returned an invalid result')
    return nearest


def _nearest_surface_precise(surface, points, samples):
    from sverchok.utils.manifolds import nearest_point_on_surface
    _, _, closest = nearest_point_on_surface([p.tolist() for p in points], surface,
                                             init_samples=samples, precise=True,
                                             method='L-BFGS-B', sequential=False,
                                             output_points=True)
    nearest = np.asarray(closest, dtype=np.float64)
    if nearest.shape != points.shape:
        raise ValueError('Surface closest point search returned an invalid result')
    return nearest


def _vector3(vector):
    return np.asarray(tuple(vector), dtype=np.float64)


class SvParametricObstacleForce:
    """Stationary obstacle, with precise/fast nearest-point backends.

    Solid mode requires FreeCAD and supports inside-to-outside projection.
    Fast curve is a polyline, fast surface/solid is a triangle BVH.
    """

    def __init__(self, geometry, domain, method, absorption, thickness,
                 resolution=50, resolution_u=25, resolution_v=25,
                 init_samples=15, deflection=0.1, engine='AUTO',
                 init_samples_u=None, init_samples_v=None):
        if domain not in {'CURVE', 'SURFACE', 'SOLID'}:
            raise ValueError('Unsupported obstacle domain: ' + domain)
        if method not in {'FAST', 'PRECISE'}:
            raise ValueError('Unsupported obstacle method: ' + method)
        if domain in {'CURVE', 'SURFACE'} and method == 'PRECISE' and scipy is None:
            raise ImportError('Precise curve/surface collisions require SciPy')
        if domain == 'SOLID' and FreeCAD is None:
            raise ImportError('Solid obstacles require FreeCAD')
        self.geometry = list(geometry) if isinstance(geometry, (list, tuple)) else [geometry]
        self.geometry = [obj for obj in self.geometry if obj is not None]
        if not self.geometry:
            raise ValueError('Connect a Curve, Surface or Solid')
        self.domain, self.method = domain, method
        self.absorption = 1.0 - min(1.0, max(0.0, _single_number(absorption, 'Absorption')))
        self.thickness = np.asarray(thickness, dtype=np.float64).reshape(-1)
        if not len(self.thickness):
            self.thickness = np.array([0.0])
        if np.any(self.thickness < 0):
            raise ValueError('Thickness cannot be negative')
        self.resolution = max(2, min(8192, int(_single_number(resolution, 'Resolution', 2))))
        self.resolution_u = max(2, min(2048, int(_single_number(resolution_u, 'Resolution U', 2))))
        self.resolution_v = max(2, min(2048, int(_single_number(resolution_v, 'Resolution V', 2))))
        if self.domain == 'SURFACE' and self.method == 'FAST' and self.resolution_u * self.resolution_v > 160000:
            raise ValueError('Surface sampling exceeds 160000 points; reduce Resolution U/V')
        self.init_samples = max(3, min(512, int(_single_number(init_samples, 'Initial Samples', 3))))
        # Old callers still get the original NxN surface sampling.
        self.init_samples_u = (self.init_samples if init_samples_u is None else
            max(3, min(512, int(_single_number(init_samples_u, 'Initial Samples U', 3)))))
        self.init_samples_v = (self.init_samples if init_samples_v is None else
            max(3, min(512, int(_single_number(init_samples_v, 'Initial Samples V', 3)))))
        self.deflection = _single_number(deflection, 'Deflection', 1e-8)
        self.delegate = None
        self.trees = []
        self.engine = engine
        if method == 'FAST':
            self._build_fast()

    def _build_fast(self):
        if self.domain == 'CURVE':
            vertices, edges = [], []
            for curve in self.geometry:
                pts, eds = _curve_segments(curve, self.resolution)
                offset = len(vertices)
                vertices.extend(pts.tolist())
                edges.extend((int(a) + offset, int(b) + offset) for a, b in eds)
            self.delegate = SvStaticPointEdgeObstacleForce(
                vertices, edges, [1 - self.absorption], self.thickness, 'EDGES', self.engine)
        else:
            for obj in self.geometry:
                if self.domain == 'SURFACE':
                    vertices, triangles = _surface_grid(obj, self.resolution_u, self.resolution_v)
                else:
                    vertices, triangles = _solid_mesh(obj, self.deflection)
                self.trees.append(_make_bvh(vertices, triangles))

    def setup(self, ps):
        if len(self.thickness) == 1:
            self._thickness = np.full(ps.v_len, self.thickness[0])
        else:
            # Sverchok's repeat-last list matching (not NumPy's cyclic resize).
            self._thickness = np.pad(self.thickness[:ps.v_len],
                                     (0, max(0, ps.v_len-len(self.thickness))),
                                     mode='edge')
        if self.delegate is not None:
            self.delegate.setup(ps)

    def _solid_is_inside(self, shape, point):
        from FreeCAD import Base
        return bool(shape.isInside(Base.Vector(*[float(x) for x in point]), 1e-7, True))

    def _nearest(self, points):
        """Return closest surface points and inside status for each particle."""
        nearest = np.zeros_like(points)
        d2 = np.full(len(points), np.inf)
        inside = np.zeros(len(points), dtype=bool)
        if self.delegate is not None:
            return (*self.delegate.nearest(points), inside)
        if self.method == 'FAST':
            for j, bvh in enumerate(self.trees):
                for i, p in enumerate(points):
                    result = bvh.find_nearest(tuple(p))
                    if result[0] is None:
                        continue
                    candidate = _vector3(result[0])
                    dist_sq = float(np.dot(p-candidate, p-candidate))
                    # Fast follows Mesh (Volume): classify using the
                    # normal of the closest outward-facing BVH triangle.
                    # Avoid FreeCAD.isInside in the simulation loop.
                    is_inside = False
                    if self.domain == 'SOLID' and result[1] is not None:
                        face_normal = _vector3(result[1])
                        if (
                            np.isfinite(face_normal).all()
                            and np.linalg.norm(face_normal) > 1e-12
                        ):
                            is_inside = (
                                float(
                                    np.dot(
                                        p - candidate,
                                        face_normal,
                                    )
                                ) < -1e-9
                            )
                    # Prefer escaping any containing solid over exterior contacts.
                    if (is_inside and not inside[i]) or (is_inside == inside[i] and dist_sq < d2[i]):
                        nearest[i], d2[i], inside[i] = candidate, dist_sq, is_inside
            return nearest, d2, inside
        for obj in self.geometry:
            if self.domain == 'CURVE':
                candidate = _nearest_curve_precise(obj, points, self.init_samples)
                candidates_inside = np.zeros(len(points), dtype=bool)
            elif self.domain == 'SURFACE':
                candidate = _nearest_surface_precise(
                    obj, points, (self.init_samples_u, self.init_samples_v))
                candidates_inside = np.zeros(len(points), dtype=bool)
            else:
                from FreeCAD import Base
                from Part import Vertex
                candidate = np.empty_like(points)
                candidates_inside = np.empty(len(points), dtype=bool)
                for i,p in enumerate(points):
                    # For an interior point Part.Solid.distToShape may report
                    # distance zero to the VOLUME. Query the boundary shell.
                    boundary = obj.OuterShell if hasattr(obj, 'OuterShell') else obj
                    result = boundary.distToShape(Vertex(Base.Vector(*[float(x) for x in p])))
                    candidate[i] = _vector3(result[1][0][0])
                    candidates_inside[i] = self._solid_is_inside(obj, p)
            distances = np.sum((points - candidate)**2, axis=1)
            mask = ((candidates_inside & ~inside) |
                    ((candidates_inside == inside) & (distances < d2)))
            nearest[mask] = candidate[mask]
            d2[mask] = distances[mask]
            inside[mask] = candidates_inside[mask]
        return nearest, d2, inside

    def add(self, ps):
        # The point/edge helper already performs a tested normal-free response.
        if self.delegate is not None:
            self.delegate.add(ps)
            return
        points = np.asarray(ps.verts, dtype=np.float64)
        nearest, d2, inside = self._nearest(points)
        radii = np.asarray(ps.rads, dtype=np.float64) + self._thickness
        active = np.where((d2 < radii*radii) | inside)[0]
        for i in active:
            distance = float(np.sqrt(max(0, d2[i])))
            if distance > 1e-10:
                # Solid interiors are projected outward, not back into the body.
                normal = (nearest[i] - points[i] if inside[i] else points[i] - nearest[i]) / distance
            else:
                velocity = np.asarray(ps.vel[i], dtype=np.float64)
                velocity_size = np.linalg.norm(velocity)
                normal = -velocity / velocity_size if velocity_size > 1e-10 else np.array([0., 0., 1.])
            ps.verts[i] = nearest[i] + normal * radii[i]
            vn = float(np.dot(ps.vel[i], normal))
            if vn < 0:
                ps.vel[i] -= (2 * vn) * normal
            ps.vel[i] *= self.absorption
            fn = float(np.dot(ps.force_resultant[i], normal))
            if fn < 0:
                ps.force_resultant[i] -= (2 * fn) * normal
            ps.force_resultant[i] *= self.absorption
