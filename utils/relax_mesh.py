# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict
from math import sqrt

import bmesh
import mathutils
from mathutils.bvhtree import BVHTree

from sverchok.data_structure import repeat_last_for_length
from sverchok.utils.sv_mesh_utils import polygons_to_edges
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.geom import center, linear_approximation

NONE = 'NONE'
BVH = 'BVH'
LINEAR = 'LINEAR'
NORMAL = 'NORMAL'

MINIMUM = 'MIN'
MAXIMUM = 'MAX'
AVERAGE = 'MEAN'

def mask_axes(src_vert, dst_vert, axes):
    if axes == {0,1,2}:
        return dst_vert
    result = []
    for axis in range(3):
        if axis in axes:
            result.append(dst_vert[axis])
        else:
            result.append(src_vert[axis])
    return result

def map_mask_axes(src_verts, dst_verts, axes):
    if axes == {0,1,2}:
        return dst_verts
    result = np.asarray(src_verts).copy()
    dst = np.asarray(dst_verts)
    for i in range(3):
        if i in axes:
            result[:,i] = dst[:,i]
    return result.tolist()

def lloyd_relax(vertices, faces, iterations, mask=None, method=NORMAL, skip_boundary=True, use_axes={0,1,2}):
    """
    supported shape preservation methods: NONE, NORMAL, LINEAR, BVH
    """

    def do_iteration(bvh, bm):
        verts_out = []
        face_centers = np.array([face.calc_center_median() for face in bm.faces])
        for bm_vert in bm.verts:
            co = bm_vert.co
            if (skip_boundary and bm_vert.is_boundary) or (mask is not None and not mask[bm_vert.index]):
                new_vert = tuple(co)
            else:    
                normal = bm_vert.normal
                cs = np.array([face_centers[face.index] for face in bm_vert.link_faces])
                
                if method == NONE:
                    new_vert = cs.mean(axis=0)
                elif method == NORMAL:
                    median = mathutils.Vector(cs.mean(axis=0))
                    dv = median - co
                    dv = dv - dv.project(normal)
                    new_vert = co + dv
                elif method == LINEAR:
                    approx = linear_approximation(cs)
                    median = mathutils.Vector(approx.center)
                    plane = approx.most_similar_plane()
                    dist = plane.distance_to_point(bm_vert.co)
                    new_vert = median + plane.normal.normalized() * dist
                elif method == BVH:
                    median = mathutils.Vector(cs.mean(axis=0))
                    new_vert, normal, idx, dist = bvh.find_nearest(median)
                else:
                    raise Exception("Unsupported volume preservation method")
                
                new_vert = tuple(new_vert)
                new_vert = mask_axes(tuple(co), new_vert, use_axes)
                
            verts_out.append(new_vert)

        return verts_out

    if mask is not None:
        mask = repeat_last_for_length(mask, len(vertices))

    bvh = BVHTree.FromPolygons(vertices, faces)
    for i in range(iterations):
        bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
        vertices = do_iteration(bvh, bm)
        bm.free()

    return vertices

