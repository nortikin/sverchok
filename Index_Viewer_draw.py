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
import bmesh
from bmesh.types import BMFace

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


def callback_enable(node, draw_verts, draw_edges, draw_faces, draw_matrix, draw_bg):
    handle = handle_read(node.name)
    if handle[0]:
        return

    handle_pixel = SpaceView3D.draw_handler_add(
        draw_callback_px, (
            node, draw_verts, draw_edges, draw_faces, draw_matrix, draw_bg),
        'WINDOW', 'POST_PIXEL')
    handle_write(node.name, handle_pixel)
    tag_redraw_all_view3d()


def callback_disable(node):
    handle = handle_read(node.name)
    if not handle[0]:
        return

    handle_pixel = handle[1]
    SpaceView3D.draw_handler_remove(handle_pixel, 'WINDOW')
    handle_delete(node.name)
    tag_redraw_all_view3d()


def draw_callback_px(node, draw_verts, draw_edges, draw_faces, draw_matrix, draw_bg):
    context = bpy.context

    # ensure data or empty lists.
    data_vector = Vector_generate(draw_verts) if draw_verts else []
    data_edges = draw_edges
    data_faces = draw_faces
    data_matrix = Matrix_generate(draw_matrix) if draw_matrix else []

    if (data_vector, data_matrix) == (0, 0):
        callback_disable(node.name)
        return

    region = context.region
    region3d = context.space_data.region_3d

    vert_idx_color = (1, 1, 1)
    edge_idx_color = (1.0, 1.0, 0.0)
    face_idx_color = (1.0, 0.8, 0.8)

    font_id = 0
    text_height = 13
    blf.size(font_id, text_height, 72)  # should check prefs.dpi

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
    def calc_median(vlist):
        a = Vector((0, 0, 0))
        for v in vlist:
            a += v
        return a * (1/len(vlist))

    for obj_index, verts in enumerate(data_vector):
        final_verts = verts

        # quicklt apply matrix if necessary
        if draw_matrix:
            matrix = data_matrix[obj_index]
            final_verts = [matrix * v for v in verts]

        if node.display_vert_index:
            for idx, v in enumerate(final_verts):
                draw_index(vert_idx_color, idx, v)

        if data_edges and node.display_edge_index:
            for edge_details in enumerate(data_edges[obj_index]):
                edge_index, (idx1, idx2) = edge_details
                v1 = Vector(final_verts[idx1])
                v2 = Vector(final_verts[idx2])
                loc = v1 + ((v2 - v1) / 2)
                draw_index(edge_idx_color, edge_index, loc)

        if data_faces and node.display_face_index:
            for face_index, f in enumerate(data_faces[obj_index]):
                verts = [Vector(final_verts[idx]) for idx in f]
                median = calc_median(verts)
                draw_index(face_idx_color, face_index, median)
