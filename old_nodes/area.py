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

from mathutils import Vector, Matrix

import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from mathutils.geometry import area_tri as area
from mathutils.geometry import tessellate_polygon as tessellate

def areas_from_polygons(verts, polygons, sum_faces=False):
    '''
    returns pols area as [float, float,...]
    vertices: list as [vertex, vertex, ...], being each vertex [float, float, float].
    faces: list as [polygon, polygon,..], being each polygon [int, int, ...].
    sum_faces if True it will return the sum of the areas as [float]
    '''
    areas = []
    concat_area = areas.append

    for polygon in polygons:
        num = len(polygon)
        if num == 3:
            concat_area(area(verts[polygon[0]], verts[polygon[1]], verts[polygon[2]]))
        elif num == 4:
            area_1 = area(verts[polygon[0]], verts[polygon[1]], verts[polygon[2]])
            area_2 = area(verts[polygon[0]], verts[polygon[2]], verts[polygon[3]])
            concat_area(area_1 + area_2)
        elif num > 4:
            ngon_area = 0.0
            subcoords = [Vector(verts[idx]) for idx in polygon]
            for tri in tessellate([subcoords]):
                ngon_area += area(*[verts[polygon[i]] for i in tri])
            concat_area(ngon_area)
        else:
            concat_area(0)

    if sum_faces:
        areas = [sum(areas)]

    return areas

class SvAreaNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Area '''
    bl_idname = 'SvAreaNode'
    bl_label = 'Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'

    replacement_nodes = [('SvAreaNodeMK2', dict(Vertices='vertices', Polygons='polygons'), dict(Area='area'))]

    sum_faces: BoolProperty(name='sum faces', default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Polygons")
        self.outputs.new('SvStringsSocket', "Area")

    def draw_buttons(self, context, layout):
        layout.prop(self, "sum_faces", text="Sum Faces")

    def process(self):
        inputs = self.inputs
        Vertices = inputs["Vertices"].sv_get(default=None)
        Polygons = inputs["Polygons"].sv_get(default=None)

        outputs = self.outputs
        if not outputs['Area'].is_linked or not all([Vertices, Polygons]):
            return

        # no smart auto extending here.
        areas = []
        for verts, faces in zip(Vertices, Polygons):
            areas.append(areas_from_polygons(verts, faces, sum_faces=self.sum_faces))
        
        outputs['Area'].sv_set(areas)


def register():
    bpy.utils.register_class(SvAreaNode)


def unregister():
    bpy.utils.unregister_class(SvAreaNode)

