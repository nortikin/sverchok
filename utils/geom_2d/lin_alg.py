# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
This module is for geometry functions handle meshes in 2D space ("XY" surface) mostly.
"""


x, y, z = 0, 1, 2


def almost_equal(v1, v2, accuracy=1e-6):
    """
    Compare floating values
    :param v1: float
    :param v2: float
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: True if values are equal else False
    """
    return abs(v1 - v2) < accuracy


def is_less(v1, v2, epsilon=1e-6):
    """
    Compare floating values
    :param v1: float
    :param v2: float
    :param epsilon: two floats figures are equal if their difference is lower then accuracy value, float
    :return: True if v1 is less then v2
    """
    return v2 - v1 > epsilon


def is_more(v1, v2, epsilon=1e-6):
    """
    Compare floating values
    :param v1: float
    :param v2: float
    :param epsilon: two floats figures are equal if their difference is lower then accuracy value, float
    :return: True if v1 is more then v2
    """
    return v1 - v2 > epsilon


def cross_product(v1, v2):
    """
    Cross product of two any dimension vectors
    :param v1: any massive
    :param v2: any massive
    :return: list
    """
    out = []
    length = len(v1)
    for i in range(length):
        out.append(v1[(i + 1) % length] * v2[(i + 2) % length] - v1[(i + 2) % length] * v2[(i + 1) % length])
    return out


def dot_product(v1, v2):
    """
    Calculate dot product of two vectors
    :param v1: massive of any length
    :param v2: massive of any length
    :return: float
    """
    out = 0
    for co1, co2 in zip(v1, v2):
        out += co1 * co2
    return out


def convert_homogeneous_to_cartesian(v):
    """
    Convert from homogeneous to cartesian system coordinate
    :param v: massive of any length
    :return: list
    """
    w = v[-1]
    out = []
    for s in v[:-1]:
        out.append(s / w)
    return out


def is_ccw(a, b, c):
    """
    Tests whether the turn formed by A, B, and C is counter clockwise
    :param a: 2d point - any massive
    :param b: 2d point - any massive
    :param c: 2d point - any massive
    :return: True if turn is counter clockwise else False
    """
    return (b[x] - a[x]) * (c[y] - a[y]) > (b[y] - a[y]) * (c[x] - a[x])


def is_ccw_polygon(all_verts=None, most_lefts=None, accuracy=1e-6):
    """
    The function get either all points or most left point and its two neighbours of the polygon
    and returns True if order of points are in counterclockwise
    :param all_verts: [(x, y, z) or (x, y), ...]
    :param most_lefts: [(x, y, z) or (x, y), ...]
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: bool
    """
    def is_vertical(points, accuracy=1e-6):
        # is 3 most left points vertical
        if almost_equal(points[0][x], points[1][x], accuracy) and almost_equal(points[0][x], points[2][x], accuracy):
            return True
        else:
            return False
    if all([all_verts, most_lefts]) or not any([all_verts, most_lefts]):
        raise ValueError('The function get either all points or most left point and its two neighbours of the polygon.')
    if all_verts:
        x_min = min(range(len(all_verts)), key=lambda i: all_verts[i][x])
        most_lefts = [all_verts[(x_min - 1) % len(all_verts)], all_verts[x_min],
                      all_verts[(x_min + 1) % len(all_verts)]]
    if is_vertical(most_lefts, accuracy):
        # here is handled corner case when most left points are vertical
        return True if most_lefts[0][y] > most_lefts[1][y] else False
    else:
        return True if is_ccw(*most_lefts) else False


def is_edges_intersect(a1, b1, a2, b2):
    """
    Returns True if line segments a1b1 and a2b2 intersect
    If point of one edge lays on another edge this recognize like intersection
    :param a1: first 2d point of fist segment - any massive
    :param b1: second 2d point of fist segment - any massive
    :param a2: first 2d point of second segment - any massive
    :param b2: second 2d point of second segment - any massive
    :return: True if edges are intersected else False
    """
    return ((is_ccw(a1, b1, a2) != is_ccw(a1, b1, b2) or is_ccw(b1, a1, a2) != is_ccw(b1, a1, b2)) and
            (is_ccw(a2, b2, a1) != is_ccw(a2, b2, b1) or is_ccw(b2, a2, a1) != is_ccw(b2, a2, b1)))


def intersect_edges(a1, a2, b1, b2):
    """
    Find intersection of two lines determined by two coordinates
    :param a1: point 1 of line a - any massive
    :param a2: point 2 of line a - any massive
    :param b1: point 1 of line b - any massive
    :param b2: point 2 of line b - any massive
    :return: returns intersection point (list) if lines are not parallel else returns False
    """
    cross_a = cross_product((a1[x], a1[y], 1), (a2[x], a2[y], 1))
    cross_b = cross_product((b1[x], b1[y], 1), (b2[x], b2[y], 1))
    hom_v = cross_product(cross_a, cross_b)
    if hom_v[2] != 0:
        return convert_homogeneous_to_cartesian(hom_v)
    elif not any(hom_v):
        return False  # two lines ara overlapping
    else:
        return False  # two lines are parallel
