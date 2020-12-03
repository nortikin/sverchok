# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import random

from mathutils.kdtree import KDTree

from sverchok.utils.surface import SvSurface
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.logging import error

def random_point(min_x, max_x, min_y, max_y):
    x = random.uniform(min_x, max_x)
    y = random.uniform(min_y, max_y)
    return x,y

def _check_min_distance(v_new, vs_old, min_r):
    kdt = KDTree(len(vs_old))
    for i, v in enumerate(vs_old):
        kdt.insert(v, i)
    kdt.balance()
    nearest, idx, dist = kdt.find(v_new)
    if dist is None:
        return True
    return (dist >= min_r)

#     for v_old in vs_old:
#         distance = np.linalg.norm(v_new - v_old)
#         if distance < min_r:
#             return False
#    return True

def _check_min_radius(point, old_points, old_radiuses, min_r):
    if not old_points:
        return True
    old_points = np.array(old_points)
    old_radiuses = np.array(old_radiuses)
    point = np.array(point)
    distances = np.linalg.norm(old_points - point, axis=1)
    ok = (old_radiuses + min_r < distances).all()
    return ok

BATCH_SIZE = 100
MAX_ITERATIONS = 1000

def populate_surface(surface, field, count, threshold,
        proportional=False, field_min=None, field_max=None,
        min_r=0, min_r_field = None,
        random_radius = False,
        avoid_spheres = None,
        seed=0, predicate=None):
    """
    Generate random points on the surface, with distribution controlled (optionally) by scalar field.

    inputs:
    * surface : SvSurface
    * field : SvScalarField. Pass None to use even (uniform) distribution.
    * count: number of points to generate.
    * threshold: do not generate points where value of scalar field is less than this value.
    * proportional: if True, then density of points will be proportional to
      scalar field value. Otherwise, values of the field will be used only to not
      generate points in places where scalar field is less than threshold.
    * field_min: (expected) minimum value of scalar field in the area of the
      surface. Mandatory if `proportional` is set to True.
    * field_max: (expected) maximum value of scalar field in the area of the
      surface. Mandatory if `proportional` is set to True.
    * min_r: minimum distance between generated points. Set to zero to disable this check.
    * seed: random generator seed value.
    * predicate: additional predicate to check if generated point is valid.
      Takes two arguments: point in UV space and the same point in 3D space.
      Optional.

    outputs: tuple:
    * Coordinates of points in surface's UV space
    * Coordinates of points in 3D space.
    """
    if min_r != 0 and min_r_field is not None:
        raise Exception("min_r and min_r_field can not be specified simultaneously")

    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()

    if avoid_spheres is not None:
        old_points = [s[0] for s in avoid_spheres]
        old_radiuses = [s[1] for s in avoid_spheres]
    else:
        old_points = []
        old_radiuses = []

    if seed == 0:
        seed = 12345
    if seed is not None:
        random.seed(seed)
    done = 0
    generated_verts = []
    generated_uv = []
    generated_radiuses = []
    iterations = 0

    while done < count:
        iterations += 1
        if iterations > MAX_ITERATIONS:
            error("Maximum number of iterations (%s) reached, stop.", MAX_ITERATIONS)
            break
        batch_us = []
        batch_vs = []
        left = count - done
        max_size = min(BATCH_SIZE, left)
        for i in range(max_size):
            u = random.uniform(u_min, u_max)
            v = random.uniform(v_min, v_max)
            batch_us.append(u)
            batch_vs.append(v)
        batch_us = np.array(batch_us)
        batch_vs = np.array(batch_vs)
        batch_ws = np.zeros_like(batch_us)
        batch_uvs = np.stack((batch_us, batch_vs, batch_ws)).T

        batch_verts = surface.evaluate_array(batch_us, batch_vs)
        batch_xs = batch_verts[:,0]
        batch_ys = batch_verts[:,1]
        batch_zs = batch_verts[:,2]

        if field is not None:
            values = field.evaluate_grid(batch_xs, batch_ys, batch_zs)

            good_idxs = values >= threshold
            if not proportional:
                candidates = batch_verts[good_idxs]
                candidate_uvs = batch_uvs[good_idxs]
            else:
                candidates = []
                candidate_uvs = []
                for uv, vert, value in zip(batch_uvs[good_idxs].tolist(), batch_verts[good_idxs].tolist(), values[good_idxs].tolist()):
                    probe = random.uniform(field_min, field_max)
                    if probe <= value:
                        candidates.append(vert)
                        candidate_uvs.append(uv)
                candidates = np.array(candidates)
                candidate_uvs = np.array(candidate_uvs)
        else:
            candidates = batch_verts
            candidate_uvs = batch_uvs

        good_radiuses = []
        if len(candidates) > 0:
            if min_r == 0 and min_r_field is None:
                good_verts = candidates.tolist()
                good_uvs = candidate_uvs.tolist()
                good_radiuses = [0 for i in range(len(good_verts))]
            elif min_r_field is not None:
                xs = np.array([p[0] for p in candidates])
                ys = np.array([p[1] for p in candidates])
                zs = np.array([p[2] for p in candidates])
                min_rs = min_r_field.evaluate_grid(xs, ys, zs).tolist()
                good_verts = []
                good_uvs = []
                for candidate_uv, candidate, min_r in zip(candidate_uvs, candidates, min_rs):
                    if random_radius:
                        min_r = random.uniform(0, min_r)
                    if _check_min_radius(candidate, old_points + generated_verts + good_verts, old_radiuses + generated_radiuses + good_radiuses, min_r):
                        good_verts.append(candidate)
                        good_uvs.append(candidate_uv)
                        good_radiuses.append(min_r)
            else: # min_r != 0
                good_verts = []
                good_uvs = []
                for candidate_uv, candidate in zip(candidate_uvs, candidates):
                    distance_ok = _check_min_distance(candidate, generated_verts + good_verts, min_r)
                    if distance_ok:
                        good_verts.append(tuple(candidate))
                        good_uvs.append(tuple(candidate_uv))

            if predicate is not None:
                results = [(uv, vert, radius) for uv, vert, radius in zip(good_uvs, good_verts, good_radiuses) if predicate(uv, vert)]
                good_uvs = [r[0] for r in results]
                good_verts = [r[1] for r in results]
                good_radiuses = [r[2] for r in results]

            generated_verts.extend(good_verts)
            generated_uv.extend(good_uvs)
            generated_radiuses.extend(good_radiuses)
            done += len(good_verts)

    return generated_uv, generated_verts, generated_radiuses

