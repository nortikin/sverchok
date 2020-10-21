# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random
import numpy as np

from mathutils.kdtree import KDTree

from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.logging import error

BATCH_SIZE = 50
MAX_ITERATIONS = 1000

def _check_all(v_new, vs_old, min_r):
    kdt = KDTree(len(vs_old))
    for i, v in enumerate(vs_old):
        kdt.insert(v, i)
    kdt.balance()
    nearest, idx, dist = kdt.find(v_new)
    if dist is None:
        return True
    return (dist >= min_r)

def field_random_probe(field, bbox, count, threshold=0, proportional=False, field_min=None, field_max=None, min_r=0, seed=0):
    """
    Generate random points within bounding box, with distribution controlled (optionally) by a scalar field.

    inputs:
    * field: SvScalarField. Pass None to use uniform distribution.
    * bbox: nested tuple: ((min_x, min_y, min_z), (max_x, max_y, max_z)).
    * count: number of points to generate.
    * threshold: do not generate points where value of scalar field is less than this value.
    * proportional: if True, then density of points will be proportional to
      values of the scalar field. Otherwise, values of the field will be used
      only to not generate points in places where scalar field value is less than
      threshold.
    * field_min: (expected) minimum value of scalar field within the bounding box.
      Mandatory if `proportional` is set to True.
    * field_max: (expected) maximum value of scalar field within the bounding box.
      Mandatory if `proportional` is set to True.
    * min_r: minimum distance between generated points. Set to zero to disable this check.
    * seed: random generator seed value.

    outputs:
        list of vertices.
    """
    if seed == 0:
        seed = 12345
    random.seed(seed)

    b1, b2 = bbox
    x_min, y_min, z_min = b1
    x_max, y_max, z_max = b2

    done = 0
    new_verts = []
    iterations = 0
    while done < count:
        iterations += 1
        if iterations > MAX_ITERATIONS:
            error("Maximum number of iterations (%s) reached, stop.", MAX_ITERATIONS)
            break
        batch_xs = []
        batch_ys = []
        batch_zs = []
        batch = []
        left = count - done
        max_size = min(BATCH_SIZE, left)
        for i in range(max_size):
            x = random.uniform(x_min, x_max)
            y = random.uniform(y_min, y_max)
            z = random.uniform(z_min, z_max)
            batch_xs.append(x)
            batch_ys.append(y)
            batch_zs.append(z)
            batch.append((x, y, z))
        batch_xs = np.array(batch_xs)#[np.newaxis][np.newaxis]
        batch_ys = np.array(batch_ys)#[np.newaxis][np.newaxis]
        batch_zs = np.array(batch_zs)#[np.newaxis][np.newaxis]
        batch = np.array(batch)

        if field is None:
            candidates = batch.tolist()
        else:
            values = field.evaluate_grid(batch_xs, batch_ys, batch_zs)
            good_idxs = values >= threshold
            if not proportional:
                candidates = batch[good_idxs].tolist()
            else:
                candidates = []
                for vert, value in zip(batch[good_idxs].tolist(), values[good_idxs].tolist()):
                    probe = random.uniform(field_min, field_max)
                    if probe <= value:
                        candidates.append(vert)

        if min_r == 0:
            good_verts = candidates
        else:
            good_verts = []
            for candidate in candidates:
                if _check_all(candidate, new_verts + good_verts, min_r):
                    good_verts.append(candidate)

        new_verts.extend(good_verts)
        done += len(good_verts)

    return new_verts

