# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from numpy.random import random
from sverchok.data_structure import numpy_full_list, repeat_last_for_length
from sverchok.utils.modules.polygon_utils import np_faces_normals, np_faces_perimeters as face_perimeter



def np_pols(pols):
    if isinstance(pols, np.ndarray):
        flat_pols = pols.flat
        p_lens = np.full(pols.shape[0], pols.shape[1])
        pol_end = np.cumsum(p_lens)
    else:
        p_lens = np.array(list(map(len, pols)))
        flat_pols = np.array([c for p in pols for c in p])
        pol_end = np.cumsum(p_lens)
    return flat_pols, p_lens, pol_end

def normal_offset(v_pols, normal_displace, random_normal):

    if normal_displace == 0:
        return face_perimeter(v_pols)[:, np.newaxis] * np_faces_normals(v_pols) * (2*random_normal-random_normal) * random(len(v_pols))[:, np.newaxis]

    if random_normal == 0:
        return face_perimeter(v_pols)[:, np.newaxis] * np_faces_normals(v_pols) * (normal_displace)

    return face_perimeter(v_pols)[:, np.newaxis] * np_faces_normals(v_pols) * (normal_displace + (2*random_normal-random_normal) * random(len(v_pols))[:, np.newaxis])

def regular_random_centers(np_faces, v_pols, randomf, vert_data):

    centers = np.sum(v_pols * randomf[:, :, np.newaxis], axis=1) / np.sum(randomf, axis=1)[:, np.newaxis]
    if vert_data:
        center_vert_data = dict()
        for key in vert_data:
            data = vert_data[key]
            np_data = data if isinstance(data, np.ndarray) else np.array(data)
            if len(np_data.shape)>1:
                center_vert_data[key] = np.sum(np_data[np_faces] * randomf[:, :, np.newaxis], axis=1) / np.sum(randomf, axis=1)[:, np.newaxis]
            else:
                center_vert_data[key] = np.sum(np_data[np_faces] * randomf, axis=1) / np.sum(randomf, axis=1)
    else:
        center_vert_data = []
    return centers, center_vert_data
def regular_mid_centers(np_faces, v_pols, vert_data):

    centers = np.sum(v_pols, axis=1) / v_pols.shape[1]
    if vert_data:
        center_vert_data = dict()
        for key in vert_data:
            data = vert_data[key]
            np_data = data if isinstance(data, np.ndarray) else np.array(data)
            if len(np_data.shape) > 1:
                center_vert_data[key] = np.sum(np_data[np_faces], axis=1)/v_pols.shape[1]
            else:
                center_vert_data[key] = np.sum(np_data[np_faces], axis=1)/v_pols.shape[1]
    else:
        center_vert_data = []
    return centers, center_vert_data

def irregular_random_centers(centers, mask, v_pols, np_faces_g, randomf, vert_data, center_vert_data, np_data_dict):
    centers[mask, :] = np.sum(v_pols * randomf[:, :, np.newaxis], axis=1) / (np.sum(randomf, axis=1)[:, np.newaxis])

    if vert_data:
        for key in vert_data:
            np_data = np_data_dict[key]
            if len(np_data.shape)>1:
                center_vert_data[key][mask] = np.sum(np_data[np_faces_g] * randomf[:, np.newaxis], axis=1) / np.sum(randomf, axis=1)[:, np.newaxis]
            else:
                center_vert_data[key][mask] = np.sum(np_data[np_faces_g] * randomf, axis=1) / np.sum(randomf, axis=1)

def irregular_mid_centers(centers, mask, v_pols, np_faces_g, vert_data, center_vert_data, np_data_dict):
    centers[mask, :] = np.sum(v_pols, axis=1) / v_pols.shape[1]

    if vert_data:
        for key in vert_data:
            np_data = np_data_dict[key]
            if len(np_data.shape) > 1:
                center_vert_data[key][mask] = np.sum(np_data[np_faces_g], axis=1) / v_pols.shape[1]
            else:
                center_vert_data[key][mask] = np.sum(np_data[np_faces_g], axis=1) / v_pols.shape[1]

