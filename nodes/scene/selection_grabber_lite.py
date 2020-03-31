# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvSelectionGrabberLite(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvSelectionGrabberLite
    Tooltip: 
    
    A short description for reader of node code
    """

    bl_idname = 'SvSelectionGrabberLite'
    bl_label = 'Selection Grabber Lite'
    bl_icon = 'MOD_MASK'

    include_vertex: bpy.props.BoolProperty(default=True, description='include vertex mask in baking', update=updateNode)
    include_edges: bpy.props.BoolProperty(default=True, description='include edges mask in baking', update=updateNode)
    include_faces: bpy.props.BoolProperty(default=True, description='include faces mask in baking', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', "Object")
        self.outputs.new('SvStringsSocket', "Vertex Mask")
        self.outputs.new('SvStringsSocket', "Edge Mask")
        self.outputs.new('SvStringsSocket', "Face Mask")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'include_vertex', text=' ', icon='VERTEXSEL')
        row.prop(self, 'include_edges', text=' ', icon='EDGESEL')
        row.prop(self, 'include_faces', text=' ', icon='FACESEL')
        # col.operator('node.copy_selection_from_object', text='Get from selected', icon='EYEDROPPER')

    def process(self):
        objects = self.inputs['Object'].sv_get()
        if not objects:
            return

        face_mask, edge_mask, vertex_mask = [], [], []

        for obj in objects:
            if obj == bpy.context.edit_object:
                bm = bmesh.from_edit_mesh(obj.data)
                if self.include_faces:
                    face_mask.append([f.select for f in bm.faces])
                if self.include_edges:
                    edge_mask.append([e.select for e in bm.edges])
                if self.include_vertex:
                    vertex_mask.append([e.select for e in bm.verts])
            else:
                mesh = obj.data
                if self.include_faces:
                    face_mask.append([f.select for f in mesh.polygons])
                if self.include_edges:
                    edge_mask.append([f.select for f in mesh.edges])
                if self.include_vertex:
                    vertex_mask.append([f.select for f in mesh.vertices])

        self.outputs['Vertex Mask'].sv_set(vertex_mask)
        self.outputs['Edge Mask'].sv_set(edge_mask)
        self.outputs['Face Mask'].sv_set(face_mask)


classes = [SvSelectionGrabberLite]
register, unregister = bpy.utils.register_classes_factory(classes)
