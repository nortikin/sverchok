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
import os, platform

from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty
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

class FloatPrecisionPrinter(pprint.PrettyPrinter):
    def __init__(self, precision2=2, precision=3, **kwargs):
        super().__init__(**kwargs)
        self.precision = precision
        self.precision2 = precision2

    def format(self, obj, context, maxlevels, level):
        if isinstance(obj, float):
            if obj<0:
                text = f"{obj:>{self.precision2+1}.{self.precision}f}"
            else:
                text = f" {obj:>{self.precision2}.{self.precision}f}"
            return text, True, False
        elif isinstance(obj, bool):
            text=" True" if obj==True else "False" 
            return text, True, False
        elif isinstance(obj, int):
            text = f"{obj:{self.precision2}d}"
            return text, True, False
        elif isinstance(obj, Matrix):
            len_rows = len(obj.row)
            indent = " "*level
            if len_rows==2:
                row0 = super().format(obj.row[0], context, maxlevels, level)
                row1 = super().format(obj.row[1], context, maxlevels, level)
                text = f"Matrix(({row0[0]},\n        {indent+row1[0]}))"
                return text, True, False
            if len_rows==3:
                row0 = super().format(obj.row[0], context, maxlevels, level)
                row1 = super().format(obj.row[1], context, maxlevels, level)
                row2 = super().format(obj.row[2], context, maxlevels, level)
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

def parse_socket(socket, rounding2, rounding, element_index, view_by_element, props):

    data = socket.sv_get(deepcopy=False)

    num_data_items = len(data)
    if num_data_items > 0 and view_by_element:
        if element_index < num_data_items:
            data = data[element_index]

    if props.chop_up:
        data = chop_up_data(data)

    # content_str = pprint.pformat(data, width=props.line_width, depth=props.depth, compact=props.compact)
    # content_array = content_str.split('\n')
    pp = FloatPrecisionPrinter(precision2=rounding2, precision=rounding, width=props.line_width, depth=props.depth, compact=props.compact)
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

class SvStethoscopeNodeLoadFontOperatorMK2(bpy.types.Operator):
    '''Load Font'''
    bl_idname = "node.sv_stethoscope_node_load_font_operator_mk2"
    bl_label = ""

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default="*.ttf;*.otf", options={'HIDDEN'})

    description_text: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        s = properties.description_text
        return s
    
    def execute(self, context):
        if not self.filepath:
            self.report({'WARNING'}, "Файл не выбран")
            return {'CANCELLED'}

        try:
            font_id = blf.load(self.filepath)
            self.report({'INFO'}, f"Шрифт загружен, font_id = {font_id}")
            # можно сохранить font_id в контексте или вернуть его как нужно
            #context.scene.my_font_id = font_id
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка загрузки: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        # определить стандартный каталог шрифтов в зависимости от ОС
        sys = platform.system()
        if sys == "Windows":
            default_font_dir = "C:/Windows/Fonts/"
        elif sys == "Darwin":
            default_font_dir = "/System/Library/Fonts"
        else:  # Linux / Unix
            default_font_dir = "/usr/share/fonts/truetype"

        # задать начальный путь (Blender откроет диалог именно тут)
        self.filepath = default_font_dir

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

user_fonts_id_cache = {} # share user_font_id over stethoscope nodes

@bpy.app.handlers.persistent
def clear_font_cache_on_load(dummy):
    user_fonts_id_cache.clear()
    pass

bpy.app.handlers.load_post.append(clear_font_cache_on_load)

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

    font_id: IntProperty(default=0, update=updateNode)

    def update_font_path(self, context):
        if self.font_pointer:
            self.font_path = self.font_pointer.filepath
            # self.user_font_id = blf.load(self.font_path)
            # self.font_id = self.user_font_id
            #self.user_font_id = 0
            if os.path.exists(self.font_path):
                if self.font_path in user_fonts_id_cache:
                    self.user_font_id = user_fonts_id_cache.get(self.font_path)
                else:
                    self.user_font_id = blf.load(self.font_path)
                    user_fonts_id_cache[self.font_path] = self.user_font_id
            else:
                self.user_font_id = 0
        else:
            self.user_font_id = 0
        updateNode(self, context)
        return

    font_pointer: bpy.props.PointerProperty(type=bpy.types.VectorFont, update=update_font_path)
    font_path: StringProperty(
        name = "Font",
        default = "",
        #subtype='FILE_PATH',
        #get = get_elem, set = set_elem,
        update=updateNode,
    )
    #user_font_id: IntProperty(default=-1, update=updateNode, options={'SKIP_SAVE'})
    @property
    def user_font_id(self):
        user_font_id = 0
        if os.path.exists(self.font_path):
            if self.font_path in user_fonts_id_cache:
                user_font_id = user_fonts_id_cache.get(self.font_path)
            else:
                user_font_id = blf.load(self.font_path)
                user_fonts_id_cache[self.font_path] = user_font_id
        return user_font_id
    
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
    rounding2: IntProperty(min=1, max=20, default=2, update=updateNode,
        description="range 1 to 20\nMinimum length of result string")
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
            row1.prop(self, "rounding2")
            row1.prop(self, "compact", icon="ALIGN_JUSTIFY", text='', toggle=True)
            row1.prop(self, "chop_up", icon="FILTER", text='')
            row2 = layout.row(align=True)
            row2.prop(self, "line_width")
            row2.prop(self, "depth")
            row3 = layout.row(align=True)
            #row3.prop(self, 'font_path')
            row3.template_ID(self, "font_pointer", open="font.open", unlink="font.unlink")  # https://docs.blender.org/api/current/bpy.types.UILayout.html#bpy.types.UILayout.template_ID

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

            # при первоначальной загрузке загрузить пользовательский шрифт для отображения:
            if self.user_font_id==-1:
                if os.path.exists(self.font_path):
                    if self.font_path in SvStethoscopeNodeMK2.user_fonts_id_cache:
                        self.user_font_id = SvStethoscopeNodeMK2.user_fonts_id_cache.get(self.font_path)
                    else:
                        # Если шрифт существует, то загрузить его
                        self.user_font_id = blf.load(self.font_path)
                        SvStethoscopeNodeMK2.user_fonts_id_cache[self.font_path] = self.user_font_id
                else:
                    # Если нет, то взять шрифт по умолчанию
                    self.user_font_id = 0
                pass

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
                    self.rounding2,
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
                'font_id': int(self.user_font_id)
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

classes = [SvStethoscopeNodeLoadFontOperatorMK2, SvStethoscopeNodeMK2]
register, unregister = bpy.utils.register_classes_factory(classes)