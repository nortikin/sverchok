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

    # Number of repetitions at the start and end of the array
    num_repeat = degree

    # Number of knots in the middle
    num_segments = num_ctrlpts - (degree + 1)

    if not clamped:
        # No repetitions at the start and end
        num_repeat = 0
        # Should conform the rule: m = n + p + 1
        num_segments = degree + num_ctrlpts - 1

    # First knots
    knot_vector = [0.0 for _ in range(0, num_repeat)]

    # Middle knots
    knot_vector += list(np.linspace(0.0, 1.0, num_segments + 2))

    # Last knots
    knot_vector += [1.0 for _ in range(0, num_repeat)]

    # Return auto-generated knot vector
    return np.array(knot_vector)

def from_tknots(degree, tknots):
    n = len(tknots)
    #m = degree + n + 1
    result = [0] * (degree+1)
    for j in range(1, n - degree):
        u = tknots[j:j+degree].sum() / degree
        result.append(u)
    result.extend([1.0] * (degree+1))
    return np.array(result)

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

def to_multiplicity(knot_vector, tolerance=1e-6):
    count = 0
    prev_u = None
    result = []
    for u in knot_vector:
        if prev_u is None:
            last_match = False
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

def concatenate(kv1, kv2, join_multiplicity):
    join_knot = kv1.max()
    kv2 = kv2 - kv2.min() + join_knot
    kv1_m = to_multiplicity(kv1)
    kv2_m = to_multiplicity(kv2)
    kv_m = dict(kv1_m[:-1] + kv2_m)
    kv_m[join_knot] = join_multiplicity
    kv_m = [(k, kv_m[k]) for k in sorted(kv_m.keys())]
    return from_multiplicity(kv_m)

def elevate_degree_pairs(pairs, delta=1):
    return [(u, count+delta) for u, count in pairs]

def elevate_degree(knot_vector, delta=1):
    pairs = to_multiplicity(knot_vector)
    return from_multiplicity(elevate_degree_pairs(pairs, delta))

def insert(knot_vector, u, count=1):
    idx = np.searchsorted(knot_vector, u)
    result = knot_vector
    for i in range(count):
        result = np.insert(result, idx, u)
    return result

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
        if abs(k - u) < tolerance:
            return count
    return 0

def difference(src_kv, dst_kv):
    src_pairs = dict(to_multiplicity(src_kv))
    dst_pairs = to_multiplicity(dst_kv)
    result = []
    for dst_u, dst_multiplicity in dst_pairs:
        src_multiplicity = src_pairs.get(dst_u, 0)
        diff = dst_multiplicity - src_multiplicity
        if diff > 0:
            result.append((dst_u, diff))
    return result

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
    for knot in knot_vector:
        if prev_knot > knot:
            return "Knot vector items are not all non-decreasing"
        prev_knot = knot

    return None

