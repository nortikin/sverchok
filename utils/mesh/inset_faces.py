# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import mathutils
from mathutils import Vector

import numpy as np
from numpy import(
    arange as np_arange,
    array as np_array,
    concatenate as np_concatenate,
    newaxis as np_newaxis,
    repeat as np_repeat,
    roll as np_roll,
    vectorize as np_vectorize,
)
from sverchok.utils.math import np_dot, np_normalize_vectors as normalize_v3
from sverchok.utils.modules.polygon_utils import np_faces_normals, np_faces_perimeters as face_perimeter
from sverchok.data_structure import numpy_full_list, has_element
IDENTITY_MATRIX = np.eye(4, dtype=float)
INVERSE_IDENTITY_MATRIX = np.array([[-1, 0,  0, 0],
                                    [0, -1,  0, 0],
                                    [0,  0, -1, 0],
                                    [0,  0,  0, 1]], dtype=float)
def vector_length(arr):
    return np.sqrt(arr[:, 0]**2 + arr[:, 1]**2 + arr[:, 2]**2)

def inset_special_np(vertices, faces, inset_rates, distances, ignores, make_inners, custom_normals, matrices,
                     zero_mode="SKIP", offset_mode='CENTER', proportional=False, concave_support=True,
                     output_old_face_id=False, output_old_v_id=False,
                     output_pols_groups=False, output_new_verts_mask=False):

    if not has_element(faces):
        return
    new_faces, new_ignores, new_insets = [], [], []
    original_face_ids, original_vertex_id, new_pols_groups, new_verts_mask = [], [], [], []
    inset_faces_id, fan_faces_id, ignores_id, fan_faces = [], [], [], []
    np_distances, np_matrices = [], []

    np_verts = vertices if isinstance(vertices, np.ndarray) else np.array(vertices)

    invert_face_mask = numpy_full_list(np_array(ignores, dtype=bool), len(faces))
    np_faces_mask = np.invert(invert_face_mask)

    if not any(np_faces_mask):
        return

    np_faces = np_array(faces)
    np_faces_id = np.arange(len(faces)) if output_old_face_id else []
    np_inset_rate = numpy_full_list(inset_rates, len(faces))
    if has_element(custom_normals):
        np_custom_normals = numpy_full_list(custom_normals, len(faces))
        use_custom_normals = True
    else:
        np_custom_normals = []
        use_custom_normals = False

    if offset_mode == 'CENTER':
        zero_inset = np.logical_and( np_inset_rate == 0, np_faces_mask==True)
        if zero_mode == 'SKIP':
            np_faces_mask[zero_inset] = False
            invert_face_mask[zero_inset] = True

            inset_pols = np_faces[np_faces_mask]
            np_distances = numpy_full_list(distances, len(faces))[np_faces_mask]
            np_inset_rate = np_inset_rate[np_faces_mask]
            np_make_inners = numpy_full_list(make_inners, len(faces)).astype(bool)[np_faces_mask]
            new_ignores = np_faces[invert_face_mask].tolist()

            if output_old_face_id:
                ignores_id = np_faces_id[invert_face_mask].tolist()
                inset_faces_id = np_faces_id[np_faces_mask]

        else: # FAN
            if output_old_face_id:
                ignores_maks = np.invert(np_faces_mask)
                ignores_id = np_faces_id[ignores_maks].tolist()
                new_ignores = np_faces[ignores_maks].tolist()
            else:
                new_ignores = np_faces[np.invert(np_faces_mask)].tolist()

            np_faces_mask[zero_inset] = False
            inset_pols = np_faces[np_faces_mask]
            np_make_inners = numpy_full_list(make_inners, len(faces)).astype(bool)[np_faces_mask]

            np_all_distances = numpy_full_list(distances, len(faces))
            np_distances = np_all_distances[np_faces_mask]
            np_inset_rate = np_inset_rate[np_faces_mask]
            fan_faces = np_faces[zero_inset]
            fan_distances = np_all_distances[zero_inset]
            if output_old_face_id:
                inset_faces_id = np_faces_id[np_faces_mask]
                fan_faces_id = np_faces_id[zero_inset]
    else: #SIDES mode
        inset_pols = np_faces[np_faces_mask]
        if offset_mode == 'SIDES':
            np_distances = numpy_full_list(distances, len(faces))[np_faces_mask]
            np_inset_rate = np_inset_rate[np_faces_mask]
        else: #MATRIX
            if len(matrices) == len(faces):
                np_matrices = np.array(matrices)[np_faces_mask]
            else:
                np_matrices = numpy_full_list(matrices, len(inset_pols))

        np_make_inners = numpy_full_list(make_inners, len(faces)).astype(bool)[np_faces_mask]
        new_ignores = np_faces[invert_face_mask].tolist()
        fan_faces = []
        if output_old_face_id:
            ignores_id = np_faces_id[invert_face_mask].tolist()
            inset_faces_id = np_faces_id[np_faces_mask]




    common_args = {
        'use_custom_normals': use_custom_normals,
        'output_old_v_id': output_old_v_id,
        'output_old_face_id': output_old_face_id,
        'output_pols_groups': output_pols_groups
    }
    new_verts = np_verts.tolist()
    if output_old_v_id:
        original_vertex_id = list(range(len(vertices)))
    if output_new_verts_mask:
        new_verts_mask.extend([0]*len(new_verts))

    variable_pols = inset_pols.dtype == 'object'
    np_len = np_vectorize(len)
    index_offset = 0

    if len(inset_pols) > 0:
        if variable_pols:
            lens = np_len(inset_pols)
            pol_types = np.unique(lens)

        else:
            pol_types = [inset_pols.shape[1]]


        for pol_sides in pol_types:
            if variable_pols:
                mask = lens == pol_sides
                pols_group = np_array(inset_pols[mask].tolist(), dtype=int)
                res = inset_regular_pols(np_verts, pols_group,
                                         np_distances[mask] if offset_mode != 'MATRIX' else [],
                                         np_inset_rate[mask] if offset_mode != 'MATRIX' else [],
                                         np_make_inners[mask],
                                         inset_faces_id[mask] if output_old_face_id else [],
                                         np_custom_normals[mask] if use_custom_normals else [],
                                         np_matrices[mask] if offset_mode == 'MATRIX' else [],
                                         offset_mode=offset_mode, proportional=proportional,
                                         concave_support=concave_support,
                                         index_offset=index_offset,
                                         **common_args)

            else:
                res = inset_regular_pols(np_verts, inset_pols,
                                         np_distances,
                                         np_inset_rate,
                                         np_make_inners,
                                         inset_faces_id if output_old_face_id else [],
                                         np_custom_normals if use_custom_normals else [],
                                         np_matrices,
                                         offset_mode=offset_mode, proportional=proportional,
                                         concave_support=concave_support,
                                         index_offset=index_offset,
                                         **common_args)
            index_offset += len(res[0])
            new_verts.extend(res[0])
            new_faces.extend(res[1])
            new_insets.extend(res[2])
            original_vertex_id.extend(res[3])
            original_face_ids.extend(res[4])
            new_pols_groups.extend(res[5])
            if output_new_verts_mask:
                new_verts_mask.extend([1]*len(res[0]))

    if zero_mode == 'FAN' and len(fan_faces) > 0:
        if variable_pols:
            lens = np_len(fan_faces)
            pol_types = np.unique(lens)
        else:
            pol_types = [inset_pols.shape[1]]
        for pol_sides in pol_types:
            if variable_pols:
                mask = lens == pol_sides
                pols_group = np_array(fan_faces[mask].tolist(), dtype=int)
                res = fan_regular_pols(
                    np_verts, pols_group, fan_distances[mask],
                    fan_faces_id[mask] if output_old_face_id else [],
                    np_custom_normals[mask] if use_custom_normals else [],
                    index_offset=index_offset,
                    **common_args)
            else:
                res = fan_regular_pols(
                    np_verts, fan_faces, fan_distances,
                    fan_faces_id if output_old_face_id else [],
                    np_custom_normals if use_custom_normals else [],
                    index_offset=index_offset,
                    **common_args)


            index_offset += len(res[0])
            new_verts.extend(res[0])
            new_faces.extend(res[1])
            original_vertex_id.extend(res[2])
            original_face_ids.extend(res[3])
            new_pols_groups.extend(res[4])
            if output_new_verts_mask:
                new_verts_mask.extend([1]*len(res[0]))

    return (new_verts,
            new_faces + new_ignores,
            new_ignores,
            new_insets,
            original_vertex_id,
            original_face_ids + ignores_id,
            new_pols_groups + [0]*len(new_ignores),
            new_verts_mask)

