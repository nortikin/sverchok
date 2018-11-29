# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import math

import bpy
import blf
import bgl
from mathutils import Vector

from sverchok.data_structure import Vector_generate, Matrix_generate

SpaceView3D = bpy.types.SpaceView3D
callback_dict = {}
point_dict = {}


def calc_median(vlist):
    a = Vector((0, 0, 0))
    for v in vlist:
        a += v
    return a / len(vlist)

def adjust_list(in_list, x, y):
    return [[old_x + x, old_y + y] for (old_x, old_y) in in_list]


def generate_points(width, height):
    amp = 5  # radius fillet

    width += 2
    height += 4
    width = ((width/2) - amp) + 2
    height -= (2*amp)

    pos_list, final_list = [], []

    n_points = 12
    seg_angle = 2 * math.pi / n_points
    for i in range(n_points + 1):
        angle = i * seg_angle
        x = math.cos(angle) * amp
        y = math.sin(angle) * amp
        pos_list.append([x, -y])

    w_list, h_list = [1, -1, -1, 1], [-1, -1, 1, 1]
    slice_list = [[i, i+4] for i in range(0, n_points, 3)]

    for idx, (start, end) in enumerate(slice_list):
        point_array = pos_list[start:end]
        w = width * w_list[idx]
        h = height * h_list[idx]
        final_list += adjust_list(point_array, w, h)

    return final_list


def get_points(index):
    '''
    index:   string representation of the index number
    returns: rounded rect point_list used for background.
    the neat thing about this is if a width has been calculated once, it
    is stored in a dict and used if another polygon is saught with that width.
    '''
    width, height = blf.dimensions(0, str(index))
    if not (width in point_dict):
        point_dict[width] = generate_points(width, height)

    return point_dict[width]


## end of util functions

# def draw_callback_px(n_id, draw_verts, draw_edges, draw_faces, draw_matrix, draw_bg, settings, text):
def draw_indices_2D(context, args):

    context = bpy.context
    region = context.region
    region3d = context.space_data.region_3d

    geom, settings = args

    vert_idx_color = settings['numid_verts_col']
    edge_idx_color = settings['numid_edges_col']
    face_idx_color = settings['numid_faces_col']
    vert_bg_color = settings['bg_verts_col']
    edge_bg_color = settings['bg_edges_col']
    face_bg_color = settings['bg_faces_col']
    display_vert_index = settings['display_vert_index']
    display_edge_index = settings['display_edge_index']
    display_face_index = settings['display_face_index']
    scale = settings['scale']
    draw_bg = settings['draw_bg']
    draw_bface = settings['draw_bface']

    font_id = 0
    text_height = int(13.0 * scale)
    blf.size(font_id, text_height, 72)  # should check prefs.dpi

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    # vars for projection
    perspective_matrix = region3d.perspective_matrix.copy()

    def draw_index(index, vec):

        vec_4d = perspective_matrix @ vec.to_4d()
        if vec_4d.w <= 0.0:
            return

        x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)

        # ''' draw text '''
        index_str = str(index)
        txt_width, txt_height = blf.dimensions(0, index_str)
        blf.position(0, x - (txt_width / 2), y - (txt_height / 2), 0)
        blf.draw(0, index_str)

    if draw_bface:

        blf.color(font_id, *vert_idx_color)
        for vidx in geom.vert_data:
            draw_index(*vidx)
    
        blf.color(font_id, *edge_idx_color)
        for eidx in geom.edge_data:
            draw_index(*eidx)

        blf.color(font_id, *face_idx_color)
        for fidx in geom.face_data:
            draw_index(*fidx)
