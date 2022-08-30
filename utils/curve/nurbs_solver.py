# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict

from sverchok.utils.geom import Spline
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.nurbs_common import SvNurbsBasisFunctions, SvNurbsMaths, from_homogenous
from sverchok.utils.curve.nurbs import SvNurbsCurve

class SvNurbsCurveGoal(object):
    def copy(self):
        raise Exception("Not implemented")

    def add(self, other):
        raise Exception("Not implemented")
        
    def get_equations(self, solver):
        raise Exception("Not implemented")

    def get_n_defined_control_points(self):
        raise Exception("Not implemented")

class SvNurbsCurvePoints(SvNurbsCurveGoal):
    def __init__(self, us, points, weights = None):
        self.us = np.asarray(us)
        self.vectors = np.asarray(points)
        if weights is None:
            self.weights = None
        else:
            self.weights = np.asarray(weights)

    @staticmethod
    def single(u, point, weight=None):
        if weight is None:
            weights = None
        else:
            weights = [weight]
        return SvNurbsCurvePoints([u], [point], weights)

    def copy(self):
        return SvNurbsCurvePoints(self.us, self.vectors, self.weights)

    def get_weights(self):
        weights = self.weights
        n_points = len(self.vectors)
        if weights is None:
            weights = np.ones((n_points,))
        elif isinstance(weights, np.ndarray) and weights.shape == (1,):
            weights = np.full((n_points,), weights[0])
        elif isinstance(weights, (int,float)):
            weights = np.full((n_points,), weights)
        return weights

    def add(self, other):
        g = self.copy()
        g.us = np.concatenate((g.us, other.us))
        g.vectors = np.concatenate((g.vectors, other.vectors))
        g.weights = np.concatenate((g.get_weights(), other.get_weights()))
        return g

    def calc_alphas(self, solver, us):
        p = solver.degree
        alphas = [solver.basis.fraction(k,p, solver.curve_weights)(us) for k in range(solver.n_cpts)]
        alphas = np.array(alphas) # (n_cpts, n_points)
        return alphas

    def get_n_defined_control_points(self):
        return len(self.us)

    def get_equations(self, solver):
        ndim = 3
        us = self.us
        vectors = self.vectors

        n_points = len(vectors)
        n_equations = ndim * n_points
        n_unknowns = ndim * solver.n_cpts

        alphas = self.calc_alphas(solver, us)

        weights = self.get_weights()

        A = np.zeros((n_equations, n_unknowns))
        B = np.zeros((n_equations, 1))
        #print(f"A: {A.shape}, W {weights.shape}, n_points {n_points}")

        for pt_idx in range(n_points):
            for cpt_idx in range(solver.n_cpts):
                alpha = alphas[cpt_idx][pt_idx]
                for dim_idx in range(ndim):
                    A[ndim*pt_idx + dim_idx, ndim*cpt_idx + dim_idx] = weights[pt_idx] * alpha

        for pt_idx, point in enumerate(vectors):
            B[pt_idx*3:pt_idx*3+3,0] = weights[pt_idx] * point[np.newaxis]

        return A, B

class SvNurbsCurveTangents(SvNurbsCurvePoints):
    def __init__(self, us, tangents, weights = None):
        self.us = np.asarray(us)
        self.vectors = np.asarray(tangents)
        if weights is None:
            self.weights = None
        else:
            self.weights = np.asarray(weights)

    @staticmethod
    def single(u, tangent, weight=None):
        if weight is None:
            weights = None
        else:
            weights = [weight]
        return SvNurbsCurveTangents([u], [tangent], weights)

    def copy(self):
        return SvNurbsCurveTangents(self.us, self.vectors, self.weights)

    def add(self, other):
        g = self.copy()
        g.us = np.concatenate((g.us, other.us))
        g.vectors = np.concatenate((g.vectors, other.vectors))
        g.weights = np.concatenate((g.get_weights(), other.get_weights()))
        return g

    def calc_alphas(self, solver, us):
        p = solver.degree
        betas = [solver.basis.weighted_derivative(k, p, 1, solver.curve_weights)(us) for k in range(solver.n_cpts)]
        betas = np.array(betas) # (n_cpts, n_points)
        return betas

