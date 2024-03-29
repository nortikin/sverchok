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

class ConverterNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Converter node temporery solution '''
    bl_idname = 'ConverterNode'
    bl_label = 'Socket Converter'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOCKET_CONVERTER'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "data")
        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket', 'data')
        self.outputs.new('SvMatrixSocket', 'matrix')
        self.outputs.new('SvObjectSocket', 'object')
        self.outputs.new('SvCurveSocket', 'curve')
        self.outputs.new('SvSurfaceSocket', 'surface')
        self.outputs.new('SvSolidSocket', 'solid')
        self.outputs.new('SvColorSocket', 'color')
        self.outputs.new('SvDictionarySocket', 'dict')

    def process(self):
        if self.inputs[0].is_linked:
            out = self.inputs[0].sv_get(deepcopy=False)
            for s in self.outputs:
                if s.is_linked:
                    s.sv_set(out)

def register():
    bpy.utils.register_class(ConverterNode)


def unregister():
    bpy.utils.unregister_class(ConverterNode)
