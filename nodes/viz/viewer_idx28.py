# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Vector
from bpy.props import (BoolProperty, FloatVectorProperty, StringProperty, FloatProperty)

from sverchok.node_tree import SverchCustomTreeNode, MatrixSocket, VerticesSocket, StringsSocket
from sverchok.data_structure import (
    dataCorrect, node_id, updateNode, fullList, Vector_generate, Matrix_generate)

from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.sv_idx_viewer28_draw import draw_indices_2D


# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)




class SvIDXViewer28(bpy.types.Node, SverchCustomTreeNode):

    ''' IDX ViewerNode '''
    bl_idname = 'SvIDXViewer28'
    bl_label = 'Viewer Index+'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def get_scale(self):
        try:
            with sv_preferences() as prefs:
                scale = prefs.index_viewer_scale
        except:
            scale = 1.0
        return scale

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

    draw_bface: BoolProperty(
        name='draw_bface', description='draw backfacing indices?',
        default=True, update=updateNode)

    display_vert_index: BoolProperty(
        name="Vertices", description="Display vertex indices",
        default=True, update=updateNode)
    display_edge_index: BoolProperty(
        name="Edges", description="Display edge indices", update=updateNode)
    display_face_index: BoolProperty(
        name="Faces", description="Display face indices", update=updateNode)

    bg_edges_col: make_color_prop("bg_edges", (.2, .2, .2, 1.0))
    bg_faces_col: make_color_prop("bg_faces", (.2, .2, .2, 1.0))
    bg_verts_col: make_color_prop("bg_verts", (.2, .2, .2, 1.0))
    numid_edges_col: make_color_prop("numid_edges", (1.0, 1.0, 0.1, 1.0))
    numid_faces_col: make_color_prop("numid_faces", (1.0, .8, .8, 1.0))
    numid_verts_col: make_color_prop("numid_verts", (0.6, 1, 0.3, 1.0))

    def sv_init(self, context):
        inew = self.inputs.new
        inew('VerticesSocket', 'verts')
        inew('StringsSocket', 'edges')
        inew('StringsSocket', 'faces')
        inew('MatrixSocket', 'matrix')


    def draw_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')

        column_all = layout.column()

        row = column_all.row(align=True)
        split = row.split()
        r = split.column()
        r.prop(self, "activate", text="Show", toggle=True, icon=view_icon)
        row.prop(self, "draw_bg", text="BG", toggle=True)
        row.prop(self, "draw_bface", text="", icon='GHOST_ENABLED', toggle=True)

        col = column_all.column(align=True)
        for item, item_icon in zip(['vert', 'edge', 'face'], ['VERTEXSEL', 'EDGESEL', 'FACESEL']):
            row = col.row(align=True)
            row.prop(self, f"display_{item}_index", toggle=True, icon=item_icon, text='')
            row.prop(self, f"numid_{item}s_col", text="")
            if self.draw_bg:
                row.prop(self, f"bg_{item}s_col", text="") 

    def get_settings_dict(self):
        '''Produce a dict of settings for the callback'''
        # A copy is needed, we can't have reference to the
        # node in a callback, it will crash blender on undo
        return {
            'bg_edges_col': self.bg_edges_col[:],
            'bg_faces_col': self.bg_faces_col[:],
            'bg_verts_col': self.bg_verts_col[:],
            'numid_edges_col': self.numid_edges_col[:],
            'numid_faces_col': self.numid_faces_col[:],
            'numid_verts_col': self.numid_verts_col[:],
            'display_vert_index': self.display_vert_index,
            'display_edge_index': self.display_edge_index,
            'display_face_index': self.display_face_index,
            'draw_bface': self.draw_bface,
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

        for _icon in ['VERTEXSEL', 'EDGESEL', 'FACESEL']:
            colz = row.column(align=True)
            colz.scale_x = little_width
            colz.label(icon=_icon, text=' ')

        colprops = [
            ['Numbers :', ['numid_verts_col', 'numid_edges_col', 'numid_faces_col']],
            ['Background :', ['bg_verts_col', 'bg_edges_col', 'bg_faces_col']]
        ]

        for label, geometry_types in colprops:
            row = col.row(align=True)
            row.label(text=label)
            for colprop in geometry_types:
                colx = row.column(align=True)
                colx.scale_x = little_width
                colx.prop(self, colprop, text="")

    def update(self):
        # used because this node should disable itself if no inputs.
        n_id = node_id(self)
        callback_disable(n_id)

    def get_geometry(self):
        inputs = self.inputs
        geom = lambda: None

        for socket in ['verts', 'edges', 'faces', 'matrix']:
            input_stream = inputs[socket].sv_get(default=[])
            if socket == 'verts' and input_stream:
                input_stream = Vector_generate(input_stream)

            setattr(geom, socket, input_stream)

        # further process geom here? <<  YES >> 
        print(len(geom.verts), len(geom.matrix))

        return geom

    def process(self):
        n_id = node_id(self)
        callback_disable(n_id)

        if not self.id_data.sv_show:
            return

        self.use_custom_color = True
        if not (self.activate and self.inputs['verts'].is_linked):
            return

        self.generate_callback(n_id)

    def generate_callback(self, n_id):

        verts = self.inputs['verts'].sv_get()
        if not verts:
            return

        config = self.get_settings_dict()
        geom = self.get_geometry()

        draw_data = {
            'tree_name': self.id_data.name[:],
            'custom_function': draw_indices_2D,
            'args': (geom, config)} 

        callback_enable(n_id, draw_data, overlay='POST_PIXEL')

    def free(self):
        callback_disable(node_id(self))

    def copy(self, node):
        ''' reset n_id on copy '''
        self.n_id = ''


def register():
    bpy.utils.register_class(SvIDXViewer28)


def unregister():
    bpy.utils.unregister_class(SvIDXViewer28)
