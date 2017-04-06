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

# pylint: disable=C0326
# pylint: disable=w0612

### ---- Key Handling ----------------------------------------------------------

verbose_nums = "ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE".split(" ")
verbose_numpads = [('NUMPAD_' + n) for n in string.digits]

CAPS = set(a for a in string.ascii_uppercase)
NUMS = set(verbose_nums)
NUMS2 = set(verbose_numpads)

NUMS = NUMS.union(NUMS2)
SPECIALS = set('BACK_SPACE LEFT_ARROW DOWN_ARROW RIGHT_ARROW UP_ARROW SPACE'.split(' '))
KEYBOARD = CAPS.union(SPECIALS)
KEYBOARD = KEYBOARD.union(NUMS)

remap_nums = {k: str(idx) for idx, k in enumerate(verbose_nums)}
remap_extras = {k: str(idx) for idx, k in enumerate(verbose_numpads)}
remap_nums.update(remap_extras)

### ---- Category Handling -----------------------------------------------------

node_cats = make_node_cats()
addon_name = sverchok.__name__
menu_prefs = {}

ddir = lambda content: [n for n in dir(content) if not n.startswith('__')]

def removed_sv_prefix(str_in):
    if str_in.startswith("Sv"):
        return str_in[2:]
    return str_in

def make_flat_nodecats():
    flat_node_list = []
    for ref in sverchok.node_list:
        for iref in ddir(ref):
            rref = getattr(ref, iref)
            if 'sv_init' in ddir(rref) and 'bl_idname' in ddir(rref):
                items = [rref.bl_label, rref.bl_idname, str(rref.__module__).replace('sverchok.nodes.', '')]
                flat_node_list.append('  |  '.join(items))
    return flat_node_list

flat_node_cats = {}
event_tracking = {'previous_event': None}

def return_search_results(search_term):
    prefilter = []
    if search_term:
        idx = 1
        for item in flat_node_cats.get('results'):
            if search_term in removed_sv_prefix(item).lower() and not item.startswith('NodeReroute'):
                prefilter.append(item.split('  |  '))
                idx += 1
            if idx > 10:
                break
    return prefilter


### ------------------------------------------------------------------------------

RED = (1, 0, 0, 1)
GREEN = (0, 1, 0, 1)
BLUE = [0.308197, 0.904497, 1.000000, 1.000000]
search_colors = (RED, GREEN, BLUE)

def draw_string(x, y, packed_strings):
    x_offset = 0
    font_id = 0
    for pstr, pcol in packed_strings:
        pstr2 = ' ' + pstr + ' '
        bgl.glColor4f(*pcol)
        text_width, text_height = blf.dimensions(font_id, pstr2)
        blf.position(font_id, (x + x_offset), y, 0)
        blf.draw(font_id, pstr2)
        x_offset += text_width


def draw_rect(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0), color2=None):

    coords = [(x, y), (x+w, y), (w+x, y-h), (x, y-h)]

    
    if not color2:
        # FLAT
        bgl.glBegin(bgl.GL_POLYGON)
        bgl.glColor4f(*color)       
        for coord in coords:
            bgl.glVertex2f(*coord)
    else:
        # GRADIENT
        bgl.glBegin(bgl.GL_QUADS)
        for col, coord in zip((color, color, color2, color2), coords):
            bgl.glColor4f(*col)
            bgl.glVertex2f(*coord)
            
    bgl.glEnd()



def draw_callback_px(self, context, start_position):

    header_height = context.area.regions[0].height
    width = context.area.width
    height = context.area.height - header_height
    begin_height = height-40

    font_id = 0

    # draw some text
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    blf.position(font_id, 20, height-40, 0)
    blf.size(font_id, 14, 72)
    blf.draw(font_id, '>>> ' + self.current_string)

    draw_rect(x=0, y=height-46, w=width, h=10*20, color=(0.0, 0.0, 0.0, 1.0))
    
    nx = 20
    found_results = flat_node_cats.get('list_return')

    if found_results:

        # // highlight
        highcol = (0.2, 0.3, 0.4, 1.0)
        lowcol = (0.2, 0.2, 0.2, 1.0)
        draw_rect(x=0, y=begin_height-(20*self.current_index)-5, w=width, h=20, color=highcol, color2=lowcol)

        # // draw search items
        for idx, search_item_result in enumerate(found_results, start=1):
            ny = begin_height-(20*idx)
            draw_string(nx, ny, zip(search_item_result, search_colors))                
  
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class SvFuzzySearchOne(bpy.types.Operator):
    """Implementing Search fuzzyness"""
    bl_idname = "node.sv_fuzzy_node_search"
    bl_label = "Fuzzy Search"

    current_string = bpy.props.StringProperty()
    chosen_bl_idname = bpy.props.StringProperty()
    current_index = bpy.props.IntProperty(default=0)
    new_direction = bpy.props.IntProperty(default=1)


    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in KEYBOARD and event.value == 'PRESS':
            if event.type in CAPS or event.type in remap_nums.keys() or event.type == 'SPACE':

                if event.type == 'SPACE':
                    final_value = ' '
                else:
                    final_value = remap_nums.get(event.type, event.type.lower())

                self.current_string = self.current_string + final_value
            elif event.type == 'BACK_SPACE':
                has_length = len(self.current_string)
                self.current_string = self.current_string[:-1] if has_length else ''
            elif event.type in {'UP_ARROW', 'DOWN_ARROW'}:
                self.new_direction = {'UP_ARROW': -1, 'DOWN_ARROW': 1}.get(event.type)
                self.current_index += self.new_direction

            flat_node_cats['list_return'] = return_search_results(self.current_string)

        elif event.type in {'LEFTMOUSE', 'RET'}:
            print('pressed enter / left mouse')
            SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')

            found_results = flat_node_cats.get('list_return')
            if found_results and len(found_results) > self.current_index:
                node_bl_idname = found_results[self.current_index][1]
                new_node = context.space_data.edit_tree.nodes.new(node_bl_idname)
                new_node.select = False
           
            print('completed')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')            
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':
            flat_node_cats['results'] = make_flat_nodecats()
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
