# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression tests for stable enums and accelerated nearest queries."""
import unittest
from unittest.mock import patch

import numpy as np

from sverchok.dependencies import scipy
from sverchok.nodes.pulga_physics.pulga_boundaries_force import (
    SvPulgaBoundingBoxForceNode,
)
from sverchok.utils.pulga_collision_domains import (
    HAS_NUMBA,
    SvStaticPointEdgeObstacleForce,
)
from sverchok.utils import pulga_parametric_obstacles as parametric


class PulgaPrCompatibilityTests(unittest.TestCase):

    def test_boundary_mode_ids_are_independent_of_freecad(self):
        expected = {
            'Box': 0,
            'Sphere': 1,
            'Sphere Surface': 2,
            'Plane': 3,
            'Mesh (Surface)': 4,
            'Mesh (Volume)': 5,
            'Mesh (Edges)': 9,
            'Curve': 10,
            'Surface': 11,
            'Solid (Surface)': 6,
            'Solid (Volume)': 7,
            'Solid Face': 8,
        }
        items = SvPulgaBoundingBoxForceNode.mode_enum_items
        self.assertEqual([item[1] for item in items], list(expected))
        self.assertEqual(
            {item[1]: item[3] for item in items},
            expected,
        )
        self.assertEqual(
            len(set(item[3] for item in items)),
            len(items),
        )

    def test_static_vertex_engine_selection(self):
        verts = [[0., 0., 0.], [1., 0., 0.]]

        numpy_force = SvStaticPointEdgeObstacleForce(
            verts, [], [0.], [0.], 'VERTS', 'NUMPY'
        )
        self.assertIsNone(numpy_force.tree)

        auto_force = SvStaticPointEdgeObstacleForce(
            verts, [], [0.], [0.], 'VERTS', 'AUTO'
        )
        if scipy is not None:
            self.assertIsNotNone(auto_force.tree)
        else:
            self.assertIsNone(auto_force.tree)

        closest, d2 = numpy_force.nearest([[.2, 0., 0.]])
        np.testing.assert_allclose(
            closest, [[0., 0., 0.]]
        )
        np.testing.assert_allclose(d2, [.04])

        if HAS_NUMBA:
            jit_force = SvStaticPointEdgeObstacleForce(
                verts, [], [0.], [0.], 'VERTS', 'NUMBA'
            )
            self.assertIsNone(jit_force.tree)

            jit_closest, jit_d2 = jit_force.nearest(
                [[.2, 0., 0.]]
            )
            np.testing.assert_allclose(
                jit_closest, closest
            )
            np.testing.assert_allclose(
                jit_d2, d2
            )

    @unittest.skipIf(
        scipy is None, 'SciPy is unavailable'
    )
    def test_precise_curve_uses_bounded_parameter(self):

        class Line:
            def get_u_bounds(self):
                return (0., 1.)

            def is_closed(self):
                return False

            def evaluate(self, t):
                return np.asarray(
                    [float(t), 0., 0.]
                )

            def evaluate_array(self, ts):
                t = np.asarray(ts, dtype=float)
                return np.column_stack((
                    t,
                    np.zeros(len(t)),
                    np.zeros(len(t)),
                ))

            def tangent_array(self, ts):
                return np.broadcast_to(
                    (1., 0., 0.),
                    (len(ts), 3),
                ).copy()

        result = parametric._nearest_curve_precise(
            Line(),
            np.asarray([[.4, .2, 0.]], dtype=float),
            20,
        )
        np.testing.assert_allclose(
            result,
            [[.4, 0., 0.]],
            atol=1e-3,
        )

    def test_fast_solid_classification_uses_bvh_normal(self):

        class Solid:
            def isInside(self, *args):
                raise AssertionError(
                    'Fast should not call FreeCAD.isInside'
                )

        solid = Solid()
        sample_vertices = np.asarray([
            [0., 0., 0.],
            [1., 0., 0.],
            [0., 1., 0.],
        ])

        with (
            patch.object(parametric, 'FreeCAD', object()),
            patch.object(
                parametric,
                '_solid_mesh',
                return_value=(
                    sample_vertices,
                    [(0, 1, 2)],
                ),
            ),
            patch.object(
                parametric,
                '_make_bvh',
            ) as make_bvh,
        ):
            bvh = make_bvh.return_value
            bvh.find_nearest.side_effect = lambda p: (
                (float(p[0]), float(p[1]), 0.),
                (0., 0., 1.),
                0,
                abs(p[2]),
            )

            force = parametric.SvParametricObstacleForce(
                [solid],
                'SOLID',
                'FAST',
                [0.],
                [0.],
            )

            locations, distances, inside = force._nearest(
                np.asarray([
                    [.2, .2, -.3],
                    [.2, .2, .3],
                ])
            )

            np.testing.assert_array_equal(
                inside,
                [True, False],
            )
            np.testing.assert_allclose(
                distances,
                [.09, .09],
            )
            np.testing.assert_allclose(
                locations[:, 2],
                [0., 0.],
            )
            self.assertEqual(
                bvh.find_nearest.call_count,
                2,
            )


if __name__ == '__main__':
    unittest.main()
