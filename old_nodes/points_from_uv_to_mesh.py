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
import bmesh
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
import numpy as np
from bpy.props import BoolProperty, StringProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import (updateNode)


def UV(self, object):
    # makes UV from layout texture area to sverchok vertices and polygons.
    bm = bmesh.new()
    bm.from_mesh(object.data)
    uv_layer = bm.loops.layers.uv[0]
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    vertices_dict = {}
    polygons_new = []
    polygons_new_append = polygons_new.append
    for fi in bm.faces:
        polygons_new_pol = []
        polygons_new_pol_append = polygons_new_pol.append
        for loop in fi.loops:
            li = loop.index
            polygons_new_pol_append(li)
            uv = loop[uv_layer].uv
            vertices_dict[li] = [ uv.x, uv.y, 0.0]

        polygons_new_append(polygons_new_pol)

    vertices_new = list( vertices_dict.values() )
    bm.clear()
    return [vertices_new, polygons_new]


class SvUVPointonMeshNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Transform vectors from UV space to Object space '''
    bl_idname = 'SvUVPointonMeshNode'
    bl_label = 'Find UV Coord on Surface'
    bl_icon = 'GROUP_UVS'
    is_scene_dependent = True
    is_animation_dependent = True

    object_ref: StringProperty(default='', update=updateNode)

    def sv_init(self, context):
        si, so = self.inputs.new, self.outputs.new
        si('SvObjectSocket', 'Mesh Object')
        si('SvVerticesSocket', 'Point on UV')
        so('SvVerticesSocket', 'Point on mesh')
        so('SvVerticesSocket', 'UVMapVert')
        so('SvStringsSocket', 'UVMapPoly')

    def process(self):
        Object, PointsUV = self.inputs
        Pom, uvV, uvP = self.outputs
        obj = Object.sv_get()[0]  # triangulate faces
        UVMAPV, UVMAPP = UV(self,obj)
        if Pom.is_linked:
            pointuv = PointsUV.sv_get()[0]
            bvh = BVHTree.FromPolygons(UVMAPV, UVMAPP, all_triangles=False, epsilon=0.0)
            ran = range(3)
            out = []
            uvMap = obj.data.uv_layers[0].data
            for Puv in pointuv:
                loc, norm, ind, dist = bvh.find_nearest(Puv)
                found_poly = obj.data.polygons[ind]
                verticesIndices = found_poly.vertices
                p1, p2, p3 = [obj.data.vertices[verticesIndices[i]].co for i in ran]
                uvMapIndices = found_poly.loop_indices
                uv1, uv2, uv3 = [uvMap[uvMapIndices[i]].uv.to_3d() for i in ran]
                V = barycentric_transform(Puv, uv1, uv2, uv3, p1, p2, p3)
                out.append(V[:])
            Pom.sv_set([out])
        if uvV.is_linked:
            uvV.sv_set([UVMAPV])
            uvP.sv_set([UVMAPP])


def register():
    bpy.utils.register_class(SvUVPointonMeshNode)


def unregister():
    bpy.utils.unregister_class(SvUVPointonMeshNode)
