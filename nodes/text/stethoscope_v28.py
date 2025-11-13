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
import os, platform, sys

from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty
from bpy.app.handlers import persistent
from bpy.props import FloatProperty
from mathutils import Vector, Matrix

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

if sys.version_info<(3,10):
    # fix for format prettyPrint for Blender <= 3.0.0 with python  3.9.x
    class FloatPrecisionPrinter(pprint.PrettyPrinter):
        def __init__(self, field_width=2, precision=3, **kwargs):
            super().__init__(**kwargs)
            self.precision = precision
            self.field_width = field_width

        def format(self, obj, context, maxlevels, level):
            res = self._safe_repr(obj, context, maxlevels, level)
            return res

        def _safe_repr(self, obj, context, maxlevels, level):
            if isinstance(obj, float):
                if obj<0:
                    text = f"{obj:>{self.field_width+1}.{self.precision}f}"
                else:
                    text = f" {obj:>{self.field_width}.{self.precision}f}"
                return text, True, False
            elif isinstance(obj, bool):
                text=" True" if obj==True else "False" 
                return text, True, False
            elif isinstance(obj, int):
                text = f"{obj:{self.field_width}d}"
                return text, True, False
            elif isinstance(obj, Matrix):
                len_rows = len(obj.row)
                indent = " "*level
                if len_rows==2:
                    row0 = self._safe_repr(list(obj.row[0]), context, maxlevels, level)
                    row1 = self._safe_repr(list(obj.row[1]), context, maxlevels, level)
                    text = f"Matrix(({row0[0]},\n        {indent+row1[0]}))"
                    return text, True, False
                if len_rows==3:
                    row0 = self._safe_repr(list(obj.row[0]), context, maxlevels, level)
                    row1 = self._safe_repr(list(obj.row[1]), context, maxlevels, level)
                    row2 = self._safe_repr(list(obj.row[2]), context, maxlevels, level)
                    text = f"Matrix(({row0[0]},\n        {indent+row1[0]},\n        {indent+row2[0]}))"
                    return text, True, False
                if len_rows==4:
                    row0 = self._safe_repr(list(obj.row[0]), context, maxlevels, level)
                    row1 = self._safe_repr(list(obj.row[1]), context, maxlevels, level)
                    row2 = self._safe_repr(list(obj.row[2]), context, maxlevels, level)
                    row3 = self._safe_repr(list(obj.row[3]), context, maxlevels, level)
                    text = f"Matrix(({row0[0]},\n        {indent+row1[0]},\n        {indent+row2[0]},\n        {indent+row3[0]}))"
                    return text, True, False
                text = f"Matrix(): invalid row size: {len_rows}!"
                return text, True, False
            elif isinstance(obj, (list, tuple)):
                # --- list/tuple ---
                if not obj:
                    return repr(obj), True, False

                # recursion for list — pprint call _safe_repr on every element
                items = []
                for x in obj:
                    s, _, _ = self._safe_repr(x, context, maxlevels, level + 1)
                    items.append(s)

                if isinstance(obj, tuple):
                    out = "(" + ", ".join(items) + ("," if len(obj) == 1 else "") + ")"
                else:
                    out = "[" + ", ".join(items) + "]"

                return out, True, False
            
            elif isinstance(obj, dict):
                # --- dict ---
                if not obj:
                    return "{}", True, False

                parts = []
                for k, v in obj.items():
                    k_str, _, _ = self._safe_repr(k, context, maxlevels, level + 1)
                    v_str, _, _ = self._safe_repr(v, context, maxlevels, level + 1)
                    parts.append(f"{k_str}: {v_str}")

                return "{" + ", ".join(parts) + "}", True, False
            
            return repr(obj), True, False
