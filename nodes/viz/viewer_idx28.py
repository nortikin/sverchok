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
from sverchok.utils.sv_idx_viewer28_draw import draw_indices_2D



# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)




class SvIDXViewer28(bpy.types.Node, SverchCustomTreeNode):

    ''' IDX ViewerNode '''
    bl_idname = 'SvIDXViewer28'
    bl_label = 'Viewer Index+'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # node id
    n_id: StringProperty(default='', options={'SKIP_SAVE'})

    activate: BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    draw_bg: BoolProperty(
        name='draw_bg', description='draw background poly?',
        default=False, update=updateNode)

    display_vert_index: BoolProperty(
        name="Vertices", description="Display vertex indices",
        default=True, update=updateNode)
    display_edge_index: BoolProperty(
        name="Edges", description="Display edge indices", update=updateNode)
    display_face_index: BoolProperty(
        name="Faces", description="Display face indices", update=updateNode)

    def make_color_prop(name, col):
        return FloatVectorProperty(
            name=name, description='', size=4, min=0.0, max=1.0,
            default=col, subtype='COLOR', update=updateNode)

    bg_edges_col: make_color_prop("bg_edges", (.2, .2, .2, 1.0))
    bg_faces_col: make_color_prop("bg_faces", (.2, .2, .2, 1.0))
    bg_verts_col: make_color_prop("bg_verts", (.2, .2, .2, 1.0))
    numid_edges_col: make_color_prop("numid_edges", (1.0, 1.0, 0.1, 1.0))
    numid_faces_col: make_color_prop("numid_faces", (1.0, .8, .8, 1.0))
    numid_verts_col: make_color_prop("numid_verts", (0.6, 1, 0.3, 1.0))

    def sv_init(self, context):
        inew = self.inputs.new
        inew('VerticesSocket', 'vertices')
        inew('StringsSocket', 'edges')
        inew('StringsSocket', 'faces')
        inew('MatrixSocket', 'matrix')

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def draw_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')

        column_all = layout.column()

        row = column_all.row(align=True)
        split = row.split()
        r = split.column()
        r.prop(self, "activate", text="Show", toggle=True, icon=view_icon)
        row.prop(self, "draw_bg", text="Background", toggle=True)

        col = column_all.column(align=True)

        row = col.row(align=True)
        row.prop(self, "display_vert_index", toggle=True, icon='VERTEXSEL', text='')
        row.prop(self, "numid_verts_col", text="")
        if self.draw_bg:
            row.prop(self, "bg_verts_col", text="")

        row = col.row(align=True)
        row.prop(self, "display_edge_index", toggle=True, icon='EDGESEL', text='')
        row.prop(self, "numid_edges_col", text="")
        if self.draw_bg:
            row.prop(self, "bg_edges_col", text="")

        row = col.row(align=True)
        row.prop(self, "display_face_index", toggle=True, icon='FACESEL', text='')
        row.prop(self, "numid_faces_col", text="")
        if self.draw_bg:
            row.prop(self, "bg_faces_col", text="")

    def get_settings(self):
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
            'display_face_index': self.display_face_index
        }.copy()

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        box = layout.box()
        little_width = 0.135

        # heading - wide column for descriptors
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Colors')  # IDX pallete

        # heading - remaining column space divided by
        # little_width factor. shows icons only
        col1 = row.column(align=True)
        col1.scale_x = little_width
        col1.label(icon='VERTEXSEL', text=' ')

        col2 = row.column(align=True)
        col2.scale_x = little_width
        col2.label(icon='EDGESEL', text=' ')

        col3 = row.column(align=True)
        col3.scale_x = little_width
        col3.label(icon='FACESEL', text=' ')

        # 'table info'
        colprops = [
            ['Numbers :', [
                'numid_verts_col', 'numid_edges_col', 'numid_faces_col']],
            ['Backgrnd :', [
                'bg_verts_col', 'bg_edges_col', 'bg_faces_col']]
        ]

        # each first draws the table row heading, 'label'
        # then for each geometry type will draw the color property
        # with the same spacing as col1, col2, col3 above
        for label, geometry_types in colprops:
            row = col.row(align=True)
            row.label(text=label)
            for colprop in geometry_types:
                col4 = row.column(align=True)
                col4.scale_x = little_width
                col4.prop(self, colprop, text="")

        layout.prop(self, 'bakebuttonshow', text='show bake UI')

    def update(self):
        # used because this node should disable itself in certain scenarios
        # : namely , no inputs.
        n_id = node_id(self)
        callback_disable(n_id)

    def process(self):
        inputs = self.inputs
        n_id = node_id(self)
        callback_disable(n_id)

        # end if tree status is set to not show
        if not self.id_data.sv_show:
            return

        self.use_custom_color = True

        if not (self.activate and inputs['vertices'].is_linked):
            return

        self.generate_callback(n_id)

    def generate_callback(self, n_id):

        try:
            with sv_preferences() as prefs:
                scale = prefs.index_viewer_scale
        except:
            # print('did not find preferences - you need to save user preferences')
            scale = 1.0

        inputs = self.inputs
        verts, matrices = [], []
        text = ''

        # gather vertices from input
        propv = inputs['vertices'].sv_get()
        verts = dataCorrect(propv)

        # end early, no point doing anything else.
        if not verts:
            return

        # read non vertex inputs in a loop and assign to data_collected
        data_collected = []
        for socket in ['edges', 'faces', 'matrix']:
            propm = inputs[socket].sv_get(default=[])
            input_stream = propm
            data_collected.append(input_stream)

        edges, faces, matrices = data_collected

        bg = self.draw_bg
        settings = self.get_settings()

        geom = None
        config = None

        draw_data = {
            'tree_name': self.id_data.name[:],
            'custom_function': draw_indices_2D,
            'args': (geom, config)
        } 

        callback_enable(n_id, draw_data)


    def free(self):
        callback_disable(node_id(self))


def register():
    bpy.utils.register_class(SvIDXViewer28)


def unregister():
    bpy.utils.unregister_class(SvIDXViewer28)
