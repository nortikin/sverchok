# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import itertools
import numpy as np

def mesh_from_pydata(mesh, verts, edges, faces):
    mesh.clear_geometry()
    flat_verts = list(itertools.chain.from_iterable(verts))
    mesh.vertices.add(len(verts))
    mesh.vertices.foreach_set('co', flat_verts)

    if edges:
        flat_edges = list(itertools.chain.from_iterable(edges))
        mesh.edges.add(len(edges))
        mesh.edges.foreach_set("vertices", flat_edges)

    if faces:
        flat_faces = list(itertools.chain.from_iterable(faces))
        vertex_index = np.array(flat_faces, dtype=np.int32)

        loop_lengths = [len(f) for f in faces]
        loop_start_indices = np.cumsum([0] + loop_lengths[:-1])
        loop_start = np.array(loop_start_indices, dtype=np.int32)
        loop_total = np.array(loop_lengths, dtype=np.int32)

        num_vertex_indices = vertex_index.shape[0]
        num_loops = loop_start.shape[0]

        mesh.loops.add(num_vertex_indices)
        mesh.loops.foreach_set("vertex_index", vertex_index)

        mesh.polygons.add(num_loops)
        mesh.polygons.foreach_set("loop_start", loop_start)
        mesh.polygons.foreach_set("loop_total", loop_total)

    mesh.update()
    mesh.validate()
