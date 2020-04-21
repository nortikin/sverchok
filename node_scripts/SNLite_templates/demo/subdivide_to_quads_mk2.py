"""
in quad_verts v
in quad_faces s
in seed s d=1 n=2
in random_factor s d=0.1 n=2
in iterations s d=1 n=2
out verts v
out faces s
"""

from sverchok.utils.modules.geom_utils import interp_v3_v3v3 as lerp
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.remove_doubles import remove_doubles
import  random


sort = lambda vex, pox: [vex[i] for i in pox]

def random_subdiv_mesh(verts_m, pols_m, iteration):

    verts, faces =[],[]
    for pol in pols_m:
        verts_out, faces_out = [], []
        new_quad = faces_out.append

        pts = sort(verts_m, pol)
        X = 0.5 +(random.random() - 0.5) * random_factor
        Y = 0.5 +(random.random() - 0.5) * random_factor
        pos_a = lerp(pts[0], pts[1], Y)
        pos_b = lerp(pts[1], pts[2], X)
        pos_c = lerp(pts[3], pts[2], 1-Y)
        pos_d = lerp(pts[0], pts[3], X)
        pos_e = lerp(pos_d, pos_b, Y)
        pos_f = lerp(pos_d, pos_b, 1-Y)

        # indices = 0, 1, 2, 3
        verts_out.extend(pts)  

        # indices =       4,     5,     6,     7,     8,     9
        verts_out.extend([pos_a, pos_b, pos_c, pos_d, pos_e, pos_f])

        new_quad([0, 4, 8, 7])
        new_quad([4, 1, 5, 8])
        new_quad([5, 2, 6, 9])
        new_quad([7, 9, 6, 3])
        faces.append(faces_out)
        verts.append(verts_out)
        
    verts, _, faces = mesh_join(verts, [],faces)
    if iteration <2 :
        return verts,faces
    else:
        return random_subdiv_mesh(verts, faces, iteration - 1)
    
if quad_verts and quad_faces:
    random.seed(seed)
    verts, faces = random_subdiv_mesh(quad_verts[0], quad_faces[0], iterations)  
    verts, _, faces, _, _ = remove_doubles(verts, faces, 1e-5, False)       
    verts =[verts]
    faces= [faces]
