# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import itertools
from collections import defaultdict

import bmesh
from mathutils import Vector

from mathutils.geometry import (
    intersect_line_line,
    intersect_line_line_2d)

from sverchok.data_structure import cross_indices_np
from sverchok.utils.cad_module_class import CAD_ops
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.math import np_dot

import numpy as np

def order_points(edge, point_list):
    ''' order these edges from distance to v1, then
    sandwich the sorted list with v1, v2 '''
    v1, v2 = edge
    dist = lambda co: (v1-co).length
    point_list = sorted(point_list, key=dist)
    return [v1] + point_list + [v2]

def remove_permutations_that_share_a_vertex(cm, bm, permutations):
    ''' Get useful Permutations '''

    final_permutations = []
    for edges in permutations:
        raw_vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        if cm.duplicates(raw_vert_indices):
            continue

        # reaches this point if they do not share.
        final_permutations.append(edges)

    return final_permutations

def get_valid_permutations(cm, bm, edge_indices):
    raw_permutations = itertools.permutations(edge_indices, 2)
    permutations = [r for r in raw_permutations if r[0] < r[1]]
    return remove_permutations_that_share_a_vertex(cm, bm, permutations)

def can_skip(cm, closest_points, vert_vectors):
    '''this checks if the intersection lies on both edges, returns True
    when criteria are not met, and thus this point can be skipped'''
    if not closest_points:
        return True
    if not isinstance(closest_points[0].x, float):
        return True
    if cm.num_edges_point_lies_on(closest_points[0], vert_vectors) < 2:
        return True

    # if this distance is larger than than VTX_PRECISION, we can skip it.
    cpa, cpb = closest_points
    return (cpa-cpb).length > cm.VTX_PRECISION

def get_intersection_dictionary(cm, bm, edge_indices):

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    permutations = get_valid_permutations(cm, bm, edge_indices)

    k = defaultdict(list)
    d = defaultdict(list)

    for edges in permutations:
        vert_vectors = cm.vectors_from_edges_tuple(bm, edges)
        v1, v2, v3, v4 = vert_vectors

        # Edges obviously can not intersect if their bounding
        # boxes do not intersect
        if (max(v1.x, v2.x) < min(v3.x, v4.x) or
            max(v1.y, v2.y) < min(v3.y, v4.y) or
            max(v1.z, v2.z) < min(v3.z, v4.z)):
                continue
        if (max(v3.x, v4.x) < min(v1.x, v2.x) or
            max(v3.y, v4.y) < min(v1.y, v2.y) or
            max(v3.z, v4.z) < min(v1.z, v2.z)):
                continue

        # Edges can not intersect if they do not lie in
        # the same plane
        if not cm.is_coplanar(vert_vectors):
            continue

        points = intersect_line_line(*vert_vectors)

        # some can be skipped.    (NaN, None, not on both edges)
        if can_skip(cm, points, vert_vectors):
            continue

        # reaches this point only when an intersection happens on both edges.
        [k[edge].append(points[0]) for edge in edges]

    # k will contain a dict of edge indices and points found on those edges.
    for edge_idx, unordered_points in k.items():
        tv1, tv2 = bm.edges[edge_idx].verts
        v1 = bm.verts[tv1.index].co
        v2 = bm.verts[tv2.index].co
        ordered_points = order_points((v1, v2), unordered_points)
        d[edge_idx].extend(ordered_points)

    return d

def update_mesh(bm, d):
    ''' Make new geometry '''

    oe = bm.edges
    ov = bm.verts

    for old_edge, point_list in d.items():
        num_edges_to_add = len(point_list)-1
        for i in range(num_edges_to_add):
            a = ov.new(point_list[i])
            b = ov.new(point_list[i+1])
            oe.new((a, b))
    bm.normal_update()

def unselect_nonintersecting(bm, d_edges, edge_indices):
    # print(d_edges, edge_indices)
    if len(edge_indices) > len(d_edges):
        reserved_edges = set(edge_indices) - set(d_edges)
        for edge in reserved_edges:
            bm.edges[edge].select = False
        # print("unselected {}, non intersecting edges".format(reserved_edges))

