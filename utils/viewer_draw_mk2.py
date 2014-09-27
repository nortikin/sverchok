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

import math
import time
from math import pi

import bpy
import mathutils
from mathutils import Vector, Matrix
from mathutils.geometry import normal
from mathutils.geometry import tessellate_polygon as tessellate

from data_structure import Vector_generate, Matrix_generate

callback_dict = {}
SpaceView3D = bpy.types.SpaceView3D

from bgl import (
    glEnable, glDisable, glBegin, glEnd,
    Buffer, GL_FLOAT, GL_BYTE, GL_INT,
    glGetIntegerv, glGetFloatv,
    glColor3f, glVertex3f, glColor4f, glPointSize, glLineWidth,
    glLineStipple, glPolygonStipple, glHint, glShadeModel,
    #
    GL_MATRIX_MODE, GL_MODELVIEW_MATRIX, GL_MODELVIEW, GL_PROJECTION,
    glMatrixMode, glLoadMatrixf, glPushMatrix, glPopMatrix, glLoadIdentity,
    glGenLists, glNewList, glEndList, glCallList, glFlush, GL_COMPILE,
    #
    GL_POINTS, GL_POINT_SIZE, GL_POINT_SMOOTH, GL_POINT_SMOOTH_HINT,
    GL_LINE, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP, GL_LINE_STIPPLE,
    GL_POLYGON, GL_POLYGON_STIPPLE, GL_TRIANGLES, GL_QUADS,
    GL_NICEST, GL_FASTEST, GL_FLAT, GL_SMOOTH, GL_LINE_SMOOTH_HINT)

# ------------------------------------------------------------------------ #
# parts taken from  "Math Vis (Console)" addon, author Campbell Barton     #
# ------------------------------------------------------------------------ #


class MatrixDraw(object):

    def __init__(self):
        self.zero = Vector((0.0, 0.0, 0.0))
        self.x_p = Vector((0.5, 0.0, 0.0))
        self.x_n = Vector((-0.5, 0.0, 0.0))
        self.y_p = Vector((0.0, 0.5, 0.0))
        self.y_n = Vector((0.0, -0.5, 0.0))
        self.z_p = Vector((0.0, 0.0, 0.5))
        self.z_n = Vector((0.0, 0.0, -0.5))
        self.bb = [Vector() for i in range(24)]

    def draw_matrix(self, mat):
        bb = self.bb
        zero_tx = mat * self.zero

        axis = [
            [(1.0, 0.2, 0.2), self.x_p],
            [(0.6, 0.0, 0.0), self.x_n],
            [(0.2, 1.0, 0.2), self.y_p],
            [(0.0, 0.6, 0.0), self.y_n],
            [(0.2, 0.2, 1.0), self.z_p],
            [(0.0, 0.0, 0.6), self.z_n]
        ]

        glLineWidth(2.0)
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
        glDisable(GL_LINE_STIPPLE)


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


def get_color_from_normal(dvk, pol, num_verts, vectorlight, colo):
    if num_verts <= 4:
        normal_no = normal(dvk[pol[0]], dvk[pol[1]], dvk[pol[2]])
    else:
        normal_no = normal(dvk[pol[0]], dvk[pol[1]], dvk[pol[2]], dvk[pol[3]])

    normal_no = (normal_no.angle(vectorlight, 0)) / pi

    r = (normal_no * colo[0]) - 0.1
    g = (normal_no * colo[1]) - 0.1
    b = (normal_no * colo[2]) - 0.1
    return (r+0.2, g+0.2, b+0.2)


def display_face(options, pol, data_vector, data_matrix, k, i):

    colo = options['face_colors']
    shade = options['shading']
    forced_tessellation = options['forced_tessellation']

    num_verts = len(pol)
    dvk = data_vector[k]

    if shade:
        vectorlight = options['light_direction']
        face_color = get_color_from_normal(dvk, pol, num_verts, vectorlight, colo)
    else:
        face_color = colo[:]

    glColor3f(*face_color)

    if (num_verts in {3, 4}) or (not forced_tessellation):
        glBegin(GL_POLYGON)
        for point in pol:
            vec = data_matrix[i] * dvk[point]
            glVertex3f(*vec)
        glEnd()

    else:
        ''' ngons, we tessellate '''
        glBegin(GL_TRIANGLES)
        v = [dvk[i] for i in pol]
        for pol in tessellate([v]):
            for point in pol:
                vec = data_matrix[i]*v[point]
                glVertex3f(*vec)
        glEnd()


def processor(dvecs, dedges, dpoly, dmatrx):
    pass


def draw_geometry(n_id, options, data_vector, data_polygons, data_matrix, data_edges):

    show_verts = options['show_verts']
    show_edges = options['show_edges']
    show_faces = options['show_faces']

    vertex_colors = options['vertex_colors']
    edge_colors = options['edge_colors']
    edge_width = options['edge_width']

    tran = options['transparent']
    shade = options['shading']

    verlen = options['verlen']
    if 'verlen_every' in options:
        verlen_every = options['verlen_every']

    if tran:
        polyholy = GL_POLYGON_STIPPLE
        edgeholy = GL_LINE_STIPPLE
        edgeline = GL_LINE_STRIP
    else:
        polyholy = GL_POLYGON
        edgeholy = GL_LINE
        edgeline = GL_LINES

    def get_max_k(i, verlen):
        k = i
        if i > verlen:
            k = verlen
        return k

    # processed_geometry = processor(data_vector, data_edges, data_edges, data_matrix)

    ''' polygons '''

 

    glCallList(the_display_list)
    glFlush()

    # restore to system state
    glLineWidth(1)

    if options["timings"]:
        stop = time.perf_counter()
        print("callback drawn in {:4f}".format(stop-start))

    # has drawn once with success.
    options['draw_list'] = 1


def unregister():
    callback_disable_all()
