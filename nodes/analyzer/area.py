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

from sverchok.utils.modules.polygon_utils import areas_from_polygons



class SvAreaNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Area '''
    bl_idname = 'SvAreaNode'
    bl_label = 'Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'

    sum_faces: BoolProperty(name='sum faces', default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('StringsSocket', "Polygons")
        self.outputs.new('StringsSocket', "Area")

    def draw_buttons(self, context, layout):
        layout.prop(self, "sum_faces", text="Sum Faces")

    def process(self):
        inputs = self.inputs
        Vertices = inputs["Vertices"].sv_get()
        Polygons = inputs["Polygons"].sv_get()

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
