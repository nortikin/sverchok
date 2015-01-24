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

from math import pi, degrees, floor, ceil, copysign
from mathutils import Vector, Matrix
import numpy as np

import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvBevelNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Bevel vertices, edges and faces'''
    bl_idname = 'SvBevelNode'
    bl_label = 'Bevel'
    bl_icon = 'OUTLINER_OB_EMPTY'

    offset_ = FloatProperty(name='Amount',
        description='Amount to offset beveled edge',
        default=0.0, min=0.0,
        update=updateNode)

    offset_modes = [
            ("0", "Offset", "Amount is offset of new edges from original", 1),
            ("1", "Width",  "Amount is width of new face", 2),
            ("2", "Depth",  "Amount is perpendicular distance from original edge to bevel face", 3),
            ("3", "Percent", "Amount is percent of adjacent edge length", 4)
        ]
    
    offsetType = EnumProperty(name='Amount Type',
        description="What distance Amount measures",
        items = offset_modes,
        update=updateNode)

    segments_ = IntProperty(name="Segments",
        description="Number of segments in bevel",
        default=1, min=1,
        update=updateNode)
    
    profile_ = FloatProperty(name="Profile",
        description="Profile shape; 0.5 - round",
        default=0.5, min=0.0, max=1.0,
        update=updateNode)
    
    vertexOnly = BoolProperty(name="Vertex only",
        description="Only bevel edges, not edges",
        default=False,
        update=updateNode)

#     clampOverlap = BoolProperty(name="Clamp overlap",
#         description="Do not allow beveled edges/vertices to overlap each other",
#         default=True,
#         update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')
        self.inputs.new('StringsSocket', 'BevelEdges')
        self.inputs.new('StringsSocket', "Offset").prop_name = "offset_"
        self.inputs.new('StringsSocket', "Segments").prop_name = "segments_"
        self.inputs.new('StringsSocket', "Profile").prop_name = "profile_"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polygons')
        self.outputs.new('StringsSocket', 'NewPolys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "offsetType")
        layout.prop(self, "vertexOnly")
        #layout.prop(self, "clampOverlap")

    def process(self):
        if not (self.inputs['Vertices'].is_linked and self.inputs['Polygons'].is_linked):
            return
        if not (any(self.outputs[name].is_linked for name in ['Vertices', 'Edges', 'Polygons', 'NewPolys'])):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        offsets_s = self.inputs['Offset'].sv_get()[0]
        segments_s = self.inputs['Segments'].sv_get()[0]
        profiles_s = self.inputs['Profile'].sv_get()[0]
        bevel_edges_s = self.inputs['BevelEdges'].sv_get(default=[[]])

        result_vertices = []
        result_edges = []
        result_faces = []
        result_bevel_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, bevel_edges_s, offsets_s, segments_s, profiles_s])

        for vertices, edges, faces, bevel_edges, offset, segments, profile in zip(*meshes):

            bm = bmesh_from_pydata(vertices, edges, faces)

            if bevel_edges:
                b_edges = []
                for edge in bevel_edges:
                    b_edge = [e for e in bm.edges if set([v.index for v in e.verts]) == set(edge)]
                    b_edges.append(b_edge[0])
            else:
                b_edges = bm.edges

            geom = list(bm.verts) + list(b_edges) + list(bm.faces)
            bevel_faces = bmesh.ops.bevel(bm, geom=geom, offset=offset,
                            offset_type=int(self.offsetType), segments=segments,
                            profile=profile, vertex_only=self.vertexOnly,
                            #clamp_overlap=self.clampOverlap,
                            material=-1)['faces']
            new_bevel_faces = [[v.index for v in face.verts] for face in bevel_faces]
            new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()

            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_bevel_faces.append(new_bevel_faces)

        self.outputs['Vertices'].sv_set(result_vertices)
        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(result_edges)
        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(result_faces)
        if self.outputs['NewPolys'].is_linked:
            self.outputs['NewPolys'].sv_set(result_bevel_faces)

def register():
    bpy.utils.register_class(SvBevelNode)


def unregister():
    bpy.utils.unregister_class(SvBevelNode)

if __name__ == '__main__':
    register()


