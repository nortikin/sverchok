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
import bmesh

from sverchok.node_tree import SverchCustomTreeNode


class SvCopySelectionFromObject(bpy.types.Operator):

    bl_idname = "node.copy_selection_from_object"
    bl_label = "Copy selection"

    @staticmethod
    def get_vertex_selection(selected_objs):
        """
        Read selection mask from given objects
        :param selected_objs: objects with mesh, bpy.types.Object
        :return: bool mask of selected vertex, [[0 ,0 ,1 ,0 , ...], [1 ,1 ,0 ,1 , ...], ...]
        """
        out = []
        for obj in selected_objs:
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
                selected_verts = [1 if vert.select else 0 for vert in bm.verts]
                out.append(selected_verts)
            else:
                selected_verts = [0 for _ in obj.data.vertices]
                obj.data.vertices.foreach_get('select', selected_verts)
                out.append(selected_verts)
        return out

    @staticmethod
    def get_edges_selection(selected_objs):
        """
        Read selection mask from given objects
        :param selected_objs: objects with mesh, bpy.types.Object
        :return: bool mask of selected edges, [[0 ,0 ,1 ,0 , ...], [1 ,1 ,0 ,1 , ...], ...]
        """
        out = []
        for obj in selected_objs:
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
                selected_edges = [1 if edge.select else 0 for edge in bm.edges]
                out.append(selected_edges)
            else:
                selected_edges = [0 for _ in obj.data.edges]
                obj.data.edges.foreach_get('select', selected_edges)
                out.append(selected_edges)
        return out

    @staticmethod
    def get_faces_selection(selected_objs):
        """
        Read selection mask from given objects
        :param selected_objs: objects with mesh, bpy.types.Object
        :return: bool mask of selected faces, [[0 ,0 ,1 ,0 , ...], [1 ,1 ,0 ,1 , ...], ...]
        """
        out = []
        for obj in selected_objs:
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
                selected_faces = [1 if face.select else 0 for face in bm.faces]
                out.append(selected_faces)
            else:
                selected_faces = [0 for _ in obj.data.polygons]
                obj.data.polygons.foreach_get('select', selected_faces)
                out.append(selected_faces)
        return out

    def execute(self, context):
        selected_objs = context.selected_objects
        if context.node.include_vertex:
            context.node.vertex_mask = self.get_vertex_selection(selected_objs)
        if context.node.include_edges:
            context.node.edges_mask = self.get_edges_selection(selected_objs)
        if context.node.include_faces:
            context.node.faces_mask = self.get_faces_selection(selected_objs)
        context.node.process_node(context)
        self.report({'INFO'}, "Mask was baked")
        return {'FINISHED'}


class SvSelectionGraber(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Get selection from object
    Node keeps selection independently of object

    Can take selection from several objects simultaneously
    """
    bl_idname = 'SvSelectionGraber'
    bl_label = 'Selection Graber'
    bl_icon = 'MOD_MASK'

    include_vertex = bpy.props.BoolProperty(default=True, description='include vertex mask in baking')
    include_edges = bpy.props.BoolProperty(default=True, description='include edges mask in baking')
    include_faces = bpy.props.BoolProperty(default=True, description='include faces mask in baking')

    def sv_init(self, context):
        self['vertex_mask'] = None
        self['edges_mask'] = None
        self['faces_mask'] = None
        self.outputs.new('StringsSocket', 'Vertex mask')
        self.outputs.new('StringsSocket', 'Edge mask')
        self.outputs.new('StringsSocket', 'Face mask')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'include_vertex', text=' ', icon='VERTEXSEL')
        row.prop(self, 'include_edges', text=' ', icon='EDGESEL')
        row.prop(self, 'include_faces', text=' ', icon='FACESEL')
        col.operator('node.copy_selection_from_object', text='Get from selected', icon='EYEDROPPER')

    def process(self):
        self.outputs['Vertex mask'].sv_set(self.vertex_mask)
        self.outputs['Edge mask'].sv_set(self.edges_mask)
        self.outputs['Face mask'].sv_set(self.faces_mask)

    @property
    def vertex_mask(self):
        if self['vertex_mask']:
            return [[i for i in l] for l in self['vertex_mask']]
        return [[]]

    @vertex_mask.setter
    def vertex_mask(self, array):
        self['vertex_mask'] = array

    @property
    def edges_mask(self):
        if self['edges_mask']:
            return [[i for i in l] for l in self['edges_mask']]
        return [[]]

    @edges_mask.setter
    def edges_mask(self, array):
        self['edges_mask'] = array

    @property
    def faces_mask(self):
        if self['faces_mask']:
            return [[i for i in l] for l in self['faces_mask']]
        return [[]]

    @faces_mask.setter
    def faces_mask(self, array):
        self['faces_mask'] = array


classes = [SvCopySelectionFromObject, SvSelectionGraber]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes[::-1]]
