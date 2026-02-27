# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import enum
import numpy as np
import sys

from sverchok.core.sv_custom_exceptions import AlgorithmError, ArgumentError
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions
    )
from sverchok.utils.math import np_dot
from sverchok.utils.geom import Spline, PlaneEquation, center, linear_approximation
from sverchok.utils.sv_logging import get_logger
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.core import other_direction, SurfaceDirection
from sverchok.utils.surface.algorithms import unify_nurbs_surfaces, make_planar_surface
from sverchok.utils.curve.nurbs_algorithms import unify_curves
from sverchok.utils.curve.nurbs_solver_applications import adjust_curve_points, interpolate_nurbs_curve
from sverchok.utils.linalg import least_squares_sparse, least_squares_with_constraints, solve_sparse

class SvNurbsSurfaceGoal:
    pass

class SvNurbsSurfacePoints(SvNurbsSurfaceGoal):
    def __init__(self, exact=False):
        self.us = []
        self.vs = []
        self.points = []
        self.weights = []
        self.exact = exact

    def append(self, u, v, point, weight = 1.0):
        self.us.append(u)
        self.vs.append(v)
        self.points.append(point)
        self.weights.append(weight)

    def extend(self, goal):
        self.us.extend(goal.us)
        self.vs.extend(goal.vs)
        self.points.extend(goal.points)
        self.weights.extend(goal.weigths)

    def clear(self):
        self.us = []
        self.vs = []
        self.points = []
        self.weights = []

    def is_empty(self):
        return len(self.us) == 0

    def get_n_points(self):
        return len(self.points)

    def copy(self):
        goal = SvNurbsSurfacePoints()
        goal.us = self.us[:]
        goal.vs = self.vs[:]
        goal.points = self.points[:]
        goal.weights = self.weights[:]
        goal.exact = self.exact
        return goal

class SvNurbsSurfaceControls(SvNurbsSurfaceGoal):
    def __init__(self, exact=False):
        self.u_idxs = []
        self.v_idxs = []
        self.control_points = []
        self.weights = []
        self.exact = exact

    def append(self, i, j, point, weight = 1.0):
        self.u_idxs.append(i)
        self.v_idxs.append(j)
        self.control_points.append(point)
        self.weights.append(weight)

    def extend(self, goal):
        self.u_idxs.extend(goal.u_idxs)
        self.v_idxs.extend(goal.v_idxs)
        self.control_points.extend(goal.control_points)
        self.weights.extend(goal.weights)

    def clear(self):
        self.u_idxs = []
        self.v_idxs = []
        self.control_points = []
        self.weights = []

    def is_empty(self):
        return len(self.u_idxs) == 0

    def get_n_points(self):
        return len(self.control_points)
    
    def copy(self):
        goal = SvNurbsSurfaceControls()
        goal.u_idxs = self.u_idxs[:]
        goal.v_idxs = self.v_idxs[:]
        goal.control_points = self.control_points[:]
        goal.weights = self.weights[:]
        goal.exact = self.exact
        return goal