else:
    class FloatPrecisionPrinter(pprint.PrettyPrinter):
        def __init__(self, field_width=2, precision=3, **kwargs):
            super().__init__(**kwargs)
            self.precision = precision
            self.field_width = field_width

        def format(self, obj, context, maxlevels, level):
            if isinstance(obj, float):
                if obj<0:
                    text = f"{obj:>{self.field_width+1}.{self.precision}f}"
                else:
                    text = f" {obj:>{self.field_width}.{self.precision}f}"
                return text, True, False
            elif isinstance(obj, bool):
                text=" True" if obj==True else "False" 
                return text, True, False
            elif isinstance(obj, int):
                text = f"{obj:{self.field_width}d}"
                return text, True, False
            elif isinstance(obj, Matrix):
                len_rows = len(obj.row)
                indent = " "*level
                if len_rows==2:
                    row0 = super().format(list(obj.row[0]), context, maxlevels, level)
                    row1 = super().format(list(obj.row[1]), context, maxlevels, level)
                    text = f"Matrix(({row0[0]},\n        {indent+row1[0]}))"
                    return text, True, False
                if len_rows==3:
                    row0 = super().format(list(obj.row[0]), context, maxlevels, level)
                    row1 = super().format(list(obj.row[1]), context, maxlevels, level)
                    row2 = super().format(list(obj.row[2]), context, maxlevels, level)
                    text = f"Matrix(({row0[0]},\n        {indent+row1[0]},\n        {indent+row2[0]}))"
                    return text, True, False
                if len_rows==4:
                    row0 = super().format(list(obj.row[0]), context, maxlevels, level)
                    row1 = super().format(list(obj.row[1]), context, maxlevels, level)
                    row2 = super().format(list(obj.row[2]), context, maxlevels, level)
                    row3 = super().format(list(obj.row[3]), context, maxlevels, level)
                    text = f"Matrix(({row0[0]},\n        {indent+row1[0]},\n        {indent+row2[0]},\n        {indent+row3[0]}))"
                    return text, True, False
                text = f"Matrix(): invalid row size: {len_rows}!"
                return text, True, False
                pass
            return super().format(obj, context, maxlevels, level)

def parse_socket(socket, field_width, rounding, element_index, view_by_element, props):

    data = socket.sv_get(deepcopy=False)

    num_data_items = len(data)
    if num_data_items > 0 and view_by_element:
        if element_index < num_data_items:
            data = data[element_index]

    if props.chop_up:
        data = chop_up_data(data)

    # content_str = pprint.pformat(data, width=props.line_width, depth=props.depth, compact=props.compact)
    # content_array = content_str.split('\n')
    pp = FloatPrecisionPrinter(field_width=field_width, precision=rounding, width=props.line_width, depth=props.depth, compact=props.compact)
    content_str = pp.pformat(data)
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
        # passthru = (rounding == 0) or ("bpy." in line)
        # out.append(line if passthru else re.sub(rounded_vals, mround, line))
        out.append(line)
    return out


def high_contrast_color(c):
    g = 2.2  # gamma
    L = 0.2126 * (c.r**g) + 0.7152 * (c.g**g) + 0.0722 * (c.b**g)
    return [(.1, .1, .1), (.95, .95, .95)][int(L < 0.5)]

fonts_id_cache = {} # share font_id over stethoscope nodes

@bpy.app.handlers.persistent
def clear_font_cache_on_load(dummy):
    '''Clear font cache on start on reload addon in development process'''
    for K in fonts_id_cache:
        blf.unload(K)
        pass
    fonts_id_cache.clear()
    pass

bpy.app.handlers.load_post.append(clear_font_cache_on_load)


class SV_PT_StethoskopeFontPanelMK2(bpy.types.Panel):
    '''Select font for text display. For numeric data, it is recommended to use monospaced text.'''
    bl_label = "Font Settings"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_context = "data"

    def draw(self, context):
        layout = self.layout
        if hasattr(context, 'node'):
            #col0 = layout.column(align=True)
            #col0.label(text=' ')
            #col0.scale_x=3.0
            col0 = layout.column(align=True)
            col0.label(text='Select fonts:')
            #col0.scale_x=0.5
            col0.template_ID(context.node, "font_pointer", open="font.open", unlink="font.unlink")  # https://docs.blender.org/api/current/bpy.types.UILayout.html#bpy.types.UILayout.template_ID
            if context.node is not None and hasattr(context.node,'font_pointer') and context.node.font_pointer:
                font_name = context.node.font_pointer.name
            else:
                font_name='-'
            col0.label(text=f'{font_name}')

        pass

