"""
in   in_verts  v
in   in_faces  s
in   in_start_face_idx s
in   in_turns s
in   in_select_mask s
in   in_paint_mask s
out  out_face_mask s
out  out_face_data s
"""

from sverchok.data_structure import zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.logging import info, debug
from sverchok.utils.turtle import Turtle

if in_select_mask is None:
    in_select_mask = [[]]
if in_paint_mask is None:
    in_paint_mask = [[]]

info(in_start_face_idx)

out_face_mask = []
out_face_data = []
objects = zip_long_repeat(in_verts, in_faces, in_start_face_idx,
        in_turns, in_select_mask, in_paint_mask)
for verts, faces, start_face, turns, select_mask, paint_mask in objects:

    if isinstance(start_face, (list, tuple)):
        if not start_face:
            start_face = random.choice(range(len(faces)))
        else:
            start_face = start_face[0]
    if isinstance(turns, (list, tuple)):
        turns = turns[0]
    
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
    
    for i in range(turns * 2):
        steps = (i+1)*2
        debug("Steps := %s", steps)
        turtle.step(steps)
        turtle.turn_prev()
        turtle.step(steps)
        turtle.turn_prev()
        
    new_face_mask = turtle.get_selection_mask()
    new_face_data = turtle.get_painting_data()
    bm.free()
    out_face_mask.append(new_face_mask)
    out_face_data.append(new_face_data)
