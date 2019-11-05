# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import Set, List

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
    mesh = DCELMesh(accuracy=accuracy)
    mesh.from_sv_edges(sv_verts, sv_edges)
    if do_intersect:
        find_intersections(mesh, accuracy)
    mesh.generate_faces_from_hedges()
    if not fill_holes:
        del_holes(mesh)
    monotone_faces_with_holes(mesh)
    return mesh.to_sv_mesh(edges=False, del_face_flag='del')


def merge_mesh_light(sv_verts, sv_faces, face_overlapping=False, accuracy=1e-5):
    """
    Rebuild faces and vertices with taking in account intersections and holes
    Also produce indexes of old faces in which new faces are
    :param sv_verts: list of SV points
    :param sv_faces: list of SV faces
    :param face_overlapping: add index mask (new face : index old face) to the output of the function if True
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: SV vertices, SV faces, index face mask (optionally)
    """
    mesh = DCELMesh(accuracy=accuracy)
    mesh.from_sv_faces(sv_verts, sv_faces, face_data={'index': list(range(len(sv_faces)))})
    find_intersections(mesh, accuracy, face_overlapping=True)  # anyway should be true
    mesh.generate_faces_from_hedges()
    mark_not_in_faces(mesh)
    monotone_faces_with_holes(mesh)
    if face_overlapping:
        return list(mesh.to_sv_mesh(edges=False, del_face_flag='del')) + [get_min_face_indexes(mesh)]
    else:
        return mesh.to_sv_mesh(edges=False, del_face_flag='del')


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


def del_holes(dcel_mesh):

    del_flag = 'del'

    def del_hole(face):
        used_del = set()  # type: Set['Face']
        stack_del = [hedge.twin for hedge in face.inners]
        while stack_del:
            next_del_face = stack_del.pop().face
            if next_del_face in used_del:
                continue
            if id(next_del_face) == id(face):
                continue
            used_del.add(next_del_face)
            next_del_face.flags.add(del_flag)
            for loop_del_hedge in next_del_face.outer.loop_hedges:
                stack_del.append(loop_del_hedge.twin)
            if next_del_face.inners:
                add_hole(next_del_face)

    def add_hole(face):
        used = set()  # type: Set['Face']
        stack = [hedge.twin for hedge in face.inners]
        while stack:
            next_face = stack.pop().face
            if next_face in used:
                continue
            if id(face) == id(next_face):
                continue
            used.add(next_face)
            for loop_hedge in next_face.outer.loop_hedges:
                stack.append(loop_hedge.twin)
            if next_face.inners:
                del_hole(next_face)

    add_hole(dcel_mesh.unbounded)


def get_min_face_indexes(dcel_mesh, del_flag='del'):
    # returns list index per face where index is index of boundary face with grater index
    # assume that order of created face is the same to order of mesh.faces list
    return [min([in_face.sv_data['index'] for in_face in face.outer.in_faces])
            for face in dcel_mesh.faces if del_flag not in face.flags]


def mark_not_in_faces(mesh, del_flag='del'):
    # mark faces which are not in any faces as for deleting
    for face in mesh.faces:
        if not face.outer.in_faces:
            face.flags.add(del_flag)
