# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import numpy.random
from math import ceil, floor, isnan

from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.math import distribute_int
from sverchok.utils.geom import CubicSpline
from sverchok.utils.curve import SvCurveLengthSolver, CurvatureIntegral


class CurvePopulationController(object):
    def set_factors(self, factor_range, factors):
        raise Exception("Not implemented")

    def get_points_count(self, i):
        raise Exception("Not implemented")

class MinMaxPerSegment(CurvePopulationController):
    def __init__(self, min_ppe, max_ppe):
        self.min_ppe = min_ppe
        self.max_ppe = max_ppe

    def set_factors(self, factor_range, factors, include_ends):
        self.factors = factors
        self.factor_range = factor_range
        self.include_ends = include_ends

    def get_points_count(self, i):
        factor = self.factors[i]
        if self.factor_range == 0 or isnan(factor):
            ppe = (self.min_ppe + self.max_ppe)/2
        else:
            ppe_range = self.max_ppe - self.min_ppe
            ppe = self.min_ppe + ppe_range * factor

        if self.include_ends:
            ppe += 2
        return ppe

class TotalCount(CurvePopulationController):
    def __init__(self, total_count):
        self.total_count = total_count

    def set_factors(self, factor_range, factors, include_ends):
        self.include_ends = include_ends
        count = self.total_count
        #if include_ends:
        count -= len(factors) + 1
        self.factors = factors
        self.factor_range = factor_range
        self.points_per_segment = [0 for _ in range(len(factors))]
        total_factor = sum(factors)
        if total_factor == 0:
            weights = [1.0/len(factors) for factor in factors]
        else:
            weights = [factor / total_factor for factor in factors]
        self.points_per_segment = [floor(w * count) for w in weights]
        done = sum(self.points_per_segment)
        while done < count:
            max_factor_index = max(range(len(factors)), key = factors.__getitem__)
            self.points_per_segment[max_factor_index] += 1
            done += 1

    def get_points_count(self, idx):
        ppe = self.points_per_segment[idx]
        if self.include_ends:
            ppe += 2
        return ppe

def populate_t_segment(key_ts, target_count):
    """
    Given key values of T parameter and target number of values,
    return list of T values distributed so that each span
    between key T values includes number of values proportional
    to span's size.
    For example,
    populate_t_segment([0, 1, 3], 7) = [0, 0.5, 1, 1.5, 2, 2.5, 3]
    """
    key_ts = np.asarray(key_ts)
    count_new = target_count - len(key_ts)
    sizes = key_ts[1:] - key_ts[:-1]
    counts = distribute_int(count_new, sizes)
    result = set(key_ts)
    for count, t_max, t_min in zip(counts, key_ts[1:], key_ts[:-1]):
        ts = np.linspace(t_min, t_max, num=count+2)[1:-1]
        result.update(ts)
    return np.asarray(list(sorted(result)))

def populate_curve_old(curve, samples_t, by_length = False, by_curvature = True, population_controller = None, curvature_clip = 100, seed = None):
    if population_controller is None:
        population_controller = MinMaxPerSegment(1, 5)

    t_min, t_max = curve.get_u_bounds()
    t_range = np.linspace(t_min, t_max, num=samples_t)

    if by_length:
        lengths = SvCurveLengthSolver(curve).calc_length_segments(t_range)
        min_length = lengths.min()
        max_length = lengths.max()
        length_range = max_length - min_length
        sv_logger.debug("Lengths range: %s - %s", min_length, max_length)
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
        sv_logger.debug("Curvatures range: %s - %s", min_curvature, max_curvature)
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

    need_random = seed is not None
    population_controller.set_factors(factor_range, factors, include_ends=not need_random)

    if seed == 0:
        seed = 12345
    if need_random:
        numpy.random.seed(seed)
    new_t = [t_min]
    for i in range(samples_t - 1):
        t1 = t_range[i]
        t2 = t_range[i+1]
        ppe = population_controller.get_points_count(i)
        ppe = ceil(ppe)
        if ppe > 0:
            if need_random:
                t_r = numpy.random.uniform(t1, t2, size=ppe).tolist()
                if t_r[0] == new_t[-1]:
                    t_r = t_r[1:]
                if t_r[-1] != t2:
                    t_r.append(t2)
            else:
                space = np.linspace(t1, t2, num=ppe, endpoint=True)
                # sv_logger.debug("Space: %s - %s (%s): %s", t1, t2, ppe, space)
                t_r = space[1:].tolist()
            new_t.extend(t_r)

    new_t = np.array(new_t)
    if need_random:
        new_t = np.sort(new_t)
    return new_t

def populate_curve(curve, n_points, resolution=100, by_length = False, by_curvature = True, random=False, seed=None):
    t_min, t_max = curve.get_u_bounds()
    factors = np.zeros((resolution,))
    ts = np.linspace(t_min, t_max, num=resolution)
    if by_length:
        lengths = SvCurveLengthSolver(curve).calc_length_segments(ts)
        lengths = np.cumsum(np.insert(lengths, 0, 0))
        factors += lengths / lengths[-1]
    if by_curvature:
        integral = CurvatureIntegral(curve, resolution, rescale_curvature = True)
        factors += integral.values
    if not by_length and not by_curvature:
        factors = np.linspace(0.0, 1.0, num=resolution)
    factors /= factors[-1]
    cpts = np.zeros((resolution, 3))
    cpts[:,0] = factors
    cpts[:,1] = ts
    spline = CubicSpline(cpts, metric='X', is_cyclic=False)
    if random:
        if seed is None:
            seed = 12345
        np.random.seed(seed)
        factor_values = np.random.uniform(0.0, 1.0, size=n_points)
        factor_values = np.sort(factor_values)
    else:
        factor_values = np.linspace(0.0, 1.0, num=n_points)
    new_ts = spline.eval(factor_values)[:,1]
    return new_ts

