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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


class SvVolumeNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: volume
    Tooltip: Calculate volume of an object
    """
    bl_idname = 'SvVolumeNodeMK2'
    bl_label = 'Volume'
    bl_icon = 'SNAP_VOLUME'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vers')
        self.inputs.new('SvStringsSocket', "Pols")
        self.outputs.new('SvStringsSocket', "Volume")

    def process(self):
        vertices = self.inputs['Vers'].sv_get(deepcopy=False, default=[])
        faces = self.inputs['Pols'].sv_get(deepcopy=False, default=[])

        out = []
        for verts_obj, faces_obj in zip(vertices, faces):
            bm = bmesh_from_pydata(verts_obj, [], faces_obj, normal_update=True)
            out.append([bm.calc_volume()])
            bm.free()

        self.outputs[0].sv_set(out)


def register():
    bpy.utils.register_class(SvVolumeNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvVolumeNodeMK2)

