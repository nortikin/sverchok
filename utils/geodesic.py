# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import isnan, pi

from sverchok.utils.geom import Spline, CubicSpline, rotate_vector_around_vector_np
from sverchok.utils.curve.splines import SvSplineCurve
from sverchok.utils.curve.algorithms import SvCurveOnSurface, SvCurveLengthSolver
from sverchok.utils.surface.algorithms import rotate_uv_vectors_on_surface
from sverchok.utils.field.rbf import SvRbfVectorField
from sverchok.utils.field.vector import SvBendAlongSurfaceField, SvVectorFieldComposition, SvPreserveCoordinateField
from sverchok.utils.math import np_multiply_matrices_vectors, np_dot, np_vectors_angle
from sverchok.utils.sv_logging import get_logger
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.interpolate import Rbf

def cubic_spline(surface, uv_pts):
    pts = surface.evaluate_array(uv_pts[:,0], uv_pts[:,1])
    tknots = Spline.create_knots(pts)
    spline = CubicSpline(uv_pts, tknots=tknots)
    return SvSplineCurve(spline)

def geodesic_curve_by_two_points(surface, point1, point2, n_points, iterations, step, tolerance=1e-3, logger=None):
    """
    Generate a geodesic line between two points on surface.

    Args:
        * surface - an instance of SvSurface.
        * point1, point2: np.ndarrays of shape (3,) (third coordinate is ignored) -
          two points in surface's UV space.
        * n_points: number of points on geodesic line to be generated.
        * iterations - maximum number of numeric method iterations.
        * tolerance - requested calculation tolerance; if this precision will be
          achieved earlier than in requested number of iterations, the calculation
          will be stopped.

    Returns:
        np.ndarray of shape (n_points, 3) (third coordinate will be zero) -
        points of calculated geodesic line in surface's UV space.
    """
    if logger is None:
        logger = get_logger()

    def invert_basis_matrices(u_vectors, v_vectors, w_vectors):
        n = len(u_vectors)
        matrices = np.zeros((n,3,3))
        matrices[:,:,0] = u_vectors
        matrices[:,:,1] = v_vectors
        matrices[:,:,2] = w_vectors
        return np.linalg.inv(matrices)

    def project(derivs, uv_pts, vectors):
        u_tangents, v_tangents = derivs.du, derivs.dv
        normals = derivs.normals()[1:-1]
        u_tangents = u_tangents[1:-1]
        v_tangents = v_tangents[1:-1]
        inv_matrices = invert_basis_matrices(u_tangents, v_tangents, normals)
        duv = np_multiply_matrices_vectors(inv_matrices, vectors)
        duv[:,2] = 0
        uv_vectors = np.zeros_like(uv_pts)
        uv_vectors[1:-1] = duv
        return uv_pts + uv_vectors

    def do_iteration(uv_pts, prev_length):
        data = surface.derivatives_data_array(uv_pts[:,0], uv_pts[:,1])
        pts = data.points

        length = np.linalg.norm(pts[1:] - pts[:-1], axis=1).sum()
        if prev_length is not None:
            diff = abs(prev_length - length)
            logger.debug(f"diff: {diff}")
            if diff < tolerance:
                return None

        dvs = pts[1:] - pts[:-1]
        sums = dvs[1:] - dvs[:-1]
        sums *= step
        uv_pts = project(data, uv_pts, sums)
        return length, uv_pts

    def process(pt1, pt2, n_segments, n_iterations):
        uv_pts = np.linspace(pt1, pt2, num=n_segments)
        prev_length = None
        for i in range(n_iterations):
            r = do_iteration(uv_pts, prev_length)
            if r is not None:
                prev_length, uv_pts = r
            else:
                logger.info(f"Stop at {i}'th iteration")
                break
        return uv_pts

    uv_pts = process(point1, point2, n_points, iterations)
    return uv_pts

