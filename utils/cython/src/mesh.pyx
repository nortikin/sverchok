import numpy as np
import cython
from cython.parallel import prange
from libc.stdint cimport uintptr_t


cimport mesh
from libcpp.vector cimport vector

import bpy
from typing import List, Tuple

def py_test(me: bpy.types.Mesh, vert_positions: List[Tuple[float, float, float]]):
    cdef vector[Vector3D] vec;
    vec.resize(len(vert_positions))

    for i, vert_pos in enumerate(vert_positions):
        vec[i] = Vector3D(vert_pos[0], vert_pos[1], vert_pos[2])

    mesh.test(me.as_pointer(), vec)


@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def create_verts(float[:] v1, float[:] v2, int n):
    n = max(n, 2)
    verts = np.zeros((n, 3), dtype=np.float32)
    cdef float[:,:] verts_view = verts
    cdef int i
    cdef float factor
    cdef float x_dist = v2[0] - v1[0]
    cdef float y_dist = v2[1] - v1[1]
    cdef float z_dist = v2[2] - v1[2]
    for i in prange(n, nogil=True):
        factor = <float>i / (n-1)
        verts_view[i, 0] = v1[0] + x_dist * factor
        verts_view[i, 1] = v1[1] + y_dist * factor
        verts_view[i, 2] = v1[2] + z_dist * factor
    return verts


@cython.boundscheck(False)
@cython.wraparound(False)
def create_edges(int n):
    n = max(n, 0)
    edges = np.zeros((n, 2), dtype=int)
    cdef int[:,:] edges_view = edges
    cdef int i
    for i in prange(n, nogil=True):
        edges_view[i, 0] = i
        edges_view[i, 1] = i+1
    return edges


@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def create_verts2(float[:,:] vs1, float[:,:] vs2, long long[:] ns):
    object_n = max(len(vs1), len(vs2))
    line_starts = np.zeros(object_n, dtype=int)
    cdef int[:] starts_view = line_starts
    cdef int i
    cdef int total = 0
    for i in range(object_n):
        starts_view[i] = total
        ni = min(i, ns.shape[0]-1)
        ns[ni] = max(ns[ni], 2)
        total += ns[ni]

    verts = np.zeros((total, 3), dtype=np.float32)
    cdef float[:,:] verts_view = verts
    cdef int oi, oi1, oi2, oin
    cdef long long n
    cdef float factor
    cdef float v1x, v1y, v1z
    cdef float v2x, v2y, v2z
    cdef float x_dist, y_dist, z_dist
    cdef int si
    for oi in prange(object_n, nogil=True):
        oi1 = min(oi, vs1.shape[0]-1)
        oi2 = min(oi, vs2.shape[0]-1)
        oin = min(oi, ns.shape[0]-1)
        v1x, v1y, v1z = vs1[oi1][0], vs1[oi1][1], vs1[oi1][2]
        v2x, v2y, v2z = vs2[oi2][0], vs2[oi2][1], vs2[oi2][2]
        n = ns[oin]
        x_dist = v2x - v1x
        y_dist = v2y - v1y
        z_dist = v2z - v1z
        si = starts_view[oi]
        for i in prange(n):
            factor = <float>i / (n-1)
            verts_view[si + i, 0] = v1x + x_dist * factor
            verts_view[si + i, 1] = v1y + y_dist * factor
            verts_view[si + i, 2] = v1z + z_dist * factor
    return verts


@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def create_verts3(float[:,:] vs1, float[:,:] vs2, long long[:] ns):
    object_n = max(len(vs1), len(vs2))
    line_starts = np.zeros(object_n, dtype=int)
    cdef int[:] starts_view = line_starts
    cdef int i
    cdef int total = 0
    for i in range(object_n):
        starts_view[i] = total
        ns[i] = max(ns[i], 2)
        total += ns[i]

    verts = np.zeros((total, 3), dtype=np.float32)
    cdef float[:,:] verts_view = verts
    cdef int oi
    cdef long long n
    cdef float factor
    cdef float v1x, v1y, v1z
    cdef float v2x, v2y, v2z
    cdef float x_dist, y_dist, z_dist
    cdef int si
    for oi in prange(object_n, nogil=True):
        v1x, v1y, v1z = vs1[oi][0], vs1[oi][1], vs1[oi][2]
        v2x, v2y, v2z = vs2[oi][0], vs2[oi][1], vs2[oi][2]
        n = ns[oi]
        x_dist = v2x - v1x
        y_dist = v2y - v1y
        z_dist = v2z - v1z
        si = starts_view[oi]
        for i in prange(n):
            factor = <float>i / (n-1)
            verts_view[si + i, 0] = v1x + x_dist * factor
            verts_view[si + i, 1] = v1y + y_dist * factor
            verts_view[si + i, 2] = v1z + z_dist * factor
    return verts


@cython.boundscheck(False)
@cython.wraparound(False)
def create_edges3(long long[:] ns, int object_number):
    cdef int e_num = 0
    line_starts = np.zeros(object_number, dtype=int)
    cdef int[:] starts_view = line_starts
    # start_pints = np.zeros(object_number, dtype=int)
    # cdef int[:] stp_view = start_pints
    cdef Py_ssize_t oi
    for oi in range(object_number):
        starts_view[oi] = e_num
        e_num += max(ns[oi] - 1, 0)
    edges = np.zeros((e_num, 2), dtype=int)
    cdef int[:,:] edges_view = edges
    cdef long n
    cdef Py_ssize_t i
    for oi in prange(object_number, nogil=True):
        n = max(ns[oi]-1, 0)
        for i in range(n):
            edges_view[starts_view[oi]+i, 0] = starts_view[oi] + oi + i
            edges_view[starts_view[oi]+i, 1] = starts_view[oi] + oi + i + 1
    return edges
