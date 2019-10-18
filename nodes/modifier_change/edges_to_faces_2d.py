# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.geom_2d.dcel import DCELMesh


class SvEdgesToFaces2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Planar edgenet to polygons
    Tooltip: Something like fill holes node

    Only X and Y dimensions of input points will be taken for work.
    """
    bl_idname = 'SvEdgesToFaces2D'
    bl_label = 'Edges to faces 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not any([soc.is_linked for soc in self.inputs]):
            return
        out = []
        for vs, es in zip(self.inputs['Verts'].sv_get(), self.inputs['Edges'].sv_get()):
            mesh = DCELMesh()
            mesh.from_sv_edges(vs, es)
            mesh.faces_from_hedges()
            out.append(mesh.to_sv_mesh())
        sv_verts, sv_faces = zip(*out)
        self.outputs['Verts'].sv_set(sv_verts)
        self.outputs['Faces'].sv_set(sv_faces)


def register():
    bpy.utils.register_class(SvEdgesToFaces2D)


def unregister():
    bpy.utils.unregister_class(SvEdgesToFaces2D)