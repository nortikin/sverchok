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
import math
import mathutils
from mathutils import Vector, Matrix
import node_Viewer
from node_Viewer import *
from util import *

global temp_handle
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


def callback_enable(name, sl1, sl2, sl3, vs, colo, tran, shade):
    global temp_handle
    handle = handle_read(name)
    if handle[0]:
        return
    handle_view = SpaceView3D.draw_handler_add(draw_callback_view, (name, sl1, sl2, sl3, vs, colo, tran, shade), 'WINDOW', 'POST_VIEW')
    handle_write(name, handle_view)
    tag_redraw_all_view3d()
    

def callback_disable(name):
    global temp_handle
    handle = handle_read(name)
    if not handle[0]:
        return
    handle_view = handle[1]
    SpaceView3D.draw_handler_remove(handle_view, 'WINDOW')
    handle_delete(name)
    tag_redraw_all_view3d()
   
    
def draw_callback_view(handle, sl1, sl2, sl3, vs, colo, tran, shade):
    context = bpy.context

    from bgl import glEnable, glDisable, glColor3f, glVertex3f, glPointSize, glLineWidth, glBegin, glEnd, glLineStipple, GL_POINTS, GL_LINE_STRIP, GL_LINES, GL_LINE, GL_LINE_STIPPLE, GL_POLYGON, GL_POLYGON_STIPPLE, GL_POLYGON_SMOOTH, glPolygonStipple
    
    # define globals, separate edgs from pols
    if tran:
        polyholy = GL_POLYGON_STIPPLE
    else:
        polyholy = GL_POLYGON
    if sl1:
        data_vector = Vector_generate(sl1)
        verlen = len(data_vector) - 1
    else:
        data_vector = []
        verlen = 0
        
    if sl2:
        if len(sl2[0][0]) == 2:
            data_edges = sl2
            data_polygons = []
        elif len(sl2[0][0]) > 2:
            data_polygons = sl2
            data_edges = []
    else:
        data_edges, data_polygons = [], []
    if sl3:
        data_matrix = Matrix_generate(sl3)
    else:
        data_matrix = []
        for i in range(0, verlen+1):
            data_matrix.append(Matrix())
    coloa = colo[0]
    colob = colo[1]
    coloc = colo[2]
    
    if data_vector == 0 and data_polygons == 0 and data_matrix == 0 and data_edges == 0:
        callback_disable(handle)
    #print ('вход', sl1, sl2, sl3)
    #print ('преобраз', data_vector)
    
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
        # x
        glColor3f(1.0, 0.2, 0.2)
        glBegin(GL_LINES)
        glVertex3f(*(zero_tx))
        glVertex3f(*(mat * x_p))
        glEnd()

        glColor3f(0.6, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(*(zero_tx))
        glVertex3f(*(mat * x_n))
        glEnd()
    
        # y
        glColor3f(0.2, 1.0, 0.2)
        glBegin(GL_LINES)
        glVertex3f(*(zero_tx))
        glVertex3f(*(mat * y_p))
        glEnd()
    
        glColor3f(0.0, 0.6, 0.0)
        glBegin(GL_LINES)
        glVertex3f(*(zero_tx))
        glVertex3f(*(mat * y_n))
        glEnd()
    
        # z
        glColor3f(0.2, 0.2, 1.0)
        glBegin(GL_LINES)
        glVertex3f(*(zero_tx))
        glVertex3f(*(mat * z_p))
        glEnd()
    
        glColor3f(0.0, 0.0, 0.6)
        glBegin(GL_LINES)
        glVertex3f(*(zero_tx))
        glVertex3f(*(mat * z_n))
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
    
        for i in range(0,24,2):
            glBegin(GL_LINE_STRIP)
            glVertex3f(*bb[i])
            glVertex3f(*bb[i+1])
            glEnd()
    
        
    
    ########
    # points
    if vs:
        if data_vector:
            glPointSize(3.0)
            glColor3f(0.8, 0.9, 1.0)
            
            for i, matrix in enumerate(data_matrix):
                glBegin(GL_POINTS)
                k = i
                if i > verlen:
                    k = verlen
                for vert in data_vector[k]:
                    vec_corrected = data_matrix[i]*vert
                    glVertex3f(*vec_corrected)
                    #print ('рисовальня', matrix, vec_corrected)
                glEnd()
                glPointSize(3.0)
    
    #######
    # lines
    if data_edges and data_vector:
        glColor3f(coloa,colob,coloc)
        glLineWidth(1.0)
        glEnable(GL_LINES)
        
        for i, matrix in enumerate(data_matrix):    # object
            k = i
            if i > verlen:
                k = verlen
            for line in data_edges[k]:                 # line
                glBegin(GL_LINES)
                for point in line:              # point
                    vec_corrected = data_matrix[i]*data_vector[k][int(point)]
                    glVertex3f(*vec_corrected)
                glEnd()
                glPointSize(1.75)
                glLineWidth(1.0)
        glDisable(GL_LINES)
        
        
    #######
    # polygons
    vectorlight = Vector((-0.66,-0.66,-0.66))
    if data_polygons and data_vector:
        glLineWidth(1.0)
        glEnable(polyholy)
        
        for i, matrix in enumerate(data_matrix):    # object
            k = i
            if i > verlen:
                k = verlen
            oblen = len(data_polygons[k])
            for j, pol in enumerate(data_polygons[k]):
                glBegin(GL_POLYGON)
                if shade:
                    normal_no_ = mathutils.geometry.normal(
                            data_vector[k][pol[0]],
                            data_vector[k][pol[1]],
                            data_vector[k][pol[2]]
                            )
                    normal_no = (normal_no_.angle(vectorlight,0))/math.pi
                    randa = (normal_no * coloa) - 0.1
                    randb = (normal_no * colob) - 0.1
                    randc = (normal_no * coloc) - 0.1
                else:
                    randa = ((j/oblen) + coloa) / 2.5
                    randb = ((j/oblen) + colob) / 2.5
                    randc = ((j/oblen) + coloc) / 2.5
                glColor3f(randa+0.2, randb+0.2, randc+0.2)
                for point in pol:
                    vec_corrected = data_matrix[i]*data_vector[k][int(point)]
                    glVertex3f(*vec_corrected)
                glEnd()
                glPointSize(1.75)
                glLineWidth(1.0)
        glDisable(polyholy)
        
    # for future bezier drawing - to remake
    #if data_edges and data_vector and bezier:
        # here 3 lines that i must understand
        #from bpy_extras.view3d_utils import location_3d_to_region_2d
        #region = context.region
        #region_data = context.region_data
        
        #glEnable(GL_BLEND)
        #glColor4f(1, 0, 0, 0.5)
        #glLineWidth(1.0)
        #glBegin(GL_LINE_STRIP)
        #for i in range(current_frame):
            #glVertex2f(*location_3d_to_region_2d(region, region_data, (math.sin(i / 10), 0, i / 10)).to_tuple())
        #glEnd()
        #glDisable(GL_BLEND)
    
    #######
    # matrix
    if data_matrix and not data_vector:
        for mat in data_matrix:
            draw_matrix(mat)
    
    