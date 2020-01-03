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


def merge_mesh_light(sv_verts, sv_faces, face_overlapping=False, is_overlap_number=False, accuracy=1e-5):
    """
    Rebuild faces and vertices with taking in account intersections and holes
    Also produce indexes of old faces in which new faces are
    :param sv_verts: list of SV points
    :param sv_faces: list of SV faces
    :param face_overlapping: add index mask (new face : index old face) to the output of the function if True
    :param is_overlap_number: returns information about number of overlapping face by another faces
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: list of SV vertices, list of SV faces, index face mask (optionally), list of overlap_number (optionally)
    """
    mesh = DCELMesh(accuracy=accuracy)
    mesh.from_sv_faces(sv_verts, sv_faces, face_data={'index': list(range(len(sv_faces)))})
    find_intersections(mesh, accuracy, face_overlapping=True)  # anyway should be true
    mesh.generate_faces_from_hedges()
    mark_not_in_faces(mesh)
    monotone_faces_with_holes(mesh)
    face_indexes = [get_min_face_indexes(mesh, 'index')] if face_overlapping else [[]]
    overlap_number = [get_number_of_overlapping_mask(mesh)] if is_overlap_number else [[]]
    return list(mesh.to_sv_mesh(edges=False, del_face_flag='del')) + face_indexes + overlap_number


def crop_mesh(sv_verts, sv_faces, sv_verts_crop, sv_faces_crop, mode='inner', accuracy=1e-5):
    """
    The function takes one SV mesh determined by polygons and crop it by polygons of another SV mesh.
    It can as creates holes in mesh so fit mesh into boundary of another mesh
    :param sv_verts: list of SV points
    :param sv_faces: list of SV faces
    :param sv_verts_crop: list of SV points
    :param sv_faces_crop: list of SV faces
    :param mode: inner or outer, switch between holes creation and feting into mesh
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: list of SV vertices, list of SV faces, index face mask (optionally)
    """
    mesh = DCELMesh(accuracy=accuracy)
    mesh.from_sv_faces(sv_verts, sv_faces, face_flag=['base' for _ in range(len(sv_faces))],
                       face_data={'index': list(range(len(sv_faces)))})
    mesh.from_sv_faces(sv_verts_crop, sv_faces_crop, face_flag=['crop' for _ in range(len(sv_faces_crop))])
    find_intersections(mesh, accuracy, face_overlapping=True)  # anyway should be true
    mesh.generate_faces_from_hedges()
    mark_not_in_faces(mesh)
    mark_crop_faces(mesh, mode)
    monotone_faces_with_holes(mesh)
    return list(mesh.to_sv_mesh(edges=False, del_face_flag='del')) + [get_min_face_indexes(mesh, 'index')]


def crop_edges(sv_verts, sv_edges, sv_verts_crop, sv_faces_crop, mode='inner', accuracy=1e-5):
    """
    The function takes one SV mesh determined by edges and crop it by polygons of another SV mesh determined by faces.
    :param sv_verts: list of SV points
    :param sv_edges: list of SV edges
    :param sv_verts_crop: list of SV points
    :param sv_faces_crop: list of SV faces
    :param mode: inner or outer, switch between holes creation and feting into mesh
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: list of SV vertices, list of SV faces
    """
    mesh = DCELMesh(accuracy=accuracy)
    mesh.from_sv_edges(sv_verts, sv_edges)
    mesh.from_sv_faces(sv_verts_crop, sv_faces_crop)
    find_intersections(mesh, accuracy, face_overlapping=True)
    [hedge.flags.add('del') for hedge in mesh.hedges if hedge.face]
    if mode == 'inner':
        [hedge.flags.add('del') for hedge in mesh.hedges if not hedge.in_faces]
    else:
        [hedge.flags.add('del') for hedge in mesh.hedges if hedge.in_faces]
    return mesh.to_sv_mesh(faces=False, del_edge_flag='del')


