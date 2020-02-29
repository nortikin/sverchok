# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
# pylint: disable=C0326

from math import degrees, sqrt
from itertools import zip_longest
from mathutils import Vector
import numpy as np


mathutils_vector_func_dict = {
    "DOT":            (1,  lambda u, v: Vector(u).dot(v),                          ('vv s'),        "Dot product"),
    "DISTANCE":       (5,  lambda u, v: (Vector(u) - Vector(v)).length,            ('vv s'),           "Distance"),
    "ANGLE_DEG":      (12, lambda u, v: degrees(Vector(u).angle(v, 0)),            ('vv s'),      "Angle Degrees"),
    "ANGLE_RAD":      (17, lambda u, v: Vector(u).angle(v, 0),                     ('vv s'),      "Angle Radians"),

    "LEN":            (4,  lambda u: sqrt((u[0]*u[0])+(u[1]*u[1])+(u[2]*u[2])),     ('v s'),             "Length"),
    "CROSS":          (0,  lambda u, v: Vector(u).cross(v)[:],                     ('vv v'),      "Cross product"),
    "ADD":            (2,  lambda u, v: (u[0]+v[0], u[1]+v[1], u[2]+v[2]),         ('vv v'),                "Add"),
    "SUB":            (3,  lambda u, v: (u[0]-v[0], u[1]-v[1], u[2]-v[2]),         ('vv v'),                "Sub"),
    "PROJECT":        (13, lambda u, v: Vector(u).project(v)[:],                   ('vv v'),            "Project"),
    "REFLECT":        (14, lambda u, v: Vector(u).reflect(v)[:],                   ('vv v'),            "Reflect"),
    "COMPONENT-WISE": (19, lambda u, v: (u[0]*v[0], u[1]*v[1], u[2]*v[2]),         ('vv v'), "Component-wise U*V"),

    "SCALAR":         (15, lambda u, s: (u[0]*s, u[1]*s, u[2]*s),                  ('vs v'),    "Multiply Scalar"),
    "1/SCALAR":       (16, lambda u, s: (u[0]/s, u[1]/s, u[2]/s),                  ('vs v'),  "Multiply 1/Scalar"),
    "ROUND":          (18, lambda u, s: Vector(u).to_tuple(abs(int(s))),           ('vs v'),     "Round s digits"),

    "NORMALIZE":      (6,  lambda u: Vector(u).normalized()[:],                     ('v v'),          "Normalize"),
    "NEG":            (7,  lambda u: (-Vector(u))[:],                               ('v v'),             "Negate"),

    "SCALE_XY":       (30, lambda u, s: (u[0]*s, u[1]*s, u[2]),                    ('vs v'),           "Scale XY"),
    "SCALE_XZ":       (31, lambda u, s: (u[0]*s, u[1],   u[2]*s),                  ('vs v'),           "Scale XZ"),
    "SCALE_YZ":       (32, lambda u, s: (u[0],   u[1]*s, u[2]*s),                  ('vs v'),           "Scale YZ"),

    "SCALAR_TO_X":    (40, lambda u, s: (s, u[1], u[2]),                           ('vs v'),        "Scalar to X"),
    "SCALAR_TO_Y":    (41, lambda u, s: (u[0], s, u[2]),                           ('vs v'),        "Scalar to Y"),
    "SCALAR_TO_Z":    (42, lambda u, s: (u[0], u[1], s),                           ('vs v'),        "Scalar to Z"),

    "SWITCH_X":       (50, lambda u, v: (v[0], u[1], u[2]),                        ('vv v'),           "Switch X"),
    "SWITCH_Y":       (51, lambda u, v: (u[0], v[1], u[2]),                        ('vv v'),           "Switch Y"),
    "SWITCH_Z":       (52, lambda u, v: (u[0], u[1], v[2]),                        ('vv v'),           "Switch Z"),

    "SWAP_XY":        (60, lambda u: (u[1], u[0], u[2]),                            ('v v'),            "Swap XY"),
    "SWAP_XZ":        (61, lambda u: (u[2], u[1], u[0]),                            ('v v'),            "Swap XZ"),
    "SWAP_YZ":        (62, lambda u: (u[0], u[2], u[1]),                            ('v v'),            "Swap YZ"),

}


vector_math_ops = [(k, descr, '', ident) for k, (ident, _, _, descr) in sorted(mathutils_vector_func_dict.items(), key=lambda k: k[1][0])]

#The NumPy Implementation

def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    magnitude = np.linalg.norm(vector, axis=1)
    magnitude[magnitude == 0] = 1.0
    return vector / magnitude[:, np.newaxis]

def angle_between(v1, v2):
    """ adapted from David Wolever https://stackoverflow.com/a/13849249 """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    print(v2_u)
    return np.arccos(np.clip(np_dot(v1_u, v2_u), -1.0, 1.0))
