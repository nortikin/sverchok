# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
#
# Adopted from Geomdl library: https://raw.githubusercontent.com/orbingol/NURBS-Python/5.x/geomdl/knotvector.py
#
"""
.. module:: knotvector
    :platform: Unix, Windows
    :synopsis: Provides utility functions related to knot vector generation and validation

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>

"""

from collections import defaultdict
import numpy as np

from sverchok.utils.geom import CubicSpline, LinearSpline

def knotvector_length(degree, num_ctrlpts):
    return degree + num_ctrlpts + 1

def generate(degree, num_ctrlpts, clamped=True):
    """ Generates an equally spaced knot vector.

    It uses the following equality to generate knot vector: :math:`m = n + p + 1`

    where;

    * :math:`p`, degree
    * :math:`n + 1`, number of control points
    * :math:`m + 1`, number of knots

    Keyword Arguments:

        * ``clamped``: Flag to choose from clamped or unclamped knot vector options. *Default: True*

    :param degree: degree
    :type degree: int
    :param num_ctrlpts: number of control points
    :type num_ctrlpts: int
    :return: knot vector
    :rtype: np.array of shape (m+1,)
    """
    if degree == 0 or num_ctrlpts == 0:
        raise ValueError("Input values should be different than zero.")

    if clamped:
        num_repeat = degree
        num_segments = num_ctrlpts - (degree + 1)
        zeros = np.zeros((num_repeat,))
        growing = np.linspace(0.0, 1.0, num = num_segments+2)
        ones = np.ones((num_repeat,))
        return np.concatenate((zeros, growing, ones))
    else:
        num_knots = degree + num_ctrlpts + 1
        return np.linspace(0.0, 1.0, num=num_knots)

def find_span(knot_vector, num_ctrlpts, knot):
    span = 0  # Knot span index starts from zero
    while span < num_ctrlpts and knot_vector[span] <= knot:
        span += 1

    return span - 1

def cubic_resample(tknots, new_count):
    tknots = np.asarray(tknots)
    old_idxs = np.linspace(0.0, 1.0, num=len(tknots))
    new_idxs = np.linspace(0.0, 1.0, num=new_count)
    resampled_tknots = CubicSpline.resample(old_idxs, tknots, new_idxs)
    return resampled_tknots

def linear_resample(tknots, new_count):
    tknots = np.asarray(tknots)
    old_idxs = np.linspace(0.0, 1.0, num=len(tknots))
    new_idxs = np.linspace(0.0, 1.0, num=new_count)
    resampled_tknots = LinearSpline.resample(old_idxs, tknots, new_idxs)
    return resampled_tknots

def add_one_by_resampling(knot_vector, index = None, degree = None):
    n = len(knot_vector)
    if index is None:
        return linear_resample(knot_vector, n+1)
    else:
        if degree is None:
            raise Exception("If index is provided, degree must be provided too")
        kv_before = knot_vector[:index]
        kv_after = knot_vector[index + degree + 1 :]
        kv = linear_resample(knot_vector[index : index + degree + 1], degree+2)
        return np.concatenate([kv_before, kv, kv_after])

def from_tknots(degree, tknots, include_endpoints=False, n_cpts=None):
    n = len(tknots)
    if n_cpts is None:
        result = [tknots[0]] * (degree+1)
        if include_endpoints:
            j_min, j_max = 0, n - degree + 1
        else:
            j_min, j_max = 1, n - degree
        for j in range(j_min, j_max):
            u = tknots[j:j+degree].sum() / degree
            result.append(u)
        result.extend([tknots[-1]] * (degree+1))
        return np.array(result)
    else:
        resampled_tknots = linear_resample(tknots, n_cpts)
        return from_tknots(degree, resampled_tknots, include_endpoints = include_endpoints)

def normalize(knot_vector):
    """ Normalizes the input knot vector to [0, 1] domain.

    :param knot_vector: knot vector to be normalized
    :type knot_vector: np.array of shape (X,)
    :return: normalized knot vector
    :rtype: np.array
    """
    if not isinstance(knot_vector, np.ndarray):
        knot_vector = np.array(knot_vector)
    m = knot_vector.min()
    M = knot_vector.max()
    if m >= M:
        raise Exception("All knot values are equal")
    return (knot_vector - m) / (M - m)

def concatenate_plain(kv1, kv2):
    M = kv1.max()
    return np.concatenate((kv1, kv2 + M))

def average(knotvectors):
    kvs = np.array(knotvectors)
    return kvs.mean(axis=0)

def calc_nodes(degree, n_cpts, knotvector):
    nodes = np.zeros((n_cpts,))
    for i in range(n_cpts):
        nodes[i] = knotvector[i+1:i+degree+1].mean()
    return nodes