class SvNurbsCurveSelfIntersections(SvNurbsCurveGoal):
    def __init__(self, us1, us2, weights = None):
        if len(us1) != len(us2):
            raise Exception("Lengths of us1 and us2 must be equal")
        self.us1 = np.asarray(us1)
        self.us2 = np.asarray(us2)
        if weights is None:
            self.weights = None
        else:
            self.weights = np.asarray(weights)

    @staticmethod
    def single(u1, u2, weight=None):
        if weight is None:
            weights = None
        else:
            weights = [weight]
        return SvNurbsCurveSelfIntersections([u1], [u2], weights)

    def copy(self):
        return SvNurbsCurveSelfIntersections(self.us1, self.us2, self.weights)

    def get_weights(self):
        weights = self.weights
        if weights is None:
            n_points = len(self.us1)
            weights = np.ones((n_points,))
        return weights

    def add(self, other):
        g = self.copy()
        g.us1 = np.concatenate((g.us1, other.us1))
        g.us2 = np.concatenate((g.us2, other.us2))
        g.weights = np.concatenate((g.get_weights(), other.get_weights()))
        return g

    def calc_alphas(self, solver):
        p = solver.degree
        alphas = [solver.basis.fraction(k,p, solver.curve_weights)(self.us1) for k in range(solver.n_cpts)]
        alphas = np.array(alphas) # (n_cpts, n_points)
        betas = [solver.basis.fraction(k,p, solver.curve_weights)(self.us2) for k in range(solver.n_cpts)]
        betas = np.array(betas) # (n_cpts, n_points)
        return alphas, betas

    def get_n_defined_control_points(self):
        return len(self.us1)

    def get_equations(self, solver):
        ndim = 3
        us1 = self.us1
        us2 = self.us2
        p = solver.degree

        n_points = len(us1)
        n_equations = ndim * n_points
        n_unknowns = ndim * solver.n_cpts

        alphas, betas = self.calc_alphas(solver)

        weights = self.get_weights()

        A = np.zeros((n_equations, n_unknowns))
        B = np.zeros((n_equations, 1))

        for pt_idx in range(n_points):
            for cpt_idx in range(solver.n_cpts):
                alpha = alphas[cpt_idx][pt_idx]
                beta = betas[cpt_idx][pt_idx]
                for dim_idx in range(ndim):
                    A[ndim*pt_idx + dim_idx, ndim*cpt_idx + dim_idx] = weights[pt_idx] * (alpha - beta)

        return A, B

class SvNurbsCurveCotangents(SvNurbsCurveSelfIntersections):
    def __init__(self, us1, us2, weights = None):
        if len(us1) != len(us2):
            raise Exception("Lengths of us1 and us2 must be equal")
        self.us1 = np.asarray(us1)
        self.us2 = np.asarray(us2)
        if weights is None:
            self.weights = None
        else:
            self.weights = np.asarray(weights)

    @staticmethod
    def single(u1, u2, weight=None):
        if weight is None:
            weights = None
        else:
            weights = [weight]
        return SvNurbsCurveCotangents([u1], [u2], weights)

    def copy(self):
        return SvNurbsCurveCotangents(self.us1, self.us2, self.weights)

    def calc_alphas(self, solver):
        p = solver.degree
        alphas = [solver.basis.weighted_derivative(k, p, 1, solver.curve_weights)(self.us1) for k in range(solver.n_cpts)]
        alphas = np.array(alphas) # (n_cpts, n_points)
        betas = [solver.basis.weighted_derivative(k, p, 1, solver.curve_weights)(self.us2) for k in range(solver.n_cpts)]
        betas = np.array(betas) # (n_cpts, n_points)
        return alphas, betas

