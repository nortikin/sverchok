"""
in verts_in v
in faces_in s
in iterations s d=1 n=1
in random_factor s d=0. n=1
in seed s d=1 n=1

out verts v
out faces s
"""

from sverchok.utils.modules.geom_utils import interp_v3_v3v3 as lerp
from sverchok.nodes.modifier_change.remove_doubles import remove_doubles
from sverchok.data_structure import match_long_repeat as mlr
import  random


sort = lambda vex, pox: [vex[i] for i in pox]

def enusure_list(data):
    return data if isinstance(data, (list,tuple)) else [data]

def subdivide_face_to_quads(pts, pol, verts_m, random_f):
    faces_p = []
    new_face = faces_p.append

    r_t = 0
    v_c_x = 0
    v_c_y = 0
    v_c_z = 0
    len_p = len(pts)
    f_index= len(verts_m)
    for i in range(len_p):
        f = 0.5
        new_p = lerp(pts[i], pts[(i+1) % len_p], f)
        verts_m.extend([new_p])
        f_c = 0.5 +(random.random() - 0.5) * random_f
        r_t += f_c
        v_c_x += pts[i][0] * f_c
        v_c_y += pts[i][1] * f_c
        v_c_z += pts[i][2] * f_c
        new_face([
            pol[i],
            f_index+i,
            f_index + len_p,
            f_index + (i + len_p - 1) % (len_p) ])

    v_c_x /= r_t
    v_c_y /= r_t
    v_c_z /= r_t

    verts_m.extend([[v_c_x, v_c_y, v_c_z]])

    return faces_p


def subdiv_mesh_to_quads(verts_mesh, pols_m, it, random_f):
    faces_mesh = []
    new_faces = faces_mesh.extend
    for pol in pols_m:
        pts = sort(verts_mesh, pol)
        faces_pol = subdivide_face_to_quads(pts, pol, verts_mesh, random_f)
        new_faces(faces_pol)

    if it < 2:
        return verts_mesh, faces_mesh
    else:
        return subdiv_mesh_to_quads(verts_mesh, faces_mesh, it-1, random_f)


if verts_in and faces_in:
    verts = []
    faces = []
    seed_l = enusure_list(seed)
    iterations_l = enusure_list(iterations)
    random_fac = enusure_list(random_factor)

    for v, f, s, it, r in zip(*mlr([verts_in, faces_in, seed_l, iterations_l, random_fac])):
        random.seed(s)
        verts_out, faces_out = subdiv_mesh_to_quads(v, f, min(it,5), r)
        verts_out, _, faces_out, _, _ = remove_doubles(verts_out, faces_out, 1e-5, False)
        verts.append(verts_out)
        faces.append(faces_out)
