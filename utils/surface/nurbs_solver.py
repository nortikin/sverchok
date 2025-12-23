# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.core.sv_custom_exceptions import AlgorithmError
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions
    )
from sverchok.utils.sv_logging import get_logger
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs_algorithms import unify_curves
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.curve.nurbs_solver_applications import adjust_curve_points

class SvNurbsSurfaceSolver:
    def __init__(self):
        self.degree_u = None
        self.degree_v = None
        self.knotvector_u = None
        self.knotvector_v = None
        self.src_control_points = None
        self.src_surface = None
        self.src_weights = None
        self.n_cpts_u = None
        self.n_cpts_v = None
        self.goals = []

    PROBLEM_WELLDETERMINED = 'WELLDETERMINED'
    PROBLEM_UNDERDETERMINED = 'UNDERDETERMINED'
    PROBLEM_OVERDETERMINED = 'OVERDETERMINED'
    PROBLEM_ANY = {PROBLEM_WELLDETERMINED, PROBLEM_UNDERDETERMINED, PROBLEM_OVERDETERMINED}

    @staticmethod
    def from_surface(surface):
        solver = SvNurbsSurfaceSolver()
        solver.degree_u = surface.get_degree_u()
        solver.degree_v = surface.get_degree_v()
        solver.knotvector_u = surface.get_knotvector_u()
        solver.knotvector_v = surface.get_knotvector_v()
        solver.src_control_points = surface.get_control_points().copy()
        solver.n_cpts_u, solver.n_cpts_v, _ = solver.src_control_points.shape
        solver.src_weights = surface.get_weights().copy()
        solver.src_surface = surface
        return solver

    @staticmethod
    def from_parameters(degree_u, degree_v, n_cpts_u, n_cpts_v, knotvector_u, knotvector_v):
        solver = SvNurbsSurfaceSolver()
        solver.degree_u = degree_u
        solver.degree_v = degree_v
        solver.knotvector_u = knotvector_u
        solver.knotvector_v = knotvector_v
        solver.n_cpts_u = n_cpts_u
        solver.n_cpts_v = n_cpts_v
        return solver

    def add_goal(self, u, v, point):
        self.goals.append((u, v, point))

    def add_goals(self, goals):
        for goal in goals:
            self.add_goal(*goal)

    def solve(self, logger = None):
        problem_type, residue, surface = self.solve_ex(logger = logger)
        return surface

    def solve_ex(self, problem_types = PROBLEM_ANY, implementation = SvNurbsMaths.NATIVE, logger = None):
        if logger is None:
            logger = get_logger()
        targets = self.goals
        us = np.array([t[0] for t in targets])
        vs = np.array([t[1] for t in targets])
        pts = np.array([t[2] for t in targets])
        basis_u = SvNurbsBasisFunctions(self.knotvector_u)
        basis_v = SvNurbsBasisFunctions(self.knotvector_v)
        if self.src_control_points is None:
            n_cpts_u, n_cpts_v = self.n_cpts_u, self.n_cpts_v
            ndim = 3
            weights = np.ones((n_cpts_u, n_cpts_v))
        else:
            n_cpts_u, n_cpts_v, ndim = self.src_control_points.shape
            weights = self.src_weights
        n_cpts = n_cpts_u * n_cpts_v
        n_points = len(targets)
        n_equations = ndim * n_points
        n_unknowns = ndim * n_cpts
        p_u = self.degree_u
        p_v = self.degree_v

        alphas_u = np.array([basis_u.function(k, p_u)(us) for k in range(n_cpts_u)])
        alphas_v = np.array([basis_v.function(k, p_v)(vs) for k in range(n_cpts_v)])

        A = np.zeros((n_equations, n_unknowns))
        for pt_idx in range(n_points):
            for cpt_u_idx in range(n_cpts_u):
                for cpt_v_idx in range(n_cpts_v):
                    cpt_idx = n_cpts_v * cpt_u_idx + cpt_v_idx
                    alpha_u = alphas_u[cpt_u_idx][pt_idx]
                    alpha_v = alphas_v[cpt_v_idx][pt_idx]
                    weight = weights[cpt_u_idx,cpt_v_idx]
                    alpha = weight * alpha_u * alpha_v
                    for dim_idx in range(ndim):
                        A[ndim*pt_idx + dim_idx, ndim*cpt_idx + dim_idx] = alpha

            denominator = A[ndim*pt_idx, :].sum()
            for dim_idx in range(ndim):
                A[ndim*pt_idx + dim_idx, :] /= denominator

        if self.src_surface is not None:
            src_points = self.src_surface.evaluate_array(us, vs)
        else:
            src_points = None

        B = np.zeros((n_equations, 1))
        for pt_idx, point in enumerate(pts):
            if src_points is not None:
                point = point - src_points[pt_idx]
            B[pt_idx*ndim:pt_idx*ndim+ndim, 0] = point[np.newaxis]

        residue = None
        if n_equations == n_unknowns:
            problem_type = SvNurbsSurfaceSolver.PROBLEM_WELLDETERMINED
            if problem_type not in problem_types:
                raise AlgorithmError("The problem is well-determined")
            try:
                A1 = np.linalg.inv(A)
                X = (A1 @ B).T
            except np.linalg.LinAlgError as e:
                logger.error(f"Matrix: {self.A}")
                raise AlgorithmError(f"Can not solve: #equations = {n_equations}, #unknowns = {n_unknowns}: {e}") from e
        elif n_equations < n_unknowns:
            problem_type = SvNurbsSurfaceSolver.PROBLEM_UNDERDETERMINED
            A1 = np.linalg.pinv(A)
            X = (A1 @ B).T
        else: # n_equations > n_unknowns
            problem_type = SvNurbsSurfaceSolver.PROBLEM_OVERDETERMINED
            if problem_type not in problem_types:
                raise AlgorithmError("The system is overdetermined")
            X, residues, rank, singval = np.linalg.lstsq(self.A, self.B)
            residue = residues.sum()

        d_cpts = X.reshape((n_cpts_u, n_cpts_v, ndim))
        if self.src_control_points is None:
            cpts = d_cpts
        else:
            cpts = self.src_control_points + d_cpts

        surface = SvNurbsMaths.build_surface(implementation=implementation,
                                          degree_u = self.degree_u,
                                          degree_v = self.degree_v,
                                          knotvector_u = self.knotvector_u,
                                          knotvector_v = self.knotvector_v,
                                          control_points = cpts,
                                          weights = self.src_weights)
        return problem_type, residue, surface

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
    second_direction = SvNurbsSurface.U if direction == SvNurbsSurface.V else SvNurbsSurface.V
    curves = [curve.reparametrize(0.0, 1.0) for curve in curves]
    curves = unify_curves(curves, accuracy=accuracy)
    u_min, u_max = surface.get_u_bounds()
    v_min, v_max = surface.get_v_bounds()
    if direction == SvNurbsSurface.V:
        surface = surface.reparametrize(0.0, 1.0, v_min, v_max)
    else:
        surface = surface.reparametrize(u_min, u_max, 0.0, 1.0)

    curve_degree = curves[0].get_degree()
    if direction == SvNurbsSurface.V:
        surface_degree = surface.get_degree_u()
    else:
        surface_degree = surface.get_degree_v()

    degree = max(curve_degree, surface_degree)
    surface = surface.elevate_degree(second_direction, target=degree)
    curves = [curve.elevate_degree(target=degree) for curve in curves]

    tolerance = 10**(-accuracy)
    dst_knots = sv_knotvector.KnotvectorDict(tolerance)
    if direction == SvNurbsSurface.V:
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
    if direction == SvNurbsSurface.V:
        surface = surface.copy(knotvector_u = updated_kv)
    else:
        surface = surface.copy(knotvector_v = updated_kv)

    surface_insertions = dst_knots.get_insertions(ms)
    for knot, diff in surface_insertions.items():
        if diff > 0:
            surface = surface.insert_knot(second_direction, knot, count=diff)

    return surface, curves

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
    target_curves = [p[1] for p in targets]
    values = np.array([p[0] for p in targets])
    surface, target_curves = unify_surface_curve(surface, direction, target_curves)
    controls = surface.get_control_points()
    weights = surface.get_weights()
    k_u,k_v = weights.shape

    target_controls = [curve.get_control_points() for curve in target_curves]

    if direction == SvNurbsSurface.V:
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
    for j, q_curve in enumerate(q_curves):
        controls = np.array([pts[j] for pts in target_controls])
        q_curve = adjust_curve_points(q_curve, values, controls, preserve_tangents = preserve_tangents, logger = logger)
        q_controls.append(q_curve.get_control_points())
        q_weights.append(q_curve.get_weights())
    q_controls = np.array(q_controls)
    q_weights = np.array(q_weights)
    if direction == SvNurbsSurface.U:
        q_controls = np.transpose(q_controls, axes=(1,0,2))
        q_weights = np.transpose(q_weights, axes=(1,0))
    return surface.copy(control_points = q_controls, weights = q_weights)

