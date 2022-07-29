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

import numpy as np

import bpy
from bpy.props import EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last_for_length
from sverchok.data_structure import match_long_repeat as mlrepeat
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from sverchok.utils.math import np_normalize_vectors


def flip_from_mask(mask, geom, reverse):
    """
    this mode expects a mask list with an element corresponding to each polygon
    """
    verts, edges, faces = geom
    mask_matched = repeat_last_for_length(mask, len(faces))
    b_faces = []
    for m, face in zip(mask_matched, faces):
        mask_val = bool(m) if not reverse else not bool(m)
        b_faces.append(face if mask_val else face[::-1])

    return verts, edges, b_faces


def flip_to_match_1st_np(geom, reverse):
    """
    this mode expects all faces to be coplanar, else you need to manually generate a flip mask.
    """
    verts, edges, faces = geom
    normals = face_normals_np(verts, faces)
    direction = normals[0]
    flips = np.isclose(np.dot(normals, direction), 1, atol=0.004)
    if reverse:
        flips = ~flips
    b_faces = [poly if flip else poly[::-1] for flip, poly in zip(flips, faces)]

    return verts, edges, b_faces


def face_normals_np(verts, faces):
    verts = np.asarray(verts)
    def first_3_indexes():
        for f in faces:
            for i in f[:3]:
                yield i
    faces = np.fromiter(first_3_indexes(), dtype=int)  # 2x faster than from list
    faces.shape = (-1, 3)
    v1 = verts[faces[:, 0]]
    v2 = verts[faces[:, 1]]
    v3 = verts[faces[:, 2]]
    d1 = v1 - v2
    d2 = v3 - v2
    normals = np.cross(d1, d2)
    np_normalize_vectors(normals)
    return normals


class SvFlipNormalsNode(ModifierNode, bpy.types.Node, SverchCustomTreeNode):
    ''' Flip face normals '''
    bl_idname = 'SvFlipNormalsNode'
    bl_label = 'Flip normals'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FLIP_NORMALS'

    mode_options = [(mode, mode, '', idx) for idx, mode in enumerate(['mask', 'match'])]

    selected_mode: EnumProperty(
        items=mode_options, description="offers flip options", default="match", update=updateNode)

    reverse: BoolProperty(update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvStringsSocket', 'Mask')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')

    def draw_buttons(self, context, layout):
        r = layout.row(align=True)
        r1 = r.split(factor=0.35)
        r1.prop(self, 'reverse', text='reverse', toggle=True)
        r2 = r1.split().row()
        r2.prop(self, "selected_mode", expand=True)

    def process(self):
        vertices_s = self.inputs['Vertices'].sv_get(default=[], deepcopy=False)
        edges_s = self.inputs['Edges'].sv_get(default=[[]], deepcopy=False)
        faces_s = self.inputs['Polygons'].sv_get(default=[], deepcopy=False)

        geom = [[], [], []]

        if self.selected_mode == 'mask':
            mask_s = self.inputs['Mask'].sv_get(default=[[True]], deepcopy=False)
            for *single_geom, mask in zip(*mlrepeat([vertices_s, edges_s, faces_s, mask_s])):
                for idx, d in enumerate(flip_from_mask(mask, single_geom, self.reverse)):
                    geom[idx].append(d)

        elif self.selected_mode == 'match':
            for single_geom in zip(*mlrepeat([vertices_s, edges_s, faces_s])):
                for idx, d in enumerate(flip_to_match_1st_np(single_geom, self.reverse)):
                    geom[idx].append(d)

        self.set_output(geom)

    def set_output(self, geom):
        _ = [self.outputs[idx].sv_set(data) for idx, data in enumerate(geom)]


def register():
    bpy.utils.register_class(SvFlipNormalsNode)


def unregister():
    bpy.utils.unregister_class(SvFlipNormalsNode)
