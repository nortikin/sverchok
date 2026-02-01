# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from dataclasses import dataclass
from sverchok.core.sv_custom_exceptions import ArgumentError, InvalidStateError
from sverchok.dependencies import scipy

@dataclass
class Summand:
    param_idx : int
    vector : np.ndarray

class Constraint:
    def __init__(self, point, summands = None):
        if summands is None:
            summands = []
        self.point = np.array(point)
        self.summands = summands

    def get_last_parameter_idx(self):
        if not self.summands:
            return None
        return max([s.param_idx for s in self.summands])

    @staticmethod
    def eye(param_idxs, ndim=3):
        vectors = np.eye(len(param_idxs))
        summands = [Summand(idx, vector) for idx, vector in zip(param_idxs, vectors)]
        zero = np.zeros((ndim,))
        return Constraint(zero, summands)

@dataclass
class Solution:
    control_points : np.ndarray
    parameters : np.ndarray
    goal_value : float
    success : bool
    message : str

class Optimizer:
    def __init__(self, n_pts, ndim=3):
        self.n_pts = n_pts
        self.constraints = dict()
        self.bounds = dict()
        self.init_values = dict()
        self.ndim = ndim
        self._orig_points = None
        self._matrix = None
        self._goal = None
        self._last_parameter_idx = None
        self._inited = False

    def allocate_parameters(self, count=1):
        if self._inited:
            raise InvalidStateError("Optimizer was already initialized")
        if self._last_parameter_idx is None:
            self._last_parameter_idx = -1
        params = np.arange(self._last_parameter_idx+1, self._last_parameter_idx + 1 + count)
        self._last_parameter_idx = params[-1]
        return params

    def set_constraint(self, idx, point, vectors=None, bounds=None):
        if self._inited:
            raise InvalidStateError("Optimizer was already initialized")
        summands = []
        param_idxs = []
        if vectors is not None:
            if bounds is None:
                bounds = [(None, None) for _ in vectors]
            param_idxs = self.allocate_parameters(count = len(vectors))
            for param_idx, vector, bounds in zip(param_idxs, vectors, bounds):
                #print(f"S[{param_idx}] = {vector}")
                summand = Summand(param_idx, vector)
                summands.append(summand)
                self.bounds[param_idx] = bounds
        self.constraints[idx] = Constraint(point, summands)
        return param_idxs

    def bind_to_existing_parameter(self, point_idx, param_idx, point, vector=None):
        if self._inited:
            raise InvalidStateError("Optimizer was already initialized")
        if vector is not None:
            summands = [Summand(param_idx, vector)]
        else:
            summands = None
        constraint = Constraint(point, summands)
        self.constraints[point_idx] = constraint

    def set_goal(self, goal):
        self._goal = goal

    def _calc_n_dimensions(self):
        result = 0
        for idx in self.constraints:
            j = self.constraints[idx].get_last_parameter_idx()
            if j is not None:
                result = max(result, j)
        return result+1

    def _init(self):
        if self._inited:
            return
        n_target = self.n_pts * self.ndim
        orig_points = np.zeros((n_target,))
        for idx in range(self.n_pts):
            if idx not in self.constraints:
                param_idxs = self.allocate_parameters(count = self.ndim)
                self.constraints[idx] = Constraint.eye(param_idxs, ndim = self.ndim)
        n_params = self._calc_n_dimensions()
        A = np.zeros((n_target, n_params))
        row_idx = 0
        for constraint_idx in range(self.n_pts):
            constraint = self.constraints[constraint_idx]
            n_rows = self.ndim
            orig_points[row_idx : row_idx + n_rows] = constraint.point#[np.newaxis].T
            for summand in constraint.summands:
                #print(f"A[{row_idx}, {summand.param_idx}] = {summand.vector}")
                A[row_idx : row_idx + n_rows, summand.param_idx] = summand.vector
            row_idx += n_rows
        print("A", A.shape)
        self._matrix = A
        self._orig_points = orig_points

    def _evaluate(self, params):
        xs = self._orig_points + self._matrix @ np.array(params)
        points = xs.reshape((self.n_pts, self.ndim))
        return points

    def minimize(self, tol=None):
        self._init()
        if self._goal is None:
            raise InvalidStateError("Goal was not set")
        def goal(params):
            return self._goal(self._evaluate(params))
        init_values = np.zeros((self._calc_n_dimensions(),))
        for p_idx in self.init_values:
            init_values[p_idx] = self.init_values[p_idx]
        bounds = [self.bounds.get(i, (None, None)) for i in range(self._last_parameter_idx+1)]
        sol = scipy.optimize.minimize(fun=goal, x0=init_values,
                                       method = 'L-BFGS-B',
                                       bounds = bounds,
                                       tol = tol)
        print(sol)
        points = self._evaluate(sol.x)
        solution = Solution(points, sol.x, sol.fun, sol.success, sol.message)
        return solution

