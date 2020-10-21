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

def _check_all(v_new, vs_old, min_r):
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

BATCH_SIZE = 100
MAX_ITERATIONS = 1000

def populate_surface(surface, field, count, threshold, proportional=False, field_min=None, field_max=None, min_r=0, seed=0):
    """
    Generate random points on the surface, with distribution controlled (optionally) by scalar field.

    inputs:
    * surface : SvSurface
    * field : SvScalarField. Pass None to use even (uniform) distribution.
    * count: number of points to generate.
    * proportional: if True, then density of points will be proportional to
      scalar field value. Otherwise, values of the field will be used only to not
      generate points in places where scalar field is less than threshold.
    * field_min: (expected) minimum value of scalar field in the area of the
      surface. Mandatory if `proportional` is set to True.
    * field_max: (expected) maximum value of scalar field in the area of the
      surface. Mandatory if `proportional` is set to True.
    * min_r: minimum distance between generated points. Set to zero to disable this check.
    * seed: random generator seed value.

    outputs: tuple:
    * Coordinates of points in surface's UV space
    * Coordinates of points in 3D space.
    """
    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()

    if seed == 0:
        seed = 12345
    random.seed(seed)
    done = 0
    new_verts = []
    new_uv = []
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

        if len(candidates) > 0:
            good_verts = []
            good_uvs = []
            for candidate_uv, candidate in zip(candidate_uvs, candidates):
                if min_r == 0 or _check_all(candidate, new_verts + good_verts, min_r):
                    good_verts.append(candidate)
                    good_uvs.append(candidate_uv)
                    done += 1
            new_verts.extend(good_verts)
            new_uv.extend(good_uvs)

    return new_uv, new_verts

