# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
import blf
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector
from mathutils.geometry import normal
from bpy.props import (
    BoolProperty, FloatVectorProperty, 
    StringProperty, FloatProperty, IntProperty, EnumProperty
)

from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.context_managers import sv_preferences
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    node_id, updateNode, fullList, Vector_generate, enum_item_5
)


round_if_needed = lambda p, n: f'({p[0]:.{n}f}, {p[1]:.{n}f}, {p[2]:.{n}f})'

# -------------------- BLF TEXT VIEWER ------------------- #

def calc_median(vlist):
    a = Vector((0, 0, 0))
    for v in vlist:
        a += v
    return a / len(vlist)

def adjust_list(in_list, x, y):
    return [[old_x + x, old_y + y] for (old_x, old_y) in in_list]


def generate_points_tris(width, height, x, y):
    amp = 5  # radius fillet

    width += 2
    height += 4
    width = ((width/2) - amp) + 2
    height -= (2*amp)

    height += 4
    width += 3    

    final_list = [
        # a
        [-width+x, +height+y],   # A         D - - - - - E
        [+width+x, -height+y],   # B         A .         |
        [-width+x, -height+y],   # C         |   .    b  |
        # b                                  |     .     |
        [-width+x, +height+y],   # D         |   a   .   |
        [+width+x, +height+y],   # E         |         . F
        [+width+x, -height+y]    # F         C - - - - - B
    ] 
    return final_list


def draw_3dview_text(context, args):

    context = bpy.context
    region = context.region
    region3d = context.space_data.region_3d

    geom, settings = args

    txt_color = settings['font_text_color']
    bg_color = settings['background_color']
    scale = settings['scale']
    draw_bg = settings['draw_background']
    anchor = settings['anchor']

    font_id = 0
    text_height = int(13.0 * scale)
    blf.size(font_id, text_height, 72)  # should check prefs.dpi

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    # vars for projection
    perspective_matrix = region3d.perspective_matrix.copy()

    final_draw_data = {}
    data_index_counter = 0

    def draw_all_text_at_once(final_draw_data):

        # build bg mesh and vcol data
        full_bg_Verts = []
        add_vert_list = full_bg_Verts.extend
        
        full_bg_colors = []
        add_vcol = full_bg_colors.extend
        for counter, (_, _, _, _, _, type_draw, pts) in final_draw_data.items():
            col = settings[f'bg_{type_draw}_col']
            add_vert_list(pts)
            add_vcol((col,) * 6)

        # draw background
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": full_bg_Verts, "color": full_bg_colors})
        batch.draw(shader)

        # draw text 
        for counter, (index_str, pos_x, pos_y, txt_width, txt_height, type_draw, pts) in final_draw_data.items():
            text_color = settings[f'numid_{type_draw}_col']
            blf.color(font_id, *text_color)
            blf.position(0, pos_x, pos_y, 0)
            blf.draw(0, index_str)

    def gather_index(index, vec, type_draw):

        vec_4d = perspective_matrix @ vec.to_4d()
        if vec_4d.w <= 0.0:
            return

        x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)

        # ---- draw text ----
        index_str = str(index)
        txt_width, txt_height = blf.dimensions(0, index_str)

        pos_x = x - (txt_width / 2)
        pos_y = y - (txt_height / 2)

        pts = generate_points_tris(txt_width, txt_height, x, y-1)
        data_index_counter = len(final_draw_data)
        final_draw_data[data_index_counter] = (index_str, pos_x, pos_y, txt_width, txt_height, type_draw, pts)

    if geom.locations_data and geom.text_data:
        for text_item, (idx, location) in zip(geom.text_data, geom.locations_data):
            gather_index(text_item, location, 'verts')
    else:
        for vidx in geom.locations_data:
            gather_index(vidx[0], vidx[1], 'verts')


    draw_all_text_at_once(final_draw_data)



