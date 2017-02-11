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
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList
from sverchok.data_structure import match_long_repeat as mlrepeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh



def flip_from_mask(mask, geom, reverse):
    """
    this mode expects a mask list with an element corresponding to each polygon
    """
    verts, edges, faces = geom
    fullList(mask, len(faces))
    b_faces = []
    for m, face in zip(mask, faces):
        mask_val = bool(mask) if not reverse else not bool(mask)
        b_faces.append(face if mask_val else face[::-1])

    return verts, edges, b_faces


def flip_to_match_1st(geom, reverse):
    """
    this mode expects all faces to be coplanar, else you need to manually generate a flip mask.
    """
    ...


class SvFlipNormalsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Flip face normals '''
    bl_idname = 'SvFlipNormalsNode'
    bl_label = 'Flip normals'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode_options = [(mode, mode, '', idx) for idx, mode in enumerate(['mask', 'match'])]
        
    selected_mode = bpy.props.EnumProperty(
        items=mode_options, description="offers flip options", default="match", update=updateNode
    )

    reverse = BoolProperty(update=updateNode)


    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('StringsSocket', 'Edges')
        self.inputs.new('StringsSocket', 'Polygons')
        # self.inputs.new('StringsSocket', 'Mask')

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polygons')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'reverse', toggle=True)
        layout.prop(self, "selected_mode", expand=True)

    def process(self):

        if not any(self.outputs[idx].is_linked for idx in range(3)):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])

        if vertices_s == [[]] and faces_s == [[]]:
            return

        geom = [[], [], []]

        if selected_mode == 'mask':
            mask_s = self.inputs['Mask'].sv_get(default=[[True]])
            for (single_geom), mask in zip(*mlrepeat([vertices_s, edges_s, faces_s, mask_s])):
                for idx, d in enumerate(flip_from_mask(mask, single_geom, reverse)):
                    geom[idx].append(d)

        elif selected_mode == 'match':
                # bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)

                #for idx, d in pydata_from_bmesh(bm):
                #    geom[idx].append(d)
                #bm.free()


        self.set_output(result_vertices, result_edges, result_faces)


    def set_output(self, *geom):
        _ = [self.outputs[idx].sv_set(data) for idx, data in enumerate(geom)]


def register():
    bpy.utils.register_class(SvFlipNormalsNode)


def unregister():
    bpy.utils.unregister_class(SvFlipNormalsNode)