def to_multiplicity(knot_vector, tolerance=1e-6):
    count = 0
    prev_u = None
    result = []
    for u in knot_vector:
        if prev_u is None:
            last_match = False
        else:
            if tolerance is None:
                last_match = (u == prev_u)
            else:
                last_match = abs(u - prev_u) < tolerance
            #print(f"Match: {u} - {prev_u} = {abs(u - prev_u)}, => {last_match}")
        if prev_u is None:
            count = 1
        elif last_match:
            count += 1
        else:
            result.append((prev_u, count))
            count = 1
        prev_u = u

    if last_match:
        result.append((u, count))
    else:
        result.append((u, 1))
    return result

def from_multiplicity(pairs):
    result = []
    for u, count in pairs:
        result.extend([u] * count)
    return np.array(result)

def is_clamped(knot_vector, degree, check_start=True, check_end=True, tolerance=1e-6):
    pairs = to_multiplicity(knot_vector, tolerance)
    m1 = pairs[0][1]
    m2 = pairs[-1][1]
    start_ok = not check_start or m1 == degree+1
    end_ok = not check_end or m2 == degree+1
    return start_ok and end_ok

def concatenate(kv1, kv2, join_multiplicity):
    join_knot = kv1.max()
    kv2 = kv2 - kv2.min() + join_knot
    kv1_m = to_multiplicity(kv1)
    kv2_m = to_multiplicity(kv2)
    kv_m = dict(kv1_m[:-1] + kv2_m)
    kv_m[join_knot] = join_multiplicity
    kv_m = [(k, kv_m[k]) for k in sorted(kv_m.keys())]
    return from_multiplicity(kv_m)

def change_degree_pairs(pairs, delta=1):
    return [(u, count+delta) for u, count in pairs]

def elevate_degree(knot_vector, delta=1):
    pairs = to_multiplicity(knot_vector)
    return from_multiplicity(change_degree_pairs(pairs, delta))

def reduce_degree(knot_vector, delta=1):
    pairs = to_multiplicity(knot_vector)
    return from_multiplicity(change_degree_pairs(pairs, -delta))

def insert(knot_vector, u, count=1):
    idx = np.searchsorted(knot_vector, u)
    result = knot_vector.tolist()
    for i in range(count):
        result.insert(idx, u)
        #result = np.insert(result, idx, u)
    return np.asarray(result)

def rescale(knot_vector, new_t_min, new_t_max):
    t_min = knot_vector[0]
    t_max = knot_vector[-1]
    k = (new_t_max - new_t_min) / (t_max - t_min)
    return k * (knot_vector - t_min) + new_t_min

def reverse(knot_vector):
    t_max = knot_vector[-1]
    t_min = knot_vector[0]
    kv = t_max - knot_vector + t_min
    return kv[::-1]

def find_multiplicity(knot_vector, u, tolerance=1e-6):
    pairs = to_multiplicity(knot_vector, tolerance)
    #print(f"kv {knot_vector} => {pairs}")
    for k, count in pairs:
        if tolerance is None:
            if k == u:
                return count
        else:
            if abs(k - u) < tolerance:
                return count
    return 0

def get_internal_knots(knot_vector, output_multiplicity = False, tolerance=1e-6):
    pairs = to_multiplicity(knot_vector, tolerance=tolerance)
    internal = pairs[1:-1]
    if output_multiplicity:
        return internal
    else:
        return [u for u,_ in internal]

def get_min_continuity(knotvector, degree):
    ms = to_multiplicity(knotvector)[1:-1]
    if not ms:
        return degree
    multiplicities = [p[1] for p in ms]
    max_mult = max(multiplicities)
    return degree - max_mult

def difference(src_kv, dst_kv, tolerance=1e-6):
    src_pairs = dict(to_multiplicity(src_kv, tolerance))
    dst_pairs = to_multiplicity(dst_kv, tolerance)
    result = []
    for dst_u, dst_multiplicity in dst_pairs:
        src_multiplicity = src_pairs.get(dst_u, 0)
        diff = dst_multiplicity - src_multiplicity
        if diff > 0:
            result.append((dst_u, diff))
    return result

def equal(kv1, kv2):
    if len(kv1) != len(kv2):
        return False
    return (kv1 == kv2).all()

def merge(kv1, kv2):
    kv2 = rescale(kv2, kv1[0], kv1[-1])

    kv1_pairs = to_multiplicity(kv1)
    kv2_pairs = to_multiplicity(kv2)

    pairs = defaultdict(int)
    for u, multiplicity in kv1_pairs:
        pairs[u] = multiplicity
    for u, multiplicity in kv2_pairs:
        pairs[u] = max(pairs[u], multiplicity)

    result = [(u, pairs[u]) for u in sorted(pairs.keys())]
    return from_multiplicity(result)

