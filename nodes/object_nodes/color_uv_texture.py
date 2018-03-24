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

import bpy
from math import *
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
import numpy as np
from bpy.props import BoolProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat)


class SvMeshUVColorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Find pixel on UV texture from surface'''
    bl_idname = 'SvMeshUVColorNode'
    bl_label = 'Set UV Color'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode1 = BoolProperty(name='normal_update', default=True, update=updateNode)
    image = StringProperty(default='', update=updateNode)
    object_ref = StringProperty(default='', update=updateNode)

    def draw_buttons(self, context,   layout):
        layout.prop_search(self, 'object_ref', bpy.data, 'objects')
        ob = bpy.data.objects.get(self.object_ref)
        if ob and ob.type == 'MESH':
            layout.prop_search(self, 'image', bpy.data, "images", text="")

    def sv_init(self, context):
        si, so = self.inputs.new, self.outputs.new
        si('VerticesSocket', 'Point on mesh')
        so('StringsSocket', 'color on mesh')

    def process(self):
        Point = self.inputs[0]
        obj = bpy.data.objects[self.object_ref]  # triangulated
        point = Point.sv_get()[0]
        ran = range(3)
        image = bpy.data.images[self.image]
        width = image.size[0]
        height = image.size[1]
        pixels = np.array(image.pixels[:]).reshape(width,height,4)
        for P in point:
            succ, location, norm,index = obj.closest_point_on_mesh(P)
            found_poly = obj.data.polygons[index]
            verticesIndices = found_poly.vertices
            p1, p2, p3 = [obj.data.vertices[verticesIndices[i]].co for i in ran]
            uvMapIndices = found_poly.loop_indices
            uvMap = obj.data.uv_layers[0]
            uv1, uv2, uv3 = [uvMap.data[uvMapIndices[i]].uv.to_3d() for i in ran]
            V = barycentric_transform(location, p1, p2, p3, uv1, uv2, uv3)
            Vx, Vy = int(V.x*width), int(V.y*height)
          #  if self.outputs[0].is_linked:
          #      self.outputs[0].sv_set(pixels[Vx, Vy])
            pixels[Vy, Vx, :] = 1  # paint white
        image.pixels = pixels.flatten().tolist()

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMeshUVColorNode)


def unregister():
    bpy.utils.unregister_class(SvMeshUVColorNode)
