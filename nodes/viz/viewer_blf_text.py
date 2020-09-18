# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Vector
from mathutils.geometry import normal
from bpy.props import (BoolProperty, FloatVectorProperty, StringProperty, FloatProperty, IntProperty, EnumProperty)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    node_id, updateNode, fullList, Vector_generate, enum_item_5)

from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.sv_idx_viewer28_draw import draw_3dview_text


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

          locations = [[v1, v2, v3, v4....], [v1, v2, v3, v4....]]  (two collections of vectors)
          text = [["str1, "str2", str3, "str4", ...], ["str1, "str2", str3, "str4", ...]] (two collections of text elements)
    - user can set the follwing properties of text
        : the viewport text-scale, globally for the text
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

    def show_viewport(self, is_show: bool):
        """It should be called by node tree to show/hide objects"""
        if not self.activate:
            return

        if is_show:
            self.process()
        else:
            callback_disable(node_id(self))

    def get_scale(self):
        return 1.0

    def make_color_prop(name, col):
        return FloatVectorProperty(
            name=name, description='', size=4, min=0.0, max=1.0,
            default=col, subtype='COLOR', update=updateNode)

    n_id: StringProperty(default='', options={'SKIP_SAVE'})

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
        items=items=enum_item_5(
            ["left", "right", "center", "top", "bottom"], 
            ["ANCHOR_LEFT", "ANCHOR_RIGHT", "ANCHOR_CENTER", "ANCHOR_TOP", "ANCHOR_BOTTOM"]),
        description="offers a way to anchor all text items to the location",
        default="middle", update=updateNode)

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
            'scale': self.get_scale()
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
        concat_text = display_data.text_data.append

        convert_if_needed = lambda chars: f'{chars}'
        
        for obj_index, final_verts in enumerate(geom.locations):

            for vpos in final_verts:
                chars = convert_if_needed(vpos)
                concat_locations((chars, vpos))
            
            if geom.text:    
                text_items = self.get_text_of_correct_length(obj_index, geom, len(final_verts))                        
                for text_item, vpos in zip(text_items, final_verts):

                    # yikes, don't feed this function nonsense :)
                    if isinstance(text_item, float):
                        chars = convert_if_needed(obj_index, text_item)
                    elif isinstance(text_item, list) and len(text_item) == 1:
                        chars = convert_if_needed(obj_index, text_item[0])
                    else:
                        # in case it receives [0, 0, 0] or (0, 0, 0).. etc
                        chars = convert_if_needed(obj_index, text_item)
                    concat_text((chars))

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
        if not (self.activate and self.inputs['verts'].is_linked):
            return True

        verts = self.inputs['verts'].sv_get()
        if not verts:
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

    def sv_copy(self, node):
        ''' reset n_id on copy '''
        self.n_id = ''


def register():
    bpy.utils.register_class(SvViewerTextBLF)


def unregister():
    bpy.utils.unregister_class(SvViewerTextBLF)
