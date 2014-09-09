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
from bpy.props import BoolProperty, StringProperty
from mathutils import Matrix

from node_tree import (SverchCustomTreeNode, SvColors,
                       StringsSocket, VerticesSocket, MatrixSocket)
from data_structure import (cache_viewer_baker,
                            dataCorrect, node_id,
                            Vector_generate, Matrix_generate,
                            updateNode, SvGetSocketAnyType)

from utils.viewer_draw_mk2 import callback_disable, callback_enable


class ViewerNode2(bpy.types.Node, SverchCustomTreeNode):
    ''' ViewerNode2 '''
    bl_idname = 'ViewerNode2'
    bl_label = 'Viewer Draw2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # node id
    n_id = StringProperty(default='', options={'SKIP_SAVE'})

    Vertex_show = BoolProperty(
        name='Vertices', description='Show or not vertices',
        default=1, update=updateNode)

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=1, update=updateNode)

    transparant = BoolProperty(
        name='Transparant', description='transparant polygons?',
        default=0, update=updateNode)

    shading = BoolProperty(
        name='Shading', description='shade the object or index representation?',
        default=0, update=updateNode)

    color_view = SvColors.color

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.use_custom_color = True

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "Vertex_show", text="Verts")
        row.prop(self, "activate", text="Show")

        row = layout.row(align=True)
        row.prop(self, "transparant", text="Transp")
        row.prop(self, "shading", text="Shade")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "color_view", text=" ")

    # reset n_id on duplicate (shift-d)
    def copy(self, node):
        self.n_id = ''

    def update(self):
        if 'matrix' not in self.inputs:
            return

        if not (self.id_data.sv_show and self.activate):
            return

        self.process()

    def process(self):
        n_id = node_id(self)

        global cache_viewer_baker
        vertex_ref = n_id + 'v'
        poledg_ref = n_id + 'ep'
        matrix_ref = n_id + 'm'
        cache_viewer_baker[vertex_ref] = []
        cache_viewer_baker[poledg_ref] = []
        cache_viewer_baker[matrix_ref] = []

        callback_disable(n_id)

        # every time you hit a dot, you pay a price, so alias and benefit
        inputs = self.inputs
        vertex_links = inputs['vertices'].links
        matrix_links = inputs['matrix'].links
        edgepol_links = self.inputs['edg_pol'].links

        if (vertex_links or matrix_links):

            if vertex_links:
                if isinstance(vertex_links[0].from_socket, VerticesSocket):
                    propv = inputs['vertices'].sv_get()
                    cache_viewer_baker[vertex_ref] = dataCorrect(propv)

            if edgepol_links:
                if isinstance(edgepol_links[0].from_socket, StringsSocket):
                    prope = inputs['edg_pol'].sv_get()
                    cache_viewer_baker[poledg_ref] = dataCorrect(prope)

            if matrix_links:
                if isinstance(matrix_links[0].from_socket, MatrixSocket):
                    propm = inputs['matrix'].sv_get()
                    cache_viewer_baker[matrix_ref] = dataCorrect(propm)

        if cache_viewer_baker[vertex_ref] or cache_viewer_baker[matrix_ref]:
            config_options = self.get_options().copy()
            callback_enable(n_id, cache_viewer_baker, config_options)
            self.color = (1, 0.3, 0.5)
        else:
            self.color = (0.1, 0.05, 0.5)

    def get_options(self):
        return {
            'show_verts': self.Vertex_show,
            'color_view': self.color_view,
            'transparent': self.transparant,
            'shading': self.shading
            }

    def update_socket(self, context):
        self.update()

    def free(self):
        global cache_viewer_baker
        n_id = node_id(self)
        callback_disable(n_id)
        cache_viewer_baker.pop(n_id+'v', None)
        cache_viewer_baker.pop(n_id+'ep', None)
        cache_viewer_baker.pop(n_id+'m', None)


def register():
    bpy.utils.register_class(ViewerNode2)


def unregister():
    bpy.utils.unregister_class(ViewerNode2)


if __name__ == '__main__':
    register()