class SvNurbsSurfaceSolver:
    def __init__(self):
        self._degree_u = None
        self._degree_v = None
        self._knotvector_u = None
        self._knotvector_v = None
        self.src_control_points = None
        self.src_surface = None
        self.src_weights = None
        self.n_cpts_u = None
        self.n_cpts_v = None
        self._goals = dict()
        self._goals[(SvNurbsSurfacePoints,False)] = SvNurbsSurfacePoints(exact=False)
        self._goals[(SvNurbsSurfaceControls,False)] = SvNurbsSurfaceControls(exact=False)
        self._goals[(SvNurbsSurfacePoints,True)] = SvNurbsSurfacePoints(exact=True)
        self._goals[(SvNurbsSurfaceControls,True)] = SvNurbsSurfaceControls(exact=True)
        self._A = dict()
        self._B = dict()
        self._alphas = dict()

    @property
    def uv_points(self):
        return self._goals[(SvNurbsSurfacePoints,False)]

    @uv_points.setter
    def uv_points(self, goal):
        self._goals[(SvNurbsSurfacePoints,False)] = goal

    @property
    def exact_uv_points(self):
        return self._goals[(SvNurbsSurfacePoints,True)]

    @exact_uv_points.setter
    def exact_uv_points(self, goal):
        self._goals[(SvNurbsSurfacePoints,True)] = goal

    @property
    def fixed_cpts(self):
        return self._goals[(SvNurbsSurfaceControls,False)]

    @fixed_cpts.setter
    def fixed_cpts(self, goal):
        self._goals[(SvNurbsSurfaceControls,False)] = goal

    @property
    def exact_fixed_cpts(self):
        return self._goals[(SvNurbsSurfaceControls,True)]

    @exact_fixed_cpts.setter
    def exact_fixed_cpts(self, goal):
        self._goals[(SvNurbsSurfaceControls,True)] = goal

    def copy(self, uv_points=None, fixed_cpts=None, knotvector_u=None, knotvector_v=None):
        solver = SvNurbsSurfaceSolver()
        solver._degree_u = self._degree_u
        solver._degree_v = self._degree_v
        if knotvector_u is None:
            solver._knotvector_u = self._knotvector_u
        else:
            solver._knotvector_u = knotvector_u
        if knotvector_v is None:
            solver._knotvector_v = self._knotvector_v
        else:
            solver._knotvector_v = knotvector_v
        solver.src_control_points = self.src_control_points
        solver.src_surface = self.src_surface
        solver.src_weights = self.src_weights
        solver.n_cpts_u = self.n_cpts_u
        solver.n_cpts_v = self.n_cpts_v
        if uv_points is None and knotvector_u is None and knotvector_v is None:
            solver.uv_points = self.uv_points.copy()
            solver._alphas[False] = self._alphas[False]
        else:
            solver.uv_points = uv_points
        if fixed_cpts is None:
            solver.fixed_cpts = self.fixed_cpts.copy()
        else:
            solver.fixed_cpts = fixed_cpts
        return solver

    PROBLEM_WELLDETERMINED = 'WELLDETERMINED'
    PROBLEM_UNDERDETERMINED = 'UNDERDETERMINED'
    PROBLEM_OVERDETERMINED = 'OVERDETERMINED'
    PROBLEM_ANY = {PROBLEM_WELLDETERMINED, PROBLEM_UNDERDETERMINED, PROBLEM_OVERDETERMINED}

    @staticmethod
    def from_surface(surface):
        solver = SvNurbsSurfaceSolver()
        solver._degree_u = surface.get_degree_u()
        solver._degree_v = surface.get_degree_v()
        solver._knotvector_u = surface.get_knotvector_u()
        solver._knotvector_v = surface.get_knotvector_v()
        solver.src_control_points = surface.get_control_points().copy()
        solver.n_cpts_u, solver.n_cpts_v, _ = solver.src_control_points.shape
        solver.src_weights = surface.get_weights().copy()
        solver.src_surface = surface
        return solver

    @staticmethod
    def from_parameters(degree_u, degree_v, n_cpts_u, n_cpts_v, knotvector_u, knotvector_v):
        solver = SvNurbsSurfaceSolver()
        solver._degree_u = degree_u
        solver._degree_v = degree_v
        solver._knotvector_u = knotvector_u
        solver._knotvector_v = knotvector_v
        solver.n_cpts_u = n_cpts_u
        solver.n_cpts_v = n_cpts_v
        return solver

    def _reset_caches(self):
        self._A = dict()
        self._B = dict()
        self._alphas = dict()

    def add_uv_point(self, u, v, point, weight=1.0, exact=False):
        self._reset_caches()
        if exact:
            self.exact_uv_points.append(u, v, point, weight=weight)
        else:
            self.uv_points.append(u, v, point, weight=weight)

    def add_uv_points(self, goals, exact=False):
        for goal in goals:
            self.add_uv_point(*goal, exact=exact)

    def set_control_point(self, i, j, point, weight=1.0, exact=False):
        self._reset_caches()
        if exact:
            self.exact_fixed_cpts.append(i, j, point, weight=weight)
        else:
            self.fixed_cpts.append(i, j, point, weight=weight)

    def _get_n_cpts(self):
        if self.src_control_points is None:
            n_cpts_u, n_cpts_v = self.n_cpts_u, self.n_cpts_v
            ndim = 3
        else:
            n_cpts_u, n_cpts_v, ndim = self.src_control_points.shape
        return n_cpts_u, n_cpts_v, ndim
    
    def _get_weights(self, n_cpts_u, n_cpts_v):
        if self.src_control_points is None:
            weights = np.ones((n_cpts_u, n_cpts_v))
        else:
            weights = self.src_weights
        return weights

    def _calc_alphas(self, exact, n_cpts_u, n_cpts_v):
        if exact in self._alphas:
            return self._alphas[exact]
        us = np.array(self._goals[(SvNurbsSurfacePoints,exact)].us)
        vs = np.array(self._goals[(SvNurbsSurfacePoints,exact)].vs)
        basis_u = SvNurbsBasisFunctions(self._knotvector_u)
        basis_v = SvNurbsBasisFunctions(self._knotvector_v)
        alphas_u = np.array([basis_u.function(k, self._degree_u)(us) for k in range(n_cpts_u)])
        alphas_v = np.array([basis_v.function(k, self._degree_v)(vs) for k in range(n_cpts_v)])
        self._alphas[exact] = (alphas_u, alphas_v)
        return self._alphas[exact]

    def _get_n_points(self):
        return sum([goal.get_n_points() for goal in self._goals.values()])

    def _get_n_equations(self):
        _n_cpts_u, _n_cpts_v, ndim = self._get_n_cpts()
        return ndim * self._get_n_points()

    def _get_n_unknowns(self):
        n_cpts_u, n_cpts_v, ndim = self._get_n_cpts()
        return n_cpts_u * n_cpts_v * ndim

    def _prepare_A(self, exact, logger):
        if exact in self._A:
            return self._A[exact]

        uv_points = self._goals[(SvNurbsSurfacePoints,exact)]
        fixed_cpts = self._goals[(SvNurbsSurfaceControls,exact)]
        n_cpts_u, n_cpts_v, ndim = self._get_n_cpts()
        weights = self._get_weights(n_cpts_u, n_cpts_v)
        n_cpts = n_cpts_u * n_cpts_v
        n_uv_points = uv_points.get_n_points()
        n_fixed_cpts = fixed_cpts.get_n_points()
        n_equations = ndim * (n_uv_points + n_fixed_cpts)
        n_unknowns = ndim * n_cpts

        # alphas_u : (n_cpts_u, n_pts)
        # alphas_v : (n_cpts_v, n_pts)
        alphas_u, alphas_v = self._calc_alphas(exact, n_cpts_u, n_cpts_v)

        pt_idxs = np.arange(n_uv_points)
        cpt_idxs = np.arange(n_cpts)# n_cpts_v * cpt_u_idxs + cpt_v_idxs
        alphas_u_t = np.transpose(alphas_u[np.newaxis], axes=(1,0,2))
        alphas_v_t = alphas_v[np.newaxis]
        weights_t = np.transpose(weights[np.newaxis], axes=(1,2,0))
        alphas = alphas_u_t * alphas_v_t * weights_t # (n_cpts_u, n_cpts_v, n_pts)
        pt_weights = np.array(uv_points.weights)
        alphas = np.reshape(alphas, (n_cpts_u*n_cpts_v, n_uv_points)).T

        A = np.zeros((n_equations, n_unknowns))

        pt_idxs_A, cpt_idxs_A = np.meshgrid(ndim*pt_idxs, ndim*cpt_idxs, indexing='ij')

        for dim_idx in range(ndim):
            A[pt_idxs_A + dim_idx, cpt_idxs_A + dim_idx] = alphas

        denominators = A[pt_idxs_A, cpt_idxs_A].sum(axis=1)
        for dim_idx in range(ndim):
            A[pt_idxs_A + dim_idx, cpt_idxs_A + dim_idx] /= denominators[pt_idxs][np.newaxis].T
        for dim_idx in range(ndim):
            A[pt_idxs_A + dim_idx, cpt_idxs_A + dim_idx] *= pt_weights[np.newaxis].T

        for j in range(n_fixed_cpts):
            cpt_u_idx = fixed_cpts.u_idxs[j]
            cpt_v_idx = fixed_cpts.v_idxs[j]
            cpt_idx = n_cpts_v * cpt_u_idx + cpt_v_idx
            for dim_idx in range(ndim):
                A[ndim*(j + n_uv_points) + dim_idx, ndim*cpt_idx + dim_idx] = fixed_cpts.weights[j]

        self._A[exact] = A
        return self._A[exact]

    def _prepare_B(self, exact):
        if exact in self._B:
            return self._B[exact]

        _, _, ndim = self._get_n_cpts()

        uv_points = self._goals[(SvNurbsSurfacePoints,exact)]
        fixed_cpts = self._goals[(SvNurbsSurfaceControls,exact)]

        n_uv_points = uv_points.get_n_points()
        n_fixed_cpts = fixed_cpts.get_n_points()
        n_equations = ndim * (n_uv_points + n_fixed_cpts)

        if self.src_surface is not None:
            us = uv_points.us
            vs = uv_points.vs
            src_points = self.src_surface.evaluate_array(us, vs)
        else:
            src_points = None

        pts = np.array(uv_points.points)

        B = np.zeros((n_equations, 1))
        for pt_idx, point in enumerate(pts):
            if src_points is not None:
                point = point - src_points[pt_idx]
            B[pt_idx*ndim:pt_idx*ndim+ndim, 0] = point[np.newaxis] * uv_points.weights[pt_idx]

        for j in range(n_fixed_cpts):
            cpt = fixed_cpts.control_points[j]
            B[(j+n_uv_points)*ndim : (j+n_uv_points)*ndim+ndim, 0] = cpt * self.fixed_cpts.weights[j]

        self._B[exact] = B
        return self._B[exact]

    def _check_has_constraints(self, n_equations, n_unknowns):
        if n_equations > n_unknowns:
            for clazz, exact in self._goals:
                if exact and not self._goals[(clazz,exact)].is_empty():
                    return True
            return False
        else:
            for clazz, exact in self._goals:
                if exact:
                    self._goals[(clazz,False)].extend(self._goals[(clazz,True)])
                    self._goals[(clazz,True)].clear()
            return False

    def solve(self, logger = None):
        problem_type, residue, surface = self.solve_ex(logger = logger)
        return surface

    def solve_ex(self, problem_types = PROBLEM_ANY, implementation = SvNurbsMaths.NATIVE, logger = None):
        if logger is None:
            logger = get_logger()

        n_cpts_u, n_cpts_v, ndim = self._get_n_cpts()

        n_equations = self._get_n_equations()
        n_unknowns = self._get_n_unknowns()
        has_constraints = self._check_has_constraints(n_equations, n_unknowns)

        A = self._prepare_A(False, logger)
        B = self._prepare_B(False)
        if has_constraints:
            exact_A = self._prepare_A(True, logger)
            exact_B = self._prepare_B(True)
        else:
            exact_A = None
            exact_B = None

        residue = None
        if n_equations == n_unknowns:
            problem_type = SvNurbsSurfaceSolver.PROBLEM_WELLDETERMINED
            if problem_type not in problem_types:
                raise AlgorithmError("The problem is well-determined")
            try:
                X = solve_sparse(A, B)
            except np.linalg.LinAlgError as e:
                logger.error(f"Matrix: {A}")
                raise AlgorithmError(f"Can not solve: #equations = {n_equations}, #unknowns = {n_unknowns}: {e}") from e
        elif n_equations < n_unknowns:
            problem_type = SvNurbsSurfaceSolver.PROBLEM_UNDERDETERMINED
            if problem_type not in problem_types:
                raise AlgorithmError("The problem is under-determined")
            X, residue = least_squares_sparse(A, B)
        else: # n_equations > n_unknowns
            problem_type = SvNurbsSurfaceSolver.PROBLEM_OVERDETERMINED
            if problem_type not in problem_types:
                raise AlgorithmError("The system is overdetermined")
            if has_constraints:
                logger.debug(f"Solving overdetermined system with constraints: #equations = {n_equations}, #unknonwns = {n_unknowns}")
                X, residue = least_squares_with_constraints(A, B, exact_A, exact_B, logger=logger)
            else:
                logger.debug(f"Solving overdetermined system without constraints: #equations = {n_equations}, #unknonwns = {n_unknowns}")
                X, residue = least_squares_sparse(A, B)

        d_cpts = X.reshape((n_cpts_u, n_cpts_v, ndim))
        if self.src_control_points is None:
            cpts = d_cpts
        else:
            cpts = self.src_control_points + d_cpts

        surface = SvNurbsMaths.build_surface(implementation=implementation,
                                          degree_u = self._degree_u,
                                          degree_v = self._degree_v,
                                          knotvector_u = self._knotvector_u,
                                          knotvector_v = self._knotvector_v,
                                          control_points = cpts,
                                          weights = self.src_weights)
        return problem_type, residue, surface

