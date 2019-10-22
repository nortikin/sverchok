# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from mathutils import Vector
from math import acos, pi
import numpy as np
from numpy.linalg import norm as np_norm

def edges_aux(vertices):
    '''create auxiliary edges array '''
    v_len = [len(v) for v in vertices]
    v_len_max = max(v_len)
    np_in = np.arange(v_len_max - 1)
    np_edges = np.array([np_in, np_in + 1]).T

    return [np_edges]

def edges_length(vertices, edges, sum_length=False, out_numpy=False):
    '''calculate edges length '''

    np_verts = np.array(vertices)
    if type(edges[0]) in (list, tuple):
        np_edges = np.array(edges)
    else:
        np_edges = edges[:len(vertices)-1, :]

    vect = np_verts[np_edges[:, 0], :] - np_verts[np_edges[:, 1], :]
    length = np.linalg.norm(vect, axis=1)
    if sum_length:
        length = np.sum(length)[np.newaxis]

    return length if out_numpy else length.tolist()

def edges_direction(vertices, edges, out_numpy=False):
    '''calculate edges direction '''

    np_verts = np.array(vertices)
    if type(edges[0]) in (list, tuple):
        np_edges = np.array(edges)
    else:
        np_edges = edges[:len(vertices)-1, :]

    vect = np_verts[np_edges[:, 1], :] - np_verts[np_edges[:, 0], :]
    dist = np_norm(vect, axis=1)
    vect_norm =vect/dist[:, np.newaxis]
    return vect_norm if out_numpy else vect_norm.tolist()

def adjacent_faces(edges, pols):
    '''calculate number of adjacent faces '''
    e_sorted = [sorted(e) for e in edges]
    ad_faces = [0 for e in edges]
    for pol in pols:
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = sorted(edge)
            if e_s in e_sorted:
                idx = e_sorted.index(e_s)
                ad_faces[idx] += 1
    return ad_faces

def faces_angle(normals, edges, pols):
    ad_faces = adjacent_faces(edges, pols)
    e_sorted = [sorted(e) for e in edges]
    ad_faces = [[] for e in edges]
    for idp, pol in enumerate(pols):
        for edge in zip(pol, pol[1:] + [pol[0]]):
            e_s = sorted(edge)
            if e_s in e_sorted:
                idx = e_sorted.index(e_s)
                ad_faces[idx].append(idp)
    angles = []
    for ed in ad_faces:
        if len(ed) > 1:
            dot_p = Vector(normals[ed[0]]).dot(Vector(normals[ed[1]]))
            ang = acos(dot_p)
        else:
            ang = 2*pi
        angles.append(ang)
    return angles
