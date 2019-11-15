# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from .dcel import HalfEdge as HalfEdge_template, DCELMesh as DCELMesh_template
from .lin_alg import is_ccw_polygon

from .dcel_debugger import Debugger


def dissolve_faces(sv_verts, sv_faces, face_mask, is_mask=False, is_index=False):
    Debugger.clear(False)
    mesh = DCELMesh()
    mesh.from_sv_faces(sv_verts, sv_faces, face_flag=['dissolve' if mark else None for mark in face_mask],
                       face_data={'index': list(range(len(sv_faces)))})
    dissolve_faces_add(mesh, 'dissolve')
    if is_mask and is_index:
        return list(mesh.to_sv_mesh(edges=False)) + [[int('dissolve' in face.flags) for face in mesh.faces]] + \
               [[face.sv_data['index'] for face in mesh.faces]]
    elif is_mask:
        return list(mesh.to_sv_mesh(edges=False)) + [[int('dissolve' in face.flags) for face in mesh.faces]]
    elif is_index:
        return list(mesh.to_sv_mesh(edges=False)) + [[face.sv_data['index'] for face in mesh.faces]]
    else:
        return mesh.to_sv_mesh(edges=False)


# #############################################################################
# ###################________dissolve mesh functions______#####################
# #############################################################################
# Implementation of  this algorithm is not even finished. I will leave it in this condition for a while.
# It intend to be faster but solving of corner cases when the algorithm produce holes is not obvious.


class HalfEdge(HalfEdge_template):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_next = None
        self.new_last = None

    @property
    def new_loop_hedges(self):
        # returns hedges bounding face
        if not self.mesh:
            raise AttributeError("This method doesn't work with hedges({}) without link to a mesh."
                                 "Besides, mesh object should have proper number of half edges "
                                 "in hedges list".format(self))
        yield self
        next_edge = self.next
        counter = 0
        while id(next_edge) != id(self):
            yield next_edge
            try:
                next_edge = next_edge.next
            except AttributeError:
                raise AttributeError(' Some of half edges has incomplete data (does not have link to next half edge)')
            counter += 1
            if counter > len(self.mesh.hedges):
                raise RecursionError('Hedge - {} does not have a loop'.format(self))


class DCELMesh(DCELMesh_template):
    HalfEdge=HalfEdge


def dissolve_faces_with_flag(mesh, flag):
    # mark unused hedges and faces
    x, y = 0, 1
    boundary_hedges = []
    un_used_hedges = set()
    for face in mesh.faces:
        if flag in face.flags:
            for hedge in face.outer.loop_hedges:
                if flag in hedge.twin.face.flags:
                    un_used_hedges.add(hedge)
                else:
                    boundary_hedges.append(hedge)
    # create new faces
    used = set()
    inner_faces = []
    for hedge in boundary_hedges:
        if hedge in used:
            continue
        last_hedge = hedge
        for loop_hedge in walk_boundary_loop(hedge, flag):
            used.add(loop_hedge)
            last_hedge.new_last = loop_hedge
            loop_hedge.new_next = last_hedge
            last_hedge = loop_hedge
        min_hedge = min([hedge for hedge in hedge.new_loop_hedges],
                        key=lambda he: (he.origin.co[x], he.origin.co[y]))
        _is_ccw = is_ccw_polygon(most_lefts=[min_hedge.last.origin.co, min_hedge.origin.co,
                                             min_hedge.next.origin.co], accuracy=mesh.accuracy)
        if _is_ccw:
            face = mesh.Face(mesh)
            face.outer = min_hedge
            face.sv_data = dict(min_hedge.face.sv_data)
            for loop_hedge in hedge.new_loop_hedges:
                loop_hedge.face = face
        else:
            face = mesh.Face(mesh)
            face.inners.append(min_hedge)
            for loop_hedge in hedge.new_loop_hedges:
                loop_hedge.face = face
            inner_faces.append(face)

    # assign inner component to found faces
    for inner_face in inner_faces:
        for hedge in walk_left(inner_face.inners[0]):
            if flag in hedge.face.flags:
                continue



        used.add(hedge)
        face = mesh.Face(mesh)
        new_faces.append(face)
        face.outer = hedge
        face.sv_data = dict(hedge.face.sv_data)  # new face get all sv data related with first edge in loop
        face.flags = set(hedge.face.flags)
        hedge.face = face
        for ccw_hedge in hedge.ccw_hedges:
            if id(ccw_hedge) != id(hedge) and flag not in ccw_hedge.face.flags:
                break
        last_hedge = ccw_hedge.twin
        hedge.last = last_hedge
        last_hedge.next = hedge
        used.add(last_hedge)
        last_hedge.face = face
        count = 0
        current_hedge = last_hedge
        while id(current_hedge) != id(hedge):
            for ccw_hedge in current_hedge.ccw_hedges:
                if id(ccw_hedge) != id(hedge) and flag not in ccw_hedge.face.flags:
                    break
            last_hedge = ccw_hedge.twin
            used.add(last_hedge)
            last_hedge.face = face
            current_hedge.last = last_hedge
            last_hedge.next = current_hedge
            current_hedge = last_hedge
            count += 1
            if count > len(mesh.hedges):
                raise RecursionError("Dissolve face algorithm can't built a loop from hedge - {}".format(hedge))
    # update faces
    mesh.faces = [face for face in mesh.faces if flag not in face.flags]
    mesh.faces.extend(new_faces)
    # update hedges
    mesh.hedges = [hedge for hedge in mesh.hedges if hedge not in un_used_hedges]
    # todo how to rebuilt points list