def calc_uv_knots(points, metric='DISTANCE'):
    n_pts_u, n_pts_v, _ = points.shape
    knots = np.array([Spline.create_knots(points[:,j], metric=metric) for j in range(n_pts_v)])
    uknots = knots.mean(axis=0)
    knots = np.array([Spline.create_knots(points[i,:], metric=metric) for i in range(n_pts_u)])
    vknots = knots.mean(axis=0)
    return uknots, vknots

def interpolate_nurbs_surface(degree_u, degree_v, points,
                              metric = 'DISTANCE',
                              uknots = None, vknots = None,
                              knotvector_u = None, knotvector_v = None,
                              implementation = SvNurbsMaths.NATIVE,
                              logger = None):
    """
    Interpolate NURBS surface from array of points.

    This implementation solves a system of MxN equations directly. In general, this is slower
    than a "shortcut" algorithm described in The NURBS Book. For performance, this method
    tries to use sparse matrices implementation from scipy, when it is available.
    For arbitrary metric, this provides more "precise" (more according to metric) results.

    Args:
        * degree_u, degree_v: surface degree along U and V direction.
        * points: points to interpolate between. List of lists of points or
            np.array of shape (n,m,3).
        * metric: metric to calculate U and V parameters of points.
        * uknots, vknots: U and V parameters of points. If not provided, will be
            calculated from metric.
        * knotvector_u, knotvector_v: surface knotvectors along U and V direction.
            If not provided, will be calculated from uknots / vknots or from metric.
            If provided, has to be compatible enough with uknots/vknots, otherwie
            thre resulting surface can have werid shape (however it still will be
            a valid interpolation).
        * implementation: NURBS mathematics implementation
        * logger: a logger instance

    Returns:
        * SvNurbsSurface instance.
    """
    points = np.asarray(points)
    n_pts_u, n_pts_v, ndim = points.shape

    if (uknots is None) != (vknots is None):
        raise ArgumentError("uknots and vknots must be either both provided or both omitted")

    if uknots is None:
        knots = np.array([Spline.create_knots(points[:,j], metric=metric) for j in range(n_pts_v)])
        uknots = knots.mean(axis=0)
    if vknots is None:
        knots = np.array([Spline.create_knots(points[i,:], metric=metric) for i in range(n_pts_u)])
        vknots = knots.mean(axis=0)

    if knotvector_u is None:
        knotvector_u = sv_knotvector.from_tknots(degree_u, uknots)
    #logger.debug("U: degree %s, N %s, knots %s => knotvector %s", degree_u, n_pts_u, uknots, knotvector_u)
    if knotvector_v is None:
        knotvector_v = sv_knotvector.from_tknots(degree_v, vknots)
    #logger.debug("V: degree %s, N %s, knots %s => knotvector %s", degree_v, n_pts_v, vknots, knotvector_v)

    solver = SvNurbsSurfaceSolver.from_parameters(degree_u, degree_v, n_pts_u, n_pts_v,
                                                  knotvector_u = knotvector_u, knotvector_v = knotvector_v)
    us, vs = np.meshgrid(uknots, vknots, indexing='ij')
    us = us.flatten()
    vs = vs.flatten()
    targets = list(zip(us, vs, np.reshape(points, (n_pts_u*n_pts_v, ndim))))
    solver.add_uv_points(targets)
    problem_type, residue, surface = solver.solve_ex(
                problem_types = SvNurbsSurfaceSolver.PROBLEM_WELLDETERMINED,
                implementation = implementation,
                logger=logger)
    return surface