def bmesh_intersect_edges_3d(bm, s_epsilon):
    edge_indices = [e.index for e in bm.edges]
    trim_indices = len(edge_indices)
    for edge in bm.edges:
        edge.select = True

    cm = CAD_ops(epsilon=s_epsilon)

    d = get_intersection_dictionary(cm, bm, edge_indices)
    unselect_nonintersecting(bm, d.keys(), edge_indices)

    # store non_intersecting edge sequencer
    add_back = [[i.index for i in edge.verts] for edge in bm.edges if not edge.select]

    update_mesh(bm, d)
    return add_back

def intersect_edges_3d(verts_in, edges_in, s_epsilon):
    bm = bmesh_from_pydata(verts_in, edges_in, [])

    trim_indices = len(bm.edges[:])

    add_back = bmesh_intersect_edges_3d(bm, s_epsilon)

    verts_out = [v.co.to_tuple() for v in bm.verts]
    edges_out = [[j.index for j in i.verts] for i in bm.edges]
    # optional correction, remove originals, add back those that are not intersecting.
    edges_out = edges_out[trim_indices:]
    edges_out.extend(add_back)
    bm.free()
    return verts_out, edges_out

# adapted from
# https://stackoverflow.com/a/18994296
# distance point line https://stackoverflow.com/a/39840218
def intersect_edges_3d_np(verts, edges, s_epsilon, only_touching=True):
    '''Brute force Numpy implementation of edges intersections'''
    indices = cross_indices_np(len(edges))
    np_verts = verts if isinstance(verts, np.ndarray) else np.array(verts)
    np_edges = edges if isinstance(edges, np.ndarray) else np.array(edges)
    eds = np_edges[indices].reshape(-1, 4)
    mask = np.invert(np.any([eds[:, 0] == eds[:, 2],
                             eds[:, 0] == eds[:, 3],
                             eds[:, 1] == eds[:, 2],
                             eds[:, 1] == eds[:, 3]],
                            axis=0))
    eds2 = eds[mask]
    indices_m = indices[mask]

    seg_v = np_verts[eds2]

    direc_a = seg_v[:, 1] - seg_v[:, 0]
    direc_b = seg_v[:, 3] - seg_v[:, 2]
    dp = seg_v[:, 2] - seg_v[:, 0]
    perp = np.cross(direc_a, direc_b, axis=1)
    perp_magnitude = np.linalg.norm(perp, axis=1)
    non_parallel = perp_magnitude > 0
    perp[non_parallel] /= perp_magnitude[non_parallel, np.newaxis]
    dist = np_dot(perp[non_parallel], dp[non_parallel])
    co_planar = np.abs(dist) < s_epsilon
    seg_v = seg_v[non_parallel][co_planar]
    # Calculate denomitator
    A = direc_a[non_parallel][co_planar]
    B = direc_b[non_parallel][co_planar]
    magA = np.linalg.norm(A, axis=1)
    magB = np.linalg.norm(B, axis=1)

    _A = A / magA[:, np.newaxis]
    _B = B / magB[:, np.newaxis]

    cross = np.cross(_A, _B, axis=1)
    denom = np.linalg.norm(cross, axis=1)**2
    t = dp[non_parallel][co_planar]
    detA = np.linalg.det(np.array([t.T, _B.T, cross.T]).T)
    detB = np.linalg.det(np.array([t.T, _A.T, cross.T]).T)
    t0 = detA / denom
    t1 = detB / denom
    if only_touching:
        valid_inter = np.all([t0 > -s_epsilon, t0 < magA + s_epsilon, t1 > -s_epsilon, t1 < magB + s_epsilon], axis=0)
    else:
        valid_inter = np.all([t0 > 0, t0 < magA , t1 > 0, t1 < magB], axis=0)
    pA = seg_v[:, 0] + (_A * t0[:, np.newaxis]) # Projected closest point on segment A
    # pB = seg_v[:,2] + (_B * t1[:, np.newaxis]) # Projected closest point on segment B
    inters = pA[valid_inter]

    n_a_m = t0[valid_inter]
    n_b_m = t1[valid_inter]
    all_coefs = np.concatenate([[n_a_m], [n_b_m]], axis=0).T.ravel()

    indices_m2 = indices_m[non_parallel][co_planar][valid_inter]
    i_ravel = indices_m2.ravel()
    new_idx = np.repeat(np.arange(len(inters)) + len(np_verts), 2)

    new_edges = []
    for i in range(len(edges)):
        intersect_mask = i_ravel == i
        coef = all_coefs[intersect_mask]
        n_i = new_idx[intersect_mask]
        iid = np.argsort(coef)
        n_i_sorted = n_i[iid]
        new_eds = np.concatenate([[np_edges[i, 0]],
                                  np.repeat(n_i_sorted, 2),
                                  [np_edges[i, 1]]]).reshape(-1,2)
        new_edges.append(new_eds)

    return np.concatenate([np_verts, inters]).tolist(), np.concatenate(new_edges).tolist()

