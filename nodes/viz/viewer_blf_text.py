# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Vector
from mathutils.geometry import normal  # takes 3 or more! :)
from bpy.props import (BoolProperty, FloatVectorProperty, StringProperty, FloatProperty)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    dataCorrect, node_id, updateNode, fullList, Vector_generate, Matrix_generate)

from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.sv_idx_viewer28_draw import draw_indices_2D, draw_indices_2D_wbg

# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)


class SvViewerTextBLF(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: blf
    Tooltip:  view text in 3dview using basic blf features (size, orientation, color..)
    """

    bl_idname = 'SvViewerTextBLF'
    bl_label = 'Viewer blf Text'
    bl_icon = 'INFO'
    sv_icon = 'SV_INDEX_VIEWER'

    def show_viewport(self, is_show: bool):
        """It should be called by node tree to show/hide objects"""
        if not self.activate:
            # just ignore request
            pass
        else:
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
        default=True,
        update=updateNode)

    draw_bg: BoolProperty(
        name='draw_bg', description='draw background poly?',
        default=False, update=updateNode)

    bg_verts_col: make_color_prop("bg_verts", (.2, .2, .2, 1.0))
    numid_verts_col: make_color_prop("numid_verts", (0.6, 1, 0.3, 1.0))

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
        row.prop(self, "draw_bg", text="BG", toggle=True)

    def get_settings_dict(self):
        '''Produce a dict of settings for the callback'''
        # A copy is needed, we can't have reference to the
        # node in a callback, it will crash blender on undo
        return {
            'bg_verts_col': self.bg_verts_col[:],
            'numid_verts_col': self.numid_verts_col[:],
            'display_vert_index': self.display_vert_index,
            'draw_bg': self.draw_bg,
            'scale': self.get_scale()
        }.copy()

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        box = layout.box()
        little_width = 0.735

        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Colors')

    def get_geometry(self):
        inputs = self.inputs
        geom = lambda: None

        for socket in ['locations', 'text']:
            input_stream = inputs[socket].sv_get(default=[])
            if socket == 'locations' and input_stream:
                input_stream = Vector_generate(input_stream)

            setattr(geom, socket, input_stream)

        # pass only data onto the draw callback that you intend to show.
        display_topology = lambda: None
        display_topology.locations_data = []
        display_topology.text_data = []

        concat_locations = display_topology.locations_data.append
        concat_text = display_topology.text_data.append

        prefix_if_needed = lambda chars: f'{chars}'
        
        for final_verts in geom.locations:


            for idx, vpos in enumerate(final_verts):
                chars = prefix_if_needed(idx)
                concat_locations((chars, vpos))
            
            if geom.text:    
                text_items = self.get_text_of_correct_length(obj_index, geom, len(final_verts))                        
                for text_item, vpos in zip(text_items, final_verts):

                    # yikes, don't feed this function nonsense :)
                    if isinstance(text_item, float):
                        chars = prefix_if_needed(obj_index, text_item)
                    elif isinstance(text_item, list) and len(text_item) == 1:
                        chars = prefix_if_needed(obj_index, text_item[0])

                    else:
                        # in case it receives [0, 0, 0] or (0, 0, 0).. etc
                        chars = prefix_if_needed(obj_index, text_item)

                    concat_text((chars))

        return display_topology

    def get_text_of_correct_length(self, obj_index, geom, num_elements_to_fill):
        """ get text elements, and extend if needed"""
        if obj_index < len(geom.text):
            text_items = geom.text[obj_index]
        else:
            text_items = geom.text[len(geom.text)-1]

        if not (len(text_items) == num_elements_to_fill):
            
            # ---- this doesn't touch the data, but returns a copy, or a modified copy -----
            if len(text_items) < num_elements_to_fill:
                return text_items + [text_items[-1], ] * (num_elements_to_fill - len(text_items))
            else:
                return text_items[:num_elements_to_fill]

        return text_items

    def end_early(self):
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

        draw_func = draw_indices_2D_wbg if self.draw_bg else draw_indices_2D
        draw_data = {
            'tree_name': self.id_data.name[:],
            'custom_function': draw_func,
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