def unify_surface_curve(surface, direction, curves, accuracy=6):
    """
    Unify degree and knotvector of a NURBS surface (in one direction)
    with a list of NURBS curves.

    Args:
        * surface: SvNurbsSurface
        * direction: SvNurbsSurface.U or SvNurbsSurface.V
        * curves: list of SvNurbsCurve
        * accuracy: precision of knotvectors unification (number of digits after decimal point)

    Returns:
        * Tuple: SvNurbsSurface and a list of SvNurbsCurve.
    """
    second_direction = other_direction(direction)
    curves = [curve.reparametrize(0.0, 1.0) for curve in curves]
    curves = unify_curves(curves, accuracy=accuracy)
    u_min, u_max = surface.get_u_bounds()
    v_min, v_max = surface.get_v_bounds()
    if direction == SurfaceDirection.V:
        surface = surface.reparametrize(0.0, 1.0, v_min, v_max)
    else:
        surface = surface.reparametrize(u_min, u_max, 0.0, 1.0)

    curve_degree = curves[0].get_degree()
    if direction == SurfaceDirection.V:
        surface_degree = surface.get_degree_u()
    else:
        surface_degree = surface.get_degree_v()

    degree = max(curve_degree, surface_degree)
    surface = surface.elevate_degree(second_direction, target=degree)
    curves = [curve.elevate_degree(target=degree) for curve in curves]

    tolerance = 10**(-accuracy)
    dst_knots = sv_knotvector.KnotvectorDict(tolerance)
    if direction == SurfaceDirection.V:
        surface_kv = surface.get_knotvector_u()
    else:
        surface_kv = surface.get_knotvector_v()
    curve_kv = curves[0].get_knotvector()

    curve_ms = sv_knotvector.to_multiplicity(curve_kv, tolerance=None)
    for u, count in curve_ms:
        dst_knots.put(u, count)
    surface_ms = sv_knotvector.to_multiplicity(surface_kv, tolerance=None)
    for u, count in surface_ms:
        dst_knots.put(u, count)
    dst_knots.calc_averages()

    curve_ms = dict(curve_ms)
    surface_ms = dict(surface_ms)

    curve_updates = dst_knots.get_updates(curve_ms.keys())
    updated_ms = []
    for knot_idx, (knot, multiplicity) in enumerate(curve_ms.items()):
        if knot_idx in curve_updates:
            updated_ms.append((curve_updates[knot_idx], multiplicity))
        else:
            updated_ms.append((knot, multiplicity))
    ms = dict(updated_ms)
    updated_kv = sv_knotvector.from_multiplicity(updated_ms)
    curves = [curve.copy(knotvector = updated_kv) for curve in curves]

    curve_insertions = dst_knots.get_insertions(ms)
    for knot, diff in curve_insertions.items():
        if diff > 0:
            curves = [curve.insert_knot(knot, diff) for curve in curves]

    surface_updates = dst_knots.get_updates(surface_ms.keys())
    updated_ms = []
    for knot_idx, (knot, multiplicity) in enumerate(surface_ms.items()):
        if knot_idx in surface_updates:
            updated_ms.append((surface_updates[knot_idx], multiplicity))
        else:
            updated_ms.append((knot, multiplicity))
    ms = dict(updated_ms)
    updated_kv = sv_knotvector.from_multiplicity(updated_ms)
    if direction == SurfaceDirection.V:
        surface = surface.copy(knotvector_u = updated_kv)
    else:
        surface = surface.copy(knotvector_v = updated_kv)

    surface_insertions = dst_knots.get_insertions(ms)
    for knot, diff in surface_insertions.items():
        if diff > 0:
            surface = surface.insert_knot(second_direction, knot, count=diff)

    return surface, curves

