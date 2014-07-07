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

import bpy
from bpy.props import StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvSetSocketAnyType, updateNode

Sv_handle_Note = {}


class SverchokNote(bpy.types.Operator):
    """Sverchok Note"""
    bl_idname = "node.sverchok_note_button"
    bl_label = "Sverchok notes"
    bl_options = {'REGISTER', 'UNDO'}

    text = StringProperty(name='text',
                          default='')

    def execute(self, context):
        name = context.screen.name
        areas = bpy.data.screens[name].areas
        text = literal_eval(self.text)

        Sv_handle_Note[text[0]] = True
        out = []
        length = len(text[1])
        width = min(47, length)  # min(round(text[2]/10), lenth)
        text2 = ''
        k = 1
        for i, t in enumerate(text[1]):
            text2 += t
            if k == width or i == len(text[1])-1:
                out.append(text2)
                text2 = ''
                k = 1
            k += 1
        Sv_handle_Note[text[0]+'text'] = str(out)
        return {'FINISHED'}


class SverchokUnNote(bpy.types.Operator):
    """Sverchok UnNote"""
    bl_idname = "node.sverchok_note_unbutton"
    bl_label = "Sverchok Un notes"
    bl_options = {'REGISTER', 'UNDO'}

    text = StringProperty(name='text',
                          default='')

    def execute(self, context):
        name = context.screen.name
        areas = bpy.data.screens[name].areas
        text = literal_eval(self.text)
        
        Sv_handle_Note[text[0]] = False
        Sv_handle_Note[text[0]+'text'] = str(['your text here'])
        return {'FINISHED'}


class NoteNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Note '''
    bl_idname = 'NoteNode'
    bl_label = 'Note'
    bl_icon = 'OUTLINER_OB_EMPTY'

    text = StringProperty(name='text',
                          default='your text here',
                          update=updateNode)

    def init(self, context):
        if self.text != 'your text here':
            self.use_custom_color = True
            self.color = (0.5,0.5,1)
        else:
            self.use_custom_color = True
            self.color = (0.05,0.05,0.1)
        self.width = 400
        self.outputs.new('StringsSocket', "Text", "Text")
    
    def draw_buttons(self, context, layout):
        global Sv_handle_Note
        if self.name not in Sv_handle_Note:
            Sv_handle_Note[self.name] = False
            name = context.screen.name
            areas = bpy.data.screens[name].areas
            for ar in areas:
                if ar.type == 'NODE_EDITOR':
                    ar.spaces.active.node_tree.nodes[self.name].width_hidden = 320
                    ar.spaces.active.node_tree.nodes[self.name].location[0] += 10
            # not works in this context. Have to be rewrited.
            # aim - to esteblish width of node 320

        if not Sv_handle_Note[self.name]:
            row = layout.row(align=True)
            row.prop(self, 'text', text='')
            row = layout.row(align=True)
            row.operator('node.sverchok_note_button', text='MIND').text = str([self.name, self.text])

        else:
            ev = literal_eval(Sv_handle_Note[self.name+'text'])
            for t in ev:
                row = layout.row(align=True)
                row.label(t)
            row = layout.row(align=True)
            row.operator('node.sverchok_note_unbutton', text='CHANGE').text = str([self.name, self.text])

    def update(self):
        if 'Text' in self.outputs and self.outputs['Text'].links:
            text = [[a] for a in self.text.split()]
            SvSetSocketAnyType(self, 'Text', [text])


def register():
    bpy.utils.register_class(NoteNode)
    bpy.utils.register_class(SverchokNote)
    bpy.utils.register_class(SverchokUnNote)


def unregister():
    bpy.utils.unregister_class(SverchokUnNote)
    bpy.utils.unregister_class(SverchokNote)
    bpy.utils.unregister_class(NoteNode)

if __name__ == '__main__':
    register()