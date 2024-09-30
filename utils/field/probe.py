# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.kdtree import SvKdTree

BATCH_SIZE = 100
MAX_ITERATIONS = 1000

def _check_min_distance(v_new, vs_old, min_r):
    if not vs_old:
        return True
    kdt = SvKdTree.new(SvKdTree.BLENDER, vs_old)
    nearest, idx, dist = kdt.query(v_new)
    if dist is None:
        return True
    ok = (dist >= min_r)
    #if not ok:
    #    print(f"V {v_new} => {nearest}, {dist} >= {min_r}")
    return ok

def _check_min_radius(point, old_points, old_radiuses, min_r):
    if not old_points:
        return True
    old_points = np.array(old_points)
    old_radiuses = np.array(old_radiuses)
    point = np.array(point)
    distances = np.linalg.norm(old_points - point, axis=1)
    ok = (old_radiuses + min_r < distances).all()
    return ok

def field_random_probe(field, bbox, count,
        threshold=0, proportional=False, field_min=None, field_max=None,
        min_r=0, min_r_field=None,
        random_radius = False,
        seed=0, predicate=None):
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
    * predicate: additional predicate to check if generated point is valid. Optional.

    outputs:
        list of vertices.
    """
    if min_r != 0 and min_r_field is not None:
        raise Exception("min_r and min_r_field can not be specified simultaneously")
    if seed == 0:
        seed = 12345
    if seed is not None:
        np.random.seed(seed)

    b1, b2 = bbox
    x_min, y_min, z_min = b1
    x_max, y_max, z_max = b2

    done = 0
    generated_verts = []
    generated_radiuses = []
    iterations = 0
    while done < count:
        iterations += 1
        if iterations > MAX_ITERATIONS:
            sv_logger.error("Maximum number of iterations (%s) reached, stop.", MAX_ITERATIONS)
            break
        left = count - done
        max_size = min(BATCH_SIZE, left)
        batch = np.random.uniform((x_min,y_min,z_min), (x_max,y_max,z_max), size=(max_size,3))

        if field is None:
            candidates = batch
        else:
            values = field.evaluate_grid(batch[:,0], batch[:,1], batch[:,2])
            good_idxs = values >= threshold
            if not proportional:
                candidates = batch[good_idxs]
            else:
                candidates = []
                probes = np.random.uniform(field_min, field_max, size=len(batch))
                probe_idxs = probes <= values
                good_idxs = np.logical_and(good_idxs, probe_idxs)
                candidates = batch[good_idxs]

        good_radiuses = []
        if min_r == 0 and min_r_field is None:
            good_verts = candidates
            good_radiuses = [0 for i in range(len(good_verts))]
        elif min_r_field is not None:
            min_rs = min_r_field.evaluate_grid(candidates[:,0], candidates[:,1], candidates[:,2])
            if random_radius:
                min_rs = np.random.uniform(
                            np.zeros((len(candidates),)),
                            min_rs
                        )
            good_verts = []
            for candidate, min_r in zip(candidates, min_rs):
                if _check_min_radius(candidate, generated_verts + good_verts, generated_radiuses + good_radiuses, min_r):
                    good_verts.append(candidate)
                    good_radiuses.append(min_r)
        else: # min_r != 0
            good_verts = []
            for candidate in candidates:
                if _check_min_distance(candidate, generated_verts + good_verts, min_r):
                    good_verts.append(candidate)
            good_radiuses = [1 for c in good_verts]

        if predicate is not None:
            pairs = [(vert, r) for vert, r in zip(good_verts, good_radiuses) if predicate(vert)]
            good_verts = [p[0] for p in pairs]
            good_radiuses = [p[1] for p in pairs]

        generated_verts.extend(good_verts)
        generated_radiuses.extend(good_radiuses)
        done += len(good_verts)

    return generated_verts, generated_radiuses

