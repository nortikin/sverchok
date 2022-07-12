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

import numpy as np
import pprint
import re
import bpy
import blf

from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty
from bpy.props import FloatProperty
from mathutils import Vector

from sverchok.settings import get_params
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode, enum_item_5
from sverchok.ui import bgl_callback_nodeview as nvBGL

from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin, get_xy_for_bgl_drawing
from sverchok.utils.nodes_mixins.console_mixin import LexMixin
from sverchok.utils.profile import profile

# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)

def chop_up_data(data):

    """
    if data is large (either due to many small lists or n big lists) here it is sliced up
    remember the user is already comfortable with seeing their data being abbreviated when big
    """
    if len(data) == 1:
        if len(data[0]) > 24:
            data = [data[0][:12] + data[0][-12:]]
    elif len(data) > 1:
        n = -1
        if len(data[0]) > 12 and len(data[n]) > 12:
            data = [data[0][:12], data[n][-12:]]
    
    # could be cleverer, because this is now optimized for the above scenarios only. they are common.

    return data

def parse_socket(socket, rounding, element_index, view_by_element, props):

    data = socket.sv_get(deepcopy=False)

    num_data_items = len(data)
    if num_data_items > 0 and view_by_element:
        if element_index < num_data_items:
            data = data[element_index]

    if props.chop_up:
        data = chop_up_data(data)

    content_str = pprint.pformat(data, width=props.line_width, depth=props.depth, compact=props.compact)
    content_array = content_str.split('\n')

    if len(content_array) > 20:
        ''' first 10, ellipses, last 10 '''
        ellipses = ['... ... ...']
        head = content_array[0:10]
        tail = content_array[-10:]
        display_text = head + ellipses + tail
    elif len(content_array) == 1:
        ''' split on subunit - case of no newline to split on. '''
        content_array = content_array[0].replace("), (", "),\n (")
        display_text = content_array.split("\n")
    else:
        display_text = content_array

    # http://stackoverflow.com/a/7584567/1243487
    rounded_vals = re.compile(r"\d*\.\d+")

    def mround(match): return f"{float(match.group()):.{rounding}g}"

    out = []
    for line in display_text:
        passthru = (rounding == 0) or ("bpy." in line)
        out.append(line if passthru else re.sub(rounded_vals, mround, line))
    return out


def high_contrast_color(c):
    g = 2.2  # gamma
    L = 0.2126 * (c.r**g) + 0.7152 * (c.g**g) + 0.0722 * (c.b**g)
    return [(.1, .1, .1), (.95, .95, .95)][int(L < 0.5)]



