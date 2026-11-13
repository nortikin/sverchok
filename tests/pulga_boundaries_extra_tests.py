# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression tests for the extended Pulga Boundaries Force modes."""
import unittest
import numpy as np

from sverchok.dependencies import scipy
from sverchok.utils.pulga_boundaries_extra import (
    nearest_on_segments, SvBoundingEdgesForce,
    SvBoundingCurveForce, SvBoundingSurfaceForce)


class ParticleSystem:
    def __init__(self, points, velocity=(1., 2., 3.), force=(4., 5., 6.)):
        self.verts = np.asarray(points, dtype=np.float64)
        self.vel = np.broadcast_to(velocity, self.verts.shape).copy()
        self.force_resultant = np.broadcast_to(force, self.verts.shape).copy()


class LineCurve:
    def evaluate(self, t):
        import numpy as np
        return self.evaluate_array(np.asarray([t]))[0]

    def is_closed(self):
        return False

    def get_u_bounds(self):
        return 0., 1.

    def evaluate_array(self, ts):
        ts = np.asarray(ts)
        return np.column_stack((ts * 4., np.zeros(len(ts)), np.zeros(len(ts))))

    def tangent_array(self, ts):
        return np.broadcast_to((4., 0., 0.), (len(ts), 3)).copy()


class PlaneSurface:
    def get_u_bounds(self):
        return 0., 1.

    def get_v_bounds(self):
        return 0., 1.

    def get_u_min(self):
        return 0.

    def get_u_max(self):
        return 1.

    def get_v_min(self):
        return 0.

    def get_v_max(self):
        return 1.

    def evaluate_array(self, us, vs):
        us, vs = np.asarray(us), np.asarray(vs)
        return np.column_stack((us, vs, np.zeros(len(us))))

    def evaluate(self, u, v):
        return np.array([u, v, 0.])

    def normal_array(self, us, vs):
        return np.broadcast_to((0., 0., 1.), (len(us), 3)).copy()


class TestPulgaBoundariesExtra(unittest.TestCase):
    def test_nearest_segments_clamps_endpoints(self):
        points, tangents = nearest_on_segments(
            [[-3., 2., 0.], [1., 2., 0.]], [[0., 0., 0.]], [[2., 0., 0.]])
        np.testing.assert_allclose(points, [[0., 0., 0.], [1., 0., 0.]])
        np.testing.assert_allclose(tangents, [[1., 0., 0.], [1., 0., 0.]])

    def test_edges_constrain_position_velocity_force(self):
        ps = ParticleSystem([[1., 2., 0.]])
        f = SvBoundingEdgesForce([[0., 0., 0.], [4., 0., 0.]], [[0, 1]])
        f.setup(ps)
        f.add(ps)
        np.testing.assert_allclose(ps.verts, [[1., 0., 0.]])
        np.testing.assert_allclose(ps.vel, [[1., 0., 0.]])
        np.testing.assert_allclose(ps.force_resultant, [[4., 0., 0.]])

    def test_curve_fast_constraint(self):
        ps = ParticleSystem([[1.5, 2., 3.]])
        f = SvBoundingCurveForce(LineCurve(), method='FAST', resolution=8)
        f.add(ps)
        np.testing.assert_allclose(ps.verts, [[1.5, 0., 0.]], atol=1.e-12)
        np.testing.assert_allclose(ps.vel, [[1., 0., 0.]])

    def test_surface_fast_projection(self):
        ps = ParticleSystem([[0.4, 0.6, 2.], [0.8, 0.2, -2.]])
        f = SvBoundingSurfaceForce(PlaneSurface(), method='FAST', resolution_u=5, resolution_v=8)
        f.add(ps)
        np.testing.assert_allclose(ps.verts[:, 2], [0., 0.], atol=1.e-12)
        np.testing.assert_allclose(ps.vel[:, 2], [0., 0.], atol=1.e-12)
        np.testing.assert_allclose(ps.force_resultant[:, 2], [0., 0.], atol=1.e-12)

    @unittest.skipIf(scipy is None, 'SciPy not installed')
    def test_curve_precise(self):
        ps = ParticleSystem([[1.6, 1., 0.]])
        SvBoundingCurveForce(LineCurve(), method='PRECISE', init_samples=20).add(ps)
        np.testing.assert_allclose(ps.verts, [[1.6, 0., 0.]], atol=1.e-4)

    @unittest.skipIf(scipy is None, 'SciPy not installed')
    def test_surface_precise_independent_uv_samples(self):
        ps = ParticleSystem([[0.4, 0.6, 2.]])
        SvBoundingSurfaceForce(PlaneSurface(), method='PRECISE',
                               init_samples_u=8, init_samples_v=11).add(ps)
        np.testing.assert_allclose(ps.verts, [[0.4, 0.6, 0.]], atol=1.e-4)
        np.testing.assert_allclose(ps.vel, [[1., 2., 0.]])




class TestSolidFastBoundaries(unittest.TestCase):
    """Test the one-time tessellation without requiring actual FreeCAD."""

    def test_fast_solid_volume_delegates_to_mesh_and_caches(self):
        from unittest.mock import patch
        from sverchok.utils.pulga_boundaries_extra import SvBoundingSolidFastForce

        class FakeSolid:
            def __init__(self):
                self.calls = 0

            def tessellate(self, deflection):
                assert deflection == 0.05
                self.calls += 1
                return ([(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)],
                        [(0, 1, 2)])

        solid = FakeSolid()
        with patch('sverchok.utils.pulga_physics_modular_core.SvBoundingMeshForce') as engine:
            force = SvBoundingSolidFastForce(solid, volume=True, deflection=0.05)
            assert solid.calls == 1
            engine.assert_called_once()
            assert engine.call_args.kwargs['volume'] is True
            force.setup(None)
            force.add(None)
            force.add(None)
            engine.return_value.setup.assert_called_once_with(None)
            assert engine.return_value.add.call_count == 2
            assert solid.calls == 1

    def test_solid_face_wrapper_and_surface_mode(self):
        from unittest.mock import patch
        from sverchok.utils.pulga_boundaries_extra import SvBoundingSolidFastForce

        class FakeFace:
            def tessellate(self, tolerance):
                return ([(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)],
                        [(0, 1, 2)])

        class FakeWrapper:
            face = FakeFace()

        with patch('sverchok.utils.pulga_physics_modular_core.SvBoundingMeshForce') as engine:
            SvBoundingSolidFastForce(FakeWrapper(), volume=False)
            assert engine.call_args.kwargs['volume'] is False

    def test_rejects_invalid_deflection(self):
        from sverchok.utils.pulga_boundaries_extra import SvBoundingSolidFastForce
        with self.assertRaises(ValueError):
            SvBoundingSolidFastForce(object(), deflection=0)

if __name__ == '__main__':
    unittest.main()
