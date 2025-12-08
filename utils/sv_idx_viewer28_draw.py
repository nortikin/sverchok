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
import gpu
from gpu_extras.batch import batch_for_shader

import mathutils
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from sverchok.data_structure import Vector_generate
from sverchok.utils.modules.drawing_abstractions import drawing 


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


def generate_points_tris(width, height, x, y):
    #amp = 5  # radius filletdraw_obj_idx
    # _width += 2
    # _height += 4
    # _width = ((_width/2) - amp) + 2
    # _height -= (2*amp)

    # _height += 4
    # _width += 3    

    border=4 # even size
    border2=border/2
    _width = width
    _height = height
    _y = y
    _x = x

    final_list = [
        # a
        [        _x-border2, +_height+_y+border2],   # A         D - - - - - E
        [+_width+_x+border2,          _y-border2],   # B         A .         |
        [        _x-border2,          _y-border2],   # C         |   .    b  |
        # b                                                      |     .     |
        [        _x-border2, +_height+_y+border2],   # D         |   a   .   |
        [+_width+_x+border2, +_height+_y+border2],   # E         |         . F
        [+_width+_x+border2,          _y-border2]    # F         C - - - - - B
    ] 
    return final_list


## end of util functions


def draw_indices_2D(context, args):

    context = bpy.context
    region = context.region
    region3d = context.space_data.region_3d

    geom, settings = args

    vert_idx_color = settings['numid_verts_col']
    edge_idx_color = settings['numid_edges_col']
    face_idx_color = settings['numid_faces_col']
    display_vert_index = settings['display_vert_index']
    display_edge_index = settings['display_edge_index']
    display_face_index = settings['display_face_index']
    scale = settings['scale']
    draw_obj_idx = settings['draw_obj_idx']
    draw_bface = settings['draw_bface']

    font_id = 0
    text_height = int(13.0 * scale)
    drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi

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
        if draw_obj_idx==True:
            txt_parts = index_str.split(':',1)
            if len(txt_parts)>1:
                object_index, txt = txt_parts
            else:
                object_index=''
                txt = txt_parts[0]
        else:
            object_index=''
            txt = index_str


        drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi
        txt_width, txt_height = blf.dimensions(font_id, txt)
        #txt_width, txt_height = blf.dimensions(font_id, f'{txt}{object_index}' if object_index else txt) # a bit more than text with object index in the screen
        # txt_width_general, txt_height_general = txt_width, txt_height = blf.dimensions(font_id, txt)
        # if object_index:
        #     drawing.blf_size(font_id, text_height*0.5, 72)
        #     text_object_index_dim_width, text_object_index_dim_height = blf.dimensions(font_id, txt)
        #     txt_width_general+=text_object_index_dim_width+2

        pos_x = x - (txt_width / 2)
        pos_y = y - (txt_height / 2)
        drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi
        blf.position(font_id, pos_x, pos_y, 0)
        blf.draw(font_id, txt)

        if object_index:
            drawing.blf_size(font_id, text_height*0.5, 72)
            #blf.position(font_id, pos_x + txt_width + 2, pos_y - text_height*0.1, 0)
            blf.position(font_id, pos_x + txt_width + 2, pos_y, 0)
            blf.draw(font_id, object_index)
        pass

    if draw_bface:

        blf.color(font_id, *vert_idx_color)
        if display_vert_index:
            for text_data, vert_data in zip(geom.text_data, geom.vert_data):
                for text_item, (idx, location) in zip(text_data, vert_data):
                    draw_index(text_item, location)
                pass
            pass
    
        blf.color(font_id, *edge_idx_color)
        if display_edge_index:
            for text_data, edge_data in zip(geom.text_data, geom.edge_data):
                for text_item, (_, location) in zip(text_data, edge_data):
                    draw_index(text_item, location)
                pass
            pass

        blf.color(font_id, *face_idx_color)
        if display_face_index:
            for text_data, face_data in zip(geom.text_data, geom.face_data):
                for text_item, (_, location) in zip(text_data, face_data):
                    draw_index(text_item, location)
                pass
            pass

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
                            text = geom.text_data[obj_index][idx] 
                            draw_index(text, world_coordinate)
                        
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
                text = geom.text_data[obj_index][idx] 
                draw_index(text, vertices[idx])

            blf.color(font_id, *edge_idx_color)
            for idx, edge in enumerate(edges):
                sorted_edge = tuple(sorted(edge))
                if sorted_edge in cache_edge_indices:
                    idx1, idx2 = sorted_edge
                    loc = vertices[idx1].lerp(vertices[idx2], 0.5)
                    text = geom.text_data[obj_index][idx] 
                    draw_index(text, loc)
                    cache_edge_indices.remove(sorted_edge)

    except Exception as err:
        print('---- ERROR in sv_idx_viewer28 Occlusion backface drawing ----')
        print(err)
        print(traceback.format_exc())

###
###
###
###
###
###
###
### --------------------------- WARNING ---------------------------
###
###
###
###
###
###
###