def merge_mesh(sv_verts_a, sv_faces_a, sv_verts_b, sv_faces_b, is_mask=True, is_index=False, accuracy=1e-6):
    """
    Merge two Sverchok mesh objects into one mesh with finding intersections and all
    Overlapping of edges and points are supported
    Also polygons can have holes
    :param sv_verts_a: list of SV points
    :param sv_faces_a: list of SV faces
    :param sv_verts_b: list of SV points
    :param sv_faces_b: list of SV faces
    :param accuracy: two floats figures are equal if their difference is lower then accuracy value, float
    :return: vertices in SV format, face in SV format
    """
    mesh = DCELMesh()
    mesh.from_sv_faces(sv_verts_a, sv_faces_a, face_flag=['mesh a' for _ in range(len(sv_faces_a))],
                       face_data={'index': list(range(len(sv_faces_a)))})
    mesh.from_sv_faces(sv_verts_b, sv_faces_b, face_flag=['mesh b' for _ in range(len(sv_faces_b))],
                       face_data={'index': list(range(len(sv_faces_b)))})
    find_intersections(mesh, accuracy, face_overlapping=True)
    mesh.generate_faces_from_hedges()
    mark_not_in_faces(mesh)
    monotone_faces_with_holes(mesh)

    if is_mask and is_index:
        return list(mesh.to_sv_mesh(edges=False, del_face_flag='del')) + [get_face_mask_by_flag(mesh, 'mesh a')] + \
               [get_face_mask_by_flag(mesh, 'mesh b')] + [get_min_face_indexes(mesh, 'index', 'mesh a')] + \
               [get_face_mask_by_flag(mesh, 'index', 'mesh b')]
    elif is_mask:
        return list(mesh.to_sv_mesh(edges=False, del_face_flag='del')) + [get_face_mask_by_flag(mesh, 'mesh a')] + \
               [get_face_mask_by_flag(mesh, 'mesh b')]
    elif is_index:
        return list(mesh.to_sv_mesh(edges=False, del_face_flag='del')) + \
               [get_min_face_indexes(mesh, 'index', 'mesh a')] + [get_face_mask_by_flag(mesh, 'index', 'mesh b')]
    else:
        return mesh.to_sv_mesh(edges=False, del_face_flag='del')


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


def get_min_face_indexes(dcel_mesh, index_flag, filter_flag=None, del_flag='del'):
    # returns list index per face where index is index of boundary face with lower index
    # assume that order of created face is the same to order of mesh.faces list
    # if flag is given the function takes in account faces with such flag
    # if there is no faces with such flag at all -1 index is added into output mask
    out = []
    if not filter_flag:
        for face in dcel_mesh.faces:
            if del_flag in face.flags:
                continue
            out.append(min([in_face.sv_data[index_flag] for in_face in face.outer.in_faces if
                            index_flag in in_face.sv_data]))
    else:
        for face in dcel_mesh.faces:
            if del_flag in face.flags:
                continue
            indexes = []
            for in_face in face.outer.in_faces:
                if filter_flag in in_face.flags:
                    indexes.append(in_face.sv_data[index_flag])
            if indexes:
                out.append(min(indexes))
            else:
                out.append(-1)
    return out


def mark_not_in_faces(mesh, del_flag='del'):
    # mark faces which are not in any faces as for deleting
    for face in mesh.faces:
        if not face.outer.in_faces:
            face.flags.add(del_flag)


def mark_crop_faces(mesh, mode, crop_name='crop', del_flag='del'):
    # mark face for deleting if they are in faces with flag crop_name or not
    for face in mesh.faces:
        inside_base = False
        inside_crop = False
        for in_face in face.outer.in_faces:
            if crop_name in in_face.flags:
                inside_crop = True
            else:
                inside_base = True
        if mode == 'inner':
            if not inside_base or not inside_crop:
                face.flags.add(del_flag)
        else:
            if inside_crop:
                face.flags.add(del_flag)


def get_face_mask_by_flag(mesh, flag, del_flag='del'):
    # returns mask of faces where 1 mean that face has given flag
    out = [0 for face in mesh.faces if del_flag not in face.flags]
    for i, face in enumerate(mesh.faces):
        if del_flag in face.flags:
            continue
        for in_face in face.outer.in_faces:
            if flag in in_face.flags:
                out[i] = 1
                break
    return out


def get_number_of_overlapping_mask(mesh, del_flag='del'):
    return [len(face.outer.in_faces) - 1 for face in mesh.faces if del_flag not in face.flags]
