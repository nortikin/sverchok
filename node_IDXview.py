import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import BoolProperty

from node_s import *
from util import *
import Index_Viewer_draw as IV


class IndexViewerNode(Node, SverchCustomTreeNode):
    ''' IDX ViewerNode '''
    bl_idname = 'IndexViewerNode'
    bl_label = 'Index Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    draw_bg = BoolProperty(
        name='draw_bg', description='draw background poly?',
        default=False,
        update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Show")
        row.prop(self, "draw_bg", text="Background")

    def update(self):
        inputs = self.inputs

        # end early
        if not ('vertices' in inputs) and not ('matrix' in inputs):
            IV.callback_disable(self.name)
            return

        # alias in case it is present
        iv_links = inputs['vertices'].links

        if self.activate and iv_links:
            IV.callback_disable(self.name)
            draw_verts, draw_matrix = [], []

            # gather vertices from input
            if isinstance(iv_links[0].from_socket, VerticesSocket):
                propv = SvGetSocketAnyType(self, inputs['vertices'])
                draw_verts = dataCorrect(propv)

            # matrix might be operating on vertices, check and act on.
            if 'matrix' in inputs:
                im_links = inputs['matrix'].links

                # end early, skips to drwa vertex indices without matrix
                if im_links and isinstance(im_links[0].from_socket, MatrixSocket):
                    propm = SvGetSocketAnyType(self, inputs['matrix'])
                    draw_matrix = dataCorrect(propm)

            bg = self.draw_bg
            IV.callback_enable(self.name, draw_verts, draw_matrix, bg)
        else:
            IV.callback_disable(self.name)

    def update_socket(self, context):
        self.update()

    def free(self):
        IV.callback_disable(self.name)


def register():
    bpy.utils.register_class(IndexViewerNode)


def unregister():
    bpy.utils.unregister_class(IndexViewerNode)


if __name__ == "__main__":
    register()