def random_centers(np_verts, faces, lens, vert_data, normal_displace, random_f, random_normal):


    if isinstance(faces, np.ndarray):
        np_faces = faces
    else:
        np_faces = np.array(faces)

    if np_faces.dtype == object:
        pol_types = np.unique(lens)
        center_vert_data = dict()
        np_data_dict = dict()
        if vert_data:
            for key in vert_data:
                data = vert_data[key]
                np_data = data if isinstance(data, np.ndarray) else np.array(data)
                np_data_dict[key] = np_data
                center_vert_data[key] = np.zeros(np_faces.shape[0], np_data.shape[1], dtype=np_data.dtype)
        else:
            center_vert_data = []
        centers = np.zeros((np_faces.shape[0], 3), dtype=float)
        for p in pol_types:
            mask = lens == p
            np_faces_g = np.array(np_faces[mask].tolist())
            v_pols = np_verts[np_faces_g]
            if random_f != 0:
                randomf = 0.5+(random(np_faces_g.shape)-0.5) * random_f
                irregular_random_centers(centers, mask, v_pols, np_faces_g,
                                         randomf, vert_data, center_vert_data,
                                         np_data_dict)
            else:
                irregular_mid_centers(centers, mask, v_pols, np_faces_g,
                                      vert_data, center_vert_data,
                                      np_data_dict)

            if random_normal != 0 or normal_displace != 0:
                centers[mask, :] += normal_offset(v_pols, normal_displace, random_normal)
    else:
        v_pols = np_verts[np_faces] #num pols, num sides
        if random_f != 0:
            randomf = 0.5 + (np.random.random(np_faces.shape) - 0.5) * random_f
            centers, center_vert_data = regular_random_centers(np_faces, v_pols, randomf, vert_data)
        else:
            centers, center_vert_data = regular_mid_centers(np_faces, v_pols, vert_data)

        if random_normal != 0 or normal_displace != 0:
            centers += normal_offset(v_pols, normal_displace, random_normal)

    return centers, center_vert_data

def random_pol_center(v_pols, f):
    randomf = 0.5+(np.random.random(v_pols.shape)-0.5) *f
    return np.sum(v_pols*randomf, axis=1) / (np.sum(randomf, axis=1))

def smooth_verts(np_verts, edges,f):
    average= np.zeros_like(np_verts)
    nums = np.zeros(len(np_verts), dtype=int)
    np.add.at(average, edges, np_verts[np.flip(edges,axis=1)])
    np.add.at(nums, edges, 1)
    masks_unreferenced = nums == 0
    average[masks_unreferenced] = np_verts[masks_unreferenced]
    return np_verts*(1-f)+average/nums[:,np.newaxis]*f

def pols_to_edges(flat_pols, lens, pol_end):
    edges = np.zeros((len(flat_pols), 2), dtype=int)
    edges[:, 0] = flat_pols
    edges[:, 1] = np.roll(flat_pols, -1)
    edges[pol_end-1, 1] = flat_pols[pol_end-lens]
    return  (edges,
             *np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True))

def subdivide(np_verts, pols_m, normal_displace, random_f, random_normal,
              edges, unique_edges, eds_inverse_idx,
              pol_end, pol_len,
              vert_map, vert_data, face_data):

    pol_center, center_vert_data = random_centers(np_verts, pols_m, pol_len,
                                                  vert_data, normal_displace,
                                                  random_f, random_normal)

    if random_f != 0:
        mid_random = 0.5+(np.random.random(unique_edges.shape)-0.5)*random_f
        mid_points = np.sum(np_verts[unique_edges]*mid_random[:, :, np.newaxis], axis=1)/np.sum(mid_random, axis=1)[:,np.newaxis]
    else:
        mid_points = np.sum(np_verts[unique_edges], axis=1)/2

    verts_out = np.concatenate([np_verts, mid_points, pol_center])

    if len(vert_map) > 0:
        vert_map = np.concatenate([vert_map,
                                   np.full(mid_points.shape[0], vert_map[-1]+1),
                                   np.full(pol_center.shape[0], vert_map[-1]+2)])
    num_verts = np_verts.shape[0]
    num_mids = mid_points.shape[0]
    num_centers = len(pols_m)
    mid_point_idx = np.arange(num_verts, num_verts + num_mids)
    center_point_idx = np.arange(num_verts + num_mids, num_verts + num_mids + num_centers)

    pols_out = np.zeros([edges.shape[0], 4], dtype=int)
    mids_idx = mid_point_idx[eds_inverse_idx]
    mid_idx_end = np.roll(mids_idx, 1)
    mid_idx_end[pol_end - pol_len] = mids_idx[pol_end-1]

    pols_out[:, 0] = edges[:, 0]
    pols_out[:, 1] = mids_idx
    pols_out[:, 2] = np.repeat(center_point_idx, pol_len)
    pols_out[:, 3] = mid_idx_end

    if face_data:
        new_face_data = dict()
        for key in face_data:
            data = face_data[key]
            if isinstance(data, np.ndarray):
                new_data = np.repeat(data, pol_len)
            else:
                new_data = [d for d, p_l in zip(data, pol_len) for i in range(p_l)]
            new_face_data[key] = new_data
    else:
        new_face_data = dict()

    if vert_data:
        new_vert_data = dict()
        for key in vert_data:
            data = vert_data[key]
            np_data = data if isinstance(data, np.ndarray) else np.array(data)

            new_data = np.concatenate([np_data,
                                       np.sum(np_data[unique_edges], axis=1)/2,
                                       center_vert_data[key]])

            new_vert_data[key] = new_data
    else:
        new_vert_data = dict()

    return verts_out, pols_out, vert_map, new_vert_data, new_face_data

