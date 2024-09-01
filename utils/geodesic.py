# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import isnan

from sverchok.utils.geom import Spline, CubicSpline, bounding_box
from sverchok.utils.curve.splines import SvSplineCurve
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.field.rbf import SvRbfVectorField
from sverchok.utils.math import np_dot, np_multiply_matrices_vectors
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
    if logger is None:
        logger = get_logger()

    def project(derivs, uv_pts, vectors):
        u_tangents, v_tangents = derivs.unit_tangents()
        u_tangents = u_tangents[1:-1]
        v_tangents = v_tangents[1:-1]
        dus = (vectors * u_tangents).sum(axis=1)
        dvs = (vectors * v_tangents).sum(axis=1)
        dns = np.zeros_like(dus)
        uv_vectors = np.stack((dus, dvs, dns)).T
        uv_vectors = np.insert(uv_vectors, 0, [0,0,0], axis=0)
        uv_vectors = np.insert(uv_vectors, len(uv_vectors), [0,0,0], axis=0)
        return uv_pts + uv_vectors

    def do_iteration(uv_pts, prev_pts):
        data = surface.derivatives_data_array(uv_pts[:,0], uv_pts[:,1])
        pts = data.points

        if prev_pts is not None:
            diff = (prev_pts - pts).max()
            #logger.debug(f"diff: {diff}")
            if diff < tolerance:
                return None

        dvs = pts[1:] - pts[:-1]
        sums = dvs[1:] - dvs[:-1]
        sums *= step
        uv_pts = project(data, uv_pts, sums)
        return pts, uv_pts

    def process(pt1, pt2, n_segments, n_iterations):
        uv_pts = np.linspace(pt1, pt2, num=n_segments)
        prev_pts = None
        for i in range(n_iterations):
            r = do_iteration(uv_pts, prev_pts)
            if r is not None:
                prev_pts, uv_pts = r
            else:
                logger.info(f"Stop at {i}'th iteration")
                break
        return uv_pts

    uv_pts = process(point1, point2, n_points, iterations)
    return uv_pts

def geodesic_cauchy_problem(surface, uv_starts, phis, target_radius, n_steps=10, closed_u = False, closed_v = False):
    step = target_radius / n_steps
    u_min, u_max, v_min, v_max = surface.get_domain()

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
        nonlocal phis
        dy = np.cross(data.du, data.normals())
        dy /= np.linalg.norm(dy, axis=1, keepdims=True)
        dx = data.du / np.linalg.norm(data.du, axis=1, keepdims=True)
        phis = phis[np.newaxis].T
        return step * (dx * np.cos(phis) + dy * np.sin(phis)) + data.points

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
        us = np.cos(phis.T)*rs
        vs = np.sin(phis.T)*rs
        us = us.flatten()
        vs = vs.flatten()
        pts = np.zeros((len(us), 3))
        pts[:,0] = us
        pts[:,1] = vs
        return pts

    def transpose(pts, n_centers, n_steps):
        #pts1 = np.reshape(pts, (n_centers, n_steps, 3))
        pts1 = np.reshape(pts, (n_steps, n_centers, 3))
        pts1 = np.transpose(pts1, (1,0,2))
        return pts1#.reshape((n_centers * n_steps, 3))

    def filter_out_nans(lists):
        has_no_nans = lambda v: not any(isnan(x) for x in v)
        return [list(filter(has_no_nans, lst)) for lst in lists]

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

    orig_points = mk_orig_points()
    uvs = np.zeros((len(all_us), 3))
    uvs[:,0] = np.array(all_us)
    uvs[:,1] = np.array(all_vs)

    n_starts = len(uv_starts)
    orig_points = transpose(orig_points, n_starts, n_steps)
    uvs = transpose(uvs, n_starts, n_steps)
    all_points = transpose(all_points, n_starts, n_steps)

    orig_points = filter_out_nans(orig_points.tolist())
    uvs = filter_out_nans(uvs.tolist())
    all_points = filter_out_nans(all_points.tolist())

    #u_min, u_max, v_min, v_max = surface.get_domain()
    #good_uvs = (uvs[:,:,0] >= u_min) & (uvs[:,:,0] <= u_max) & (uvs[:,:,1] >= v_min) & (uvs[:,:,1] <= v_max)

    #uvs = uvs[good_uvs]
    #orig_points = orig_points[good_uvs]
    #all_points = all_points[good_uvs]

    return orig_points, uvs, all_points

def make_rbf(orig_points, tgt_points):
    orig_us = orig_points[:,0]
    orig_vs = orig_points[:,1]
    orig_ws = orig_points[:,2]
    rbf = Rbf(orig_us, orig_vs, orig_ws, tgt_points,
        function = 'thin_plate',
        smooth = 0.0,
        epsilon = 1.0,
        mode = 'N-D')
    return SvRbfVectorField(rbf, relative=True)

