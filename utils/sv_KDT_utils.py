# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import kdtree
import numpy as np
from sverchok.dependencies import scipy

from sverchok.data_structure import match_long_repeat as mlr

# documentation/blender_python_api_2_70_release/mathutils.kdtree.html
def create_kdt(verts):
    '''Basic kdt setup'''
    size = len(verts)
    kd = kdtree.KDTree(size)
    for i, xyz in enumerate(verts):
        kd.insert(xyz, i)
    kd.balance()

    return kd


def kdt_closest_verts_range(verts, v_find, dists, out):
    '''Find vertices in desired distance'''
    kd = create_kdt(verts)
    out.extend([kd.find_range(vert, dist) for vert, dist in zip(*mlr([v_find, dists]))])


def kdt_closest_verts_find_n(verts, v_find, nums, out):
    '''Find  the N closest vertices ordered by distance'''
    kd = create_kdt(verts)
    out.extend([kd.find_n(vert, num) for vert, num in zip(*mlr([v_find, nums]))])

def kdt_closest_path(verts, radius, start_index, result, cycle):
    '''Creates path joining each vertice with the closest free neighbor'''
    kd = create_kdt(verts)
    edge_set = set()
    free_ids = set(range(len(verts)))
    r = radius

    idx = start_index
    free_ids.remove(idx)
    for id in range(len(verts)):

        n_list = kd.find_range(verts[idx], r[idx])

        found = False
        for _, index, _ in n_list:
            if (index == idx) or (index not in free_ids):
                continue
            free_ids.remove(index)
            edge_set.add(tuple(sorted([idx, index])))
            idx = index
            found = True
            break

        if not found:
            for id_new in free_ids:
                idx = id_new
                free_ids.remove(idx)
                break
    if cycle:
        edge_set.add(tuple(sorted([start_index, idx])))

    result.append(list(edge_set))

def kdt_closest_edges(verts, socket_inputs):
    '''Join verts pairs by defining distance range and number of connections'''
    mindist, maxdist, maxNum, skip = socket_inputs

    # make kdtree
    kd = create_kdt(verts)

    # set minimum values
    maxNum = max(maxNum, 1)
    skip = max(skip, 0)

    # makes edges
    edges = set()
    edges_add = edges.add
    max_dist = abs(maxdist)
    min_dist = abs(mindist)
    for i, vtx in enumerate(verts):
        num_edges = 0

        # this always returns closest first followed by next closest, etc.
        #              co  index  dist
        for edge_idx, (_, index, dist) in enumerate(kd.find_range(vtx, max_dist)):

            if skip > 0:
                if edge_idx < skip:
                    continue

            if (dist <= min_dist) or (i == index):
                continue

            edge = tuple(sorted([i, index]))
            if not edge in edges:
                edges_add(edge)
                num_edges += 1

            if num_edges == maxNum:
                break

    return list(edges)


def scipy_kdt_closest_edges_fast(vs, min_dist, max_dist):
    new_tree = scipy.spatial.cKDTree
    kd_tree = new_tree(np.array(vs))
    indexes_max = kd_tree.query_pairs(r=max_dist)
    indexes_min = kd_tree.query_pairs(r=min_dist)
    return list(indexes_max ^ indexes_min)

def scipy_kdt_closest_max_queried(vs, min_dist, max_dist, maxNum, skip):
    new_tree = scipy.spatial.cKDTree
    kd_tree = new_tree(np.array(vs))
    skip_f = max(skip-1,0)
    dist, idx = kd_tree.query(np.array(vs), distance_upper_bound=max_dist, k=maxNum+1+skip_f )
    all_edges = np.zeros([maxNum * len(vs), 2], dtype=np.int32)
    start = 0
    for i in range(1+skip_f, maxNum+1+skip_f):
        mask = np.all((max_dist > dist[:, i], dist[:, i] > min_dist), axis=0)
        orig = idx[mask, 0]
        end = start + len(orig)
        all_edges[start:end, 0] = orig
        all_edges[start:end, 1] = idx[mask, i]
        start = end

    if start:
        return np.unique(np.sort(all_edges[:start], axis=1), axis=0).tolist()
    return []

def scipy_kdt_closest_edges_no_skip(vs, min_dist, max_dist, maxNum, skip):
    new_tree = scipy.spatial.cKDTree
    np_vs = np.array(vs)
    kd_tree = new_tree(np_vs)
    # set minimum values
    maxNum = max(maxNum, 1)
    skip = max(skip, 0)

    # makes edges
    e = set()
    query = kd_tree.query_ball_point(np_vs, max_dist)
    for i, (rel, vtx) in enumerate(zip(query, np_vs)):
        if len(rel) < 2:
            continue

        num_edges = 0
        for idx in rel:
            if idx == i:
                continue
            dist = np.linalg.norm(vtx-np_vs[idx])
            if dist <= abs(min_dist):
                continue
            edge = tuple(sorted([i, idx]))

            if not edge in e:
                e.add(edge)
                num_edges += 1

            if num_edges == maxNum:
                break

    return list(e)