def edges_from_ed_inter_double_removal(ed_inter):
    '''create edges from intersections library'''
    edges_out = []
    for e in ed_inter:
        # sort by first element of tuple (distances)
        e_s = sorted(e)
        e_s = [e for i, e in enumerate(e_s) if e[1] != e_s[i-1][1]]
        for i in range(1, len(e_s)):
            # if e_s[i-1][1] != e_s[i][1]:
            if(e_s[i-1][1], e_s[i][1]) not in edges_out:
                edges_out.append((e_s[i-1][1], e_s[i][1]))
    return edges_out

def edges_from_ed_inter(ed_inter):
    '''create edges from intersections library'''
    edges_out = []
    for e in ed_inter:
        # sort by first element of tuple (distances)
        e_s = sorted(e)
        e_s = [e for i, e in enumerate(e_s) if e[1] != e_s[i-1][1]]
        for i in range(1, len(e_s)):
            edges_out.append((e_s[i-1][1], e_s[i][1]))
    return edges_out

def intersect_edges_2d(verts, edges, epsilon):
    '''Iterate through edges  and expose them to intersect_line_line_2d'''
    verts_in = [Vector(v) for v in verts]
    ed_lengths = [(verts_in[e[1]] - verts_in[e[0]]).length for e in edges]
    verts_out = verts
    edges_out = []
    ed_inter = [[] for e in edges]
    e_idx = range(len(edges))
    for e, d, i in zip(edges, ed_lengths, e_idx):
        # if there is no intersections this will create a normal edge
        ed_inter[i].append([0.0, e[0]])
        ed_inter[i].append([d, e[1]])
        v1 = verts_in[e[0]]
        v2 = verts_in[e[1]]
        if d == 0:
            continue

        for e2, d2, j in zip(edges[:i], ed_lengths[:i], e_idx[:i]):

            if d2 < epsilon:
                continue
            if (e2[0] in e) or (e2[1] in e):
                continue

            v3 = verts_in[e2[0]]
            v4 = verts_in[e2[1]]
            vx = intersect_line_line_2d(v1, v2, v3, v4)
            if vx:
                d_to_1 = (vx - v1.to_2d()).length
                d_to_2 = (vx - v3.to_2d()).length

                new_id = len(verts_out)

                if d_to_1 < epsilon:
                    new_id = e[0]
                elif d_to_1 > d - epsilon:
                    new_id = e[1]
                elif d_to_2 < epsilon:
                    new_id = e2[0]
                elif d_to_2 > d2 - epsilon:
                    new_id = e2[1]
                if new_id == len(verts_out):
                    verts_out.append((vx.x, vx.y, v1.z))

                # first item stores distance to origin, second the vertex id
                ed_inter[i].append([d_to_1, new_id])
                ed_inter[j].append([d_to_2, new_id])


    edges_out = edges_from_ed_inter(ed_inter)

    return verts_out, edges_out

