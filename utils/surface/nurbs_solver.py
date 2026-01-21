# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import enum
from dataclasses import dataclass
import numpy as np

from sverchok.core.sv_custom_exceptions import AlgorithmError, ArgumentError
from sverchok.utils.nurbs_common import (
        SvNurbsMaths, SvNurbsBasisFunctions
    )
from sverchok.utils.sv_logging import get_logger
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.core import SurfaceSide
from sverchok.utils.surface.algorithms import unify_nurbs_surfaces
from sverchok.utils.curve.nurbs_algorithms import unify_curves
from sverchok.utils.surface.nurbs import SvNurbsSurface, other_direction
from sverchok.utils.curve.nurbs_solver_applications import adjust_curve_points, interpolate_nurbs_curve

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
        degree = surface.get_degree_u() if direction == SvNurbsSurface.U else surface.get_degree_v()
        target_tangents = [_interpolate_tangents(degree, p.tangents, p.curve.calc_greville_ts(), fixed_curve.calc_greville_ts(), logger) for p, fixed_curve in zip(targets, target_curves)]
        target_tangents = np.transpose(np.array(target_tangents), axes=(1,0,2))
    else:
        n_ctrlpts = len(target_curves[0].get_control_points())
        target_tangents = [None for _ in range(n_ctrlpts)]
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
    for j, (q_curve, q_tangents) in enumerate(zip(q_curves, target_tangents)):
        tgt_controls = np.array([pts[j] for pts in target_controls])
        new_q_curve = adjust_curve_points(q_curve, values, tgt_controls, preserve_tangents = preserve_tangents, tangents = q_tangents, logger = logger)
        q_controls.append(new_q_curve.get_control_points())
        q_weights.append(new_q_curve.get_weights())
    q_controls = np.array(q_controls)
    q_weights = np.array(q_weights)
    if direction == SvNurbsSurface.U:
        q_controls = np.transpose(q_controls, axes=(1,0,2))
        q_weights = np.transpose(q_weights, axes=(1,0))
    print(f"Out: {surface.get_control_points().shape} => {q_controls.shape}")
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

@dataclass
class SnapSurfaceInput:
    surface: SvNurbsSurface
    direction : str
    side : SurfaceSide
    invert_tangents : bool

def snap_nurbs_surfaces(input1, input2, bias = SnapSurfaceBias.MID, tangents = SnapSurfaceTangents.ANY, logger = None):
    if logger is None:
        logger = get_logger()

    def get_range(direction, surface):
        if direction == SvNurbsSurface.U:
            return surface.get_u_bounds()
        else:
            return surface.get_v_bounds()

    def get_parameter(direction, side, surface):
        p1, p2 = get_range(direction, surface)
        if side is SurfaceSide.MIN:
            return p1
        else:
            return p2
        
    def get_greville_pts(direction, iso_curve, p):
        qs = iso_curve.calc_greville_ts()
        ps = np.array([p for _ in qs])
        if direction == SvNurbsSurface.U:
            return ps, qs
        else:
            return qs, ps
        
    def get_tangents(direction, derivs):
        if direction == SvNurbsSurface.U:
            vecs = derivs.du
        else:
            vecs = derivs.dv
        return vecs

    unify_directions = set([other_direction(input1.direction), other_direction(input2.direction)])
    logger.debug("Before unify: %s %s %s", input1.surface, input2.surface, unify_directions)
    surface1, surface2 = unify_nurbs_surfaces([input1.surface, input2.surface], directions=unify_directions)
    logger.debug("After unify: %s %s", surface1, surface2)
    surface1 = surface1.reparametrize(0, 1, 0, 1)
    surface2 = surface2.reparametrize(0, 1, 0, 1)
    s1p = get_parameter(input1.direction, input1.side, surface1)
    s2p = get_parameter(input2.direction, input2.side, surface2)
    iso1 = surface1.iso_curve(input1.direction, s1p)
    iso2 = surface2.iso_curve(input2.direction, s2p)

    if bias is SnapSurfaceBias.MID:
        target_curve = iso1.lerp_to(iso2, 0.5)
    elif bias is SnapSurfaceBias.SURFACE1:
        target_curve = iso1
    else: # SURFACE2
        target_curve = iso2
    
    us1, vs1 = get_greville_pts(input1.direction, iso1, s1p)
    us2, vs2 = get_greville_pts(input2.direction, iso2, s2p)
    
    derivs1 = surface1.derivatives_data_array(us1, vs1)
    derivs2 = surface2.derivatives_data_array(us2, vs2)
    
    tangents1 = get_tangents(input1.direction, derivs1)
    tangents2 = get_tangents(input2.direction, derivs2)
    if input1.invert_tangents:
        tangents1 *= -1
    if input2.invert_tangents:
        tangents2 *= -1

    preserve_tangents = False
    if tangents is SnapSurfaceTangents.MATCH:
        target_tangents = (tangents1 + tangents2)*0.5
    elif tangents is SnapSurfaceTangents.SURFACE1:
        target_tangents = tangents1
    elif tangents is SnapSurfaceTangents.SURFACE2:
        target_tangents = tangents2
    elif tangents is SnapSurfaceTangents.PRESERVE:
        target_tangents = None
        preserve_tangents = True
    else: # ANY
        target_tangents = None
        preserve_tangents = False

    if target_tangents is not None:
        target_tangents1 = target_tangents
        target_tangents2 = -target_tangents
    else:
        target_tangents1 = None
        target_tangents2 = None
    
    target1 = SvNurbsSurfaceAdjustTarget(s1p, target_curve, target_tangents1)
    target2 = SvNurbsSurfaceAdjustTarget(s2p, target_curve, target_tangents2)
    
    new_surface1 = adjust_nurbs_surface_for_curves(surface1, input1.direction, [target1], preserve_tangents = preserve_tangents, logger=logger)
    new_surface2 = adjust_nurbs_surface_for_curves(surface2, input2.direction, [target2], preserve_tangents = preserve_tangents, logger=logger)
    
    return new_surface1, new_surface2