# project from https://stackoverflow.com/a/55226228
def reflect(v1, v2):
    mirror = unit_vector(v2)
    dot2 = 2 * np.sum(mirror * v1, axis=1)
    return v1 - (dot2[:, np.newaxis] * mirror)

def scale_two_axis(v1, s, axis1, axis2):
    v1[:,[axis1, axis2]] *= s[:,np.newaxis]
    return v1

def scalar_to_axis(v1, s, axis):
    v1[:, axis] = s
    return v1

def switch_component(v1, v2, component):
    v1[:, component] = v2[:, component]
    return v1

def swap_component(v1, component1, component2):
    v1[:,[component1, component2]] = v1[:,[component2, component1]]
    return v1

def np_dot(u, v):
    return np.sum(u * v, axis=1)

def np_project(u, v):
    return v * (np_dot(u, v)/np_dot(v, v))[:, np.newaxis]

def np_round(v,s):
    factor = np.power(10, s.astype('int'))[:, np.newaxis]
    return np.round(v* factor)/factor


numpy_vector_func_dict = {
    "DOT":            (1,  lambda u, v: np.sum(u * v, axis=1),          ('vv s'),        "Dot product"),
    "DISTANCE":       (5,  lambda u, v: np.linalg.norm(u - v, axis=1),  ('vv s'),           "Distance"),
    "ANGLE DEG":      (12, lambda u, v: np.degrees(angle_between(u, v)),('vv s'),      "Angle Degrees"),
    "ANGLE RAD":      (17, lambda u, v: angle_between(u, v),            ('vv s'),      "Angle Radians"),

    "LEN":            (4,  lambda u: np.linalg.norm(u, axis=1),         ('v s'),              "Length"),
    "CROSS":          (0,  lambda u, v: np.cross(u, v),                 ('vv v'),      "Cross product"),
    "ADD":            (2,  lambda u, v: u+v,                            ('vv v'),                "Add"),
    "SUB":            (3,  lambda u, v: u-v,                            ('vv v'),                "Sub"),
    "PROJECT":        (13, lambda u, v: np_project(u,v),                ('vv v'),            "Project"),
    "REFLECT":        (14, lambda u, v: reflect(u, v),                  ('vv v'),            "Reflect"),
    "COMPONENT-WISE": (19, lambda u, v: u * v,                          ('vv v'), "Component-wise U*V"),

    "SCALAR":         (15, lambda u, s: u*s[:, np.newaxis],             ('vs v'),    "Multiply Scalar"),
    "1/SCALAR":       (16, lambda u, s: u/s[:, np.newaxis],             ('vs v'),  "Multiply 1/Scalar"),
    "ROUND":          (18, lambda u, s: np_round(u,s),                  ('vs v'),     "Round s digits"),

    "NORMALIZE":      (6,  lambda u: unit_vector(u),                    ('v v'),           "Normalize"),
    "NEG":            (7,  lambda u: -u,                                ('v v'),              "Negate"),

    "SCALE_XY":       (30, lambda u, s: scale_two_axis(u, s, 0, 1),     ('vs v'),           "Scale XY"),
    "SCALE_XZ":       (31, lambda u, s: scale_two_axis(u, s, 0, 2),     ('vs v'),           "Scale XZ"),
    "SCALE_YZ":       (32, lambda u, s: scale_two_axis(u, s, 1, 2),     ('vs v'),           "Scale YZ"),

    "SCALAR_TO_X":    (40, lambda u, s: scalar_to_axis(u, s, 0),        ('vs v'),        "Scalar to X"),
    "SCALAR_TO_Y":    (41, lambda u, s: scalar_to_axis(u, s, 1),        ('vs v'),        "Scalar to Y"),
    "SCALAR_TO_Z":    (42, lambda u, s: scalar_to_axis(u, s, 2),        ('vs v'),        "Scalar to Z"),

    "SWITCH_X":       (50, lambda u, v: switch_component(u, v, 0),      ('vv v'),           "Switch X"),
    "SWITCH_Y":       (51, lambda u, v: switch_component(u, v, 1),      ('vv v'),           "Switch Y"),
    "SWITCH_Z":       (52, lambda u, v: switch_component(u, v, 2),      ('vv v'),           "Switch Z"),

    "SWAP_XY":        (60, lambda u: swap_component(u, 0, 1),         ('v v'),           "Swap XY"),
    "SWAP_XZ":        (61, lambda u: swap_component(u, 0, 2),         ('v v'),           "Swap XZ"),
    "SWAP_YZ":        (62, lambda u: swap_component(u, 1, 2),         ('v v'),           "Swap YZ"),

}