def geodesic_curve_by_two_points_uv(surface, point1, point2, n_points, n_iterations, step, tolerance=1e-3, logger=None):
    if logger is None:
        logger = get_logger()

    def do_iteration(uv_pts):
        surface_pts = surface.evaluate_array(uv_pts[:,0], uv_pts[:,1]) # (n, 3)
        vectors = surface_pts[1:] - surface_pts[:-1] # (n-1, 3)
        lengths = np.linalg.norm(vectors, axis=1,keepdims=True) # (n-1, 1)
        uv_vectors = uv_pts[1:] - uv_pts[:-1] # (n-1, 2)
        uv_vectors /= np.linalg.norm(uv_vectors, axis=1, keepdims=True)
        duv = lengths[1:]*uv_vectors[1:] - lengths[:-1]*uv_vectors[:-1] # (n-2, 2)
        new_uv_pts = uv_pts.copy()
        new_uv_pts[1:-1] += step * duv
        dlen = lengths.sum()
        return new_uv_pts, dlen

    uv_pts = np.linspace(point1, point2, num=n_points)
    prev_dlen = None
    for i in range(n_iterations):
        uv_pts, dlen = do_iteration(uv_pts)
        if prev_dlen is not None:
            diff = abs(dlen - prev_dlen)
            logger.debug(f"diff: {diff}")
            if diff < tolerance:
                logger.info(f"Stop at {i}'th iteration")
                break
        prev_dlen = dlen
    return uv_pts

class GeodesicSolution:
    """
    Class incapsulating result of calling geodesic_cauchy_problem method.

    orig_points, uv_points and surface_points are lists of np.ndarrays of shape (n,3).
    Shapes of different list items can differ.
    """
    def __init__(self, rhos, orig_points, uv_points, surface_points):
        self.rhos = rhos
        self.orig_points = orig_points
        self.uv_points = uv_points
        self.surface_points = surface_points

    def get(self, i):
        return GeodesicSolution([self.rhos[i]], [self.orig_points[i]], [self.uv_points[i]], [self.surface_points[i]])

    def shift(self, orig_centers):
        return GeodesicSolution(
                self.rhos,
                [o1 + o2 for o1,o2 in zip(self.orig_points, orig_centers)],
                self.uv_points,
                self.surface_points)

    def add(self, sol):
        return GeodesicSolution(
                self.rhos + sol.rhos,
                self.orig_points + sol.orig_points,
                self.uv_points + sol.uv_points,
                self.surface_points + sol.surface_points
            )

    def get_uv_point_by_rho(self, i, rho, method='cubic'):
        if method == 'cubic':
            return self.get_uv_line(i).evaluate_array(rho)
        elif method == 'nearest':
            idx = self.rhos[i].searchsorted(rho, 'right') - 1
            return self.uv_points[i][idx]
        else:
            raise Exception("Unsupported method")

    def get_orig_point_by_rho(self, i, rho, method='cubic'):
        if method == 'cubic':
            return self.get_orig_line(i).evaluate_array(rho)
        elif method == 'nearest':
            idx = self.rhos[i].searchsorted(rho, 'right') - 1
            return self.orig_points[i][idx]
        else:
            raise Exception("Unsupported method")

    def get_uv_points_by_rho(self, rho, method='cubic'):
        points = []
        for i in range(len(self.rhos)):
            pt = self.get_uv_point_by_rho(i, rho, method=method)
            points.append(pt)
        return np.array(points)

    def get_points_count(self):
        return sum(len(line) for line in self.orig_points)

    def get_all_orig_points(self):
        return np.concatenate(self.orig_points)

    def get_all_uv_points(self):
        return np.concatenate(self.uv_points)

    def get_all_surface_points(self):
        return np.concatenate(self.surface_points)

    def get_uv_line(self, i):
        uv_pts = self.uv_points[i]
        spline = CubicSpline(uv_pts, metric='POINTS')
        return SvSplineCurve(spline)

    def get_curve(self, i):
        pts = self.surface_points[i]
        spline = CubicSpline(pts, metric='POINTS')
        return SvSplineCurve(spline)

    def get_orig_line(self, i):
        orig_pts = self.orig_points[i]
        spline = CubicSpline(orig_pts, metric='POINTS')
        return SvSplineCurve(spline)

    def get_tangent_angles(self, surface, i, ts, alpha):
        n = len(ts)
        uv_curve = self.get_uv_line(i)
        curve = self.get_curve(i)
        uv_pts = uv_curve.evaluate_array(ts)
        data = surface.derivatives_data_array(uv_pts[:,0], uv_pts[:,1])
        matrices = np.empty((n, 3, 3))
        matrices[:,:,0] = data.du
        matrices[:,:,1] = data.dv
        matrices[:,:,2] = data.normals()
        tangents_3d = curve.tangent_array(ts)
        tangents_3d = rotate_vector_around_vector_np(tangents_3d, data.normals(), np.array([alpha]))
        inv_matrices = np.linalg.inv(matrices)
        uv_tangents = np_multiply_matrices_vectors(inv_matrices, tangents_3d)
        return np.arctan2(-uv_tangents[:,1], uv_tangents[:,0])

    def rotate_tangents(self, surface, i, ts, alpha):
        n = len(ts)
        uv_curve = self.get_uv_line(i)
        uv_pts = uv_curve.evaluate_array(ts)
        uv_tangents = uv_curve.tangent_array(ts)
        angles = np.full((n,), alpha)
        res = rotate_uv_vectors_on_surface(surface, uv_pts, uv_tangents, angles)
        return res[:,0], -res[:,1]

