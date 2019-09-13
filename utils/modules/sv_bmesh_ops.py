# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bmesh

def recursive_search(found_set, current_vertex):
    """
    helper function for "find_islands_treemap"
    : finds all connected vertex indices, given an input set and vertex of bm.
    """

    for polygon in current_vertex.link_faces:
        for vert in polygon.verts:
            if vert.index not in found_set:
                found_set.add(vert.index)
                found_items = recursive_search(found_set, vert)
                if found_items:
                    found_set.update(found_items)
                    
    return found_set

def vertex_emitter(bm):
    """
    helper function for "find_island_treemap"
    : turns a bm into an iterable of verts, to use next with.
    """
    for v in bm.verts:
        yield v

def find_islands_treemap(bm):
    """
    importable function to obtain all islands in a given bmesh.
    : returns a dict of island integers and the vertex indices associated with that island.
    """
    
    island_index = 0
    islands = {}

    vertex_iterator = vertex_emitter(bm)
    vertex_0 = next(vertex_iterator)
    islands[island_index] = recursive_search({0}, vertex_0)
        
    for vertex in vertex_iterator:
        if vertex.index not in islands[island_index]:
            island_index += 1
            islands[island_index] = recursive_search({vertex.index}, vertex)

    return islands

# usage
# island_dict = find_islands_treemap(bm)
# returns a dict of islands and associated vertices
