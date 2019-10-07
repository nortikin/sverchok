# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import kdtree
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
    edges = [[]]
    edge_set = set()
    seen = set()
    seen_end = set()
    r = radius

    idx = start_index

    for id in range(len(verts)):

        n_list = kd.find_range(verts[idx], r[idx])
        seen_end.add(idx)
        found = False
        for co, index, dist in n_list:
            if (index == idx) or (index in seen_end):
                continue
            seen_end.add(index)
            edge_set.add(tuple(sorted([idx, index])))
            idx = index
            found = True
            break
        if not found and id <  len(verts):
            for id_new in range(len(verts)):
                if id_new not in seen_end:
                    idx = id_new
                    break
    if cycle:
        edge_set.add(tuple(sorted([start_index, idx])))

    result.append(list(edge_set))


def kdt_closest_edges(verts, socket_inputs, egdes_output):
    '''Join verts pairs by defining distance range and number of connections'''
    mindist, maxdist, maxNum, skip = socket_inputs

    # make kdtree
    kd = create_kdt(verts)

    # set minimum values
    maxNum = max(maxNum, 1)
    skip = max(skip, 0)

    # makes edges
    e = set()

    for i, vtx in enumerate(verts):
        num_edges = 0

        # this always returns closest first followed by next closest, etc.
        #              co  index  dist
        for edge_idx, (_, index, dist) in enumerate(kd.find_range(vtx, abs(maxdist))):

            if skip > 0:
                if edge_idx < skip:
                    continue

            if (dist <= abs(mindist)) or (i == index):
                continue

            edge = tuple(sorted([i, index]))
            if not edge in e:
                e.add(edge)
                num_edges += 1

            if num_edges == maxNum:
                break

    egdes_output.sv_set([list(e)])