class SvStethoscopeNodeMK2(SverchCustomTreeNode, bpy.types.Node, LexMixin, SvNodeViewDrawMixin):
    """
        Triggers: scope 
        Tooltip: Display data output of a node in nodeview
        
        this node uses nodeview bgl callbacks to display text/numbers/structures
        generated by other nodes.
        """
        
    bl_idname = 'SvStethoscopeNodeMK2'
    bl_label = 'Stethoscope MK2'
    bl_icon = 'LONGDISPLAY'

    def update_font_path(self, context):
        #clear_font_cache_on_load(None)
        if self.font_pointer:
            self.font_path = self.font_pointer.filepath
        else:
            self.font_path = ""
        updateNode(self, context)
        return

    font_pointer: bpy.props.PointerProperty(type=bpy.types.VectorFont, update=update_font_path)
    font_path: StringProperty(
        name = "Font",
        default = "",
        update=updateNode,
    )
    @property
    def font_id(self):
        font_id = 0
        if self.font_path in fonts_id_cache:
            font_id = fonts_id_cache.get(self.font_path)
        elif os.path.exists(self.font_path):
            font_id = blf.load(self.font_path)
            fonts_id_cache[self.font_path] = font_id
        return font_id
    
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

    view_by_element : BoolProperty(update=updateNode, description='If count of input objects more 0 then one can show every object independently')
    num_elements    : IntProperty (default=0)
    element_index   : IntProperty (default=0, update=updateNode)
    rounding        : IntProperty (default=    3, min= 0, max=5, update=updateNode, name="Precision", description="range 0 to 5\n : 0 performs no rounding\n : 5 rounds to 5 digits\nNot affected if there is no fractional part")
    field_width     : IntProperty (default=    2, min= 1,        update=updateNode, name="Field Width", description="min 1\nMinimum length of number converted to string.\nUsed for float, int or boolean values")
    line_width      : IntProperty (default=   60, min=20,        update=updateNode, name='Line Width (chars)')
    compact         : BoolProperty(default=False,                update=updateNode, description="this tries to show as much data per line as the linewidth will allow")
    depth           : IntProperty (default=    5, min= 0,        update=updateNode, description="List nesting level",  )
    chop_up         : BoolProperty(default=False,                update=updateNode, description="perform extra data examination to reduce size of data before pprint (pretty printing, pformat)")

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

            text_mode_layout = layout.column(align=True)
            row.prop(self, "text_color", text='')
            row0 = text_mode_layout.row(align=True)
            row0.prop(self, "field_width")
            row0.prop(self, "compact", icon="ALIGN_JUSTIFY", text='', toggle=True)
            row0.prop(self, "chop_up", icon="FILTER", text='')
            row1 = text_mode_layout.row(align=True)
            row1.prop(self, "rounding")
            row2 = text_mode_layout.row(align=True)
            row2.prop(self, "line_width")
            row3 = text_mode_layout.row(align=True)
            row3.prop(self, "depth")
            row4 = text_mode_layout.row(align=True)
            row4.popover(panel="SV_PT_StethoskopeFontPanelMK2", icon='FILE_FONT', text="")
            if self.font_pointer:
                font_name = self.font_pointer.name
            else:
                font_name='-'
            row4.label(text=font_name)


            # layout.prop(self, "socket_name")
            #layout.label(text=f'input has {self.num_elements} elements')
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
        #layout.prop(self, 'font_id')
        pass

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
                    self.field_width,
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

            draw_data = dict({
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],
                'content': processed_data,
                'location': get_xy_for_bgl_drawing,
                'color': self.text_color[:],
                'scale' : float(scale),
                'mode': self.selected_mode[:],
                'font_id': int(self.font_id)
            })
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
        pass

classes = [ 
            SV_PT_StethoskopeFontPanelMK2,
            SvStethoscopeNodeMK2,
        ]

#register, unregister = bpy.utils.register_classes_factory(classes) - need individual call to clear fonts cache on reload addon

@persistent
def load_fonts_after_start(dummy):
    from sverchok.ui.fonts.load_fonts import load_fonts
    load_fonts()

def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)
    clear_font_cache_on_load(None)
    bpy.app.handlers.load_post.append(load_fonts_after_start)

def unregister():
    for class_name in reversed( classes ):
        bpy.utils.unregister_class(class_name)
    bpy.app.handlers.load_post.remove(load_fonts_after_start)