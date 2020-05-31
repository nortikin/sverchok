# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import sys
import math
import traceback

import bpy
import blf
import bgl
import mathutils
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from sverchok.data_structure import Vector_generate

SpaceView3D = bpy.types.SpaceView3D
callback_dict = {}
point_dict = {}

# pylint: disable=W0703
# pylint: disable=C0301


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


def draw_indices_2D(context, args):

    context = bpy.context
    region = context.region
    region3d = context.space_data.region_3d

    geom, settings = args

    vert_idx_color = settings['numid_verts_col']
    edge_idx_color = settings['numid_edges_col']
    face_idx_color = settings['numid_faces_col']
    # vert_bg_color = settings['bg_verts_col']
    # edge_bg_color = settings['bg_edges_col']
    # face_bg_color = settings['bg_faces_col']
    display_vert_index = settings['display_vert_index']
    display_edge_index = settings['display_edge_index']
    display_face_index = settings['display_face_index']
    scale = settings['scale']
    # draw_bg = settings['draw_bg']
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

        # ---- draw text ----
        index_str = str(index)
        txt_width, txt_height = blf.dimensions(0, index_str)

        level = 5 # 5 or 0
        # blf.enable(0, blf.SHADOW)
        # blf.shadow(0, level, 0, 0, 0, 1)
        # blf.shadow_offset(0, 1, -1)
        blf.position(0, x - (txt_width / 2), y - (txt_height / 2), 0)
        blf.draw(0, index_str)
        # blf.disable(0, blf.SHADOW)

    if draw_bface:

        blf.color(font_id, *vert_idx_color)
        if geom.vert_data and geom.text_data:
            for text_item, (idx, location) in zip(geom.text_data, geom.vert_data):
                draw_index(text_item, location)
        else:
            for vidx in geom.vert_data:
                draw_index(*vidx)
    
        blf.color(font_id, *edge_idx_color)
        for eidx in geom.edge_data:
            draw_index(*eidx)

        blf.color(font_id, *face_idx_color)
        for fidx in geom.face_data:
            draw_index(*fidx)

        # if drawing all geometry, we end early.
        return

    eye = Vector(region3d.view_matrix[2][:3])
    eye.length = region3d.view_distance
    eye_location = region3d.view_location + eye  

    try:

        for obj_index, polygons in enumerate(geom.faces):
            edges = geom.edges[obj_index] if obj_index < len(geom.edges) else []
            vertices = geom.verts[obj_index]
            bvh = BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0)

            cache_vert_indices = set()
            cache_edge_indices = set()

            blf.color(font_id, *face_idx_color)
            for idx, polygon in enumerate(polygons):

                # check the face normal, reject it if it's facing away.

                face_normal = geom.face_normals[obj_index][idx]
                world_coordinate = geom.face_medians[obj_index][idx]

                result_vector = eye_location - world_coordinate
                dot_value = face_normal.dot(result_vector.normalized())

                if dot_value < 0.0:
                    continue # reject

                # cast ray from eye towards the median of the polygon, the reycast will return (almost definitely..)
                # but if the return idx does not correspond with the polygon index, then it is occluded :)

                # bvh.ray_cast(origin, direction, distance=sys.float_info.max) : returns
                # if hit: (Vector location, Vector normal, int index, float distance) else all (None, ...)

                direction = world_coordinate - eye_location
                hit = bvh.ray_cast(eye_location, direction)
                if hit:
                    if hit[2] == idx:
                        if display_face_index:
                            draw_index(idx, world_coordinate)
                        
                        if display_vert_index:
                            for j in polygon:
                                cache_vert_indices.add(j)

                        # this could be woefully slow...
                        if display_edge_index and edges:
                            for j in range(len(polygon)-1):
                                cache_edge_indices.add(tuple(sorted([polygon[j], polygon[j+1]])))
                            cache_edge_indices.add(tuple(sorted([polygon[-1], polygon[0]])))

            blf.color(font_id, *vert_idx_color)
            for idx in cache_vert_indices:
                draw_index(idx, vertices[idx])

            blf.color(font_id, *edge_idx_color)
            for idx, edge in enumerate(edges):
                sorted_edge = tuple(sorted(edge))
                if sorted_edge in cache_edge_indices:
                    idx1, idx2 = sorted_edge
                    loc = vertices[idx1].lerp(vertices[idx2], 0.5)
                    draw_index(idx, loc)
                    cache_edge_indices.remove(sorted_edge)

    except Exception as err:
        print('---- ERROR in sv_idx_viewer28 Occlusion backface drawing ----')
        print(err)
        print(traceback.format_exc())
