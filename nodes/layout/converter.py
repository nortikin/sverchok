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
from sverchok.data_structure import SvGetSocketAnyType, SvSetSocketAnyType


class ConverterNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Converter node temporery solution '''
    bl_idname = 'ConverterNode'
    bl_label = 'Socket Converter'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "data")
        self.outputs.new('VerticesSocket', 'vertices')
        self.outputs.new('StringsSocket', 'data')
        self.outputs.new('MatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        pass

    def process(self):
        if "data" in self.inputs and self.inputs[0].is_linked:            
            out = SvGetSocketAnyType(self, self.inputs[0], deepcopy=False)
            for s in self.outputs:
                if s.is_linked:
                    SvSetSocketAnyType(self, s.name, out)

def register():
    bpy.utils.register_class(ConverterNode)


def unregister():
    bpy.utils.unregister_class(ConverterNode)
