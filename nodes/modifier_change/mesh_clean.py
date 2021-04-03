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
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.sv_mesh_utils import clean_meshes


class SvMeshCleanNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    '''
    Triggers: Duplicated + unreferenced
    Tooltip: Cleans input mesh by removing doubled, unreferenced or bad formed elements
    '''
    bl_idname = 'SvMeshCleanNode'
    bl_label = 'Mesh Clean'
    bl_icon = 'SHADING_RENDERED'

    remove_unreferenced_edges: BoolProperty(
        name='Unreferenced Edges',
        description='Remove the edges that point to un-existing vertices',
        default=False,
        update=updateNode)
    remove_unreferenced_faces: BoolProperty(
        name='Unreferenced Faces',
        description='Remove the faces that point to un-existing vertices',
        default=False,
        update=updateNode)

    remove_loose_verts: BoolProperty(
        name='Unused Vertices',
        description='Removes the vertices not used to create any edge or face',
        default=False,
        update=updateNode)


    remove_duplicated_edges: BoolProperty(
        name='Duplicated Edges',
        description='Remove duplicated edges. Note that (0,1) and (1,0) will be considered identical.',
        default=False,
        update=updateNode)
    remove_duplicated_faces: BoolProperty(
        name='Duplicated Faces',
        description='Remove duplicated faces. Note that faces as (0,1,2,3) and (1,0,3,2) will be considered identical.',
        default=False,
        update=updateNode)

    remove_degenerated_edges: BoolProperty(
        name='Degenerated Edges',
        description='Check for edges with repeated indices and remove them',
        default=False,
        update=updateNode)
    remove_degenerated_faces: BoolProperty(
        name='Degenerated Faces',
        description='Check for repeated indices on every face and remove them, if it has less than 3 vertices then the face will be removed',
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices").is_mandatory = True
        self.inputs.new('SvStringsSocket', "Edges").nesting_level = 3
        self.inputs.new('SvStringsSocket', "Faces").nesting_level = 3

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

        self.outputs.new('SvStringsSocket', "Removed Vertices Idx")
        self.outputs.new('SvStringsSocket', "Removed Edges Idx")
        self.outputs.new('SvStringsSocket', "Removed Faces Idx")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.label(text='Remove:')
        col.prop(self, 'remove_unreferenced_edges', toggle=True)
        col.prop(self, 'remove_unreferenced_faces', toggle=True)
        col.prop(self, 'remove_duplicated_edges', toggle=True)
        col.prop(self, 'remove_duplicated_faces', toggle=True)
        col.prop(self, 'remove_degenerated_edges', toggle=True)
        col.prop(self, 'remove_degenerated_faces', toggle=True)
        col.prop(self, 'remove_loose_verts', toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")


    def process_data(self, params):
        vertices, edges, faces = params
        calc_verts_idx, calc_edges_idx, calc_faces_idx = [s.is_linked for s in self.outputs[3:]]
        return clean_meshes(
            vertices, edges, faces,
            remove_unreferenced_edges=self.remove_unreferenced_edges,
            remove_unreferenced_faces=self.remove_unreferenced_faces,
            remove_duplicated_edges=self.remove_duplicated_edges,
            remove_duplicated_faces=self.remove_duplicated_faces,
            remove_degenerated_edges=self.remove_degenerated_edges,
            remove_degenerated_faces=self.remove_degenerated_faces,
            remove_loose_verts=self.remove_loose_verts,
            calc_verts_idx=calc_verts_idx,
            calc_edges_idx=calc_edges_idx,
            calc_faces_idx=calc_faces_idx)

def register():
    bpy.utils.register_class(SvMeshCleanNode)


def unregister():
    bpy.utils.unregister_class(SvMeshCleanNode)
