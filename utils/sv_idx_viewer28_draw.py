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
    width, height = blf.dimensions(0, index)
    if not (width in point_dict):
        point_dict[width] = generate_points(width, height)

    return point_dict[width]


## end of util functions

# def draw_callback_px(n_id, draw_verts, draw_edges, draw_faces, draw_matrix, draw_bg, settings, text):
def draw_indices_2D(context, args):

    context = bpy.context
    region = context.region
    region3d = context.space_data.region_3d

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

    font_id = 0
    text_height = int(13.0 * scale)
    blf.size(font_id, text_height, 72)  # should check prefs.dpi

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    # vars for projection
    perspective_matrix = region3d.perspective_matrix.copy()

    def draw_index(rgb, rgb2, index, vec, text=''):

        # vec_4d = perspective_matrix * vec.to_4d()
        # if vec_4d.w <= 0.0:
        #     return

        # x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        # y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)
        # if text:
        #     index = str(text[0])
        # else:
        #     index = str(index)

        # if draw_bg:
        #     polyline = get_points(index)

        #     ''' draw polygon '''
        #     bgl.glColor4f(*rgb2)
        #     bgl.glBegin(bgl.GL_POLYGON)
        #     for pointx, pointy in polyline:
        #         bgl.glVertex2f(pointx+x, pointy+y)
        #     bgl.glEnd()

        # ''' draw text '''
        # txt_width, txt_height = blf.dimensions(0, index)
        # bgl.glColor4f(*rgb)
        # blf.position(0, x - (txt_width / 2), y - (txt_height / 2), 0)
        # blf.draw(0, index)
        pass

    ########
    # points


    for obj_index, verts in enumerate(data_vector):
        final_verts = verts

        if draw_matrix:
            matrix = data_matrix[obj_index]
            final_verts = [matrix @ v for v in verts]

        if display_vert_index:
            for idx, v in enumerate(final_verts):
                draw_index(vert_idx_color, vert_bg_color, idx, v)

        if data_edges and display_edge_index:
            for edge_index, (idx1, idx2) in enumerate(data_edges[obj_index]):

                v1 = Vector(final_verts[idx1])
                v2 = Vector(final_verts[idx2])
                loc = v1 + ((v2 - v1) / 2)
                draw_index(edge_idx_color, edge_bg_color, edge_index, loc)

        if data_faces and display_face_index:
            for face_index, f in enumerate(data_faces[obj_index]):
                verts = [Vector(final_verts[idx]) for idx in f]
                median = calc_median(verts)
                draw_index(face_idx_color, face_bg_color, face_index, median)

