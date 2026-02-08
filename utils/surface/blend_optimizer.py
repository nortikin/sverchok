# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from dataclasses import dataclass
import enum
import numpy as np

from sverchok.core.sv_custom_exceptions import NoConvergenceException, SvUnsupportedOptionException
from sverchok.utils.geom import RangeBoundary
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsDerivativesCalculator
from sverchok.utils.surface.core import SurfaceDirection, SvSurface, other_direction
from sverchok.utils.surface.algorithms import unify_nurbs_surfaces
from sverchok.utils.surface.optimizer import NonLinearConstraint, Optimizer, LinearConstraint, Summand

@dataclass
class BlendSurfaceInput:
    surface : SvSurface
    direction : SurfaceDirection
    boundary : RangeBoundary
    invert : bool

class BlendSurfaceConstraint(enum.Enum):
    G1 = enum.auto()
    NORMALS_MATCH = enum.auto()
    CURVATURE_MATCH = enum.auto()

class BlendSurfaceOptimizer:

    def __init__(self, input1, input2):
        self.surface1 = input1.surface
        self.direction1 = input1.direction
        self.boundary1 = input1.boundary
        self.surface2 = input2.surface
        self.direction2 = input2.direction
        self.boundary2 = input2.boundary
        self.invert1 = input1.invert
        self.invert2 = input2.invert

    def _get_cpts(self,surface, direction, side):
        cpts = surface.get_control_points()
        if direction == SurfaceDirection.V:
            cpts = np.transpose(cpts, (1,0,2))
        if side == RangeBoundary.MIN:
            cpts_last = cpts[0,:]
            cpts_prev = cpts[1,:]
        else:
            cpts_last = cpts[-1,:]
            cpts_prev = cpts[-2,:]
        return cpts_prev, cpts_last

    def _get_range(self,direction, surface):
        if direction == SurfaceDirection.U:
            return surface.get_u_bounds()
        else:
            return surface.get_v_bounds()

    def _get_parameter(self, direction, side, surface):
        p1, p2 = self._get_range(direction, surface)
        if side is RangeBoundary.MIN:
            return p1
        else:
            return p2

    def _init(self, n_along):
        unify_directions = set([other_direction(self.direction1), other_direction(self.direction2)])
        self.surface1, self.surface2 = unify_nurbs_surfaces([self.surface1, self.surface2], directions = unify_directions)
        if self.direction1 == SurfaceDirection.U:
            self.degree_across = self.surface1.get_degree_v()
            self.degree_along = self.surface1.get_degree_u()
            self.kv_across = self.surface1.get_knotvector_v()
        else:
            self.degree_across = self.surface1.get_degree_u()
            self.degree_along = self.surface1.get_degree_v()
            self.kv_across = self.surface1.get_knotvector_u()
        self.kv_along = sv_knotvector.generate(self.degree_along, n_along)

        self.cpts1_prev, self.cpts1_last = self._get_cpts(self.surface1, self.direction1, self.boundary1)
        self.cpts2_prev, self.cpts2_last = self._get_cpts(self.surface2, self.direction2, self.boundary2)

        self.n_along = n_along
        self.n_across = len(self.cpts1_last)

    def _mk_goal(self, lambda_bending = 1.0, lambda_curvature = 0.0, use_cpts = True):
        if not use_cpts:    
            nodes_across = sv_knotvector.calc_nodes(self.degree_across, self.n_across, self.kv_across)
            nodes_along = sv_knotvector.calc_nodes(self.degree_along, self.n_along, self.kv_along)
            calculator_u = SvNurbsDerivativesCalculator.from_knotvector(self.kv_along, self.degree_along, self.n_along, 3, nodes_along)
            calculator_v = SvNurbsDerivativesCalculator.from_knotvector(self.kv_across, self.degree_along, self.n_across, 3, nodes_across)
            
        def goal(p):
            cpts = p.reshape((self.n_along, self.n_across, 3))
                    
            if not use_cpts:            
                dus = np.array([calculator_u.copy(control_points = cpts[:,i]).second_derivatives() for i in range(self.n_across)])
                dus = np.transpose(dus, axes=(1,0,2))
                dvs = np.array([calculator_v.copy(control_points = cpts[i,:]).second_derivatives() for i in range(self.n_along)])
            else:
                I = np.arange(1, self.n_along-1)
                J = np.arange(1, self.n_across-1)
                II, JJ = np.meshgrid(I, J, indexing='ij')
                #I0 = np.arange(self.n_along)
                #II0, JJ0 = np.meshgrid(I0, J, indexing='ij')
                dus = np.zeros((self.n_along, self.n_across, 3))
                dvs = np.zeros((self.n_along, self.n_across, 3))
                dus[II,JJ] = cpts[II,JJ-1] - 2*cpts[II,JJ] + cpts[II,JJ+1]
                dvs[II,JJ] = cpts[II-1,JJ] - 2*cpts[II,JJ] + cpts[II+1,JJ]
                
                #dus[II0,0] = 12*(p[II0,0] - 2*p[II0,1] + 2*p[II0,2]) / (du1**2)
                #dus[II0,-1] = 12*(p[II0,-1] - 2*p[II0,-2] + 2*p[II0,-3]) / (dun**2)
                #dvs[II,0] = p[II-1,0] - 2*p[II,0] + p[II+1,0]
                #dvs[II,-1] = p[II-1,-1] - 2*p[II,-1] + p[II+1,-1]
                #dus[0,JJ] = p[0,JJ-1] - 2*p[0,JJ] + p[0,JJ+1]
                #dus[-1,JJ] = p[-1,JJ-1] - 2*p[-1,JJ] + p[-1,JJ+1]
            
            curvature = 0.0
            if lambda_curvature > 0.0:
                crosses = np.cross(dus, dvs)
                curvature = (crosses * crosses).sum()
            bending = 0.0
            if lambda_bending > 0.0:
                bending = (dus * dus).sum() + (dvs * dvs).sum()
                
            return lambda_curvature * curvature + lambda_bending * bending

        return goal

    def solve(self,
              implementation = SvNurbsMaths.NATIVE,
              constraint = BlendSurfaceConstraint.G1,
              lambda_bending = 1.0,
              lambda_curvature = 0.0,
              use_cpts = True,
              tolerance = 1e-5,
              **kwargs):
        if constraint is BlendSurfaceConstraint.G1:
            opt = self._setup_g1(**kwargs)
        elif constraint is BlendSurfaceConstraint.NORMALS_MATCH:
            opt = self._setup_normals_match(**kwargs)
        elif constraint is BlendSurfaceConstraint.CURVATURE_MATCH:
            opt = self._setup_curvature_match(**kwargs)
        else:
            raise SvUnsupportedOptionException("Unsupported constraint: " + constraint)

        goal = self._mk_goal(lambda_curvature = lambda_curvature, lambda_bending = lambda_bending,
                use_cpts = use_cpts)
        
        opt.set_goal(goal)

        solution = opt.minimize(tol = tolerance)
        if not solution.success:
            raise NoConvergenceException(solution.message)
        #print(solution.parameters)
        cpts = solution.control_points.reshape((self.n_along, self.n_across, 3))
        
        surface = SvNurbsMaths.build_surface(implementation,
                    degree_u = self.degree_across, degree_v = self.degree_along,
                    knotvector_u = sv_knotvector.generate(self.degree_across, self.n_along),
                    knotvector_v = self.kv_across,
                    control_points = cpts)
        return surface

    def _setup_g1(self,
              min_alpha = 0.1):
        self._init(n_along = 4)

        opt = Optimizer(self.n_across*self.n_along)
        for i in range(self.n_across):
            gamma0 = self.cpts1_last[i]
            gamma1 = self.cpts1_last[i] - self.cpts1_prev[i]
            if self.invert1:
                gamma1 *= -1
            opt.set_constraint(i, gamma0)
            opt.set_constraint(self.n_across + i, gamma0, [gamma1], bounds = [(min_alpha,1)])
            gamma0 = self.cpts2_last[i]
            gamma1 = self.cpts2_last[i] - self.cpts2_prev[i]
            if self.invert2:
                gamma1 *= -1
            opt.set_constraint(2*self.n_across + i, gamma0, [gamma1], bounds = [(min_alpha,1)])
            opt.set_constraint(3*self.n_across + i, gamma0)
        
        return opt

    def _setup_normals_match(self,
              min_alpha = 0.01,
              min_beta = 0.01, max_beta = None):
        self._init(n_along = 6)

        s1p = self._get_parameter(self.direction1, self.boundary1, self.surface1)
        s2p = self._get_parameter(self.direction2, self.boundary2, self.surface2)
        
        nodes_across = sv_knotvector.calc_nodes(self.degree_across, self.n_across, self.kv_across)
        iso_1_along = [self.surface1.iso_curve(other_direction(self.direction1), t) for t in nodes_across]
        iso_2_along = [self.surface2.iso_curve(other_direction(self.direction2), t) for t in nodes_across]
        gamma2_1_along = [c.second_derivative(s1p) for c in iso_1_along]
        gamma2_2_along = [c.second_derivative(s2p) for c in iso_2_along]
        
        opt = Optimizer(self.n_across*self.n_along)
        for i in range(self.n_across):
            opt.set_constraint(i, self.cpts1_last[i])
            
            gamma0 = self.cpts1_last[i]
            gamma1 = (self.cpts1_last[i] - self.cpts1_prev[i]) * 3
            gamma2 = gamma2_1_along[i]
            if self.invert1:
                gamma1 *= -1
                gamma2 *= -1
            #print(f"S1: Gamma0 {gamma0}, Gamma1 {gamma1}, Gamma2 {gamma2}")
            alpha1 = opt.set_constraint(1*self.n_across + i, gamma0, [gamma1/9], bounds = [(min_alpha,9)])[0]
            beta1 = opt.allocate_parameters()[0]
            opt.constraints[2*self.n_across + i] = LinearConstraint(gamma0, [
                                                    Summand(alpha1, gamma1/3.0),
                                                    Summand(beta1, gamma2/27.0)
                                                ])
            opt.bounds[beta1] = (min_beta, max_beta)
            
            gamma0 = self.cpts2_last[i]
            gamma1 = (self.cpts2_last[i] - self.cpts2_prev[i]) * 3 # / 9
            gamma2 = gamma2_2_along[i]
            if self.invert2:
                gamma1 *= -1
                gamma2 *= -1
            #print(f"S2: Gamma0 {gamma0}, Gamma1 {gamma1}, Gamma2 {gamma2}")
            alpha2 = opt.set_constraint(4*self.n_across + i, gamma0, [gamma1/9], bounds = [(min_alpha,9)])[0]
            beta2 = opt.allocate_parameters()[0]
            opt.constraints[3*self.n_across + i] = LinearConstraint(gamma0, [
                                                    Summand(alpha2, gamma1/3.0),
                                                    Summand(beta2, gamma2/27.0)
                                                ])
            opt.bounds[beta2] = (min_beta, max_beta)
            opt.set_constraint(5*self.n_across + i, gamma0)
                
        return opt

    def _setup_curvature_match(self, min_alpha = 0.01):
        self._init(n_along = 6)

        s1p = self._get_parameter(self.direction1, self.boundary1, self.surface1)
        s2p = self._get_parameter(self.direction2, self.boundary2, self.surface2)
        
        nodes_across = sv_knotvector.calc_nodes(self.degree_across, self.n_across, self.kv_across)
        iso_1_along = [self.surface1.iso_curve(other_direction(self.direction1), t) for t in nodes_across]
        iso_2_along = [self.surface2.iso_curve(other_direction(self.direction2), t) for t in nodes_across]

        def mk_curvature_constraint(orig_point, orig_tangent, normal, kappa0):
            def function(params):
                alpha = params[0]
                beta = params[1]
                gamma1 = alpha * orig_tangent * 9
                d1 = kappa0 * (gamma1 * gamma1).sum() / 27
                curvature_pt_base = orig_point + d1*normal
                result = curvature_pt_base + beta * orig_tangent
                #print(f"G0 {orig_point}, G1 {gamma1}, K0 {kappa0}, normal {normal}, d1 {d1}, pt_base {curvature_pt_base}, alpha {alpha}, beta {beta} => {result}")
                return result
            return function

        opt = Optimizer(self.n_across*self.n_along)
        for i in range(self.n_across):
            gamma0 = self.cpts1_last[i]
            opt.set_constraint(i, gamma0)

            gamma1 = iso_1_along[i].tangent(s1p)
            if self.invert1:
                gamma1 *= -1
            alpha1 = opt.set_constraint(1*self.n_across + i, gamma0, [gamma1], bounds = [(min_alpha,9)])[0]

            kappa0 = iso_1_along[i].curvature(s1p)
            normal1 = iso_1_along[i].main_normal(s1p)

            beta1 = opt.allocate_parameters()[0]
            opt.constraints[2*self.n_across + i] = NonLinearConstraint(
                                mk_curvature_constraint(gamma0, gamma1, normal1, kappa0),
                                [alpha1, beta1])
            opt.bounds[beta1] = (min_alpha, None)


            gamma0 = self.cpts2_last[i]
            gamma1 = -iso_2_along[i].tangent(s2p)
            if self.invert2:
                gamma1 *= -1

            alpha2 = opt.set_constraint(4*self.n_across + i, gamma0, [gamma1], bounds = [(min_alpha,9)])[0]

            kappa0 = iso_2_along[i].curvature(s2p)
            normal2 = iso_2_along[i].main_normal(s2p)
            beta2 = opt.allocate_parameters()[0]
            opt.constraints[3*self.n_across + i] = NonLinearConstraint(
                                mk_curvature_constraint(gamma0, gamma1, normal2, kappa0),
                                [alpha2, beta2])
            opt.bounds[beta2] = (min_alpha, None)

            opt.set_constraint(5*self.n_across + i, gamma0)
        return opt

