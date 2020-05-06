# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import numpy.random
from math import ceil, isnan

from sverchok.utils.logging import debug, info, exception
from sverchok.utils.curve import SvCurve, SvCurveLengthSolver

def populate_curve(curve, samples_t, by_length = False, by_curvature = True, min_ppe = 1, max_ppe = 5, curvature_clip = 100, seed = None):
    t_min, t_max = curve.get_u_bounds()
    t_range = np.linspace(t_min, t_max, num=samples_t)

    if by_length:
        lengths = SvCurveLengthSolver(curve).calc_length_segments(t_range)
        min_length = lengths.min()
        max_length = lengths.max()
        length_range = max_length - min_length
        debug("Lengths range: %s - %s", min_length, max_length)
        if length_range == 0:
            lengths = np.zeros(samples_t - 1)
        else:
            lengths = (lengths - min_length) / length_range
    else:
        lengths = np.zeros(samples_t - 1)
        length_range = 0

    if by_curvature:
        curvatures = curve.curvature_array(t_range)
        curvatures_0 = curvatures[:-1]
        curvatures_1 = curvatures[1:]
        curvatures = np.vstack((curvatures_0, curvatures_1)).max(axis=0)
        if curvature_clip:
            curvatures = curvatures.clip(0, curvature_clip)
        min_curvature = curvatures.min()
        max_curvature = curvatures.max()
        curvatures_range = max_curvature - min_curvature
        debug("Curvatures range: %s - %s", min_curvature, max_curvature)
        if curvatures_range == 0:
            curvatures = np.zeros(samples_t - 1)
        else:
            curvatures = (curvatures - min_curvature) / curvatures_range
    else:
        curvatures = np.zeros(samples_t - 1)
        curvatures_range = 0

    factors = curvatures + lengths
    factor_range = curvatures_range + length_range
    if by_length and by_curvature:
        factors = factors / 2.0
        factor_range = factor_range / 2.0
    max_factor = factors.max()
    if max_factor != 0:
        factors = factors / max_factor

    ppe_range = max_ppe - min_ppe

    need_random = seed is not None
    if seed == 0:
        seed = 12345
    if need_random:
        numpy.random.seed(seed)
    new_t = [t_min]
    for i in range(samples_t - 1):
        t1 = t_range[i]
        t2 = t_range[i+1]
        factor = factors[i]
        if factor_range == 0 or isnan(factor):
            ppe = (min_ppe + max_ppe)/2
        else:
            ppe = min_ppe + ppe_range * factor
        ppe = ceil(ppe)
        if ppe > 0:
            if need_random:
                t_r = numpy.random.uniform(t1, t2, size=ppe).tolist()
                if t_r[0] == new_t[-1]:
                    t_r = t_r[1:]
                if t_r[-1] != t2:
                    t_r.append(t2)
            else:
                space = np.linspace(t1, t2, num=ppe+2, endpoint=True)
                #debug("Space: %s - %s (%s): %s", t1, t2, ppe, space)
                t_r = space[1:].tolist()
            new_t.extend(t_r)

    new_t = np.array(new_t)
    if need_random:
        new_t = np.sort(new_t)
    return new_t