def draw_indices_2D_wbg(context, args):

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
    draw_obj_idx = settings['draw_obj_idx']
    draw_bg = settings['draw_bg']
    draw_bface = settings['draw_bface']

    font_id = 0
    text_height = int(13.0 * scale)
    drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    # vars for projection
    perspective_matrix = region3d.perspective_matrix.copy()

    final_draw_data = {}
    data_index_counter = 0

    def draw_all_text_at_once(final_draw_data):

        # build bg mesh and vcol data
        full_bg_Verts = []
        add_vert_list = full_bg_Verts.extend
        
        full_bg_colors = []
        add_vcol = full_bg_colors.extend
        for counter, (_, _, _, _, _, type_draw, pts) in final_draw_data.items():
            col = settings[f'bg_{type_draw}_col']
            add_vert_list(pts)
            add_vcol((col,) * 6)

        # draw background
        shader_name = f'{"2D_" if bpy.app.version < (3, 4) else ""}SMOOTH_COLOR'
        shader = gpu.shader.from_builtin(shader_name)
        batch = batch_for_shader(shader, 'TRIS', {"pos": full_bg_Verts, "color": full_bg_colors})
        batch.draw(shader)

        # draw text 
        for counter, (index_str, pos_x, pos_y, txt_width, txt_height, type_draw, pts) in final_draw_data.items():
            drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi
            text_color = settings[f'numid_{type_draw}_col']
            if draw_obj_idx==True:
                txt_parts = index_str.split(':',1)
                if len(txt_parts)>1:
                    object_index, txt = txt_parts
                else:
                    object_index=''
                    txt = txt_parts[0]
            else:
                object_index=''
                txt = index_str

            blf.color(font_id, *text_color)
            blf.position(font_id, pos_x, pos_y, 0)
            blf.draw(font_id, txt)

            if object_index:
                txt_width, txt_height = blf.dimensions(font_id, txt)
                drawing.blf_size(font_id, text_height*0.5, 72)
                blf.position(font_id, pos_x + txt_width+2, pos_y, 0)
                blf.draw(font_id, object_index)

    def gather_index(index, vec, type_draw):

        vec_4d = perspective_matrix @ vec.to_4d()
        if vec_4d.w <= 0.0:
            return

        x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)

        # ---- draw text ----
        index_str = str(index)
        if draw_obj_idx==True:
            txt_parts = index_str.split(':',1)
            if len(txt_parts)>1:
                object_index, txt = txt_parts
            else:
                object_index=''
                txt = txt_parts[0]
        else:
            object_index=''
            txt = index_str

        drawing.blf_size(font_id, text_height, 72)
        txt_width, txt_height = blf.dimensions(font_id, txt)
        pos_x = x - (txt_width / 2)
        pos_y = y - (txt_height / 2)
        if object_index:
            drawing.blf_size(font_id, text_height*0.5, 72)
            txt_index_width, txt_index_height = blf.dimensions(font_id, f'{object_index}') # a bit more than text with object index in the screen
            txt_width+=txt_index_width+2
        pts = generate_points_tris(txt_width, txt_height, pos_x, pos_y)
        data_index_counter = len(final_draw_data)
        final_draw_data[data_index_counter] = (index_str, pos_x, pos_y, txt_width, txt_height, type_draw, pts)

    # THIS SECTION IS ONLY EXECUTED IF BOTH FORWARD AND BACKFACING ARE DRAWN

    if draw_bface:

        # blf.color(font_id, *vert_idx_color)
        if display_vert_index:
            for text_data, vert_data in zip(geom.text_data, geom.vert_data):
                for text_item, (idx, location) in zip(text_data, vert_data):
                    gather_index(text_item, location, 'verts')
                pass
            pass
    
        # blf.color(font_id, *edge_idx_color)
        if display_edge_index:
            for text_data, edge_data in zip(geom.text_data, geom.edge_data):
                for text_item, eidx in zip(text_data, edge_data):
                    gather_index(text_item, eidx[1], 'edges')
                pass
            pass

        # blf.color(font_id, *face_idx_color)
        if display_face_index:
            for text_data, face_data in zip(geom.text_data, geom.face_data):
                for text_item, fidx in zip(text_data, face_data):
                    gather_index(text_item, fidx[1], 'faces')
                pass
            pass

        draw_all_text_at_once(final_draw_data)
        # if drawing all geometry, we end early.
        return

    # THIS SECTION IS ONLY EXECUTED IF ONLY FORWARD FACING  / NON OCCLUDED FACES ARE GOING TO BE DRAWN.

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

            # blf.color(font_id, *face_idx_color)
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
                            text = geom.text_data[obj_index][idx] 
                            gather_index(text, world_coordinate, 'faces')
                        
                        if display_vert_index:
                            for j in polygon:
                                cache_vert_indices.add(j)

                        # this could be woefully slow...
                        if display_edge_index and edges:
                            for j in range(len(polygon)-1):
                                cache_edge_indices.add(tuple(sorted([polygon[j], polygon[j+1]])))
                            cache_edge_indices.add(tuple(sorted([polygon[-1], polygon[0]])))

            # blf.color(font_id, *vert_idx_color)
            for idx in cache_vert_indices:
                text = geom.text_data[obj_index][idx] 
                gather_index(text, vertices[idx], 'verts')

            # blf.color(font_id, *edge_idx_color)
            for idx, edge in enumerate(edges):
                sorted_edge = tuple(sorted(edge))
                if sorted_edge in cache_edge_indices:
                    idx1, idx2 = sorted_edge
                    loc = vertices[idx1].lerp(vertices[idx2], 0.5)
                    text = geom.text_data[obj_index][idx] 
                    gather_index(text, loc, 'edges')
                    cache_edge_indices.remove(sorted_edge)

        draw_all_text_at_once(final_draw_data)

    except Exception as err:
        print('---- ERROR in sv_idx_viewer28 Occlusion backface drawing ----')
        print(err)
        print(traceback.format_exc())

