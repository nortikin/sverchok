# SPDX-License-Identifier: GPL-3.0-or-later
"""Geometric sampling and reaction tests for parametric Pulga obstacles.

Run with Blender/Sverchok Python so mathutils.bvhtree is available.
"""
import unittest
import numpy as np

from sverchok.utils.pulga_parametric_obstacles import (
    _surface_grid, _curve_segments, SvParametricObstacleForce)


class Line:
    def get_u_bounds(self):
        return (0., 1.)

    def evaluate_array(self, ts):
        return np.column_stack((ts, np.zeros(len(ts)), np.zeros(len(ts))))


class Plane:
    def get_u_bounds(self):
        return (0., 1.)

    def get_v_bounds(self):
        return (0., 1.)

    def evaluate_array(self, us, vs):
        return np.column_stack((us, vs, np.zeros(len(us))))


class FakeSystem:
    def __init__(self, coordinates, velocity=None):
        self.verts = np.asarray(coordinates, dtype=np.float64)
        self.v_len = len(self.verts)
        self.vel = np.asarray(velocity if velocity is not None else np.zeros_like(self.verts), dtype=np.float64)
        self.rads = np.full(self.v_len, 0.2, dtype=np.float64)
        self.force_resultant = np.zeros_like(self.verts)


class ParametricObstacleTests(unittest.TestCase):
    def test_curve_samples(self):
        vs, es = _curve_segments(Line(), 6)
        self.assertEqual(vs.shape, (6,3))
        self.assertEqual(es.shape, (5,2))
        self.assertTrue(np.allclose(vs[3], [0.6,0.,0.]))

    def test_surface_mesh(self):
        vs, faces = _surface_grid(Plane(), 5,4)
        self.assertEqual(vs.shape, (20,3))
        self.assertEqual(len(faces), 24)

    def test_fast_curve_repulsion(self):
        force = SvParametricObstacleForce([Line()], 'CURVE', 'FAST', [0.], [0.], resolution=11)
        ps = FakeSystem([[0.5,0.05,0.]], [[0.,-0.1,0.]])
        force.setup(ps)
        force.add(ps)
        self.assertAlmostEqual(ps.verts[0,1], .2, places=5)
        self.assertGreater(ps.vel[0,1], 0.)

    def test_fast_surface_both_sides(self):
        for z, direction in ((.05,1),(-.05,-1)):
            with self.subTest(z=z):
                ps = FakeSystem([[.5,.5,z]], [[0.,0.,-direction]])
                force = SvParametricObstacleForce([Plane()], 'SURFACE', 'FAST', [0.], [0.],
                                                  resolution_u=5,resolution_v=5)
                force.setup(ps)
                force.add(ps)
                self.assertAlmostEqual(ps.verts[0,2], .2*direction, places=5)
                self.assertGreater(ps.vel[0,2]*direction,0.)

    def test_fast_surface_outside_radius_unchanged(self):
        ps = FakeSystem([[.5,.5,1.0]])
        force = SvParametricObstacleForce(Plane(), 'SURFACE', 'FAST', [0.], [0.],
                                          resolution_u=5,resolution_v=5)
        force.setup(ps)
        force.add(ps)
        self.assertAlmostEqual(ps.verts[0,2],1.0)

    def test_precise_surface_independent_initial_samples(self):
        # The nearest-point code needs Blender/Sverchok, as do the other tests.
        from sverchok.utils.manifolds import nearest_point_on_surface

        class CountedPlane(Plane):
            def __init__(self):
                self.sample_count = 0
            def get_u_min(self):
                return 0.0
            def get_u_max(self):
                return 1.0
            def get_v_min(self):
                return 0.0
            def get_v_max(self):
                return 1.0
            def evaluate_array(self, us, vs):
                self.sample_count += len(us)
                return super().evaluate_array(us, vs)

        plane = CountedPlane()
        nearest_point_on_surface([[0.3, 0.4, 0.1]], plane,
                                 init_samples=(4, 7), precise=False)
        self.assertEqual(plane.sample_count, 28)
        plane.sample_count = 0
        nearest_point_on_surface([[0.3, 0.4, 0.1]], plane,
                                 init_samples=4, precise=False)
        self.assertEqual(plane.sample_count, 16)

    def test_surface_uses_supplied_resolution(self):
        a,b = _surface_grid(Plane(), 3,8)
        self.assertEqual(len(a),24)
        self.assertEqual(len(b),28)


if __name__ == '__main__':
    unittest.main()