def normalize_or_calc(v1, v2, normals):
    arr = v1 + v2
    lens = vector_length(arr)
    mask = lens != 0
    arr[mask, 0] /= lens[mask]
    arr[mask, 1] /= lens[mask]
    arr[mask, 2] /= lens[mask]
    zero_length_mask = np.invert(mask)
    arr[zero_length_mask, :] = normalize_v3(np.cross(normals[zero_length_mask, :], v1[zero_length_mask, :]))
    arr[zero_length_mask, :] = (np.cross(normals[zero_length_mask, :], v1[zero_length_mask, :]))
    return arr

def sides_mode_inset(v_pols, np_inset_rate, np_distances,
                     concave_support, proportional,
                     use_custom_normals, custom_normals):
    pol_sides = v_pols.shape[1]
    dirs = np.zeros(v_pols.shape, dtype=float)

    if concave_support:
        normals = custom_normals if use_custom_normals else np_faces_normals(v_pols)
        for i in range(pol_sides):
            side1 = normalize_v3(v_pols[:, (i+1)%pol_sides]- v_pols[:, i])
            side2 = normalize_v3(v_pols[:, i-1]- v_pols[:, i])
            dirs[:, i] = normalize_or_calc(side1, side2, normals)
            dirs[:, i] *= (np_inset_rate/(np.sqrt(1-np.clip(np_dot(side1, dirs[:, i]), -1.0, 1.0)**2)))[:, np_newaxis]

        average = np.sum(v_pols, axis=1)/pol_sides
        concave_mask = np_dot(average[:, np_newaxis, :] - v_pols, dirs, axis=2) < 0

        dirs[concave_mask] *= -1
    else:
        for i in range(pol_sides):
            side1 = normalize_v3(v_pols[:, (i+1)%pol_sides]- v_pols[:, i])
            side2 = normalize_v3(v_pols[:, i-1]- v_pols[:, i])
            dirs[:, i] = normalize_v3(normalize_v3(v_pols[:, (i+1)%pol_sides]- v_pols[:, i]) +
                                      normalize_v3(v_pols[:, i-1]- v_pols[:, i])
                                      )

            dirs[:, i] *= (np_inset_rate/(np.sqrt(1-np.clip(np_dot(side1, dirs[:, i]), -1.0, 1.0)**2)))[:, np_newaxis]

    if proportional:
        dirs *= face_perimeter(v_pols)[:, np_newaxis, np_newaxis]
    if any(np_distances != 0):
        if  not concave_support:
            normals = custom_normals if use_custom_normals else np_faces_normals(v_pols)
        z_offset = normals * np_distances[:, np_newaxis]
        inner_points = dirs + v_pols + z_offset[:, np_newaxis, :]
    else:
        inner_points = dirs + v_pols
    return inner_points

