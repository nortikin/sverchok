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

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', "Object")
        self.outputs.new('SvStringsSocket', "Vertex Mask")
        self.outputs.new('SvStringsSocket', "Edge Mask")
        self.outputs.new('SvStringsSocket', "Face Mask")

    def process(self):
        objects = self.inputs['Object'].sv_get()
        if not objects:
            return

        include_vertex = self.outputs["Vertex Mask"].is_linked
        include_edges = self.outputs["Edge Mask"].is_linked
        include_faces = self.outputs["Face Mask"].is_linked

        face_mask, edge_mask, vertex_mask = [], [], []

        for obj in objects:
            mesh = obj.data

            if obj == bpy.context.edit_object:
                bm = bmesh.from_edit_mesh(mesh)
                if include_faces:
                    face_mask.append([f.select for f in bm.faces])
                if include_edges:
                    edge_mask.append([e.select for e in bm.edges])
                if include_vertex:
                    vertex_mask.append([e.select for e in bm.verts])
            else:
                if include_faces:
                    face_mask.append([f.select for f in mesh.polygons])
                if include_edges:
                    edge_mask.append([f.select for f in mesh.edges])
                if include_vertex:
                    vertex_mask.append([f.select for f in mesh.vertices])

        self.outputs['Vertex Mask'].sv_set(vertex_mask)
        self.outputs['Edge Mask'].sv_set(edge_mask)
        self.outputs['Face Mask'].sv_set(face_mask)


classes = [SvSelectionGrabberLite]
register, unregister = bpy.utils.register_classes_factory(classes)
