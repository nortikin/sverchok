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
        si,so = self.inputs.new,self.outputs.new
        si('VerticesSocket', "Vertices")
        si('StringsSocket', 'Edges')
        si('StringsSocket', 'Polygons')
        si('StringsSocket', 'BevelEdges')
        si('StringsSocket', "Offset").prop_name = "offset_"
        si('StringsSocket', "Segments").prop_name = "segments_"
        si('StringsSocket', "Profile").prop_name = "profile_"
        so('VerticesSocket', 'Vertices')
        so('StringsSocket', 'Edges')
        so('StringsSocket', 'Polygons')
        so('StringsSocket', 'NewPolys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "offsetType")
        layout.prop(self, "vertexOnly")
        #layout.prop(self, "clampOverlap")

    def process(self):
        InV,InE,InP,BE,O,S,Pr = self.inputs
        oV,oE,oP,NP = self.outputs
        if not (InV.is_linked and InP.is_linked):
            return
        if not (any(self.outputs[name].is_linked for name in ['Vertices', 'Edges', 'Polygons', 'NewPolys'])):
            return
        vertices_s = InV.sv_get(default=[[]])
        edges_s = InE.sv_get(default=[[]])
        faces_s = InP.sv_get(default=[[]])
        offsets_s = O.sv_get()[0]
        segments_s = S.sv_get()[0]
        profiles_s = Pr.sv_get()[0]
        bevel_edges_s = BE.sv_get(default=[[]])
        out,result_bevel_faces = [],[]
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
            out.append(pydata_from_bmesh(bm))
            bm.free()
            result_bevel_faces.append(new_bevel_faces)
        oV.sv_set([[i[0]] for i in out])
        if oE.is_linked:
            oE.sv_set([[i[1]] for i in out])
        if oP.is_linked:
            oP.sv_set([[i[2]] for i in out])
        if NP.is_linked:
            NP.sv_set(result_bevel_faces)


def register():
    bpy.utils.register_class(SvBevelNode)


def unregister():
    bpy.utils.unregister_class(SvBevelNode)
