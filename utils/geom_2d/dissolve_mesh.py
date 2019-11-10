# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from .dcel import DCELMesh

from .dcel_debugger import Debugger


def dissolve_faces(sv_verts, sv_faces, face_mask, is_mask=False, is_index=False):
    mesh = DCELMesh()
    mesh.from_sv_faces(sv_verts, sv_faces, face_flag=['dissolve' if mark else None for mark in face_mask],
                       face_data={'index': list(range(len(sv_faces)))})
    dissolve_faces_with_flag(mesh, 'dissolve')
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


def dissolve_faces_with_flag(mesh, flag):
    # mark unused hedges and faces
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
    new_faces = []
    for hedge in boundary_hedges:
        if hedge in used:
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
