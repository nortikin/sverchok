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

import math

import bpy
import mathutils
from mathutils import Vector, Matrix

from data_structure import Vector_generate, Matrix_generate

callback_dict = {}
SpaceView3D = bpy.types.SpaceView3D

# ------------------------------------------------------------------------ #
# THIS part taken from  "Math Vis (Console)" addon, author Campbell Barton #
# With some editing for Sverchok                                           #
# ------------------------------------------------------------------------ #


def tag_redraw_all_view3d():
    context = bpy.context

    # Py cant access notifers
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()


def callback_enable(n_id, cached_view, options):
    global callback_dict
    if n_id in callback_dict:
        return

    config = (n_id, cached_view, options)
    handle_view = SpaceView3D.draw_handler_add(
        draw_callback_view, config, 'WINDOW', 'POST_VIEW')

    callback_dict[n_id] = handle_view
    tag_redraw_all_view3d()


def callback_disable_all():
    global callback_dict
    temp_list = list(callback_dict.keys())
    for name in temp_list:
        if name:
            callback_disable(name)


def callback_disable(n_id):
    global callback_dict
    handle_view = callback_dict.get(n_id, None)
    if not handle_view:
        return

    SpaceView3D.draw_handler_remove(handle_view, 'WINDOW')
    del callback_dict[n_id]
    tag_redraw_all_view3d()