def intersect_edges_2d_double_removal(verts, edges, epsilon):
    '''Iterate through edges  and expose them to intersect_line_line_2d'''
    verts_in = [Vector(v) for v in verts]
    ed_lengths = [(verts_in[e[1]] - verts_in[e[0]]).length for e in edges]
    verts_out = verts
    edges_out = []
    ed_inter = [[] for e in edges]
    for e, d, i in zip(edges, ed_lengths, range(len(edges))):
        # if there is no intersections this will create a normal edge
        ed_inter[i].append([0.0, e[0]])
        ed_inter[i].append([d, e[1]])
        v1 = verts_in[e[0]]
        v2 = verts_in[e[1]]
        if d == 0:
            continue

        for e2, d2, j in zip(edges, ed_lengths, range(len(edges))):

            if i <= j or d2 == 0:
                continue
            if (e2[0] in e) or (e2[1] in e):
                continue

            v3 = verts_in[e2[0]]
            v4 = verts_in[e2[1]]
            vx = intersect_line_line_2d(v1, v2, v3, v4)
            if vx:
                d_to_1 = (vx - v1.to_2d()).length
                d_to_2 = (vx - v3.to_2d()).length

                new_id = len(verts_out)
                if (vx.x, vx.y, v1.z) in verts_out:
                    new_id = verts_out.index((vx.x, vx.y, v1.z))
                else:
                    if d_to_1 < epsilon:
                        new_id = e[0]
                    elif d_to_1 > d - epsilon:
                        new_id = e[1]
                    elif d_to_2 < epsilon:
                        new_id = e2[0]
                    elif d_to_2 > d2 - epsilon:
                        new_id = e2[1]
                    if new_id == len(verts_out):
                        verts_out.append((vx.x, vx.y, v1.z))

                # first item stores distance to origin, second the vertex id
                ed_inter[i].append([d_to_1, new_id])
                ed_inter[j].append([d_to_2, new_id])


    edges_out = edges_from_ed_inter_double_removal(ed_inter)

    return verts_out, edges_out

# adapted from https://stackoverflow.com/a/3252222/16039380
def perp(a):
    b = np.empty_like(a)
    b[:, 0] = -a[:,1]
    b[:, 1] = a[:,0]
    return b

def perp_single(a):
    b = np.empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

def intersect_edges_2d_np(verts, edges, epsilon, only_touching=True):
    '''Brute force Numpy implementation of edges intersections'''
    indices = cross_indices_np(len(edges))
    np_verts = verts if isinstance(verts, np.ndarray) else np.array(verts)
    np_edges = edges if isinstance(edges, np.ndarray) else np.array(edges)
    eds = np_edges[indices].reshape(-1, 4)
    mask = np.invert(np.any([eds[:, 0] == eds[:, 2],
                             eds[:, 0] == eds[:, 3],
                             eds[:, 1] == eds[:, 2],
                             eds[:, 1] == eds[:, 3]],
                            axis=0))
    eds2 = eds[mask]
    indices_m = indices[mask]

    seg_v = np_verts[eds2]

    direc_a = seg_v[:, 1] - seg_v[:, 0]
    direc_b = seg_v[:, 3] - seg_v[:, 2]
    dp = seg_v[:, 0] - seg_v[:, 2]

    perp_direc_a = perp(direc_a)
    denom_a = np_dot(perp_direc_a, direc_b)
    num_a = np_dot(perp_direc_a, dp )
    n_a = (num_a / denom_a.astype(float))
    perp_direc_b = perp(direc_b)
    denom_b = np_dot(perp_direc_b, direc_a)
    num_b = np_dot(perp_direc_b, -dp)
    n_b = (num_b / denom_b.astype(float))
    inter = n_a[:, np.newaxis] * direc_b + seg_v[:, 2]

    if only_touching:
        valid_inter = np.all([n_a > -epsilon, n_a < 1+epsilon, n_b > -epsilon, n_b < 1+epsilon], axis=0)
    else:
        valid_inter = np.all([n_a > 0, n_a < 1, n_b > 0, n_b < 1], axis=0)

    n_a_m = n_a[valid_inter]
    n_b_m = n_b[valid_inter]
    all_coefs = np.concatenate([[n_b_m], [n_a_m]], axis=0).T.ravel()

    indices_m2 = indices_m[valid_inter]
    i_ravel = indices_m2.ravel()

    inters = inter[valid_inter]
    new_idx = np.repeat(np.arange(len(inters)) + len(np_verts), 2)

    new_edges = []
    for i in range(len(edges)):
        intersect_mask = i_ravel == i
        coef = all_coefs[intersect_mask]
        n_i = new_idx[intersect_mask]
        iid = np.argsort(coef)
        n_i_sorted = n_i[iid]
        new_eds = np.concatenate([[np_edges[i, 0]],
                                  np.repeat(n_i_sorted, 2),
                                  [np_edges[i, 1]]]).reshape(-1, 2)
        new_edges.append(new_eds)

    return np.concatenate([np_verts, inters]).tolist(), np.concatenate(new_edges).tolist()