def is_closer_left(slop1, slop2):
    slop1 = slop1 if slop1 <= 2 else 2 - slop1 % 2 if slop1 != 4.0 else 0
    slop2 = slop2 if slop2 <= 2 else 2 - slop2 % 2 if slop2 != 4.0 else 0
    return True if slop1 < slop2 else False


def walk_left(hedge):
    # return next hedge closest to -X direction
    count = 0
    start_hedge = hedge
    while count <= len(hedge.mesh.hesges):
        next_candidate = None
        for ccw_hedge in start_hedge.twin.ccw_hedges:
            if id(ccw_hedge) == id(start_hedge.twin):
                # avoid going in back direction
                continue
            if not next_candidate:
                # any candidate is okay
                next_candidate = ccw_hedge
                continue
            if is_closer_left(ccw_hedge.slop, next_candidate.slop):
                # next candidate should be closer to -X direction
                next_candidate = ccw_hedge
            else:
                # according that half edges are sorted in ccw order, best candidate already has been found
                break
        if not next_candidate:
            raise ValueError('Looks like the end of tail is reached, what to do next?')
        yield next_candidate
        start_hedge = next_candidate
        count += 1
    raise RecursionError('It looks like you forget to exit from left walk')


def walk_boundary_loop(hedge, bound_flag):
    # in back direction
    # yield hedge
    for ccw_hedge in hedge.ccw_hedges:
        if id(ccw_hedge) != id(hedge) and bound_flag not in ccw_hedge.face.flags:
            break
    current_hedge = ccw_hedge.twin
    yield current_hedge
    count = 0
    while id(current_hedge) != id(hedge):
        for ccw_hedge in current_hedge.ccw_hedges:
            if id(ccw_hedge) != id(hedge) and bound_flag not in ccw_hedge.face.flags:
                break
        current_hedge = ccw_hedge.twin
        yield current_hedge
        count += 1
        if count > len(hedge.mesh.hedges):
            raise RecursionError("Dissolve face algorithm can't built a loop from hedge - {}".format(hedge))


def get_leftmost_hedge_in_point(hedge, flag):
    # can return None if such hedge does not exist
    # given hedge should be boundary half edge of dissolving faces
    dissolved_hedge = None
    for ccw_hedge in hedge.ccw_hedges:
        if id(ccw_hedge) == id(hedge):
            # avoid going in back direction
            continue
        if flag not in ccw_hedge.face.flags:
            # that means that all dissolved half edges was looked up
            break
        if not dissolved_hedge:
            # any candidate is okay
            dissolved_hedge = ccw_hedge
            continue
        if is_closer_left(ccw_hedge.slop, dissolved_hedge.slop):
            # next candidate should be closer to -X direction
            dissolved_hedge = ccw_hedge
        else:
            # according that half edges are sorted in ccw order, best candidate already has been found
            break
    return dissolved_hedge


def get_leftmost_dissolved_hedge(left_loop_hedge, flag):
    # left_loop_hedge - half edge with origin which is leftmost point of a loop
    dis_hedge = get_leftmost_hedge_in_point(left_loop_hedge, flag)
    if dis_hedge:
        return dis_hedge

    used = set()
    next_two_candidates = [left_loop_hedge.new_next, left_loop_hedge.new_last]
    while next_two_candidates:
        low_hedge = next_two_candidates.pop()
        used.add(low_hedge)
        low_candidate = get_leftmost_hedge_in_point(low_hedge, flag)
        up_hedge = next_two_candidates.pop()
        used.add(up_hedge)
        up_candidate = get_leftmost_hedge_in_point(up_hedge, flag)

        if low_candidate and up_candidate:
            return low_candidate if is_closer_left(low_candidate, up_candidate) else up_candidate
        elif low_candidate:
            return low_candidate
        elif up_candidate:
            return up_candidate
        else:
            next_up_hedge = up_hedge.new_next
            next_low_hedge = low_hedge.new_last
            if next_up_hedge not in used and  next_low_hedge not in used:
                next_two_candidates.extend([next_up_hedge, next_low_hedge])
            elif next_low_hedge not in used:
                low_candidate = get_leftmost_hedge_in_point(next_low_hedge, flag)
                if low_candidate:
                    return low_candidate
                else:
                    raise LookupError('Did not manage to find any dissolved half edges connected to given loop')
            elif next_up_hedge not in used:
                up_candidate = get_leftmost_hedge_in_point(next_up_hedge, flag)
                if up_candidate:
                    return up_candidate
                else:
                    raise LookupError('Did not manage to find any dissolved half edges connected to given loop')
            else:
                raise LookupError('Did not manage to find any dissolved half edges connected to given loop')