def draw_callback_view(n_id, cached_view, options):
    context = bpy.context
    from bgl import (
        glEnable, glDisable, glColor3f, glVertex3f, glColor4f, glPointSize,
        glLineWidth, glBegin, glEnd, glLineStipple, glPolygonStipple, glHint,
        GL_POINTS, GL_LINE_STRIP, GL_LINES, GL_LINE, GL_LINE_LOOP, GL_LINE_STIPPLE,
        GL_POLYGON, GL_POLYGON_STIPPLE, GL_TRIANGLES, GL_QUADS, GL_POINT_SIZE,
        GL_POINT_SMOOTH, GL_POINT_SMOOTH_HINT, GL_NICEST, GL_FASTEST)

    sl1 = cached_view[n_id + 'v']
    sl2 = cached_view[n_id + 'ep']
    sl3 = cached_view[n_id + 'm']
    show_verts = options['show_verts']
    show_edges = options['show_edges']
    show_faces = options['show_faces']
    colo = options['face_colors']
    tran = options['transparent']
    shade = options['shading']
    vertex_colors = options['vertex_colors']
    edge_colors = options['edge_colors']
    edge_width = options['edge_width']

    if tran:
        polyholy = GL_POLYGON_STIPPLE
        edgeholy = GL_LINE_STIPPLE
        edgeline = GL_LINE_STRIP
    else:
        polyholy = GL_POLYGON
        edgeholy = GL_LINE
        edgeline = GL_LINES

    if sl1:
        data_vector = Vector_generate(sl1)
        verlen = len(data_vector)-1
        verlen_every = [len(d)-1 for d in data_vector]
    else:
        data_vector = []
        verlen = 0

    data_polygons = []
    data_edges = []
    if sl2:
        if sl2[0]:
            if len(sl2[0][0]) == 2:
                data_edges = sl2
                data_polygons = []
            elif len(sl2[0][0]) > 2:
                data_polygons = sl2
                data_edges = []

    if sl3:
        data_matrix = Matrix_generate(sl3)
    else:
        data_matrix = [Matrix() for i in range(verlen+1)]

    if (data_vector, data_polygons, data_matrix, data_edges) == (0, 0, 0, 0):
        callback_disable(n_id)

    coloa = colo[0]
    colob = colo[1]
    coloc = colo[2]

    # draw_matrix vars
    zero = Vector((0.0, 0.0, 0.0))
    x_p = Vector((0.5, 0.0, 0.0))
    x_n = Vector((-0.5, 0.0, 0.0))
    y_p = Vector((0.0, 0.5, 0.0))
    y_n = Vector((0.0, -0.5, 0.0))
    z_p = Vector((0.0, 0.0, 0.5))
    z_n = Vector((0.0, 0.0, -0.5))
    bb = [Vector() for i in range(24)]

    def draw_matrix(mat):
        zero_tx = mat * zero
        glLineWidth(2.0)

        axis = [
            [(1.0, 0.2, 0.2), x_p],
            [(0.6, 0.0, 0.0), x_n],
            [(0.2, 1.0, 0.2), y_p],
            [(0.0, 0.6, 0.0), y_n],
            [(0.2, 0.2, 1.0), z_p],
            [(0.0, 0.0, 0.6), z_n]
        ]

        for col, axial in axis:
            glColor3f(*col)
            glBegin(GL_LINES)
            glVertex3f(*(zero_tx))
            glVertex3f(*(mat * axial))
            glEnd()

        # bounding box vertices
        i = 0
        glColor3f(1.0, 1.0, 1.0)
        series1 = (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)
        series2 = (-0.5, 0.5)
        z = 0
        for x in series1:
            for y in series2:
                bb[i][:] = x, y, z
                bb[i] = mat * bb[i]
                i += 1
        for y in series1:
            for x in series2:
                bb[i][:] = x, y, z
                bb[i] = mat * bb[i]
                i += 1

        # bounding box drawing
        glLineWidth(1.0)
        glLineStipple(1, 0xAAAA)
        glEnable(GL_LINE_STIPPLE)

        for i in range(0, 24, 2):
            glBegin(GL_LINE_STRIP)
            glVertex3f(*bb[i])
            glVertex3f(*bb[i+1])
            glEnd()

    glDisable(GL_POINT_SIZE)

    ''' polygons '''

    vectorlight = options['light_direction']
    if data_polygons and data_vector:

        glLineWidth(1.0)
        glEnable(polyholy)
        normal = mathutils.geometry.normal

        for i, matrix in enumerate(data_matrix):
            k = i
            if i > verlen:
                k = verlen

            oblen = len(data_polygons[k])
            for j, pol in enumerate(data_polygons[k]):

                if max(pol) > verlen_every[k]:
                    pol = data_edges[k][-1]
                    j = len(data_edges[k])-1

                if shade:
                    dvk = data_vector[k]
                    normal_no_ = normal(dvk[pol[0]], dvk[pol[1]], dvk[pol[2]])
                    normal_no = (normal_no_.angle(vectorlight, 0)) / math.pi
                    randa = (normal_no * coloa) - 0.1
                    randb = (normal_no * colob) - 0.1
                    randc = (normal_no * coloc) - 0.1
                else:
                    randa = ((j/oblen) + coloa) / 2.5
                    randb = ((j/oblen) + colob) / 2.5
                    randc = ((j/oblen) + coloc) / 2.5

                face_color = (randa+0.2, randb+0.2, randc+0.2)
                if len(pol) > 4:
                    glBegin(GL_TRIANGLES)
                    glColor3f(*face_color)

                    v = [data_vector[k][i] for i in pol]
                    tess_poly = mathutils.geometry.tessellate_polygon([v])
                    for a, b, c in tess_poly:
                        glVertex3f(*(data_matrix[i]*v[a]))
                        glVertex3f(*(data_matrix[i]*v[b]))
                        glVertex3f(*(data_matrix[i]*v[c]))

                elif len(pol) == 4:
                    glBegin(GL_POLYGON)
                    glColor3f(*face_color)
                    for point in pol:
                        vec_corrected = data_matrix[i]*data_vector[k][int(point)]
                        glVertex3f(*vec_corrected)
                else:
                    glBegin(GL_TRIANGLES)
                    glColor3f(*face_color)
                    for point in pol:
                        vec_corrected = data_matrix[i]*data_vector[k][int(point)]
                        glVertex3f(*vec_corrected)

                glEnd()

                if show_edges:
                    glLineWidth(edge_width)
                    glBegin(GL_LINE_LOOP)
                    glColor3f(*edge_colors)
                    for point in pol:
                        vec_corrected = data_matrix[i]*data_vector[k][int(point)]
                        glVertex3f(*vec_corrected)
                    glEnd()

                glPointSize(1.75)
                glLineWidth(1.0)
        glDisable(polyholy)

    ''' edges '''

    if data_edges and data_vector and show_edges:
        glColor3f(*edge_colors)
        glLineWidth(edge_width)
        glEnable(edgeholy)

        for i, matrix in enumerate(data_matrix):    # object
            k = i
            if i > verlen:   # filter to share objects
                k = verlen
            for line in data_edges[k]:                 # line
                if max(line) > verlen_every[k]:
                    line = data_edges[k][-1]
                glBegin(edgeline)
                for point in line:              # point
                    vec_corrected = data_matrix[i]*data_vector[k][int(point)]
                    glVertex3f(*vec_corrected)
                glEnd()
                # glPointSize(1.75)
                # glLineWidth(1.0)
        glDisable(edgeholy)

    ''' vertices '''

    glEnable(GL_POINT_SIZE)
    glEnable(GL_POINT_SMOOTH)
    #glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
    glHint(GL_POINT_SMOOTH_HINT, GL_FASTEST)

    vsize = options['vertex_size']

    if show_verts and data_vector:
        glPointSize(vsize)
        glColor3f(*vertex_colors)

        for i, matrix in enumerate(data_matrix):
            glBegin(GL_POINTS)
            k = i
            if i > verlen:
                k = verlen
            for vert in data_vector[k]:
                vec_corrected = data_matrix[i]*vert
                glVertex3f(*vec_corrected)
            glEnd()

    #######
    # matrix
    if data_matrix and not data_vector:
        for mat in data_matrix:
            draw_matrix(mat)


def unregister():
    callback_disable_all()
