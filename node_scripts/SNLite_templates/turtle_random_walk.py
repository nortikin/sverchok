"""
in   in_verts  v
in   in_faces  s
in   in_start_face_idx s d=[[]] n=2
in   in_steps s
in   in_select_mask s
in   in_paint_mask s
in   in_seed s 
out  out_face_mask   s
out  out_face_data s
"""

import random

from sverchok.data_structure import zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.logging import debug, info
from sverchok.utils.turtle import Turtle

if in_select_mask is None:
    in_select_mask = [[]]
if in_paint_mask is None:
    in_paint_mask = [[]]

out_face_mask = []
out_face_data = []
objects = zip_long_repeat(in_verts, in_faces, in_start_face_idx, in_steps,
            in_select_mask, in_paint_mask, in_seed)
for verts, faces, start_face, steps, select_mask, paint_mask, seed in objects:
    info(seed)
    if isinstance(seed, (list, tuple)):
        seed = seed[0]
    random.seed(seed)
    if isinstance(start_face, (list, tuple)):
        if not start_face:
            start_face = random.choice(range(len(faces)))
        else:
            start_face = start_face[0]
    if isinstance(steps, (list, tuple)):
        steps = steps[0]
    
    bm = bmesh_from_pydata(verts, [], faces, normal_update=True)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    turtle = Turtle(bm)
    
    # When manually assigning the current_face, remember
    # to assign current_loop correspondingly!
    turtle.current_face = bm.faces[start_face]
    turtle.current_loop = turtle.current_face.loops[0]
    
    if select_mask:
        turtle.start_selecting(Turtle.MASK, select_mask)
    else:
        turtle.start_selecting()
    if paint_mask:
        turtle.start_painting(paint_mask)
        
    for i in range(steps):
        steps = int( random.uniform(4, 12) )
        for j in range(steps):
            for k in range(len(turtle.current_face.edges)):
                bound = turtle.is_looking_at_boundary
                next_face = turtle.get_next_face(count=2)
                if bound or next_face.select:
                    r = random.uniform(0, 1)
                    if r > 0.5:
                        turtle.turn_next()
                    else:
                        turtle.turn_prev()
                else:
                    break
            turtle.step()
        rot = int( random.uniform(-3, 3) )
        if rot > 0:
            turtle.turn_next(rot)
        else:
            turtle.turn_next(- rot)
        
    new_face_mask = turtle.get_selection_mask()
    new_face_data = turtle.get_painting_data()
    bm.free()
    out_face_mask.append(new_face_mask)
    out_face_data.append(new_face_data)
