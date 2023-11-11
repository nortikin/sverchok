import numpy as np
import unittest
from math import pi

from sverchok.utils.testing import SverchokTestCase, requires
from sverchok.utils.nurbs_common import SvNurbsMaths, elevate_bezier_degree, from_homogenous
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsBasisFunctions, SvNurbsCurve
from sverchok.utils.curve.nurbs_solver import *
from sverchok.utils.curve.nurbs_solver_applications import interpolate_nurbs_curve_with_tangents

class NurbsSolverTests(SverchokTestCase):
    def test_interpolate_with_tangents(self):
        degree = 3
        points = np.array([[0,0,0], [1,0,0], [1,1,0]], dtype=np.float64)
        tangents = np.array([[-1,1,0], [1,1,0], [-1,-1,0]], dtype=np.float64)
        curve = interpolate_nurbs_curve_with_tangents(degree, points, tangents)
        print("CPTS:", curve.get_control_points())
        ts = np.array([0, 0.5, 1])
        tangents_result = curve.tangent_array(ts)
        print("Tgs:", tangents_result)

    def test_tangents_alphas(self):
        degree = 3
        #points = np.array([[0,0,0], [1,0,0], [1,1,0]], dtype=np.float64)
        tangents = np.array([[-1,1,0], [1,1,0], [-1,-1,0]], dtype=np.float64)
        ts = np.array([0, 0.5, 1.0])
        solver = SvNurbsCurveSolver(degree = degree)
        solver.set_curve_params(n_cpts = len(tangents))
        goal = SvNurbsCurveTangents(ts, tangents)
        solver.add_goal(goal)
        solver._init()
        alphas = goal.calc_alphas(solver, ts)
        print("A", alphas)


