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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat)


class SvRayCastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' RayCast Object '''
    bl_idname = 'SvRayCastObjectNode'
    bl_label = 'object_raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode = BoolProperty(name='input mode', default=False, update=updateNode)
    mode2 = BoolProperty(name='output mode', default=False, update=updateNode)

    def sv_init(self, context):
        si,so = self.inputs.new,self.outputs.new
        si('StringsSocket', 'Objects')
        si('VerticesSocket', 'start').use_prop = True
        si('VerticesSocket', 'end').use_prop = True
        so('VerticesSocket', "HitP")
        so('VerticesSocket', "HitNorm")
        so('StringsSocket', "FaceINDEX")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "mode",   text="In Mode")
        row.prop(self,    "mode2",   text="Out Mode")

    def process(self):
        o,s,e = self.inputs
        outfin,OutLoc,OutNorm,IND,obj,sm1,sm2 = [],[],[],[],o.sv_get(),self.mode,self.mode2
        st, en = match_long_repeat([s.sv_get()[0], e.sv_get()[0]])
        for OB in obj:
            out = []
            if sm1:
                i = 0
                obmat = OB.matrix_local.inverted()
                while i < len(en):
                    out.append(OB.ray_cast(obmat*Vector(st[i]), obmat*Vector(en[i])))
                    i = i+1
            else:
                i = 0
                while i < len(en):
                    out.append(OB.ray_cast(st[i], en[i]))
                    i = i+1
            outfin.append(out)
        for i,i2 in zip(obj,outfin):
            omw = i.matrix_world
            for i in i2:
                OutNorm.append(i[1][:])
                IND.append(i[2])
                OutLoc.append((omw*i[0])[:] if sm2 else i[0][:])
        for i,i2 in zip(self.outputs,[[OutLoc],[OutNorm],[IND]]):
            if i.is_linked:
                i.sv_set(i2)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRayCastNode)


def unregister():
    bpy.utils.unregister_class(SvRayCastNode)
