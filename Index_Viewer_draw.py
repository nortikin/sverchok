# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy
import blf
import bgl
import math
import mathutils
from mathutils import Vector, Matrix
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d

import node_Viewer
from node_Viewer import *
from util import *

SpaceView3D = bpy.types.SpaceView3D
point_dict = {}


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

def tag_redraw_all_view3d():
    context = bpy.context

    # Py cant access notifers
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()


def callback_enable(name, draw_verts, draw_matrix, draw_bg):
    handle = handle_read(name)
    if handle[0]:
        return

    handle_pixel = SpaceView3D.draw_handler_add(
        draw_callback_px, (name, draw_verts, draw_matrix, draw_bg),
        'WINDOW', 'POST_PIXEL')
    handle_write(name, handle_pixel)
    tag_redraw_all_view3d()


def callback_disable(name):
    handle = handle_read(name)
    if not handle[0]:
        return

    handle_pixel = handle[1]
    SpaceView3D.draw_handler_remove(handle_pixel, 'WINDOW')
    handle_delete(name)
    tag_redraw_all_view3d()


def draw_callback_px(name, draw_verts, draw_matrix, draw_bg):
    context = bpy.context
    data_vector = []
    data_matrix = []

    if draw_verts:
        data_vector = Vector_generate(draw_verts)

    if draw_matrix:
        data_matrix = Matrix_generate(draw_matrix)

    if (data_vector, data_matrix) == (0, 0):
        callback_disable(name)
        return

    region = context.region
    region3d = context.space_data.region_3d

    vert_idx_color = (1, 1, 1)
    font_id = 0
    text_height = 13
    blf.size(font_id, text_height, 72)

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    # vars for projection
    perspective_matrix = region3d.perspective_matrix.copy()

    def draw_index(rgb, index, vec):

        vec_4d = perspective_matrix * vec.to_4d()
        if vec_4d.w <= 0.0:
            return

        x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)
        index = str(index)

        if draw_bg:
            polyline = get_points(index)

            ''' draw polygon '''
            bgl.glColor4f(0.103, 0.2, 0.2, 0.2)
            bgl.glBegin(bgl.GL_POLYGON)
            for pointx, pointy in polyline:
                bgl.glVertex2f(pointx+x, pointy+y)
            bgl.glEnd()

        ''' draw text '''
        txt_width, txt_height = blf.dimensions(0, index)
        bgl.glColor3f(*rgb)
        blf.position(0, x - (txt_width / 2), y - (txt_height / 2), 0)
        blf.draw(0, index)

    ########
    # points

    if data_vector:

        idx = 0
        for verts in data_vector:

            if draw_matrix:
                matrix = data_matrix[0]
                for v in verts:
                    vc = matrix * v
                    draw_index(vert_idx_color, idx, vc)
                    idx += 1
            else:
                for v in verts:
                    draw_index(vert_idx_color, idx, v)
                    idx += 1