class SvNurbsSurfaceAdjustTarget:
    def __init__(self, p_value, curve, tangents=None):
        self.p_value = p_value
        self.curve = curve
        self.tangents = tangents

    def __repr__(self):
        return f"<Target: p_value={self.p_value}, curve={self.curve}, tangents={self.tangents}>"

def _interpolate_tangents(degree, vectors, src_ts, dst_ts, logger):
    #print(f"Interpolate: {len(vectors)}: {len(src_ts)} => {len(dst_ts)}")
    if len(src_ts) == len(dst_ts) and (src_ts == dst_ts).all():
        return vectors
    curve = interpolate_nurbs_curve(degree, vectors, tknots=src_ts, logger=logger)
    return curve.evaluate_array(dst_ts)

def adjust_nurbs_surface_for_curves(surface, direction, targets, preserve_tangents=False, logger=None):
    """
    Adjust NURBS surface in such a way that at specified value of U/V parameter
    it would pass through specified NURBS curve.

    Args:
        * surface: SvNurbsSurface
        * direction: SvNurbsSurface.U or SvNurbsSurface.V
        * targets: list of 2-tuples; in each tuple, first component must be the
            value of U/V surface parameter, and the second component must be a
            SvNurbsCurve to pass through.
        * preserve_tangents: if True, then preserve surface tangents along second parameter.

    Returns:
        * SvNurbsSurface.
    """
    if logger is None:
        logger = get_logger()
    any_tangent_provided = any(p.tangents is not None for p in targets)
    all_tangents_provided = all(p.tangents is not None for p in targets)
    if preserve_tangents and any_tangent_provided:
        raise ArgumentError("preserve_tangents and tangents can not be provided simultaneously")
    if any_tangent_provided and not all_tangents_provided:
        raise ArgumentError("Either all tangents or none of tangents must be provided")
    target_curves = [p.curve for p in targets]
    target_tangents = [p.tangents for p in targets]
    values = np.array([p.p_value for p in targets])
    surface, target_curves = unify_surface_curve(surface, direction, target_curves)
    if any_tangent_provided:
        degree = surface.get_degree_u() if direction == SurfaceDirection.U else surface.get_degree_v()
        target_tangents = [_interpolate_tangents(degree, p.tangents, p.curve.calc_greville_ts(), fixed_curve.calc_greville_ts(), logger) for p, fixed_curve in zip(targets, target_curves)]
        target_tangents = np.transpose(np.array(target_tangents), axes=(1,0,2))
    else:
        n_ctrlpts = len(target_curves[0].get_control_points())
        target_tangents = [None for _ in range(n_ctrlpts)]
    controls = surface.get_control_points()
    weights = surface.get_weights()
    k_u,k_v = weights.shape

    target_controls = [curve.get_homogenous_control_points() for curve in target_curves]

    if direction == SurfaceDirection.V:
        q_curves = [SvNurbsMaths.build_curve(surface.get_nurbs_implementation(),
                        surface.get_degree_v(),
                        surface.get_knotvector_v(),
                        controls[j,:], weights[j,:]) for j in range(k_u)]
    else:
        q_curves = [SvNurbsMaths.build_curve(surface.get_nurbs_implementation(),
                        surface.get_degree_u(),
                        surface.get_knotvector_u(),
                        controls[:,j], weights[:,j]) for j in range(k_v)]
    q_controls = []
    q_weights = []
    for j, (q_curve, q_tangents) in enumerate(zip(q_curves, target_tangents)):
        tgt_controls = np.array([pts[j] for pts in target_controls])
        #print("Target controls:", tgt_controls)
        new_q_curve = adjust_curve_points(q_curve, values, tgt_controls, preserve_tangents = preserve_tangents, tangents = q_tangents, logger = logger)
        q_controls.append(new_q_curve.get_control_points())
        q_weights.append(new_q_curve.get_weights())
    q_controls = np.array(q_controls)
    q_weights = np.array(q_weights)
    if direction == SurfaceDirection.U:
        q_controls = np.transpose(q_controls, axes=(1,0,2))
        q_weights = np.transpose(q_weights, axes=(1,0))
    #print(f"Out: {surface.get_control_points().shape} => {q_controls.shape}")
    return surface.copy(control_points = q_controls, weights = q_weights)