def apply_matrices_to_v_pols(verts, matrices):

    verts_co_4d = np.ones(shape=(verts.shape[0], verts.shape[1], 4), dtype=np.float)
    verts_co_4d[:, :, :-1] = verts  # cos v (x,y,z,1) - point,   v(x,y,z,0)- vector
    return np.einsum('aij,akj->aki', matrices, verts_co_4d)[:, :, :-1]


def matrix_mode_inset(v_pols, matrices, use_custom_normals, custom_normals):
    pol_sides = v_pols.shape[1]
    average = np.sum(v_pols, axis=1)/pol_sides
    if use_custom_normals:
        normals = custom_normals
    else:
        normals = np_faces_normals(v_pols)

    pol_matrix = np.repeat(IDENTITY_MATRIX[np.newaxis, :, :], len(v_pols), axis=0)

    mask = np.all([normals[:, 0] == 0, normals[:, 1] == 0], axis=0)
    mask2 = normals[:, 2] <= 0
    mask4 = mask*mask2
    r_mask = np.invert(mask)

    x_axis = np.zeros(normals.shape, dtype=float)
    x_axis[:, 0] = normals[:, 1] * -1
    x_axis[:, 1] = normals[:, 0]
    y_axis = np.cross(normals, x_axis, axis=1)

    pol_matrix[r_mask, :3, 2] = normals[r_mask, :]
    pol_matrix[r_mask, :3, 1] = y_axis[r_mask, :]
    pol_matrix[r_mask, :3, 0] = x_axis[r_mask, :]
    pol_matrix[mask4, :, :] = INVERSE_IDENTITY_MATRIX[np.newaxis, :]
    pol_matrix[:, :3, 3] = average


    inverted_mat = np.linalg.inv(pol_matrix)

    matrices = np.matmul(matrices, inverted_mat)
    matrices = np.matmul(pol_matrix, matrices)

    return apply_matrices_to_v_pols(v_pols, matrices)
    # verts_out =[v_pols_transformed.reshape(-1,3)]