def subdiv_mesh_to_quads_np(vertices, polygons,
                            iterations, normal_displace,
                            random_f, random_normal, random_seed,
                            smooth_f,
                            vert_data, face_data,
                            output_edges=True,
                            output_vert_map=True):
    np.random.seed(int(random_seed))
    np_verts = vertices if isinstance(vertices, np.ndarray) else np.array(vertices)
    if output_vert_map:
        vert_map = np.zeros(np_verts.shape[0], dtype=int)
    else:
        vert_map = np.array([], dtype=int)

    matched_vert_data = dict()
    if vert_data:
        for key in vert_data:
            matched_vert_data[key] = numpy_full_list(vert_data[key], np_verts.shape[0])

    matched_face_data = dict()
    if face_data:
        for key in face_data:
            data = face_data[key]
            if isinstance(data, np.ndarray):
                matched_face_data[key] = numpy_full_list(data, len(polygons))
            else:
                matched_face_data[key] = repeat_last_for_length(data, len(polygons))


    flat_pols, pol_len, pol_end = np_pols(polygons)
    edges, unique_edges, eds_inverse_idx = pols_to_edges(flat_pols, pol_len, pol_end)
    return subdiv_mesh_to_quads_inner(
        np_verts, polygons,
        pol_len, pol_end,
        edges, unique_edges, eds_inverse_idx,
        iterations, normal_displace,
        random_f, random_normal,
        smooth_f,
        vert_map, matched_vert_data, matched_face_data,
        output_edges=output_edges,
        max_iterations=iterations)

def get_item(data, i):
    return data[i%len(data)]

def subdiv_mesh_to_quads_inner(
        np_verts, pols_m,
        pol_len, pol_end,
        edges, unique_edges, eds_inverse_idx,
        it, normal_displace,
        random_f, random_normal,
        smooth_f,
        vert_map, vert_data, face_data,
        output_edges=True,
        max_iterations=1):

    iteration_num = max_iterations-it
    verts_out, pols_out, vert_map_out, vert_data_out, face_data_out = subdivide(
        np_verts, pols_m,
        get_item(normal_displace, iteration_num),
        get_item(random_f, iteration_num),
        get_item(random_normal, iteration_num),
        edges, unique_edges, eds_inverse_idx,
        pol_end, pol_len,
        vert_map, vert_data, face_data)


    actual_smooth_f = get_item(smooth_f, iteration_num)
    if actual_smooth_f == 0:
        do_smooth_f = False
    else:
        do_smooth_f = True
    if output_edges or do_smooth_f or it >= 2:
        p_lens = np.full(pols_out.shape[0], 4)
        p_end = np.cumsum(p_lens)
        new_all_edges, new_edges, new_eds_inverse_idx = pols_to_edges(pols_out.flat, p_lens, p_end)
        if do_smooth_f:
            verts_out = smooth_verts(verts_out, new_edges, actual_smooth_f)
    else:
        new_edges = []

    if it < 2:
        return verts_out, new_edges, pols_out, vert_map_out, vert_data_out, face_data_out


    return subdiv_mesh_to_quads_inner(
        verts_out, pols_out,
        p_lens, p_end,
        new_all_edges, new_edges, new_eds_inverse_idx,
        it-1, normal_displace,
        random_f, random_normal,
        smooth_f,
        vert_map_out, vert_data_out, face_data_out,
        output_edges=output_edges,
        max_iterations=max_iterations)
