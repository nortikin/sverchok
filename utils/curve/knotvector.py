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

def normalize(knot_vector):
    """ Normalizes the input knot vector to [0, 1] domain.

    :param knot_vector: knot vector to be normalized
    :type knot_vector: np.array of shape (X,)
    :return: normalized knot vector
    :rtype: np.array
    """
    m = knot_vector.min()
    M = knot_vector.max()
    if m >= M:
        raise Exception("All knot values are equal")
    return (knot_vector - m) / (M - m)

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