class SvStethoscopeNodeMK2(bpy.types.Node, SverchCustomTreeNode, LexMixin, SvNodeViewDrawMixin):
    """
        Triggers: scope 
        Tooltip: Display data output of a node in nodeview
        
        this node uses nodeview bgl callbacks to display text/numbers/structures
        generated by other nodes.
        """
        
    bl_idname = 'SvStethoscopeNodeMK2'
    bl_label = 'Stethoscope MK2'
    bl_icon = 'LONGDISPLAY'

    font_id: IntProperty(default=0, update=updateNode)

    text_color: FloatVectorProperty(
        name="Color", description='Text color',
        size=3, min=0.0, max=1.0,
        default=(.1, .1, .1), subtype='COLOR',
        update=updateNode)

    activate: BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    #mode_options = [(i, i, '', idx) for idx, i in enumerate(["text-based", "graphical", "sv++"])]
    selected_mode: bpy.props.EnumProperty(
        items=enum_item_5(["text-based", "graphical", "sv++"], ['ALIGN_LEFT', 'ALIGN_TOP', 'SCRIPTPLUGINS']),
        description="select the kind of display, text/graphical/sv++",
        default="text-based", update=updateNode
    )

    view_by_element: BoolProperty(update=updateNode)
    num_elements: IntProperty(default=0)
    element_index: IntProperty(default=0, update=updateNode)
    rounding: IntProperty(min=0, max=5, default=3, update=updateNode,
        description="range 0 to 5\n : 0 performs no rounding\n : 5 rounds to 5 digits")
    line_width: IntProperty(default=60, min=20, update=updateNode, name='Line Width (chars)')
    compact: BoolProperty(default=False, update=updateNode, description="this tries to show as much data per line as the linewidth will allow")
    depth: IntProperty(default=5, min=0, update=updateNode)
    chop_up: BoolProperty(default=False, update=updateNode, 
        description="perform extra data examination to reduce size of data before pprint (pretty printing, pformat)")

    def get_theme_colors_for_contrast(self):
        try:
            current_theme = bpy.context.preferences.themes.items()[0][0]
            editor = bpy.context.preferences.themes[current_theme].node_editor
            self.text_color = high_contrast_color(editor.space.back)
        except:
            print('-', end='')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.get_theme_colors_for_contrast()
        if hasattr(self.id_data, 'update_gl_scale_info'):  # node groups does not have the method
            self.id_data.update_gl_scale_info()

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        icon = 'RESTRICT_VIEW_OFF' if self.activate else 'RESTRICT_VIEW_ON'
        row.prop(self, "activate", icon=icon, text='')
        row.separator()
        row.prop(self, 'selected_mode', expand=True, icon_only=True)
        if self.selected_mode == 'text-based':

            row.prop(self, "text_color", text='')
            row1 = layout.row(align=True)
            row1.prop(self, "rounding")
            row1.prop(self, "compact", icon="ALIGN_JUSTIFY", text='', toggle=True)
            row1.prop(self, "chop_up", icon="FILTER", text='')
            row2 = layout.row(align=True)
            row2.prop(self, "line_width")
            row2.prop(self, "depth")
            # layout.prop(self, "socket_name")
            layout.label(text=f'input has {self.num_elements} elements')
            layout.prop(self, 'view_by_element', toggle=True)
            if self.num_elements > 0 and self.view_by_element:
                layout.prop(self, 'element_index', text='get index')

        elif self.selected_mode == "sv++":
            row1 = layout.row(align=True)
            row1.prop(self, "line_width", text='Columns')
            row1.prop(self, "rounding")
            layout.prop(self, 'element_index', text="index")
            layout.prop(self, "local_scale")
        else:
            row.prop(self, "text_color", text='')
            pass

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'font_id')

    def get_preferences(self):
        return get_params({
            'stethoscope_view_scale': 1.0, 'render_location_xy_multiplier': 1.0}, direct=True)

    def process(self):
        inputs = self.inputs
        n_id = node_id(self)

        # end early
        nvBGL.callback_disable(n_id)

        if self.activate and inputs[0].is_linked:
            scale, self.location_theta = self.get_preferences()

            # gather vertices from input
            data = inputs[0].sv_get(deepcopy=False)
            self.num_elements = len(data)

            if self.selected_mode == 'text-based':
                props = lambda: None
                props.line_width = self.line_width
                props.compact = self.compact
                props.depth = self.depth or None
                props.chop_up = self.chop_up

                processed_data = parse_socket(
                    inputs[0],
                    self.rounding,
                    self.element_index,
                    self.view_by_element,
                    props
                )

            elif self.selected_mode == "sv++":
                nvBGL.callback_enable(n_id, self.draw_data)
                return

            else:
                # display the __repr__ version of the incoming data
                processed_data = data

            draw_data = {
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],
                'content': processed_data,
                'location': get_xy_for_bgl_drawing,
                'color': self.text_color[:],
                'scale' : float(scale),
                'mode': self.selected_mode[:],
                'font_id': int(self.font_id)
            }
            nvBGL.callback_enable(n_id, draw_data)

    def sv_free(self):
        nvBGL.callback_disable(node_id(self))

    def sv_update(self):
        if not ("Data" in self.inputs):
            return
        try:
            if not self.inputs[0].other:
                nvBGL.callback_disable(node_id(self))        
        except:
            print('stethoscope update holdout (not a problem)')


def register():
    bpy.utils.register_class(SvStethoscopeNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvStethoscopeNodeMK2)