ORDER_UV = 'UV'
ORDER_VU = 'VU'

def adjust_nurbs_surface_for_points_iso(surface, targets, preserve_tangents_u=False, preserve_tangents_v=False, directions_order=ORDER_UV, logger=None):
    curve_targets = []
    for target_u, target_v, target_pt in targets:
        if directions_order == ORDER_UV:
            target_curve = surface.iso_curve(fixed_direction = SvNurbsSurface.U, param = target_u)
            target_curve = adjust_curve_points(target_curve, [target_v], [target_pt], preserve_tangents = preserve_tangents_u, logger = logger)
            preserve_tangents_adjust = preserve_tangents_v
            curve_targets.append((target_u, target_curve))
            second_direction = SvNurbsSurface.V
        else:
            target_curve = surface.iso_curve(fixed_direction = SvNurbsSurface.V, param = target_v)
            target_curve = adjust_curve_points(target_curve, [target_u], [target_pt], preserve_tangents = preserve_tangents_v, logger = logger)
            preserve_tangents_adjust = preserve_tangents_u
            curve_targets.append((target_v, target_curve))
            second_direction = SvNurbsSurface.U
    return adjust_nurbs_surface_for_curves(surface, second_direction, curve_targets, preserve_tangents = preserve_tangents_adjust, logger = logger)

def adjust_nurbs_surface_for_points(surface, targets, implementation = SvNurbsMaths.NATIVE, logger = None):
    solver = SvNurbsSurfaceSolver.from_surface(surface)
    solver.add_goals(targets)
    problem_type, residue, surface = solver.solve_ex(implementation = implementation, logger = logger)
    return surface

