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
from ast import literal_eval
import textwrap

import bpy
from bpy.props import StringProperty, IntProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, updateNode, node_id


TEXT_WIDTH = 6

def format_text(text, width):
    return textwrap.wrap(text, width // TEXT_WIDTH)


class NoteNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Note '''
    bl_idname = 'NoteNode'
    bl_label = 'Note'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def update_width(self, context):
        global t_w
        t_w = self.text_width
        
    def update_text(self, context):
        self.format_text()
        updateNode(self, context)
        
    text = StringProperty(name='text',
                          default='your text here',
                          update=update_text)
    text_cache = {}
    n_id = StringProperty(default='')
    
    text_width = IntProperty(min=1, update=update_width)

    def format_text(self):
        n_id = node_id(self)
        tl = format_text(self.text, self.width)
        self.text_cache[n_id] = (self.width, tl)
        return tl
        
    def init(self, context):
        n_id = node_id(self)
        self.width = 400
        self.color = (.9, .9, .9)
        self.use_custom_color = True
        self.outputs.new('StringsSocket', "Text", "Text")
    
    def draw_buttons(self, context, layout):
            
        row = layout.row()
        row.prop(self, "text")
        col = layout.column(align=True)
        if self.n_id in self.text_cache:
            data = self.text_cache.get(self.n_id)
            if data and data[0] == self.width:
                for line in data[1]:
                    col.label(text=line)
                return
                
        text_lines = format_text(self.text, self.width)
        for line in text_lines:
            col.label(text=line)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "text_width")
        
    def update(self):
        n_id = node_id(self)
        if not n_id in self.text_cache:
            self.format_text()
            
        if 'Text' in self.outputs and self.outputs['Text'].links:
            text = self.text.split(" ")
            SvSetSocketAnyType(self, 'Text', [text])
    
    def copy(self, node):
        n_id = ''

def register():
    bpy.utils.register_class(NoteNode)

def unregister():
    bpy.utils.unregister_class(NoteNode)

if __name__ == '__main__':
    register()