def check(degree, knot_vector, num_ctrlpts):
    """ Checks the validity of the input knot vector.

    Please refer to The NURBS Book (2nd Edition), p.50 for details.

    :param degree: degree of the curve or the surface
    :type degree: int
    :param knot_vector: knot vector to be checked
    :type knot_vector: np.array of shape (X,)
    :param num_ctrlpts: number of control points
    :type num_ctrlpts: int
    :return: String with error description, if the knotvector is invalid;
            None, if the knotvector is valid.
    """
    if not isinstance(knot_vector, (list, tuple, np.ndarray)):
        raise TypeError("Knot vector must be a list, tuple, or numpy array")
    if knot_vector is None or len(knot_vector) == 0:
        raise ValueError("Input knot vector cannot be empty")

    # Check the formula; m = p + n + 1
    m = len(knot_vector)
    rhs = degree + num_ctrlpts + 1
    if m != rhs:
        return f"Knot vector has invalid length {m}; for degree {degree} and {num_ctrlpts} control points it must have {rhs} items"

    # Check ascending order
    prev_knot = knot_vector[0]
    for i, knot in enumerate(knot_vector):
        if prev_knot > knot:
            print(knot_vector)
            return f"Knot vector items are not all non-decreasing: u[{i-1}] = {prev_knot} > u[{i}] = {knot}"
        prev_knot = knot

    return None

def check_multiplicity(degree, knot_vector, tolerance=1e-6):
    ms = to_multiplicity(knot_vector, tolerance)
    n = len(ms)
    for idx, (u, count) in enumerate(ms):
        if idx == 0 or idx == n-1:
            if count > degree+1:
                return f"First/Last knot u={u} multiplicity {count} is more than degree+1 {degree+1}"
        else:
            if count > degree:
                return f"Inner knot u={u} multiplicity {count} is more than degree {degree}"
    return None

class KnotvectorDict(object):
    def __init__(self, tolerance):
        self.knots = defaultdict(int)
        self.tolerance = tolerance
        self._averages = []
        self._bucket_ranges = []

    def put(self, knot, multiplicity):
        self.knots[knot] = max(self.knots[knot], multiplicity)

    def calc_averages(self):
        tolerance = self.tolerance
        all_knots = []
        buckets = []
        all_knots = list(sorted(self.knots.keys()))
        current_bucket = [all_knots[0]]
        for knot in all_knots[1:]:
            if knot - current_bucket[0] <= tolerance:
                current_bucket.append(knot)
            else:
                buckets.append(current_bucket)
                current_bucket = [knot]
        buckets.append(current_bucket)
        self._averages = []
        self._bucket_ranges = []
        for bucket in buckets:
            avg = sum(bucket) / len(bucket)
            self._averages.append(avg)
            k1 = bucket[0]
            k2 = bucket[-1]
            self._bucket_ranges.append((k1, k2))

    def get_updates(self, knots):
        result = dict()
        for src_knot_idx, knot in enumerate(knots):
            for avg_idx, (k1, k2) in enumerate(self._bucket_ranges):
                if k1 <= knot <= k2:
                    result[src_knot_idx] = self._averages[avg_idx]
                    break
        return result

    def get_insertions(self, multiplicities):
        existing = defaultdict(int)
        for avg_idx, avg in enumerate(self._averages):
            for knot, multiplicity in multiplicities.items():
                k1, k2 = self._bucket_ranges[avg_idx]
                if k1 <= knot <= k2:
                    existing[avg_idx] += multiplicity
        required = defaultdict(int)
        for orig_knot, orig_multiplicity in self.knots.items():
            for avg_idx, (k1, k2) in enumerate(self._bucket_ranges):
                if k1 <= orig_knot <= k2:
                    required[avg_idx] = max(required[avg_idx], orig_multiplicity)
        result = defaultdict()
        all_knots = set()
        all_knots.update(existing.keys())
        all_knots.update(required.keys())
        for knot_idx in all_knots:
            knot = self._averages[knot_idx]
            diff = required[knot_idx] - existing[knot_idx]
            if diff > 0:
                result[knot] = diff
        return result

    def items(self):
        required = defaultdict(int)
        for orig_knot, orig_multiplicity in self.knots.items():
            for avg_idx, (k1, k2) in enumerate(self._bucket_ranges):
                if k1 <= orig_knot <= k2:
                    avg = self._averages[avg_idx]
                    required[avg] = max(required[avg], orig_multiplicity)
        return required.items()