def inset_regular_pols(np_verts, np_pols,
                       np_distances, np_inset_rate, np_make_inners,
                       np_faces_id, custom_normals,
                       matrices,
                       offset_mode='CENTER',
                       proportional=False,
                       concave_support=True,
                       index_offset=0,
                       use_custom_normals=False,
                       output_old_face_id=True,
                       output_old_v_id=True,
                       output_pols_groups=True):

    pols_number = np_pols.shape[0]
    pol_sides = np_pols.shape[1]
    v_pols = np_verts[np_pols] #shape [num_pols, num_corners, 3]
    if offset_mode == 'SIDES':
        inner_points = sides_mode_inset(v_pols, np_inset_rate, np_distances,
                                        concave_support, proportional,
                                        use_custom_normals, custom_normals)
    elif offset_mode == 'MATRIX':
        inner_points = matrix_mode_inset(v_pols, matrices,
                                         use_custom_normals, custom_normals)
    else:
        if any(np_distances != 0):
            if use_custom_normals:
                normals = custom_normals
            else:
                normals = np_faces_normals(v_pols)
            average = np.sum(v_pols, axis=1)/pol_sides #+ normals*np_distances[:, np_newaxis] #shape [num_pols, 3]
            inner_points = average[:, np_newaxis, :] + (v_pols - average[:, np_newaxis, :]) * np_inset_rate[:, np_newaxis, np_newaxis] + normals[:, np_newaxis, :]*np_distances[:, np_newaxis, np_newaxis]
        else:
            average = np.sum(v_pols, axis=1)/pol_sides  #shape [num_pols, 3]
            inner_points = average[:, np_newaxis, :] + (v_pols - average[:, np_newaxis, :]) * np_inset_rate[:, np_newaxis, np_newaxis]


    idx_offset = len(np_verts) + index_offset

    new_v_idx = np_arange(idx_offset, pols_number * pol_sides + idx_offset).reshape(pols_number, pol_sides)

    side_pols = np.zeros([pols_number, pol_sides, 4], dtype=int)
    side_pols[:, :, 0] = np_pols
    side_pols[:, :, 1] = np_roll(np_pols, -1, axis=1)
    side_pols[:, :, 2] = np_roll(new_v_idx, -1, axis=1)
    side_pols[:, :, 3] = new_v_idx

    side_faces = side_pols.reshape(-1, 4)

    new_insets = new_v_idx[np_make_inners]

    if pol_sides == 4:
        new_faces = np_concatenate([side_faces, new_insets]).tolist()
    else:
        new_faces = side_faces.tolist() + new_insets.tolist()

    old_v_id = np_pols.flatten().tolist() if output_old_v_id else []
    if output_old_face_id:
        side_ids = np.repeat(np_faces_id[:, np_newaxis], pol_sides, axis=1)
        inset_ids = np_faces_id[np_make_inners]
        old_face_id = np.concatenate((side_ids.flatten(), inset_ids)).tolist()
    else:
        old_face_id = []

    if output_pols_groups:
        pols_groups = np_repeat([1, 2], [len(side_faces), len(new_insets)]).tolist()
    else:
        pols_groups = []

    return (inner_points.reshape(-1, 3).tolist(),
            new_faces,
            new_insets.tolist(),
            old_v_id,
            old_face_id,
            pols_groups
            )

def fan_regular_pols(np_verts, np_pols,
                     np_distances, np_faces_id,
                     custom_normals,
                     index_offset=0,
                     use_custom_normals=False,
                     output_old_v_id=True,
                     output_old_face_id=True,
                     output_pols_groups=True):

    pols_number = np_pols.shape[0]
    pol_sides = np_pols.shape[1]
    v_pols = np_verts[np_pols] #shape [num_pols, num_corners, 3]

    if (len(np_distances) > 1 and np.any(np_distances != 0)) or np_distances != 0:
        if use_custom_normals:
            normals = custom_normals
        else:
            normals = np_faces_normals(v_pols)
        average = np.sum(v_pols, axis=1)/pol_sides + normals*np_distances[:, np_newaxis] #shape [num_pols, 3]
    else:
        average = np.sum(v_pols, axis=1)/pol_sides


    idx_offset = len(np_verts) + index_offset
    new_idx = np_arange(idx_offset, pols_number + idx_offset)
    new_pols = np.zeros([pols_number, pol_sides, 3], dtype=int)
    new_pols[:, :, 0] = np_pols
    new_pols[:, :, 1] = np_roll(np_pols, -1, axis=1)
    new_pols[:, :, 2] = new_idx[:, np_newaxis]



    old_vert_id = np_pols[:, 0].tolist() if output_old_v_id else []

    if output_old_face_id:
        old_face_id = np_repeat(np_faces_id[:, np_newaxis], pol_sides, axis=1).tolist()
    else:
        old_face_id = []

    if output_pols_groups:
        pols_groups = np_repeat(1, len(new_pols)*pol_sides).tolist()
    else:
        pols_groups = []

    return (average.tolist(),
            new_pols.reshape(-1, 3).tolist(),
            old_vert_id,
            old_face_id,
            pols_groups,
            )


