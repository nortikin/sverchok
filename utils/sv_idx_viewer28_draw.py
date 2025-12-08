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

class TextInfo:
    def __init__(self, _text, _object_index, _index, _location, _normal=None):
        self.text=_text
        self.object_index = _object_index
        self.index = _index  # index vert, edge or face
        self.location = _location
        self.normal = _normal

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

def draw_indices_2D_wbg(context, args):

    context = bpy.context
    region = context.region
    region3d = context.space_data.region_3d

    geom, settings = args

    vert_idx_color      = settings['numid_verts_col']
    edge_idx_color      = settings['numid_edges_col']
    face_idx_color      = settings['numid_faces_col']
    vert_bg_color       = settings['bg_verts_col']
    edge_bg_color       = settings['bg_edges_col']
    face_bg_color       = settings['bg_faces_col']
    display_vert_index  = settings['display_vert_index']
    display_edge_index  = settings['display_edge_index']
    display_face_index  = settings['display_face_index']
    scale               = settings['scale']
    text_mode           = settings['text_mode']
    draw_obj_idx        = settings['draw_obj_idx']
    draw_bg             = settings['draw_bg']
    draw_bface          = settings['draw_bface']

    font_id             = 0
    text_height         = int(13.0 * scale)
    drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi

    region_mid_width    = region.width / 2.0
    region_mid_height   = region.height / 2.0

    # vars for projection
    perspective_matrix  = region3d.perspective_matrix.copy()

    final_draw_data     = {}
    data_index_counter  = 0

    object_index_index_gap=2
    def draw_all_text_at_once(final_draw_data):
        if draw_bg==True:
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
        for counter, (text_info, pos_x, pos_y, txt_width, txt_height, type_draw, _) in final_draw_data.items():
            drawing.blf_size(font_id, text_height, 72)  # should check prefs.dpi
            text_color = settings[f'numid_{type_draw}_col']

            blf.color(font_id, *text_color)
            blf.position(font_id, pos_x, pos_y, 0)
            text = str(text_info.index)
            if text_mode in ['TEXT_ONLY', 'TEXT_INDEX']:
                text = str(text_info.text)
            blf.draw(font_id, text)

            txt_width, txt_height = blf.dimensions(font_id, text)
            drawing.blf_size(font_id, text_height*0.5, 72)
            object_index_width, object_index_height = blf.dimensions(font_id, str(text_info.object_index))
            if draw_obj_idx:
                blf.position(font_id, pos_x + txt_width+2, pos_y, 0)
                blf.draw(font_id, str(text_info.object_index) )

            if text_mode in ['TEXT_INDEX']:
                drawing.blf_size(font_id, text_height*0.5, 72)
                blf.position(font_id, pos_x + txt_width+2, pos_y+object_index_height+object_index_index_gap, 0)
                blf.draw(font_id, str(text_info.index) )
            pass
        return

    def gather_index(text_info, type_draw):

        vec_4d = perspective_matrix @ text_info.location.to_4d()
        if vec_4d.w <= 0.0:
            return

        x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)

        # ---- draw text ----
        text=str(text_info.index)
        if text_mode in ['TEXT_ONLY', 'TEXT_INDEX']:
            text=str(text_info.text)

        drawing.blf_size(font_id, text_height, 72)
        txt_width, txt_height = blf.dimensions(font_id, text)
        pos_x = x - (txt_width / 2)
        pos_y = y - (txt_height / 2)

        drawing.blf_size(font_id, text_height*0.5, 72)
        object_index_width, object_index_height = blf.dimensions(font_id, str(text_info.object_index))
        text_index_width, text_index_height = blf.dimensions(font_id, str(text_info.index))
        txt_extra_width, txt_extra_height = 0,0
        if draw_obj_idx and text_mode in ['TEXT_INDEX']:
            txt_extra_width  = max(object_index_width , text_index_width)
            txt_extra_height = object_index_height + text_index_height + object_index_index_gap
        elif draw_obj_idx:
            txt_extra_width  = object_index_width
            txt_extra_height = object_index_height + text_index_height + object_index_index_gap
        elif text_mode in ['TEXT_INDEX']:
            txt_extra_width  = text_index_width
            txt_extra_height = object_index_height + text_index_height + object_index_index_gap
            
        txt_width+=txt_extra_width+2
        txt_height = max(txt_height, txt_extra_height)
        pts = generate_points_tris(txt_width, txt_height, pos_x, pos_y)
        data_index_counter = len(final_draw_data)
        final_draw_data[data_index_counter] = (text_info, pos_x, pos_y, txt_width, txt_height, type_draw, pts)
        return

    # THIS SECTION IS ONLY EXECUTED IF BOTH FORWARD AND BACKFACING ARE DRAWN

    if draw_bface or not geom.faces:

        if display_vert_index:
            for vert_data in geom.vert_data:
                for vidx in vert_data:
                    gather_index(vidx, 'verts')
                pass
            pass
    
        if display_edge_index:
            for edge_data in geom.edge_data:
                for eidx in edge_data:
                    gather_index(eidx, 'edges')
                pass
            pass

        if display_face_index:
            for face_data in geom.face_data:
                for fidx in face_data:
                    gather_index(fidx, 'faces')
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

        for obj_index, vert_data in enumerate(geom.vert_data):
            polygons = geom.faces[obj_index]
            edges = geom.edges[obj_index] if obj_index < len(geom.edges) else []
            vertices = geom.verts[obj_index]
            bvh = BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0)

            cache_vert_indices = set()
            cache_edge_indices = set()

            for idx, polygon in enumerate(polygons):
                # check the face normal, reject it if it's facing away.
                face_normal      = geom.face_data[obj_index][idx].normal
                world_coordinate = geom.face_data[obj_index][idx].location

                result_vector = eye_location - world_coordinate
                dot_value     = face_normal.dot(result_vector.normalized())

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
                            gather_index(geom.face_data[obj_index][idx], 'faces')
                    pass
                pass
            
            if display_edge_index:
                eps=1e-5
                for idx, edge in enumerate(edges):
                    world_coordinate = geom.edge_data[obj_index][idx].location
                    result_vector = eye_location - world_coordinate
                    dist = result_vector.length
                    if dist==0:
                        continue
                    
                    # cast ray from eye towards the median of the edge, the reycast will return (almost definitely..)

                    direction = world_coordinate - eye_location
                    direction.normalize()
                    hit = bvh.ray_cast(eye_location, direction)
                    if hit:
                        hit_co, hit_no, hit_index, hit_dist = hit
                        if hit_co is None or (hit_dist>=dist - eps):
                            cache_edge_indices.add(tuple(sorted([edge[0], edge[1]])))
                        pass
                    pass
            
            if display_vert_index:
                eps=1e-5
                for idx, vert in enumerate(vertices):
                    world_coordinate = geom.vert_data[obj_index][idx].location
                    result_vector = eye_location - world_coordinate
                    dist = result_vector.length
                    if dist==0:
                        continue
                    
                    # cast ray from eye towards the vert, the reycast will return (almost definitely..)
                    direction = world_coordinate - eye_location
                    direction.normalize()
                    hit = bvh.ray_cast(eye_location, direction)
                    if hit:
                        hit_co, hit_no, hit_index, hit_dist = hit
                        if hit_co is None or (hit_dist>=dist - eps):
                            cache_vert_indices.add(idx)
                        pass
                    pass

            for idx in cache_vert_indices:
                gather_index(geom.vert_data[obj_index][idx], 'verts')

            for edge_index, edge in enumerate(edges):
                if edge[0]>edge[1]:
                    sorted_edge = ( edge[1], edge[0] )
                else:
                    sorted_edge = tuple( edge )

                if sorted_edge in cache_edge_indices:
                    gather_index(geom.edge_data[obj_index][edge_index], 'edges')
                    cache_edge_indices.remove(sorted_edge)

        draw_all_text_at_once(final_draw_data)

    except Exception as err:
        print('---- ERROR in sv_idx_viewer28 Occlusion backface drawing ----')
        print(err)
        print(traceback.format_exc())

