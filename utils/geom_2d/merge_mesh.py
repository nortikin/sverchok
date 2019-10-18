# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


def from_sv_faces(sv_verts, sv_faces, accuracy=1e-6):
    """
    Merge Sverchok mesh objects into one mesh with finding intersections and all
    Overlapping of edges and points are supported
    Also polygons can have holes
    :param sv_verts: [[[x1, y1, z1], [x2, y2, z2], ...]-obj_1, [[x1, y1, z1], [x2, y2, z2], ...]-obj_2, ..., obj_n]
    :param sv_faces: [[[i1, i2, .., in], face2, .., face n]-obj_1, [[i1, .., in], face2, .., face n]-obj_2, .., obj_n]
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: vertices in SV format, face in SV format
    """
    mesh = DCELMesh()
    [mesh.from_sv_faces(vs, fs) for vs, fs in zip(sv_verts, sv_faces)]
    find_intersections(half_edges, accuracy)
    half_edges = [he for he in half_edges if he.edge]  # ignore half edges without "users"
    sv_faces = build_faces_list(half_edges, accuracy)
    new_half_edges = []
    for face in sv_faces:
        if face.outer and face.inners:
            new_half_edges.extend(make_monotone(face, accuracy))
    if new_half_edges:
        half_edges.extend(new_half_edges)
        sv_faces = rebuild_face_list(half_edges)
    return to_sv_mesh_from_faces(half_edges, sv_faces)


def from_sv_edges(vert_objects, face_objects, accuracy=1e-5):
    """
    Merge Sverchok mesh objects determined by edges into one mesh with finding intersections and all
    Overlapping of edges and points are supported
    Also polygons can have holes
    :param vert_objects: [[[x1, y1, z1], [x2, y2, z2], ...]-obj_1, [[x1, y1, z1], [x2, y2, z2], ...]-obj_2, ..., obj_n]
    :param face_objects: [[[i1, i2, .., in], face2, .., face n]-obj_1, [[ .., in], face2, .., face n]-obj_2, .., obj_n]
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: vertices in SV format, face in SV format
    """
    pass