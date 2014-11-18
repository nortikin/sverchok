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
import mathutils
from mathutils import Vector
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import (updateNode, Vector_generate, SvSetSocketAnyType,
                                     SvGetSocketAnyType, match_long_repeat)


class SvRayCastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' RayCast Object '''
    bl_idname = 'SvRayCastObjectNode'
    bl_label = 'object_raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('VerticesSocket', 'start').use_prop = True
        self.inputs.new('VerticesSocket', 'end').use_prop = True
        self.outputs.new('VerticesSocket', "HitP")
        self.outputs.new('VerticesSocket', "HitNorm")
        self.outputs.new('StringsSocket', "INDEX")

    def process(self):

        SSSAT = SvSetSocketAnyType
        bcsrc = bpy.context.scene.ray_cast
        outputs = self.outputs
        out = []
        OutLoc = []
        OutNorm = []
        IND = []

        st = Vector_generate(self.inputs['start'].sv_get())
        en = Vector_generate(self.inputs['end'].sv_get())
        start = [Vector(x) for x in st[0]]
        end = [Vector(x) for x in en[0]]
        if len(start) != len(end):
            temp = match_long_repeat([start, end])
            start, end = temp[0], temp[1]

        obj = self.inputs['Objects'].sv_get()[0]
        i = 0
        while i < len(end):
            out.append(obj.ray_cast(start[i], end[i]))
            i = i+1
        for i in out:
            OutNorm.append(i[1][:])
            IND.append(i[2])
            OutLoc.append(i[0][:])

        if outputs['HitP'].links:
            SSSAT(self, 'HitP', [OutLoc])
        if outputs['HitNorm'].links:
            SSSAT(self, 'HitNorm', [OutNorm])
        if outputs['INDEX'].links:
            SSSAT(self, 'INDEX', [IND])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRayCastNode)


def unregister():
    bpy.utils.unregister_class(SvRayCastNode)