'''
Old implementation, slower, left here because polygon order may differ with the new implementation
'''

def inset_special_mathutils(vertices, faces, inset_rates, distances, ignores, make_inners, zero_mode="SKIP"):

    new_faces = []
    new_ignores = []
    new_insets = []

    def get_average_vector(verts, n):
        dummy_vec = Vector()
        for v in verts:
            dummy_vec = dummy_vec + v
        return dummy_vec * 1/n

    def do_tri(face, lv_idx, make_inner):
        a, b, c = face
        d, e, f = lv_idx-2, lv_idx-1, lv_idx
        out_faces = []
        out_faces.append([a, b, e, d])
        out_faces.append([b, c, f, e])
        out_faces.append([c, a, d, f])
        if make_inner:
            out_faces.append([d, e, f])
            new_insets.append([d, e, f])
        return out_faces

    def do_quad(face, lv_idx, make_inner):
        a, b, c, d = face
        e, f, g, h = lv_idx-3, lv_idx-2, lv_idx-1, lv_idx
        out_faces = []
        out_faces.append([a, b, f, e])
        out_faces.append([b, c, g, f])
        out_faces.append([c, d, h, g])
        out_faces.append([d, a, e, h])
        if make_inner:
            out_faces.append([e, f, g, h])
            new_insets.append([e, f, g, h])
        return out_faces

    def do_ngon(face, lv_idx, make_inner):
        '''
        setting up the forloop only makes sense for ngons
        '''
        num_elements = len(face)
        face_elements = list(face)
        inner_elements = [lv_idx-n for n in range(num_elements-1, -1, -1)]
        # padding, wrap-around
        face_elements.append(face_elements[0])
        inner_elements.append(inner_elements[0])

        out_faces = []
        add_face = out_faces.append
        for j in range(num_elements):
            add_face([face_elements[j], face_elements[j+1], inner_elements[j+1], inner_elements[j]])

        if make_inner:
            temp_face = [idx[-1] for idx in out_faces]
            add_face(temp_face)
            new_insets.append(temp_face)

        return out_faces

    def new_inner_from(face, inset_by, distance, make_inner):
        '''
        face:       (idx list) face to work on
        inset_by:   (scalar) amount to open the face
        axis:       (vector) axis relative to face normal
        distance:   (scalar) push new verts on axis by this amount
        make_inner: create extra internal face

        # dumb implementation first. should only loop over the verts of face 1 time
        to get
         - new faces
         - avg vertex location
         - but can't lerp until avg is known. so each input face is looped at least twice.
        '''
        current_verts_idx = len(vertices)
        n = len(face)
        verts = [vertices[i] for i in face]
        avg_vec = get_average_vector(verts, n)

        if abs(inset_by) < 1e-6:
            normal = mathutils.geometry.normal(*verts)
            new_vertex = avg_vec.lerp(avg_vec + normal, distance)
            vertices.append(new_vertex)
            new_vertex_idx = current_verts_idx
            for i, j in zip(face, face[1:]):
                new_faces.append([i, j, new_vertex_idx])
            new_faces.append([face[-1], face[0], new_vertex_idx])
            return

        # lerp and add to vertices immediately
        new_verts_prime = [avg_vec.lerp(v, inset_by) for v in verts]

        if distance:
            local_normal = mathutils.geometry.normal(*new_verts_prime)
            new_verts_prime = [v.lerp(v+local_normal, distance) for v in new_verts_prime]

        vertices.extend(new_verts_prime)

        tail_idx = (current_verts_idx + n) - 1

        get_faces_prime = {3: do_tri, 4: do_quad}.get(n, do_ngon)
        new_faces_prime = get_faces_prime(face, tail_idx, make_inner)
        new_faces.extend(new_faces_prime)

    for face, inset_by, ignore, dist, inner in zip(faces, inset_rates, ignores, distances, make_inners):

        good_inset = (inset_by > 0) or (zero_mode == 'FAN')
        if good_inset and (not ignore):
            new_inner_from(face, inset_by, dist, inner)
        else:
            new_faces.append(face)
            new_ignores.append(face)

    new_verts = [v[:] for v in vertices]
    return new_verts, new_faces, new_ignores, new_insets, [], []
