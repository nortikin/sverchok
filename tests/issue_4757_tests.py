import numpy as np
import unittest
from math import pi

from mathutils import Matrix

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.geom import circle_by_three_points
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.nurbs import SvGeomdlCurve, SvNativeNurbsCurve, SvNurbsBasisFunctions, SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import concatenate_nurbs_curves
from sverchok.utils.nurbs_common import SvNurbsMaths, elevate_bezier_degree, from_homogenous
from sverchok.utils.surface.nurbs import SvGeomdlSurface, SvNativeNurbsSurface
from sverchok.utils.surface.algorithms import SvCurveLerpSurface
from sverchok.dependencies import geomdl, FreeCAD

class ConcatenateTests(SverchokTestCase):
    def test_concat_4757(self):

        def run_test(implementation, use_nurbs):
            with self.subTest(implementation=implementation, use_nurbs=use_nurbs):
                cpts1 = np.array([[-1,-1,0], [1,-1,0]])
                cpts2 = np.array([[1,-1,0], [1,1,0]])
                cpts3 = np.array([[1,1,0], [0.464, 0.538, 0], [-0.423, 0.536, 0], [-1,1,0]])
                cpts4 = np.array([[-1,1,0], [-1,-1,0]])

                kv1 = knotvector = sv_knotvector.generate(1, 2)
                kv3 = knotvector = sv_knotvector.generate(3, 4)

                curve1 = SvNurbsCurve.build(implementation, 1, kv1, cpts1) 
                curve2 = SvNurbsCurve.build(implementation, 1, kv1, cpts2) 
                curve3 = SvNurbsCurve.build(implementation, 3, kv3, cpts3) 
                curve4 = SvNurbsCurve.build(implementation, 1, kv1, cpts4) 

                if use_nurbs:
                    curve = concatenate_nurbs_curves([curve1, curve2, curve3, curve4])
                else:
                    curve = concatenate_curves([curve1, curve2, curve3, curve4])

                self.assertEquals(len(curve.get_control_points()), 13)

        run_test(SvNurbsMaths.NATIVE, True)
        run_test(SvNurbsMaths.NATIVE, False)
        if geomdl is not None:
            run_test(SvNurbsMaths.GEOMDL, True)
            run_test(SvNurbsMaths.GEOMDL, False)
        if FreeCAD is not None:
            run_test(SvNurbsMaths.FREECAD, True)
            run_test(SvNurbsMaths.FREECAD, False)

