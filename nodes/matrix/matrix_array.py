# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty
from mathutils import Matrix, Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Matrix_generate, updateNode) #, fullList_deep_copy)
from sverchok.utils.sv_mesh_utils import mesh_join_ext


class Svb28MatrixArrayNode(bpy.types.Node, SverchCustomTreeNode):

    """
    Triggers: 
    Tooltip: 
    
    A short description for reader of node code
    """

    bl_idname = 'Svb28MatrixArrayNode'
    bl_label = 'Matrix Array'
    bl_icon = 'MOD_ARRAY'

    join_post: BoolProperty(name='Join', default=False, update=updateNode)

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', "Verts")
        inew('SvStringsSocket', "Edges")
        inew('SvStringsSocket', "Faces")
        inew('SvMatrixSocket', "Matrices")

        onew = self.outputs.new
        onew('SvVerticesSocket', "Verts")
        onew('SvStringsSocket', "Edges")
        onew('SvStringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        r = layout.row(align=True)
        r.prop(self, "join_post", text='Post Merge')

    def process(self):

        verts = self.inputs['Verts'].sv_get()[0]
        edges = self.inputs['Edges'].sv_get(default=[[]])[0]
        faces = self.inputs['Faces'].sv_get(default=[[]])[0]
        matrices = self.inputs['Matrices'].sv_get(default=[Matrix().Identity(4)])

        final_verts, final_edges, final_faces = [], [], []
        for matrix in matrices:
            final_verts.append([(matrix @ Vector(v))[:] for v in verts])
            final_edges.append(edges)
            final_faces.append(faces)

        if self.join_post:
            final_verts, final_edges, final_faces = mesh_join_ext(final_verts, final_edges, final_faces, wrap=True)


        self.outputs['Verts'].sv_set(final_verts)
        self.outputs['Edges'].sv_set(final_edges)
        self.outputs['Faces'].sv_set(final_faces)


def register():
    bpy.utils.register_class(Svb28MatrixArrayNode)


def unregister():
    bpy.utils.unregister_class(Svb28MatrixArrayNode)