ORDER_UV = 'UV'
ORDER_VU = 'VU'

def adjust_nurbs_surface_for_points_iso(surface, targets, preserve_tangents_u=False, preserve_tangents_v=False, directions_order=ORDER_UV, logger=None):
    curve_targets = []
    for target_u, target_v, target_pt in targets:
        if directions_order == ORDER_UV:
            target_curve = surface.iso_curve(fixed_direction = SurfaceDirection.U, param = target_u)
            target_curve = adjust_curve_points(target_curve, [target_v], [target_pt], preserve_tangents = preserve_tangents_u, logger = logger)
            preserve_tangents_adjust = preserve_tangents_v
            curve_targets.append((target_u, target_curve))
            second_direction = SurfaceDirection.V
        else:
            target_curve = surface.iso_curve(fixed_direction = SurfaceDirection.V, param = target_v)
            target_curve = adjust_curve_points(target_curve, [target_u], [target_pt], preserve_tangents = preserve_tangents_v, logger = logger)
            preserve_tangents_adjust = preserve_tangents_u
            curve_targets.append((target_v, target_curve))
            second_direction = SurfaceDirection.U
    return adjust_nurbs_surface_for_curves(surface, second_direction, curve_targets, preserve_tangents = preserve_tangents_adjust, logger = logger)

