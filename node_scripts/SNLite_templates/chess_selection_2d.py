'''
in verts v d=[] n=0
in faces s d=[] n=0
out face_mask s
'''

from sverchok.utils.geom_2d.dcel import DCELMesh


def main(sv_points, sv_faces):
    mesh = DCELMesh()
    mesh.from_sv_faces(sv_points, sv_faces)
    mark_faces(mesh)
    return [int(face.select) for face in mesh.faces]


def mark_faces(mesh):
    # https://en.wikipedia.org/wiki/Depth-first_search
    used = set()
    for face in mesh.faces:
        if face in used:
            continue
        stack = [(face, 'add')]
        while stack:
            next_face, type_face = stack.pop()
            if next_face in used:
                continue
            used.add(next_face)
            if type_face == 'add':
                next_face.select = True
            for hedge in next_face.outer.loop_hedges:
                if hedge.twin.face in used or hedge.twin.face.is_unbounded:
                    continue
                stack.append((hedge.twin.face, 'sub' if type_face == 'add' else 'add'))


for p, f in zip(verts, faces):
    face_mask.append(main(p, f))