class SvViewerTextBLF(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: blf
    Tooltip:  view text in 3dview using basic blf features (size, orientation, color..)

    The idea is that you can display with this node the following:

    - if the locations socket is only connected, then you can display their coordinates 
        : and add rounding per component

    - if both location and text socket are connected a few things happen
        : if the length of text and location lists aren't equal, the node matches them at runtime
        : if a text element is empty, this is skipped
        : the node expects this kind of input

          locations = [[v1, v2, v3, v4....], [v1, v2, v3, v4....], n]  (n-collections of vectors)
          text = [["str1, "str2", str3, "str4", ...], ["str1, "str2", str3, "str4", ...], n] (n-collections of text elements)

    - user can set the following properties of text
        : the viewport text-scale, globally for the node
        : text anchor globally (at the moment: L R C T B )
        : text color
        : background polygon color, and whether to show it or not. 
        - showing background polygon may be moderately more processor intensive, as it must first calculate all polygon sizes
          and locations and draw them all first, then draw text over all of them.

    """

    bl_idname = 'SvViewerTextBLF'
    bl_label = 'Viewer blf Text'
    bl_icon = 'INFO'
    sv_icon = 'SV_INDEX_VIEWER'

    def make_color_prop(name, col):
        return FloatVectorProperty(
            name=name, description='', size=4, min=0.0, max=1.0,
            default=col, subtype='COLOR', update=updateNode)

    activate: BoolProperty(
        name='Show', description='Activate node?',
        default=True, update=updateNode)

    draw_background: BoolProperty(
        name='draw_background', description='draw background polygons or not',
        default=False, update=updateNode)

    coordinate_rounding: IntProperty(
        name="rounding", default=3, min=0, soft_max=8, 
        description="in coordinate mode, Use this slider to adjust how precise you want to display each coordinate",
        update=updateNode)

    skip_empty_strings: BoolProperty(name="Skip empty Strings", update=updateNode)

    anchor_direction: EnumProperty(
        items=enum_item_5(
            ["left", "right", "center", "top", "bottom"], 
            ["ANCHOR_LEFT", "ANCHOR_RIGHT", "ANCHOR_CENTER", "ANCHOR_TOP", "ANCHOR_BOTTOM"]),
        description="offers a way to anchor all text items to the location",
        default="center", update=updateNode)

    background_color: make_color_prop("background_color", (.2, .2, .2, 1.0))
    font_text_color: make_color_prop("font_text_color", (0.6, 1, 0.3, 1.0))
    text_node_scale: FloatProperty(name="text scale", default=1.0, min=0.1, update=updateNode)

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', 'locations')
        inew('SvStringsSocket', 'text')


    def draw_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')

        column_all = layout.column()

        row = column_all.row(align=True)
        split = row.split()
        r = split.column()
        r.prop(self, "activate", text="Show", toggle=True, icon=view_icon)
        row.prop(self, "draw_background", text="BG", toggle=True)
        new_row = layout.row()
        new_row.prop(self, "anchor_direction", expand=True)


    def get_settings_dict(self):
        
        """
        Produce a dict of settings for the callback
            
        A copy is needed, we can't have reference to the node in a callback, 
        it will crash blender on undo
        """

        return {
            'background_color': self.background_color[:],
            'font_text_color': self.font_text_color[:],
            'draw_background': self.draw_background,
            'anchor': self.anchor_direction,
            'scale': self.text_node_scale
        }.copy()

    def get_geometry(self):
        inputs = self.inputs
        geom = lambda: None

        for socket in ['locations', 'text']:
            input_stream = inputs[socket].sv_get(default=[])
            if socket == 'locations' and input_stream:
                input_stream = Vector_generate(input_stream)

            setattr(geom, socket, input_stream)

        # pass only data onto the draw callback that you intend to show.
        display_data = lambda: None
        display_data.locations_data = []
        display_data.text_data = []

        concat_locations = display_data.locations_data.append
        concat_text = display_data.text_data.extend

        for obj_index, locations in enumerate(geom.locations):

            for vpos in locations:
                chars = round_if_needed(vpos, self.coordinate_rounding)
                concat_locations((chars, vpos))
            
            if geom.text:    
                text_items = self.get_text_of_correct_length(obj_index, geom, len(locations))                        
                concat_text(text_items)

        return display_data

    def get_text_of_correct_length(self, obj_index, geom, num_elements_to_fill):

        """ 
        if the len(locations) is larger than len(text), then this auto extends till they match
        """

        if obj_index < len(geom.text):
            text_items = geom.text[obj_index]
        else:
            text_items = geom.text[len(geom.text)-1]

        if not (len(text_items) == num_elements_to_fill):
            
            if len(text_items) < num_elements_to_fill:
                return text_items + [text_items[-1], ] * (num_elements_to_fill - len(text_items))
            else:
                return text_items[:num_elements_to_fill]

        return text_items

    def end_early(self):
        
        """
        self.process can end/break early depending on various scenarios, listed in the code below
        """
        
        if not self.id_data.sv_show:
            return True

        self.use_custom_color = True
        if not (self.activate and self.inputs['locations'].is_linked):
            return True

        if not self.inputs['locations'].sv_get():
            return True


    def process(self):
        n_id = node_id(self)

        callback_disable(n_id)
        if self.end_early():
            return

        config = self.get_settings_dict()
        geom = self.get_geometry()
        
        draw_data = {
            'tree_name': self.id_data.name[:],
            'custom_function': draw_3dview_text,
            'args': (geom, config)} 

        callback_enable(n_id, draw_data, overlay='POST_PIXEL')


    def sv_free(self):
        callback_disable(node_id(self))

    def show_viewport(self, is_show: bool):
        """It should be called by node tree to show/hide objects"""
        if not self.activate:
            return

        if is_show:
            self.process()
        else:
            callback_disable(node_id(self))


def register():
    bpy.utils.register_class(SvViewerTextBLF)


def unregister():
    bpy.utils.unregister_class(SvViewerTextBLF)