def edges_relax(vertices, edges, faces, iterations, k, mask=None, method=NONE, target=AVERAGE, skip_boundary=True, use_axes={0,1,2}):
    """
    supported shape preservation methods: NONE, NORMAL, BVH
    """

    def do_iteration(bvh, bm, verts):
        verts = np.asarray(verts)
        v1s = verts[edges[:,0]]
        v2s = verts[edges[:,1]]
        edge_vecs = v2s - v1s
        edge_lens = np.linalg.norm(edge_vecs, axis=1)

        if target == MINIMUM:
            target_len = np.min(edge_lens)
        elif target == MAXIMUM:
            target_len = np.max(edge_lens)
        elif target == AVERAGE:
            target_len = np.mean(edge_lens)
        else:
            raise Exception("Unsupported target edge length type")

        forces = defaultdict(lambda: np.zeros((3,)))
        counts = defaultdict(int)
        for edge_idx, (v1_idx, v2_idx) in enumerate(edges):
            edge_vec = edge_vecs[edge_idx]
            edge_len = edge_lens[edge_idx]
            d_len = (edge_len - target_len)/2.0
            dv1 =   d_len * edge_vec
            dv2 = - d_len * edge_vec
            forces[v1_idx] += dv1
            forces[v2_idx] += dv2
            counts[v1_idx] += 1
            counts[v2_idx] += 1
        
        target_verts = verts.copy()
        for v_idx in range(len(verts)):
            if skip_boundary and bm.verts[v_idx].is_boundary:
                continue
            if mask is not None and not mask[v_idx]:
                continue
            count = counts[v_idx]
            if count:
                forces[v_idx] /= count
            target_verts[v_idx] += k*forces[v_idx]

        if method == NONE:
            verts_out = target_verts.tolist()
        elif method == NORMAL:
            verts_out = []
            for bm_vert in bm.verts:
                normal = bm_vert.normal
                dv = mathutils.Vector(target_verts[bm_vert.index]) - bm_vert.co
                dv = dv - dv.project(normal)
                new_vert = tuple(bm_vert.co + dv)
                verts_out.append(new_vert)
        elif method == BVH:
            verts_out = []
            for vert in target_verts:
                new_vert, normal, idx, dist = bvh.find_nearest(vert)
                verts_out.append(tuple(new_vert))
        else:
            raise Exception("Unsupported shape preservation method")
        
        return map_mask_axes(verts, verts_out, use_axes)

    if not edges or not edges[0]:
        edges = polygons_to_edges([faces], unique_edges=True)[0]
    edges = np.array(edges)
    if mask is not None:
        mask = repeat_last_for_length(mask, len(vertices))
    bvh = BVHTree.FromPolygons(vertices, faces)
    for i in range(iterations):
        bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
        vertices = do_iteration(bvh, bm, vertices)
        bm.free()

    return vertices

def faces_relax(vertices, edges, faces, iterations, k, mask=None, method=NONE, target=AVERAGE, skip_boundary=True, use_axes={0,1,2}):
    """
    supported shape preservation methods: NONE, NORMAL, BVH
    """

    def do_iteration(bvh, bm):
        areas = np.array([face.calc_area() for face in bm.faces])
        vert_cos = np.array([tuple(vert.co) for vert in bm.verts])
        if target == MINIMUM:
            target_area = areas.min()
        elif target == MAXIMUM:
            target_area = areas.max()
        elif target == AVERAGE:
            target_area = areas.mean()
        else:
            raise Exception("Unsupported target face area type")

        forces = defaultdict(lambda: np.zeros((3,)))
        counts = defaultdict(int)
        for bm_face in bm.faces:
            face_vert_idxs = [vert.index for vert in bm_face.verts]
            face_verts = vert_cos[face_vert_idxs]
            mean = face_verts.mean(axis=0)
            face_verts_0 = face_verts - mean
            src_area = areas[bm_face.index]
            scale = sqrt(target_area / src_area)
            dvs = (scale - 1) * face_verts_0
            for vert_idx, dv in zip(face_vert_idxs, dvs):
                forces[vert_idx] += dv
                counts[vert_idx] += 1
        
        target_verts = vert_cos.copy()
        for bm_vert in bm.verts:
            idx = bm_vert.index
            if skip_boundary and bm_vert.is_boundary:
                continue
            if mask is not None and not mask[idx]:
                continue
            count = counts[idx]
            if count:
                forces[idx] /= count
            force = forces[idx]
            target_verts[idx] += k*force

        if method == NONE:
            verts_out = target_verts.tolist()
        elif method == NORMAL:
            verts_out = []
            for bm_vert in bm.verts:
                idx = bm_vert.index
                dv = mathutils.Vector(target_verts[idx]) - bm_vert.co
                normal = bm_vert.normal
                dv = dv - dv.project(normal)
                new_vert = tuple(bm_vert.co + dv)
                verts_out.append(new_vert)

        elif method == BVH:
            verts_out = []
            for bm_vert in bm.verts:
                new_vert, normal, idx, dist = bvh.find_nearest(bm_vert.co)
                verts_out.append(tuple(new_vert))

        else:
            raise Exception("Unsupported shape preservation method")

        return map_mask_axes(vert_cos, verts_out, use_axes)

    if mask is not None:
        mask = repeat_last_for_length(mask, len(vertices))
    if not edges or not edges[0]:
        edges = polygons_to_edges([faces], unique_edges=True)[0]

    bvh = BVHTree.FromPolygons(vertices, faces)
    for i in range(iterations):
        bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
        vertices = do_iteration(bvh, bm)
        bm.free()

    return vertices

