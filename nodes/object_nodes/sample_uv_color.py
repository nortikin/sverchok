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
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
import numpy as np
from bpy.props import BoolProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class SvSampleUVColorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Sample pixel color on UV texture from surface'''
    bl_idname = 'SvSampleUVColorNode'
    bl_label = 'Sample UV Color'
    bl_icon = 'UV'

    image: StringProperty(default='', update=updateNode)
    object_ref: StringProperty(default='', update=updateNode)

    def draw_buttons(self, context,   layout):
        layout.prop_search(self, 'object_ref', bpy.data, 'objects')
        ob = bpy.data.objects.get(self.object_ref)
        if ob and ob.type == 'MESH':
            layout.prop_search(self, 'image', bpy.data, "images", text="")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Point on mesh')
        self.outputs.new('SvColorSocket', 'Color on UV')

    def process(self):
        Points = self.inputs[0]
        Colors = self.outputs[0]
        if Colors.is_linked:
            obj = bpy.data.objects[self.object_ref]  # triangulate faces
            bvh = BVHTree.FromObject(obj, bpy.context.scene, deform=True, render=False, cage=False, epsilon=0.0)
            point = Points.sv_get()[0]
            outc = []
            ran = range(3)
            image = bpy.data.images[self.image]
            width, height = image.size
            pixels = np.array(image.pixels[:]).reshape(width, height, 4)
            uvMap = obj.data.uv_layers[0].data
            for P in point:
                loc, norm, ind, dist = bvh.find_nearest(P)
                found_poly = obj.data.polygons[ind]
                verticesIndices = found_poly.vertices
                p1, p2, p3 = [obj.data.vertices[verticesIndices[i]].co for i in ran]
                uvMapIndices = found_poly.loop_indices
                uv1, uv2, uv3 = [uvMap[uvMapIndices[i]].uv.to_3d() for i in ran]
                V = barycentric_transform(loc, p1, p2, p3, uv1, uv2, uv3)
                outc.append(pixels[int(V.x*(width-1)), int(V.y*(height-1))].tolist())
            Colors.sv_set([outc])


def register():
    bpy.utils.register_class(SvSampleUVColorNode)


def unregister():
    bpy.utils.unregister_class(SvSampleUVColorNode)