def geodesic_cauchy_problem(surface, uv_starts,
                            angles = None,
                            u_tangents = None, v_tangents = None,
                            orig_u_tangents = None, orig_v_tangents = None,
                            target_radius=1.0,
                            n_steps=10,
                            closed_u = False, closed_v = False):
    """
    Solve Cauchy problem to generate geodesic line: given start point (in UV space)
    and direction (in UV space), draw a geodesic curve in that direction, of
    requested length.

    This method can generate several geodesic lines in one call.

    The method uses simple Euler method to solve differential equation of geodesic
    lines on surface. So it generates a series of points, which can be afterwards
    interpolated with a cubic spline or another algorithm.

    Initial direction of geodesic lines can be provided in one of two ways: by providing
    angles, or by providing u_tangents and v_tangents.

    Args:
        * surface - an instance of SvSurface
        * uv_starts - np.ndarray of shape (n, 3) (third coordinate is ignored) -
          starting points of geodesic curves, in UV space
        * angles - np.ndarray of shape (n,) - angles, in radians, counted
          counterclockwise from surface's derivative vector in U parameter direction.
          Can be provided instead of u_tangents and v_tangents.
        * u_tangents, v_tangents - np.ndarrays of shape (n,): initial tangent direction
          expressed as coefficients for surface's derivatives in U and V parametric
          directions. Can be provided instead of angles.
        * orig_u_tangents, orig_v_tangents - np.ndarrays of shape (n,): initial tangent
          direction for "original" (undeformed) UV space. If not provided, u_tangents
          and v_tangents will be used.
        * target_radius - requested length of geodesic curves.
        * n_steps - number of steps for calculation; it is also the number of points
          which will be generated.
        * closed_u, closed_v - indicates whether the surface is closed in U and/or V
          direction.

    Returns:
        an instance of GeodesicSolution.
    """
    step = target_radius / n_steps
    u_min, u_max, v_min, v_max = surface.get_domain()

    if u_tangents is None or v_tangents is None and angles is not None:
        u_tangents = np.cos(angles)
        v_tangents = np.sin(angles)
        by_angles = True
    elif u_tangents is not None and v_tangents is not None:
        by_angles = False

    if orig_u_tangents is None:
        orig_u_tangents = u_tangents
    if orig_v_tangents is None:
        orig_v_tangents = v_tangents

    def decompose_array(dus, dvs, normals, pts):
        n = len(pts)
        matrices = np.zeros((n,3,3))
        matrices[:,:,0] = dus
        matrices[:,:,1] = dvs
        matrices[:,:,2] = normals
        inv = np.linalg.inv(matrices)
        res = np_multiply_matrices_vectors(inv, pts)
        return res[:,0], res[:,1]

    def initial_points(data):
        if by_angles:
            dy = np.cross(data.du, data.normals())
            dy /= np.linalg.norm(dy, axis=1, keepdims=True)
            dx = data.du / np.linalg.norm(data.du, axis=1, keepdims=True)
            return step * (dx * u_tangents[np.newaxis].T + dy * v_tangents[np.newaxis].T) + data.points
        else:
            return step * (data.du * u_tangents[np.newaxis].T + data.dv * v_tangents[np.newaxis].T) + data.points

    def do_step(data, us, vs, vectors, radius):
        vectors = radius * vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        circle_du, circle_dv = decompose_array(data.du, data.dv, data.normals(), vectors)
        circle_pts_on_surface = surface.evaluate_array(us + circle_du, vs + circle_dv)
        circle_vectors = circle_pts_on_surface - data.points
        circle_rs_on_surface = np.linalg.norm(circle_vectors, axis=1)
        circle_du /= circle_rs_on_surface
        circle_dv /= circle_rs_on_surface
        new_us = us + radius*circle_du
        new_vs = vs + radius * circle_dv
        if closed_u:
            new_us = np.mod(new_us - u_min, u_max - u_min) + u_min
        if closed_v:
            new_vs = np.mod(new_vs - v_min, v_max - v_min) + v_min
        return new_us, new_vs, data.points

    def do_iteration(us, vs, prev_surface_pts, radius):
        data = surface.derivatives_data_array(us, vs)
        vectors = data.points - prev_surface_pts
        return do_step(data, us, vs, vectors, radius)

    def mk_orig_points():
        rs = np.linspace(0, target_radius, num=n_steps)[np.newaxis].T
        us = orig_u_tangents*rs
        vs = orig_v_tangents*rs
        us = us.flatten()
        vs = vs.flatten()
        pts = np.zeros((len(us), 3))
        pts[:,0] = us
        pts[:,1] = vs
        return rs, pts

    def transpose(pts, n_centers, n_steps):
        pts1 = np.reshape(pts, (n_steps, n_centers, 3))
        pts1 = np.transpose(pts1, (1,0,2))
        return pts1#.reshape((n_centers * n_steps, 3))

    def filter_out_nans(lists):
        has_no_nans = lambda v: not any(isnan(x) for x in v)
        r = [list(filter(has_no_nans, lst)) for lst in lists]
        return list(np.array(r))

    us0, vs0 = uv_starts[:,0], uv_starts[:,1]
    data = surface.derivatives_data_array(us0, vs0)
    pts1 = initial_points(data)
    us, vs, pts = do_step(data, us0, vs0, pts1 - data.points, step)

    all_points = data.points.tolist()
    all_us = us0.tolist()
    all_us.extend(us.tolist())
    all_vs = vs0.tolist()
    all_vs.extend(vs.tolist())
    for i in range(n_steps - 1):
        us, vs, points = do_iteration(us, vs, data.points, step)
        all_points.extend(points.tolist())
        if i != n_steps - 2:
            all_us.extend(us.tolist())
            all_vs.extend(vs.tolist())

    all_us = np.array(all_us)
    all_vs = np.array(all_vs)

    rhos, orig_points = mk_orig_points()
    uvs = np.zeros((len(all_us), 3))
    uvs[:,0] = np.array(all_us)
    uvs[:,1] = np.array(all_vs)

    n_starts = len(uv_starts)
    orig_points = transpose(orig_points, n_starts, n_steps)
    uvs = transpose(uvs, n_starts, n_steps)
    all_points = transpose(all_points, n_starts, n_steps)

    orig_points = filter_out_nans(orig_points)
    uvs = filter_out_nans(uvs)
    all_points = filter_out_nans(all_points)

    return GeodesicSolution([rhos[:,0]], orig_points, uvs, all_points)

