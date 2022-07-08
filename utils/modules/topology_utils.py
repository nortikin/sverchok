# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import collections

def separate_loose(ve, pe):
    # verts, poly_edges = [], []

    # build links
    node_links = {}
    for edge_face in pe:
        for i in edge_face:
            if i not in node_links:
                node_links[i] = set()
            node_links[i].update(edge_face)

    nodes = set(node_links.keys())
    n = nodes.pop()
    node_set_list = [set([n])]
    node_stack = collections.deque()
    node_stack_append = node_stack.append
    node_stack_pop = node_stack.pop
    node_set = node_set_list[-1]

    # find separate sets
    while nodes:
        for node in node_links[n]:
            if node not in node_set:
                node_stack_append(node)
        if not node_stack:  # new mesh part
            n = nodes.pop()
            node_set_list.append(set([n]))
            node_set = node_set_list[-1]
        else:
            while node_stack and n in node_set:
                n = node_stack_pop()
            nodes.discard(n)
            node_set.add(n)

    # create new meshes from sets, new_pe is the slow line.
    verts = []
    poly_edges = []
    if len(node_set_list) > 1:

        for node_set in node_set_list:
            mesh_index = sorted(node_set)
            vert_dict = {j: i for i, j in enumerate(mesh_index)}
            new_vert = [ve[i] for i in mesh_index]
            new_pe = [[vert_dict[n] for n in fe]
                      for fe in pe
                      if fe[0] in node_set]
            
            verts.append(new_vert)
            poly_edges.append(new_pe)
        return verts, poly_edges

    elif node_set_list:  # no reprocessing needed
        return [ve], [pe]