# #############################################################################
# ###################________dissolve mesh functions______#####################
# ###################____________second approach__________#####################
# #############################################################################
# This algorithm much more easier but should be slower.


def dissolve_faces_add(mesh, flag):
    faces = []
    used = set()
    for face in mesh.faces:
        if flag not in face.flags:
            faces.append(face)
            continue
        if face in used:
            continue
        used.add(face)
        faces.append(face)
        Debugger.print(face, 'start face')
        candidate_faces = [hedge.twin.face for hedge in face.outer.loop_hedges
                           if flag in hedge.twin.face.flags and hedge.twin.face not in used]
        checked_faces = set(candidate_faces)  # detect faces which already was added to the stack
        Debugger.print(list(candidate_faces), 'candidate_faces')
        while candidate_faces:
            Debugger.print(list(candidate_faces), 'candidate_faces')
            face_candidate = candidate_faces.pop()
            Debugger.print(face_candidate, 'candidate')  # + f', is addable-{is_addable(face, face_candidate)}')
            # print([hedge.origin.co for hedge in face_candidate.outer.loop_hedges])
            if is_addable(face, face_candidate):
                used.add(face_candidate)
                candidate_faces.extend(get_next_candidates(face_candidate, checked_faces, flag))
                # Debugger.print(face_candidate, 'candidate2')
                # print([hedge.origin.co for hedge in face_candidate.outer.loop_hedges])
                add_faces(face, face_candidate)
    mesh.faces = faces
    mesh.hedges = [hedge for face in mesh.faces for hedge in face.outer.loop_hedges]


def get_next_candidates(face, checked_faces, flag):
    out = []
    for hedge in face.outer.loop_hedges:
        if flag in hedge.twin.face.flags and hedge.twin.face not in checked_faces:
            checked_faces.add(hedge.twin.face)
            out.append(hedge.twin.face)
    return out


def is_addable(face, candidate):
    # does not take in account possible common points yet
    in_common_edge = False
    number_common_lines = 0
    start_from_common_hedge = False
    for i, loop_hedge in enumerate(candidate.outer.loop_hedges):
        if loop_hedge.twin.face == face:
            if in_common_edge:
                continue
            else:
                in_common_edge = True
                number_common_lines += 1
                if i == 0:
                    start_from_common_hedge = True
        else:
            in_common_edge = False
    if in_common_edge and start_from_common_hedge:
        # here case is detected when one common line take in account two times
        number_common_lines -= 1
    return True if number_common_lines == 1 else False


def add_faces(face, dis_face):
    last_hedge_1, next_hedge_1 = None, None
    last_hedge_2, next_hedge_2 = None, None
    dis_hedges = []
    # print([hedge.origin.co for hedge in face.outer.loop_hedges])
    Debugger.print(face, 'face')
    Debugger.print(dis_face, 'dis_face')
    for loop_hedge in dis_face.outer.loop_hedges:
        if loop_hedge.twin.face == face and loop_hedge.last.twin.face != face:
            last_hedge_1, next_hedge_1 = loop_hedge.last, loop_hedge.twin.next
        elif loop_hedge.twin.face != face and loop_hedge.last.twin.face == face:
            last_hedge_2, next_hedge_2 = loop_hedge.last.twin.last, loop_hedge
        if loop_hedge.twin.face == face:
            dis_hedges.append(loop_hedge)
        else:
            loop_hedge.face = face
    [setattr(hedge, 'mesh', None) for hedge in dis_hedges]
    [setattr(hedge.twin, 'mesh', None) for hedge in dis_hedges]
    dis_face.mesh = None
    face.outer = last_hedge_1
    last_hedge_1.next = next_hedge_1
    next_hedge_1.last = last_hedge_1
    last_hedge_2.next = next_hedge_2
    next_hedge_2.last = last_hedge_2