def adjust_nurbs_surface_for_points(surface, targets, implementation = SvNurbsMaths.NATIVE, logger = None):
    solver = SvNurbsSurfaceSolver.from_surface(surface)
    solver.add_uv_points(targets)
    problem_type, residue, surface = solver.solve_ex(implementation = implementation, logger = logger)
    return surface

class SnapSurfaceBias(enum.Enum):
    SURFACE1 = enum.auto()
    SURFACE2 = enum.auto()
    MID = enum.auto()

class SnapSurfaceTangents(enum.Enum):
    ANY = enum.auto()
    PRESERVE = enum.auto()
    MATCH = enum.auto()
    SURFACE1 = enum.auto()
    SURFACE2 = enum.auto()

def snap_nurbs_surfaces(surfaces, direction, bias = SnapSurfaceBias.MID, tangents = SnapSurfaceTangents.ANY, cyclic = False, logger = None):
    if logger is None:
        logger = get_logger()

    #second_direction = other_direction(direction)

    def get_range(surface):
        if direction == SurfaceDirection.V:
            return surface.get_u_bounds()
        else:
            return surface.get_v_bounds()

    def get_greville_pts(iso_curve, p):
        qs = iso_curve.calc_greville_ts()
        ps = np.array([p for _ in qs])
        if direction == SurfaceDirection.U:
            return ps, qs
        else:
            return qs, ps
        
    def get_tangents(derivs):
        if direction == SurfaceDirection.U:
            vecs = derivs.du
        else:
            vecs = derivs.dv
        return vecs

    preserve_tangents = tangents == SnapSurfaceTangents.PRESERVE

    class Problem:
        def __init__(self, surface):
            self.surface = surface
            self.param1, self.param2 = get_range(surface)
            self.curve1 = None
            self.curve2 = None
            self.tangents1 = None
            self.tangents2 = None

        def __repr__(self):
            return f"<Problem surface={self.surface}, c1={self.curve1}, c2={self.curve2}>"

        def solve(self):
            targets = []
            if self.curve1 is not None:
                target = SvNurbsSurfaceAdjustTarget(self.param1, self.curve1, self.tangents1)
                targets.append(target)
            if self.curve2 is not None:
                target = SvNurbsSurfaceAdjustTarget(self.param2, self.curve2, self.tangents2)
                targets.append(target)
            logger.debug("Targets: %s", targets)
            return adjust_nurbs_surface_for_curves(self.surface, direction, targets, preserve_tangents = preserve_tangents, logger=logger)

    def setup_problems(problem1, problem2):
        iso1 = problem1.surface.iso_curve(direction, problem1.param2)
        iso2 = problem2.surface.iso_curve(direction, problem2.param1)

        if bias is SnapSurfaceBias.MID:
            target_curve = iso1.lerp_to(iso2, 0.5)
        elif bias is SnapSurfaceBias.SURFACE1:
            target_curve = iso1
        else: # SURFACE2
            target_curve = iso2
        problem1.curve2 = problem2.curve1 = target_curve
        
        us1, vs1 = get_greville_pts(iso1, problem1.param2)
        us2, vs2 = get_greville_pts(iso2, problem2.param1)
        
        derivs1 = problem1.surface.derivatives_data_array(us1, vs1)
        derivs2 = problem2.surface.derivatives_data_array(us2, vs2)
        
        tangents1 = get_tangents(derivs1)
        tangents2 = get_tangents(derivs2)

        if tangents is SnapSurfaceTangents.MATCH:
            target_tangents = (tangents1 + tangents2)*0.5
        elif tangents is SnapSurfaceTangents.SURFACE1:
            target_tangents = tangents1
        elif tangents is SnapSurfaceTangents.SURFACE2:
            target_tangents = tangents2
        elif tangents is SnapSurfaceTangents.PRESERVE:
            target_tangents = None
        else: # ANY
            target_tangents = None

        if target_tangents is not None:
            target_tangents1 = target_tangents
            target_tangents2 = target_tangents
        else:
            target_tangents1 = None
            target_tangents2 = None

        problem1.tangents2 = target_tangents1
        problem2.tangents1 = target_tangents2
    
    unify_directions = {other_direction(direction)}
    logger.debug("Before unify: %s %s", surfaces, unify_directions)
    surfaces = unify_nurbs_surfaces(surfaces, directions=unify_directions)
    logger.debug("After unify: %s", surfaces)

    problems = [Problem(s) for s in surfaces]
    for p1, p2 in zip(problems[:-1], problems[1:]):
        setup_problems(p1, p2)
    if cyclic:
        setup_problems(problems[-1], problems[0])
    logger.debug("Problems: %s", problems)

    return [p.solve() for p in problems]

