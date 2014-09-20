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


class TextBaker(object):

    def __init__(self, node):
        self.node = node

    def collect_text_to_bake(self):
        node = self.node
        inputs = node.inputs

        def has_good_link(name, TypeSocket):
            if inputs[name].links:
                if isinstance(inputs[name].links[0].from_socket, TypeSocket):
                    return True

        def get_data(name, fallback=[]):
            if name in {'edges', 'faces', 'text'}:
                TypeSocket = StringsSocket
            else:
                TypeSocket = MatrixSocket if name == 'matrix' else VerticesSocket

            if has_good_link(name, TypeSocket):
                d = dataCorrect(SvGetSocketAnyType(node, inputs[name]))
                if name == 'matrix':
                    d = Matrix_generate(d) if d else []
                elif name == 'vertices':
                    d = Vector_generate(d) if d else []
                return d
            return fallback

        data_vector = get_data('vertices')
        if not data_vector:
            return

        data_edges = get_data('edges')
        data_faces = get_data('faces')
        data_matrix = get_data('matrix')
        data_text = get_data('text', '')

        for obj_index, verts in enumerate(data_vector):
            final_verts = verts

            if data_text:
                text_obj = data_text[obj_index]
            else:
                text_obj = ''

            if data_matrix:
                matrix = data_matrix[obj_index]
                final_verts = [matrix * v for v in verts]

            if node.display_vert_index:
                for idx, v in enumerate(final_verts):
                    if text_obj:
                        self.bake(idx, v, text_obj[idx])
                    else:
                        self.bake(idx, v)

            if data_edges and node.display_edge_index:
                for edge_index, (idx1, idx2) in enumerate(data_edges[obj_index]):

                    v1 = Vector(final_verts[idx1])
                    v2 = Vector(final_verts[idx2])
                    loc = v1 + ((v2 - v1) / 2)
                    if text_obj:
                        self.bake(edge_index, loc, text_obj[edge_index])
                    else:
                        self.bake(edge_index, loc)

            if data_faces and node.display_face_index:
                for face_index, f in enumerate(data_faces[obj_index]):
                    verts = [Vector(final_verts[idx]) for idx in f]
                    median = self.calc_median(verts)
                    if text_obj:
                        self.bake(face_index, median, text_obj[face_index])
                    else:
                        self.bake(face_index, median)

    def bake(self, index, origin, text_=''):
        node = self.node
        text = str(text_[0] if text_ else index)

        # Create and name TextCurve object
        name = 'sv_text_' + text
        tcu = bpy.data.curves.new(name=name, type='FONT')
        obj = bpy.data.objects.new(name, tcu)
        obj.location = origin
        bpy.context.scene.objects.link(obj)

        # TextCurve attributes
        tcu.body = text

        try:
            tcu.font = bpy.data.fonts[node.fonts]
        except:
            tcu.font = bpy.data.fonts[0]

        tcu.offset_x = 0
        tcu.offset_y = 0
        tcu.resolution_u = 2
        tcu.shear = 0
        tcu.size = node.font_size
        tcu.space_character = 1
        tcu.space_word = 1
        tcu.align = 'CENTER'

        tcu.extrude = 0.0
        tcu.fill_mode = 'NONE'

    def calc_median(self, vlist):
        a = Vector((0, 0, 0))
        for v in vlist:
            a += v
        return a / len(vlist)


class SvBakeText (bpy.types.Operator):

    """3Dtext baking"""
    bl_idname = "object.sv_text_baking"
    bl_label = "bake text"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.node.bake()
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

    font_size = FloatProperty(
        name="font_size", description='',
        min=0.01, default=0.1,
        update=updateNode)

    def make_color_prop(name, col):
        return FloatVectorProperty(
            name=name, description='', size=4, min=0.0, max=1.0,
            default=col, subtype='COLOR', update=updateNode)

    bg_edges_col = make_color_prop("bg_edges", (.2, .2, .2, 1.0))
    bg_faces_col = make_color_prop("bg_faces", (.2, .2, .2, 1.0))
    bg_verts_col = make_color_prop("bg_verts", (.2, .2, .2, 1.0))
    numid_edges_col = make_color_prop("numid_edges", (1.0, 1.0, 0.1, 1.0))
    numid_faces_col = make_color_prop("numid_faces", (1.0, .8, .8, 1.0))
    numid_verts_col = make_color_prop("numid_verts", (1, 1, 1, 1.0))

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

            row = col.row(align=True)
            row.prop_search(self, 'fonts', bpy.data, 'fonts', text='', icon='FONT_DATA')

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
        }

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

        layout.prop(self, 'bakebuttonshow', text='show bake UI')

    def update(self):
        inputs = self.inputs
        n_id = node_id(self)
        IV.callback_disable(n_id)

        # check if UI is populated.
        if not ('text' in inputs):
            return

        # end if tree status is set to not show
        if not self.id_data.sv_show:
            return

        self.use_custom_color = True

        if self.activate and inputs['vertices'].links:
            self.process(n_id, IV)
            self.color = READY_COLOR
        else:
            self.color = FAIL_COLOR

    def process(self, n_id, IV):
        inputs = self.inputs
        iv_links = inputs['vertices'].links
        im_links = inputs['matrix'].links

        draw_verts, draw_matrix = [], []
        text = ''

        # gather vertices from input
        if isinstance(iv_links[0].from_socket, VerticesSocket):
            propv = SvGetSocketAnyType(self, inputs['vertices'])
            draw_verts = dataCorrect(propv)

        # idea to make text in 3d
        if inputs['text'].links:
            text_so = SvGetSocketAnyType(self, inputs['text'])
            text = dataCorrect(text_so)
            fullList(text, len(draw_verts))
            for i, t in enumerate(text):
                fullList(text[i], len(draw_verts[i]))

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

    def update_socket(self, context):
        self.update()

    def free(self):
        IV.callback_disable(node_id(self))

    def bake(self):
        baker_obj = TextBaker(self)
        baker_obj.collect_text_to_bake()


def register():
    bpy.utils.register_class(IndexViewerNode)
    bpy.utils.register_class(SvBakeText)


def unregister():
    bpy.utils.unregister_class(SvBakeText)
    bpy.utils.unregister_class(IndexViewerNode)


if __name__ == '__main__':
    register()
