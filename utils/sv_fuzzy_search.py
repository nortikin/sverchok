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


import string

import bpy
import bgl
import blf
from bpy.types import SpaceNodeEditor

import sverchok
from sverchok.menu import make_node_cats



### ---- Key Handling ----------------------------------------------------------

verbose_nums = "ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE".split(" ")
verbose_numpads = [('NUMPAD_' + n) for n in string.digits]

CAPS = set(a for a in string.ascii_uppercase)
NUMS = set(verbose_nums)
NUMS2 = set(verbose_numpads)

NUMS = NUMS.union(NUMS2)
SPECIALS = {'BACK_SPACE', 'UP', 'DOWN', 'LEFT', 'RIGHT'}
KEYBOARD = CAPS.union(SPECIALS)
KEYBOARD = KEYBOARD.union(NUMS)

remap_nums = {k: str(idx) for idx, k in enumerate(verbose_nums)}
remap_extras = {k: str(idx) for idx, k in enumerate(verbose_numpads)}
remap_nums.update(remap_extras)

### ---- Category Handling -----------------------------------------------------

node_cats = make_node_cats()
addon_name = sverchok.__name__
menu_prefs = {}

def make_flat_nodecats():
    flat_node_list = []
    for cat_name, cat_content in dict(node_cats).items():
        for node_ref in cat_content:
            if not node_ref[0] == 'separator':
                flat_node_list.append(node_ref[0])  # maybe return lookups too
    return flat_node_list

flat_node_cats = make_flat_nodecats()   # produces bl_idnames.


### ------------------------------------------------------------------------------


def draw_callback_px(self, context, start_position):

    font_id = 0
    x, y = start_position

    # draw some text
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    blf.position(font_id, x, y, 0)
    blf.size(font_id, 30, 72)
    blf.draw(font_id, '>>> ' + self.current_string)
    
    '''
    draw results

    flat_node_cats will contain bl_idnames
    bl_label <--- getattr(bpy.types, bl_idname)
    
    '''
    if self.current_string:
        idx = 1
        for item in flat_node_cats:
            if self.current_string in item.lower():
                bl_label = getattr(bpy.types, item).bl_label
                blf.position(font_id, x, y-(30*idx), 0)
                blf.draw(font_id, '         |  ' + bl_label)
                idx += 1
            if idx > 10:
                break

  
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class SvFuzzySearchOne(bpy.types.Operator):
    """Implementing Search fuzzyness"""
    bl_idname = "node.sv_fuzzy_node_search"
    bl_label = "Fuzzy Search"

    current_string = bpy.props.StringProperty()

    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in KEYBOARD and event.value == 'PRESS':
            # print(event.type)
            if event.type in CAPS or event.type in remap_nums.keys() or event.type == 'SPACE':

                if event.type == 'SPACE':
                    final_value = ' '
                else:
                    final_value = remap_nums.get(event.type, event.type.lower())

                self.current_string = self.current_string + final_value
            elif event.type == 'BACK_SPACE':
                has_length = len(self.current_string)
                self.current_string = self.current_string[:-1] if has_length else ''
            # print(self.current_string)

        elif event.type in {'LEFTMOUSE', 'RET'}:
            print('completed')
            SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')            
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')            
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':

            start_position = 20, 20   # event.mouse_region_x, event.mouse_region_y
            args = (self, context, start_position)
            self._handle = SpaceNodeEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "NODE_EDITOR not found, cannot run operator")
            return {'CANCELLED'}


classes = [SvFuzzySearchOne,]


def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in classes]