def intersect_edges_2d_np_big(verts, edges, epsilon, only_touching=True):
    '''Brute force Numpy implementation of edges intersections. Avoids to do to it all at once to prevent stack overflow'''
    np_verts = verts if isinstance(verts, np.ndarray) else np.array(verts)
    np_edges = edges if isinstance(edges, np.ndarray) else np.array(edges)
    n = len(edges)
    n_as, n_bs, indices_m2s, inters_s = [], [], [], []
    for i in range(n-1):

        np_j = np.arange(i+1, n, dtype=np.int32)
        edgs_i = np_edges[i]
        eds_j = np_edges[np_j]
        mask = np.invert(np.any([edgs_i[np.newaxis, 0] == eds_j[:, 0],
                                 edgs_i[np.newaxis, 0] == eds_j[:, 1],
                                 edgs_i[np.newaxis, 1] == eds_j[:, 0],
                                 edgs_i[np.newaxis, 1] == eds_j[:, 1]],
                                axis=0))
        eds_j2 = eds_j[mask]
        indices_j_m = np_j[mask]
        seg_j = np_verts[eds_j2]
        direc_b = seg_j[:, 1] - seg_j[:, 0]


        np_i = np.full(len(indices_j_m), i, dtype=np.int32)
        indices_m = np.stack((np_i, indices_j_m), axis=-1)

        seg_a = np_verts[edgs_i]
        direc_a = seg_a[1, :]- seg_a[0, :]
        perp_direc_a = perp_single(direc_a)

        dp = seg_a[np.newaxis, 0, :] - seg_j[:, 0]

        denom_a = np_dot(perp_direc_a[np.newaxis, :], direc_b)
        perp_direc_b = perp(direc_b)
        denom_b = np_dot(perp_direc_b, direc_a[np.newaxis, :])
        parallel_mask = np.all([denom_a != 0, denom_b != 0], axis=0)

        dp = dp[parallel_mask]
        denom_a = denom_a[parallel_mask]
        direc_b = direc_b[parallel_mask]
        num_a = np_dot(perp_direc_a[np.newaxis, :], dp)

        n_a = (num_a / denom_a.astype(float))
        perp_direc_b = perp_direc_b[parallel_mask]
        denom_b = denom_b[parallel_mask]
        num_b = np_dot(perp_direc_b, -dp)
        n_b = (num_b / denom_b.astype(float))
        inter = n_a[:, np.newaxis] * direc_b + seg_j[parallel_mask, 0]
        if only_touching:
            valid_inter = np.all([n_a > -epsilon, n_a < 1+epsilon, n_b > -epsilon, n_b < 1+epsilon], axis=0)
        else:
            valid_inter = np.all([n_a > 0, n_a < 1, n_b > 0, n_b < 1], axis=0)
        n_a_m = n_a[valid_inter]
        n_b_m = n_b[valid_inter]
        indices_m2 = indices_m[parallel_mask][valid_inter]
        inters = inter[valid_inter]
        n_as.append(n_a_m)
        n_bs.append(n_b_m)
        indices_m2s.append(indices_m2)
        inters_s.append(inters)

    c_n_as = np.concatenate(n_as)
    c_n_bs = np.concatenate(n_bs)
    c_indices_m2s = np.concatenate(indices_m2s)
    c_inters_s = np.concatenate(inters_s)
    all_coefs = np.concatenate([[c_n_bs], [c_n_as]], axis=0).T.ravel()
    i_ravel = c_indices_m2s.ravel()

    new_idx = np.repeat(np.arange(len(c_inters_s)) + len(np_verts), 2)

    new_edges = []
    for i in range(len(edges)):
        intersect_mask = i_ravel == i
        coef = all_coefs[intersect_mask]
        n_i = new_idx[intersect_mask]
        iid = np.argsort(coef)
        n_i_sorted = n_i[iid]
        new_eds = np.concatenate([[np_edges[i, 0]],
                                  np.repeat(n_i_sorted, 2),
                                  [np_edges[i, 1]]]).reshape(-1, 2)
        new_edges.append(new_eds)

    return np.concatenate([np_verts, c_inters_s]).tolist(), np.concatenate(new_edges).tolist()


def remove_doubles_from_edgenet(verts_in, edges_in, distance):
    bm = bmesh_from_pydata(verts_in, edges_in, [])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=distance)
    verts_out = [v.co.to_tuple() for v in bm.verts]
    edges_out = [[j.index for j in i.verts] for i in bm.edges]

    return verts_out, edges_out