class SvNurbsCurveSolver(SvCurve):
    def __init__(self, degree):
        self.degree = degree
        self.n_cpts = None
        self.curve_weights = None
        self.knotvector = None
        self.goals = []
        self.A = self.B = None

    def copy(self):
        solver = SvNurbsCurveSolver(self.degree)
        solver.n_cpts = self.n_cpts
        solver.curve_weights = self.curve_weights
        solver.knotvector = self.knotvector
        solver.goals = self.goals[:]
        solver.A = self.A
        solver.B = self.B
        return solver

    def evaluate(self, t):
        return self.to_nurbs().evaluate(t)

    def evaluate_array(self, ts):
        return self.to_nurbs().evaluate_array(ts)

    def get_u_bounds(self):
        return self.to_nurbs().get_u_bounds()

    def get_degree(self):
        return self.degree

    def get_control_points(self):
        return self.to_nurbs().get_control_points()

    def set_curve_weights(self, weights):
        if len(weights) != self.n_cpts:
            raise Exception("Number of weights must be equal to the number of control points")
        self.curve_weights = np.asarray(weights)

    def set_curve_params(self, n_cpts, knotvector = None, weights = None):
        self.n_cpts = n_cpts
        if knotvector is not None:
            err = sv_knotvector.check(self.degree, knotvector, n_cpts)
            if err is not None:
                raise Exception(err)
            self.knotvector = np.asarray(knotvector)
        else:
            self.knotvector = sv_knotvector.generate(self.degree, n_cpts)
        self.curve_weights = weights

    def guess_curve_params(self):
        n_equations = sum(g.get_n_defined_control_points() for g in self.goals)
        self.n_cpts = n_equations
        self.knotvector = sv_knotvector.generate(self.degree, self.n_cpts)

    def add_goal(self, goal):
        self.goals.append(goal)

    def set_goals(self, goals):
        self.goals = goals[:]

    def _sort_goals(self):
        goal_dict = defaultdict(list)
        for goal in self.goals:
            goal_dict[type(goal)].append(goal)
        goals = []
        for clazz in goal_dict:
            clz_goals = goal_dict[clazz]
            goal = clz_goals[0]
            for other_goal in clz_goals[1:]:
                goal = goal.add(other_goal)
            goals.append(goal)
        self.goals = goals

    def _init(self):
        if self.n_cpts is None:
            raise Exception("Number of control points is not specified; specify it in the constructor, in set_curve_params() call, or call guess_curve_params()")
        if self.knotvector is None:
            raise Exception("Knotvector is not specified; specify it in the constructor, in set_curve_params() call, or call guess_curve_params()")
        ndim = 3
        n = self.n_cpts
        p = self.degree
        if self.curve_weights is None:
            self.curve_weights = np.ones((n,))
        self.basis = SvNurbsBasisFunctions(self.knotvector)

        self._sort_goals()
        As = []
        Bs = []
        for goal in self.goals:
            Ai, Bi = goal.get_equations(self)
            As.append(Ai)
            Bs.append(Bi)
        self.A = np.concatenate(As)
        self.B = np.concatenate(Bs)

    def solve(self, src_curve = None, implementation = SvNurbsMaths.NATIVE):
        self._init()

        ndim = 3
        n = self.n_cpts
        n_equations, n_unknowns = self.A.shape
        print(f"A: {self.A.shape}")
        if n_equations == n_unknowns:
            A1 = np.linalg.inv(self.A)
            X = (A1 @ self.B).T
        elif n_equations < n_unknowns:
            A1 = np.linalg.pinv(self.A)
            X = (A1 @ self.B).T
        else: # n_equations > n_unknowns
            X, residues, rank, singval = np.linalg.lstsq(self.A, self.B)
            print(residues)
            
        d_cpts = X.reshape((n, ndim))
        if src_curve is None:
            return SvNurbsCurve.build(implementation, self.degree, self.knotvector, d_cpts, self.curve_weights)
        else:
            cpts = src_curve.get_control_points() + d_cpts
            return SvNurbsCurve.build(implementation, self.degree, self.knotvector, cpts, self.curve_weights)

    def to_nurbs(self, implementation = SvNurbsMaths.NATIVE):
        solver = self.copy()
        solver.guess_curve_params()
        return solver.solve(implementation = implementation)

