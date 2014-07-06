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

import bpy
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty

from node_tree import SverchCustomTreeNode, MatrixSocket, VerticesSocket
from data_structure import dataCorrect, node_id, updateNode, SvGetSocketAnyType, \
                            fullList
from utils import index_viewer_draw as IV


# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)


class IndexViewerNode(bpy.types.Node, SverchCustomTreeNode):
    ''' IDX ViewerNode '''
    bl_idname = 'IndexViewerNode'
    bl_label = 'Index Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # node id
    n_id = StringProperty(default='', options={'SKIP_SAVE'})

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    draw_bg = BoolProperty(
        name='draw_bg', description='draw background poly?',
        default=False,
        update=updateNode)

    display_vert_index = BoolProperty(
        name="Vertices", description="Display vertex indices",
        default=True,
        update=updateNode)
    display_edge_index = BoolProperty(
        name="Edges", description="Display edge indices",
        update=updateNode)
    display_face_index = BoolProperty(
        name="Faces", description="Display face indices",
        update=updateNode)

    # color props
    bg_edges_col = FloatVectorProperty(
        name="bg_edges", description='',
        size=4, min=0.0, max=1.0,
        default=(.2, .2, .2, 1.0), subtype='COLOR',
        update=updateNode)

    bg_faces_col = FloatVectorProperty(
        name="bg_faces", description='',
        size=4, min=0.0, max=1.0,
        default=(.2, .2, .2, 1.0), subtype='COLOR',
        update=updateNode)

    bg_verts_col = FloatVectorProperty(
        name="bg_verts", description='',
        size=4, min=0.0, max=1.0,
        default=(.2, .2, .2, 1.0), subtype='COLOR',
        update=updateNode)

    numid_edges_col = FloatVectorProperty(
        name="numid_edges", description='',
        size=4, min=0.0, max=1.0,
        default=(1.0, 1.0, 0.1, 1.0), subtype='COLOR',
        update=updateNode)

    numid_faces_col = FloatVectorProperty(
        name="numid_faces", description='',
        size=4, min=0.0, max=1.0,
        default=(1.0, .8, .8, 1.0), subtype='COLOR',
        update=updateNode)

    numid_verts_col = FloatVectorProperty(
        name="numid_verts", description='',
        size=4, min=0.0, max=1.0,
        default=(1, 1, 1, 1.0), subtype='COLOR',
        update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('StringsSocket', 'faces', 'faces')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.inputs.new('StringsSocket', 'text', 'text')

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Show")
        row.prop(self, "draw_bg", text="Background")

        layout.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        row.active = (self.activate)

        row.prop(self, "display_vert_index", toggle=True)
        row.prop(self, "display_edge_index", toggle=True)
        row.prop(self, "display_face_index", toggle=True)

    def get_settings(self):
        '''Produce a dict of settings for the callback'''
        settings = {}
        # A copy is needed, we can't have reference to the
        # node in a callback, it will crash blender on undo
        settings['bg_edges_col'] = self.bg_edges_col[:]
        settings['bg_faces_col'] = self.bg_faces_col[:]
        settings['bg_verts_col'] = self.bg_verts_col[:]
        settings['numid_edges_col'] = self.numid_edges_col[:]
        settings['numid_faces_col'] = self.numid_faces_col[:]
        settings['numid_verts_col'] = self.numid_verts_col[:]
        settings['display_vert_index'] = self.display_vert_index
        settings['display_edge_index'] = self.display_edge_index
        settings['display_face_index'] = self.display_face_index

        return settings

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
            ['Numbers :', ['numid_verts_col', 'numid_edges_col', 'numid_faces_col']],
            ['Backgrnd :', ['bg_verts_col', 'bg_edges_col', 'bg_faces_col']]
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

    def update(self):
        inputs = self.inputs
        text=''

        # if you change this change in free() also
        n_id = node_id(self)
        # end early
        if not ('vertices' in inputs) and not ('matrix' in inputs):
            IV.callback_disable(n_id)
            return
        # end if tree status is set to not show
        if not self.id_data.sv_show:
            IV.callback_disable(n_id)
            return

        # alias in case it is present
        iv_links = inputs['vertices'].links

        if self.activate and iv_links:
            IV.callback_disable(n_id)
            draw_verts, draw_matrix = [], []

            # gather vertices from input
            if isinstance(iv_links[0].from_socket, VerticesSocket):
                propv = SvGetSocketAnyType(self, inputs['vertices'])
                draw_verts = dataCorrect(propv)
            
            # idea to make text in 3d
            if 'text' in inputs and inputs['text'].links:
                text_so = SvGetSocketAnyType(self, inputs['text'])
                text = dataCorrect(text_so)
                fullList(text, len(draw_verts))
                for i, t in enumerate(text):
                    fullList(text[i], len(draw_verts[i]))
                
            # matrix might be operating on vertices, check and act on.
            if 'matrix' in inputs:
                im_links = inputs['matrix'].links

                # end early, skips to drwa vertex indices without matrix
                if im_links and isinstance(im_links[0].from_socket, MatrixSocket):
                    propm = SvGetSocketAnyType(self, inputs['matrix'])
                    draw_matrix = dataCorrect(propm)

            data_feind = []
            for socket in ['edges', 'faces']:
                try:
                    propm = SvGetSocketAnyType(self, inputs[socket])
                    input_stream = dataCorrect(propm)
                except:
                    input_stream = []
                finally:
                    data_feind.append(input_stream)

            draw_edges, draw_faces = data_feind

            bg = self.draw_bg
            settings = self.get_settings()
            IV.callback_enable(
                n_id, draw_verts, draw_edges, draw_faces, draw_matrix, bg, settings.copy(), text)
            self.use_custom_color = True
            self.color = READY_COLOR
        else:
            IV.callback_disable(n_id)
            self.use_custom_color = True
            self.color = FAIL_COLOR

    def update_socket(self, context):
        self.update()

    def free(self):
        IV.callback_disable(node_id(self))


def register():
    bpy.utils.register_class(IndexViewerNode)


def unregister():
    bpy.utils.unregister_class(IndexViewerNode)