def make_rbf(orig_points, tgt_points, **kwargs):
    """
    Build RBF field, which maps orig_points to tgt_points.
    """
    orig_us = orig_points[:,0]
    orig_vs = orig_points[:,1]
    orig_ws = orig_points[:,2]
    if 'function' not in kwargs:
        kwargs['function'] = 'thin_plate'
    if 'smooth' not in kwargs:
        kwargs['smooth'] = 0.0
    if 'epsilon' not in kwargs:
        kwargs['epsilon'] = 1.0
    rbf = Rbf(orig_us, orig_vs, orig_ws, tgt_points,
            mode = 'N-D',
            **kwargs)
    return SvRbfVectorField(rbf, relative=True)

class ExponentialMap:
    def __init__(self, surface, orig_points, uv_points, surface_points):
        self.surface = surface
        self.orig_points = orig_points
        self.uv_points = uv_points
        self.surface_points = surface_points

    def get_uv_field(self, **kwargs):
        return make_rbf(self.orig_points, self.uv_points, **kwargs)

    def get_field(self, **kwargs):
        bend = SvBendAlongSurfaceField(self.surface, axis=2, autoscale=True)
        bend.u_bounds = self.surface.get_u_bounds()
        bend.v_bounds = self.surface.get_v_bounds()
        uv = self.get_uv_field(**kwargs)
        uv = SvPreserveCoordinateField(uv, axis=2)
        return SvVectorFieldComposition(uv.to_absolute(), bend.to_absolute()).to_relative()

