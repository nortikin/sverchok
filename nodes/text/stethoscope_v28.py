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
import bpy
import blf
import os

from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty
from bpy.app.handlers import persistent
from mathutils import Matrix

from sverchok.settings import get_params
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode, enum_item_5
from sverchok.ui import bgl_callback_nodeview as nvBGL

from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin, get_xy_for_bgl_drawing
from sverchok.utils.nodes_mixins.console_mixin import LexMixin

# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)

def _sized(x):
    return hasattr(x, '__len__') and not isinstance(x, (str, bytes))


def _head_tail(seq, n=12):
    """first n + last n items, concatenated (not summed) for numpy arrays"""
    if isinstance(seq, np.ndarray):
        return np.concatenate((seq[:n], seq[-n:]))
    return seq[:n] + seq[-n:]


def chop_up_data(data):
    """
    if data is large (either due to many small lists or n big lists) here it is sliced up
    remember the user is already comfortable with seeing their data being abbreviated when big
    """
    if len(data) == 1:
        if _sized(data[0]) and len(data[0]) > 24:
            data = [_head_tail(data[0])]
    elif len(data) > 1:
        first, last = data[0], data[-1]
        if _sized(first) and _sized(last) and len(first) > 12 and len(last) > 12:
            data = [first[:12], last[-12:]]
        elif len(data) > 24:
            # a single long list of small items (vectors, numbers), e.g. when viewing by element
            data = _head_tail(data)

    # could be cleverer, because this is now optimized for the above scenarios only. they are common.

    return data


def numpy_summary(data):
    """one line describing numpy content, so it is still visible after conversion to lists"""
    if isinstance(data, np.ndarray):
        return f"# ndarray {data.shape} {data.dtype}"
    if isinstance(data, (list, tuple)) and data:
        arrays = [d for d in data if isinstance(d, np.ndarray)]
        if arrays:
            first = arrays[0]
            many = f"{len(arrays)} x " if len(arrays) > 1 else ""
            return f"# {many}ndarray, first: {first.shape} {first.dtype}"
    return None


def numpy_to_python(obj):
    """ndarrays -> nested lists, numpy scalars -> python scalars, so the printer can format them"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if type(obj) is list:
        return [numpy_to_python(x) for x in obj]
    if type(obj) is tuple:
        return tuple(numpy_to_python(x) for x in obj)
    if type(obj) is dict:
        return {k: numpy_to_python(v) for k, v in obj.items()}
    return obj

class FloatPrecisionPrinter(pprint.PrettyPrinter):
    def __init__(self, field_width=2, precision=3, **kwargs):
        super().__init__(**kwargs)
        self.precision = precision
        self.field_width = field_width

    def format(self, obj, context, maxlevels, level):
        if isinstance(obj, bool):
            text = " True" if obj else "False"
            return text, True, False
        elif isinstance(obj, float):
            if obj < 0:
                text = f"{obj:>{self.field_width+1}.{self.precision}f}"
            else:
                text = f" {obj:>{self.field_width}.{self.precision}f}"
            return text, True, False
        elif isinstance(obj, int):
            text = f"{obj:{self.field_width}d}"
            return text, True, False
        elif isinstance(obj, Matrix):
            num_rows = len(obj.row)
            if num_rows not in (2, 3, 4):
                return f"Matrix(): invalid row size: {num_rows}!", True, False
            fmt = super().format
            rows = [fmt(list(row), context, maxlevels, level)[0] for row in obj.row]
            separator = f",\n        {' ' * level}"
            return f"Matrix(({separator.join(rows)}))", True, False
        return super().format(obj, context, maxlevels, level)


def parse_socket(data, field_width, rounding, element_index, view_by_element, props):

    num_data_items = len(data)
    if num_data_items > 0 and view_by_element:
        data = data[min(element_index, num_data_items - 1)]

    summary = numpy_summary(data)

    if props.chop_up:
        data = chop_up_data(data)

    data = numpy_to_python(data)

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

    if summary:
        display_text = [summary] + display_text
    return display_text


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


class SV_PT_StethoskopeFontPanelMK2(bpy.types.Panel):
    '''Select font for text display. For numeric data, it is recommended to use monospaced text.'''
    # Do not use that combination of params else this panel will registered in the N-panel: 
    # bl_label = "Font Settings"
    # bl_space_type = 'NODE_EDITOR'
    # bl_region_type = 'UI'
    # bl_category = "Node"
    # bl_context = "data"

    # use this combination - popover will visible only in a node
    bl_idname="SV_PT_StethoskopeFontPanelMK2"
    bl_label = "Font Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 14 # popover width

    def draw(self, context):
        layout = self.layout
        if hasattr(context, 'node'):
            col0 = layout.column(align=True)
            col0.label(text='Select fonts:')
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
        new_path = self.font_pointer.filepath if self.font_pointer else ""
        if new_path != self.font_path:
            self.font_path = new_path  # font_path's own update calls updateNode
        else:
            updateNode(self, context)

    font_pointer: bpy.props.PointerProperty(type=bpy.types.VectorFont, update=update_font_path)
    font_path: StringProperty(
        name = "Font",
        default = "",
        update=updateNode,
    )
    @property
    def font_id(self):
        font_id = 0
        path = bpy.path.abspath(self.font_path) if self.font_path else ""  # handles blend-relative "//" paths
        if path in fonts_id_cache:
            font_id = fonts_id_cache.get(path)
        elif path and os.path.exists(path):
            font_id = blf.load(path)
            fonts_id_cache[path] = font_id
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
    rounding        : IntProperty (default=    3, min= 0, soft_max=10, update=updateNode, name="Precision", description="Number of decimals shown for floats\n : 0 rounds to whole numbers\n : 5 shows 5 decimals\nInts and bools are not affected")
    field_width     : IntProperty (default=    2, min= 1,              update=updateNode, name="Field Width", description="min 1\nMinimum length of number converted to string.\nUsed for float, int or boolean values")
    line_width      : IntProperty (default=   60, min=20,              update=updateNode, name='Line Width (chars)')
    compact         : BoolProperty(default=False,                      update=updateNode, description="this tries to show as much data per line as the linewidth will allow")
    depth           : IntProperty (default=    5, min= 0,              update=updateNode, description="List nesting level shown, 0 = no limit")
    chop_up         : BoolProperty(default=False,                      update=updateNode, description="perform extra data examination to reduce size of data before pprint (pretty printing, pformat)")

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
                    data,
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

HANDLERS = (clear_font_cache_on_load, load_fonts_after_start)

def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)
    clear_font_cache_on_load(None)
    for handler in HANDLERS:
        if handler not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(handler)

def unregister():
    for class_name in reversed( classes ):
        bpy.utils.unregister_class(class_name)
    for handler in HANDLERS:
        if handler in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(handler)
    clear_font_cache_on_load(None)