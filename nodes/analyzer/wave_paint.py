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
from bpy.props import EnumProperty, IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import (bmesh_from_pydata,
        wave_markup_faces, wave_markup_verts,
        fill_faces_layer, fill_verts_layer
    )

class SvWavePainterNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: wave pattern
    Tooltip: Mark up mesh faces or vertices with a wave pattern
    """

    bl_idname = 'SvWavePainterNode'
    bl_label = 'Wave Paint'
    bl_icon = 'FILTER'

    face_modes = [
            ("edge", "By Edge", "Neighbours are faces with common edge", 0),
            ("vertex", "By Vertex", "Neighbours are faces with common vertex", 1)
        ]
    
    face_mode : EnumProperty(
            name = "Neighbour faces",
            description = "Neighbour faces definition mode",
            items = face_modes,
            update = updateNode)

    vert_modes = [
            ("edge", "By Edge", "Neighbours are vertices with common edge", 0),
            ("face", "By Face", "Neighbours are vertices with common face", 1)
        ]

    vert_mode : EnumProperty(
            name = "Neighbour vertices",
            description = "Neighbour vertices definition mode",
            items = vert_modes,
            update = updateNode)

    modes = [
            ("vertex", "Vertices", "Paint on vertices", 0),
            ("face", "Faces", "Paint on faces", 1)
        ]

    mode : EnumProperty(
            name = "Mode",
            description = "Painting mode",
            items = modes,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Paint on:")
        layout.prop(self, 'mode', expand=True)
        layout.label(text="Neighbours:")
        if self.mode == 'vertex':
            layout.prop(self, 'vert_mode', expand=True)
        else:
            layout.prop(self, 'face_mode', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvStringsSocket', "InitMask")
        self.inputs.new('SvStringsSocket', "ObstacleMask")

        self.outputs.new('SvStringsSocket', "WaveFront")
        self.outputs.new('SvStringsSocket', "WaveDistance")

    def process(self):

        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get()
        init_masks_s = self.inputs['InitMask'].sv_get() # mandatory input
        obstacle_masks_s = self.inputs['ObstacleMask'].sv_get(default = [[]])

        wave_front_out = []
        wave_distances_out = []
        meshes = zip_long_repeat(vertices_s, edges_s, faces_s, init_masks_s, obstacle_masks_s)
        for vertices, edges, faces, init_mask, obstacle_masks in meshes:
            bm = bmesh_from_pydata(vertices, edges, faces)
            if obstacle_masks:
                if self.mode == 'face':
                    fullList(obstacle_masks, len(faces))
                    bm.faces.layers.int.new("wave_obstacle")
                    bm.faces.ensure_lookup_table()
                    fill_faces_layer(bm, obstacle_masks, "wave_obstacle", int, 1)
                else: #verts
                    fullList(obstacle_masks, len(vertices))
                    bm.verts.layers.int.new("wave_obstacle")
                    bm.verts.ensure_lookup_table()
                    fill_verts_layer(bm, obstacle_masks, "wave_obstacle", int, 1)

            if self.mode == 'face':
                by_vert = self.face_mode == 'vertex'
                new_wave_front = wave_markup_faces(bm, init_mask, neighbour_by_vert=by_vert, find_shortest_path=True)
                distance = bm.faces.layers.float.get("wave_path_distance")
                new_distances = [face[distance] for face in bm.faces]
            else: # verts
                by_edge = self.vert_mode == 'edge'
                new_wave_front = wave_markup_verts(bm, init_mask, neighbour_by_edge=by_edge, find_shortest_path=True)
                distance = bm.verts.layers.float.get("wave_path_distance")
                new_distances = [vert[distance] for vert in bm.verts]

            bm.free()
            wave_front_out.append(new_wave_front)
            wave_distances_out.append(new_distances)

        self.outputs['WaveFront'].sv_set(wave_front_out)
        self.outputs['WaveDistance'].sv_set(wave_distances_out)

def register():
    bpy.utils.register_class(SvWavePainterNode)


def unregister():
    bpy.utils.unregister_class(SvWavePainterNode)