def exponential_map(surface, uv_center, radius, radius_steps=10, angle_steps=8, closed_u=False, closed_v=False):
    angles = np.linspace(0, 2*pi, num=angle_steps, endpoint=False)
    uv_centers = np.empty((angle_steps, 3))
    uv_centers[:] = uv_center

    solution = geodesic_cauchy_problem(surface, uv_centers,
                                       angles=angles,
                                       target_radius = radius,
                                       n_steps = radius_steps,
                                       closed_u=closed_u, closed_v=closed_v)

    orig_points = solution.get_all_orig_points()
    uv_points = solution.get_all_uv_points()
    points = solution.get_all_surface_points()

    unq_orig_points, unq_idxs = np.unique(orig_points, axis=0, return_index=True)
    unq_uv_points = uv_points[unq_idxs]
    unq_points = points[unq_idxs]
    return ExponentialMap(surface, unq_orig_points, unq_uv_points, unq_points)

BY_PARAMETER = 'T'
BY_LENGTH = 'L'
def curve_exponential_map(surface, uv_curve, v_radius, u_steps, v_steps, u_mode=BY_PARAMETER, length_resolution=50, closed_u=False, closed_v=False):
    u_min, u_max = uv_curve.get_u_bounds()
    if u_mode == BY_PARAMETER:
        orig_us = center_us
        center_us = np.linspace(u_min, u_max, num=u_steps)
    else:
        curve_3d = SvCurveOnSurface(uv_curve, surface, axis=2)
        calculator = SvCurveLengthSolver(curve_3d)
        calculator.prepare('SPL', length_resolution)
        length = calculator.get_total_length()
        lengths = np.linspace(0, length, num=u_steps)
        orig_us = calculator.solve(lengths)
        center_us = lengths
    orig_centers = np.zeros((u_steps, 3))
    orig_centers[:,0] = center_us

    uv_starts = uv_curve.evaluate_array(orig_us)
    uv_tangents = uv_curve.tangent_array(orig_us)

    uv_tangents_1 = rotate_uv_vectors_on_surface(surface, uv_starts, uv_tangents, np.full((u_steps,), -pi/2))
    uv_tangents_2 = rotate_uv_vectors_on_surface(surface, uv_starts, uv_tangents, np.full((u_steps,), pi/2))

    solution = GeodesicSolution([], [], [], [])
    lines = geodesic_cauchy_problem(surface, uv_starts,
                                    u_tangents = uv_tangents_1[:,0],
                                    v_tangents = uv_tangents_1[:,1],
                                    orig_u_tangents = np.full((u_steps,), 0),
                                    orig_v_tangents = np.full((u_steps,), 1),
                                    target_radius = v_radius, n_steps = v_steps,
                                    closed_u=closed_u, closed_v=closed_v)
    solution = solution.add(lines.shift(orig_centers))
    lines = geodesic_cauchy_problem(surface, uv_starts,
                                    u_tangents = uv_tangents_2[:,0],
                                    v_tangents = uv_tangents_2[:,1],
                                    orig_u_tangents = np.full((u_steps,), 0),
                                    orig_v_tangents = np.full((u_steps,), -1),
                                    target_radius = v_radius, n_steps = v_steps,
                                    closed_u=closed_u, closed_v=closed_v)
    solution = solution.add(lines.shift(orig_centers))

    orig_points = solution.get_all_orig_points()
    uv_points = solution.get_all_uv_points()
    points = solution.get_all_surface_points()

    unq_orig_points, unq_idxs = np.unique(orig_points, axis=0, return_index=True)
    unq_uv_points = uv_points[unq_idxs]
    unq_points = points[unq_idxs]
    return ExponentialMap(surface, unq_orig_points, unq_uv_points, unq_points)