def nurbs_surface_from_points(points, degree_u, degree_v, num_cpts_u, num_cpts_v, weights = None, normal = None, implementation = SvNurbsMaths.NATIVE, logger = None):
    """
    Generate a NURBS surface which passes either through or near the specified points.
    Parameters:
    * points - points to draw a surface through. np.array of shape (n,3).
    * degree_u, degree_v - degrees of the surface along U and V directions.
    * num_cpts_u, num_cpts_v - number of surface's control points along U and V.

    If total number of control points (num_cpts_u * num_cpts_v) is equal to the
    number of points specified, then the system will be well-determined, so
    this will do interpolation (although depending on location of points, it
    may fail).
    If total number of control points is less than the number of points
    specified, then the system will be overdetermined, so this will do
    approximation.
    If total number of control points is more than the number of points
    specified, then the system will be underdetermined, i.e. there are many
    surfaces passing through these points. In this case, the method will select
    the surface which has all it's control points as close to origin (0.0, 0.0,
    0.0) as possible.

    Return values:
    * SvNurbsSurface instance
    * uv_points - coordinates of points provided in UV space of the surface.
        np.array of shape (n, 3).
    """

    if logger is None:
        logger = get_logger()

    def calc_y_axis(plane, x_axis):
        normal = np.array(plane.normal)
        y_axis = np.cross(x_axis, normal)
        y_axis /= np.linalg.norm(y_axis)
        return y_axis

    if normal is None:
        linear = linear_approximation(points)
        origin = linear.center
        plane = linear.most_similar_plane()
    else:
        origin = center(points)
        plane = PlaneEquation.from_normal_and_point(normal, origin)

    n_pts = len(points)
    if weights is None:
        weights = np.ones((n_pts,))
    if len(weights) != n_pts:
        raise ArgumentError(f"Number of provided points {n_pts} != number of weights {len(weights)}")

    start = points[0]
    start_projection = np.asarray(plane.projection_of_point(start))
    x_axis = start_projection - origin
    x_axis /= np.linalg.norm(x_axis)
    y_axis = calc_y_axis(plane, x_axis)
    distances = np.linalg.norm(points - origin, axis=1)
    max_distance = distances.max()
    
    planar_surface = make_planar_surface(origin,
                    x_axis, y_axis,
                    degree_u, degree_v,
                    num_cpts_u, num_cpts_v,
                    max_distance*2, max_distance*2,
                    implementation = implementation)
    
    us = np_dot(points, x_axis)
    vs = np_dot(points, y_axis)
    us_min, us_max = us.min(), us.max()
    vs_min, vs_max = vs.min(), vs.max()
    us = (us - us_min) / (us_max - us_min)
    vs = (vs - vs_min) / (vs_max - vs_min)

    solver = SvNurbsSurfaceSolver.from_surface(planar_surface)
    goals = list(zip(us, vs, points, weights))
    solver.add_uv_points(goals)
    problem_type, residue, surface = solver.solve_ex(logger = logger, implementation = implementation)
    uv_points = np.zeros((n_pts, 3))
    uv_points[:,0] = us
    uv_points[:,1] = vs
    logger.info("Problem type: %s, residue: %s", problem_type, residue)
    return surface, uv_points

