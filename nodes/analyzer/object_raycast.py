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
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import (updateNode, Vector_generate, match_long_repeat)


class SvRayCastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' RayCast Object '''
    bl_idname = 'SvRayCastObjectNode'
    bl_label = 'object_raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode = BoolProperty(name='mode of points', description='mode for input points',
                        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('VerticesSocket', 'start').use_prop = True
        self.inputs.new('VerticesSocket', 'end').use_prop = True
        self.outputs.new('VerticesSocket', "HitP")
        self.outputs.new('VerticesSocket', "HitNorm")
        self.outputs.new('StringsSocket', "INDEX")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "mode",   text="Mode")

    def process(self):

        outfin = []
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

        obj = self.inputs['Objects'].sv_get()
        for OB in obj:
            out = []
            if self.mode:
                i = 0
                while i < len(end):
                    out.append(OB.ray_cast(OB.matrix_local.inverted()*start[i], OB.matrix_local.inverted()*end[i]))
                    i = i+1
            else:
                i = 0
                while i < len(end):
                    out.append(OB.ray_cast(start[i], end[i]))
                    i = i+1
            outfin.append(out)

        g = 0
        while g < len(obj):
            for i in outfin[g]:
                OutNorm.append(i[1][:])
                IND.append(i[2])
                OutLoc.append((obj[g].matrix_world*i[0])[:])
            g = g+1

        self.outputs['HitP'].sv_set([OutLoc])
        self.outputs['HitNorm'].sv_set([OutNorm])
        self.outputs['INDEX'].sv_set([IND])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRayCastNode)


def unregister():
    bpy.utils.unregister_class(SvRayCastNode)
