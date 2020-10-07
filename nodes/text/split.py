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


class TextSplitNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Text split node '''
    bl_idname = 'TextSplitNode'
    bl_label = 'Text Split'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_DEL_LEVELS'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'text')
        self.outputs.new('SvStringsSocket', 'text')

    def process(self):
        if self.outputs['text'].is_linked:
            text = self.inputs['text'].sv_get()
            self.outputs['text'].sv_set(self._split_text(text))

    def _split_text(self, text):
        if isinstance(text, list):
            for i, value in enumerate(text):
                text[i] = self._split_text(value)
            return text
        else:
            return text.split()


def register():
    bpy.utils.register_class(TextSplitNode)


def unregister():
    bpy.utils.unregister_class(TextSplitNode)
