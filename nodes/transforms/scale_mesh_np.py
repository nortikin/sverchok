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
import numpy as np
from bpy.props import FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, enum_item as e


class SvScaleNpNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Scale Numpy '''
    bl_idname = 'SvScaleNpNode'
    bl_label = 'ScaleNP'
    bl_icon = 'MAN_SCALE'

    Modes = ["Center", "Axis"]

    factor = FloatProperty(name='Factor', description='scaling factor',
                           default=1.0, options={'ANIMATABLE'}, update=updateNode)

    def update_mode(self, context):
        self.inputs['Center'].hide_safe = self.Mod == "all"
        self.inputs['Factor'].hide_safe = self.Mod == "all"
        self.inputs['Multiply axis'].hide_safe = not self.Mod == "all"
        updateNode(self, context)

    Mod = EnumProperty(name="getmode", default="Center", items=e(Modes), update=update_mode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "Mod", "")

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('VerticesSocket', "Center").use_prop = True
        self.inputs.new('VerticesSocket', "Multiply axis").hide_safe = True
        self.inputs["Multiply axis"].use_prop = True
        self.inputs.new('StringsSocket', "Factor").prop_name = "factor"
        self.outputs.new('VerticesSocket', "Vertices")

    def process(self):
        if self.outputs[0].is_linked:
            Ve, Ce, Mu, Fa = self.inputs
            V = Ve.sv_get()
            C = Ce.sv_get()[0]
            out = []
            if self.Mod == "Center":
                F = Fa.sv_get()[0]
                V, C, F = match_long_repeat([V, C, F])
                V, C, F = np.array(V), np.array(C), np.array(F)
                for v, c, f in zip(V, C, F):
                    out.append((c + f * (v - c)).tolist())
            elif self.Mod == "Axis":
                M = Mu.sv_get()[0]
                V, M = match_long_repeat([V, M])
                V, M = np.array(V), np.array(M)
                for v, m in zip(V, M):
                    v *= m
                    out.append(v.tolist())
            self.outputs[0].sv_set(out)


def register():
    bpy.utils.register_class(SvScaleNpNode)


def unregister():
    bpy.utils.unregister_class(SvScaleNpNode)