def rectangular_exponential_map(surface, uv_center, u_radius, v_radius, n_v_lines, u_steps, v_steps):
    u_line1 = geodesic_cauchy_problem(surface, np.array([uv_center]), angles=np.array([0]), target_radius=u_radius, n_steps=u_steps)
    u_line2 = geodesic_cauchy_problem(surface, np.array([uv_center]), angles=np.array([pi]), target_radius=u_radius, n_steps=u_steps)

    u_rhos = np.linspace(0, u_radius, num=n_v_lines)
    u_points1 = u_line1.get_uv_point_by_rho(0, u_rhos)
    u_points2 = u_line2.get_uv_point_by_rho(0, u_rhos)
    orig_u_points1 = u_line1.get_orig_point_by_rho(0, u_rhos)
    orig_u_points1 = np.transpose(orig_u_points1[np.newaxis], axes=(1,0,2))
    orig_u_points2 = u_line2.get_orig_point_by_rho(0, u_rhos)
    orig_u_points2 = np.transpose(orig_u_points2[np.newaxis], axes=(1,0,2))

    u_tangents_1, v_tangents_1 = u_line1.rotate_tangents(surface, 0, u_rhos, -pi/2)
    u_tangents_2, v_tangents_2 = u_line1.rotate_tangents(surface, 0, u_rhos, +pi/2)
    u_tangents_3, v_tangents_3 = u_line2.rotate_tangents(surface, 0, u_rhos, -pi/2)
    u_tangents_4, v_tangents_4 = u_line2.rotate_tangents(surface, 0, u_rhos, +pi/2)

    v_lines1 = geodesic_cauchy_problem(surface, u_points1,
                                       u_tangents = u_tangents_1,
                                       v_tangents = v_tangents_1,
                                       target_radius=v_radius, n_steps=v_steps)
    v_lines2 = geodesic_cauchy_problem(surface, u_points1,
                                       u_tangents = u_tangents_2,
                                       v_tangents = v_tangents_2,
                                       target_radius=v_radius, n_steps=v_steps)
    v_lines3 = geodesic_cauchy_problem(surface, u_points2,
                                       u_tangents = u_tangents_3,
                                       v_tangents = v_tangents_3,
                                       target_radius=v_radius, n_steps=v_steps)
    v_lines4 = geodesic_cauchy_problem(surface, u_points2,
                                       u_tangents = u_tangents_4,
                                       v_tangents = v_tangents_4,
                                       target_radius=v_radius, n_steps=v_steps)

    solution = u_line1
    solution = solution.add(u_line2)
    solution = solution.add(v_lines1.shift(orig_u_points1))
    solution = solution.add(v_lines2.shift(orig_u_points1))
    solution = solution.add(v_lines3.shift(orig_u_points2))
    solution = solution.add(v_lines4.shift(orig_u_points2))

    orig_points = solution.get_all_orig_points()
    uv_points = solution.get_all_uv_points()
    points = solution.get_all_surface_points()

    unq_orig_points, unq_idxs = np.unique(orig_points, axis=0, return_index=True)
    unq_uv_points = uv_points[unq_idxs]
    unq_points = points[unq_idxs]
    return ExponentialMap(surface, unq_orig_points, unq_uv_points, unq_points)

