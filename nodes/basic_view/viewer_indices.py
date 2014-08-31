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
from mathutils import Vector
from bpy.props import (BoolProperty, FloatVectorProperty, StringProperty,
                       FloatProperty, EnumProperty)

from node_tree import SverchCustomTreeNode, MatrixSocket, VerticesSocket, StringsSocket
from data_structure import (
    dataCorrect, node_id, updateNode, SvGetSocketAnyType, fullList,
    Vector_generate, Matrix_generate)

from utils import index_viewer_draw as IV


# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)


class SvBakeText (bpy.types.Operator):

    """3Dtext baking"""
    bl_idname = "object.sv_text_baking"
    bl_label = "bake text"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        n = context.node
        n.collect_text_to_bake()
        return {'FINISHED'}


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

    bakebuttonshow = BoolProperty(
        name='bakebuttonshow', description='show bake button on node',
        default=False,
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

    fonts = StringProperty(name='fonts', default='', update=updateNode)
    # fontsize
    #fonts = EnumProperty(items=[('Bfont', 'Bfont', 'Bfont')],
    #                     name='fonts', update=updateNode)

    font_size = FloatProperty(
        name="font_size", description='',
        min=0.01, default=0.1,
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

        if self.bakebuttonshow:
            row = col.row(align=True)
            row.scale_y = 3
            row.operator('object.sv_text_baking', text='B A K E')
            row = col.row(align=True)
            row.prop(self, "font_size")
            #fonts_ = [(n.name,n.name,n.name) for n in bpy.data.fonts]
            #self.fonts = EnumProperty(items=fonts_, name='fonts', update=updateNode)
            row = col.row(align=True)
            row.prop(self, "fonts")

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
            ['Numbers :', [
                'numid_verts_col', 'numid_edges_col', 'numid_faces_col']],
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

        layout.prop(self, 'bakebuttonshow')

    # baking
    def collect_text_to_bake(self):
        # n_id, settings, text
        context = bpy.context

        # ensure data or empty lists.
        # gather vertices from input
        if self.inputs['vertices'].links:
            if isinstance(self.inputs['vertices'].links[0].from_socket, VerticesSocket):
                propv = dataCorrect(
                    SvGetSocketAnyType(self, self.inputs['vertices']))
                data_vector = Vector_generate(propv) if propv else []
        else:
            return
        data_edges, data_faces = [], []
        if self.inputs['edges'].links:
            if isinstance(self.inputs['edges'].links[0].from_socket, StringsSocket):
                data_edges = dataCorrect(
                    SvGetSocketAnyType(self, self.inputs['edges']))
        if self.inputs['faces'].links:
            if isinstance(self.inputs['faces'].links[0].from_socket, StringsSocket):
                data_faces = dataCorrect(
                    SvGetSocketAnyType(self, self.inputs['faces']))
        data_matrix = []
        if self.inputs['matrix'].links:
            if isinstance(self.inputs['matrix'].links[0].from_socket, MatrixSocket):
                matrix = dataCorrect(
                    SvGetSocketAnyType(self, self.inputs['matrix']))
                data_matrix = Matrix_generate(matrix) if matrix else []
        data_text = ''
        if self.inputs['text'].links:
            if isinstance(self.inputs['text'].links[0].from_socket, StringsSocket):
                data_text = dataCorrect(
                    SvGetSocketAnyType(self, self.inputs['text']))

        display_vert_index = self.display_vert_index
        display_edge_index = self.display_edge_index
        display_face_index = self.display_face_index

        ########
        # points
        def calc_median(vlist):
            a = Vector((0, 0, 0))
            for v in vlist:
                a += v
            return a / len(vlist)

        for obj_index, verts in enumerate(data_vector):
            final_verts = verts
            if data_text:
                text_obj = data_text[obj_index]
            else:
                text_obj = ''

            # quickly apply matrix if necessary
            if data_matrix:
                matrix = data_matrix[obj_index]
                final_verts = [matrix * v for v in verts]

            if display_vert_index:
                for idx, v in enumerate(final_verts):
                    if text_obj:
                        self.bake(idx, v, text_obj[idx])
                    else:
                        self.bake(idx, v)

            if data_edges and display_edge_index:
                for edge_index, (idx1, idx2) in enumerate(data_edges[obj_index]):

                    v1 = Vector(final_verts[idx1])
                    v2 = Vector(final_verts[idx2])
                    loc = v1 + ((v2 - v1) / 2)
                    if text_obj:
                        self.bake(edge_index, loc, text_obj[edge_index])
                    else:
                        self.bake(edge_index, loc)

            if data_faces and display_face_index:
                for face_index, f in enumerate(data_faces[obj_index]):
                    verts = [Vector(final_verts[idx]) for idx in f]
                    median = calc_median(verts)
                    if text_obj:
                        self.bake(face_index, median, text_obj[face_index])
                    else:
                        self.bake(face_index, median)

    def bake(self, index, origin, text_=''):
        if text_:
            text = str(text_[0])
        else:
            text = str(index)
        # Create and name TextCurve object
        bpy.ops.object.text_add(view_align=False,
                                enter_editmode=False,location=origin)
        ob = bpy.context.object
        ob.name = 'sv_text_' + text
        tcu = ob.data
        tcu.name = 'sv_text_' + text
        # TextCurve attributes
        tcu.body = text
        try:
            tcu.font = bpy.data.fonts[self.fonts]
        except:
            tcu.font = bpy.data.fonts[0]
        tcu.offset_x = 0
        tcu.offset_y = 0
        tcu.resolution_u = 2
        tcu.shear = 0
        Tsize = self.font_size
        tcu.size = Tsize
        tcu.space_character = 1
        tcu.space_word = 1
        tcu.align = 'CENTER'
        # Inherited Curve attributes
        tcu.extrude = 0.0
        tcu.fill_mode = 'NONE'

    def update(self):
        inputs = self.inputs
        text = ''

        # if you change this change in free() also
        n_id = node_id(self)
        IV.callback_disable(n_id)

        # end early
        # check if UI is populated.
        if not ('text' in inputs):
            return

        # end if tree status is set to not show
        if not self.id_data.sv_show:
            return

        # alias in case it is present
        iv_links = inputs['vertices'].links
        self.use_custom_color = True

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
                n_id, draw_verts, draw_edges, draw_faces,
                draw_matrix, bg, settings.copy(), text)
                
            self.color = READY_COLOR
        else:
            self.color = FAIL_COLOR

    def update_socket(self, context):
        self.update()

    def free(self):
        IV.callback_disable(node_id(self))


def register():
    bpy.utils.register_class(IndexViewerNode)
    bpy.utils.register_class(SvBakeText)


def unregister():
    bpy.utils.unregister_class(SvBakeText)
    bpy.utils.unregister_class(IndexViewerNode)


if __name__ == '__main__':
    register()

