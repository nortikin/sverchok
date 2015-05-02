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
import numpy
from bpy.props import EnumProperty,StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


def Obm(m):
        m = [(i,i,"") for i in m]
        return m


class SvNumpyArrayNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Numpy Props '''
    bl_idname = 'SvNumpyArrayNode'
    bl_label = 'numpy_props'
    bl_icon = 'OUTLINER_OB_EMPTY'

    Modes = ['tolist','conj','flatten','reshape','repeat','resize',
             'transpose','swapaxes','squeeze','partition','searchsorted','round',
             'take','clip','ptp','all','any','choose','sort','sum','cumsum','mean',
             'var','std','prod','cumprod']
    Mod = EnumProperty(name="getmodes", default="tolist", items=Obm(Modes), update=updateNode)
    st = StringProperty(default='', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'List')
        self.outputs.new('StringsSocket', 'Value')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Mod", "Get")
        layout.prop(self, "st", text="args")

    def process(self):
        if self.outputs['Value'].is_linked:
            L = self.inputs['List'].sv_get()
            L = numpy.array(L) if not isinstance(L,numpy.ndarray) else L
            Ln = eval("L."+self.Mod+"("+self.st+")")
            self.outputs['Value'].sv_set(Ln)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvNumpyArrayNode)


def unregister():
    bpy.utils.unregister_class(SvNumpyArrayNode)
