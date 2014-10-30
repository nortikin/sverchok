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
import textwrap

import bpy

from bpy.props import StringProperty, IntProperty, BoolProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, updateNode, node_id, SvGetSocketAnyType


TEXT_WIDTH = 6

def format_text(text, width):
    out = []
    for t in text.splitlines():
        out.extend(textwrap.wrap(t, width // TEXT_WIDTH))
        out.append("")
    return out


class NoteNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Note '''
    bl_idname = 'NoteNode'
    bl_label = 'Note'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def update_text(self, context):
        self.format_text()
        # recursion protection, should be solved with better structure
        if not self.inputs[0].links:
            updateNode(self, context)
        
    text = StringProperty(name='text',
                          default='your text here',
                          update=update_text)
    text_cache = {}
    n_id = StringProperty(default='')
    show_text = BoolProperty(default=False, name="Show text", 
                             description="Show text box in node")
    
    def format_text(self):
        n_id = node_id(self)
        tl = format_text(self.text, self.width)
        self.text_cache[n_id] = (self.width, tl)
        
    def init(self, context):
        n_id = node_id(self)
        self.width = 400
        self.color = (0.5, 0.5, 1)
        self.use_custom_color = True
        self.inputs.new('StringsSocket', "Text In", "Text In")
        self.outputs.new('StringsSocket', "Text Out", "Text Out")
    
    def draw_buttons(self, context, layout):
        if self.show_text:
            row = layout.row()
            row.scale_y = 1.1
            row.prop(self, "text", text='')
        
        def draw_lines(col, lines):
            skip = False
            for l in lines:
                if l:
                    col.label(text=l)
                    skip = False
                elif skip:
                    continue
                else:
                    col.label(text=l)
                    skip = True
                    
        col = layout.column(align=True)
        if self.n_id in self.text_cache:
            data = self.text_cache.get(self.n_id)
            if data and data[0] == self.width:
                draw_lines(col, data[1])
                return
        text_lines = format_text(self.text, self.width)
        draw_lines(col, text_lines)
        
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "text")
        layout.prop(self, "show_text", toggle=True)
        layout.prop(self.outputs[0], "hide", toggle=True, text="Output socket")
        layout.prop(self.inputs[0], "hide", toggle=True, text="Input socket")
        op = layout.operator("node.sverchok_text_callback", text="From clipboard")
        op.fn_name = "from_clipboard"
        op = layout.operator("node.sverchok_text_callback", text="To text editor")
        op.fn_name = "to_text"

    def to_text(self):
        sv_n_t = "Sverchok Note Buffer"
        text = bpy.data.texts.get(sv_n_t)
        if not text:
            text = bpy.data.texts.new(sv_n_t)
        text.clear()
        text.write(self.text)
    
    def from_clipboard(self):
        self.text = bpy.context.window_manager.clipboard
        
    def update(self):
        if 'Text In' in self.inputs and self.inputs['Text In'].links:
            self.text = str(SvGetSocketAnyType(self,self.inputs['Text In']))

        n_id = node_id(self)
        if not n_id in self.text_cache:
            self.format_text()
            
        if 'Text Out' in self.outputs and self.outputs['Text Out'].links:
            # I'm not sure that this makes sense, but keeping it like 
            # old note right now. Would expect one value, and optional
            # split, or split via a text processing node, 
            # but keeping this for now
            text = [[a] for a in self.text.split()]
            SvSetSocketAnyType(self, 'Text Out', [text])
    
    def copy(self, node):
        self.n_id = ''
        node_id(self)

def register():
    bpy.utils.register_class(NoteNode)

def unregister():
    bpy.utils.unregister_class(NoteNode)

if __name__ == '__main__':
    register()
