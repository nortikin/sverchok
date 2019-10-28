# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from .intersections import Point as InterPoint, HalfEdge as InterHalfEdge, DCELMesh as InterDCELMesh, find_intersections
from .make_monotone import Point as MonPoint, HalfEdge as MonHalfEdge, DCELMesh as MonDCELMesh, \
                           monotone_faces_with_holes

from .dcel_debugger import Debugger


def edges_to_faces(sv_verts, sv_edges, do_intersect=True, fill_holes=True, accuracy=1e-5):
    """
    Fill faces of Sverchok mesh determined by edges
    Optionally can be found self intersections and created holes
    Overlapping of edges and points are supported
    :param sv_verts: list of SV points
    :param sv_edges: list of SV edges
    :param do_intersect: if True self intersections will be taken in account
    :param fill_holes: if False can produce holes in case if
     there are such faces incise another face without intersections with one
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: list of SV points, list of SV faces
    """
    Debugger.clear(False)
    mesh = DCELMesh(accuracy=accuracy)
    mesh.from_sv_edges(sv_verts, sv_edges)
    if do_intersect:
        find_intersections(mesh, accuracy)
    mesh.generate_faces_from_hedges()
    Debugger.add_hedges(mesh.hedges)
    Debugger.print([p.hedge for p in mesh.points], 'phedge')
    monotone_faces_with_holes(mesh)
    return mesh.to_sv_mesh(edges=False)


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


# #############################################################################
# ###################________merge mesh functions_________#####################
# #############################################################################


class Point(InterPoint, MonPoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class HalfEdge(InterHalfEdge, MonHalfEdge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DCELMesh(InterDCELMesh, MonDCELMesh):
    Point = Point
    HalfEdge = HalfEdge
