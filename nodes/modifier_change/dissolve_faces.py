# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import zip_longest

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.dcel import DCELMesh


class SvDissolveFaces(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Split face into monotone pieces
    Can spilt face with holes
    One object - one polygon
    """
    bl_idname = 'SvDissolveFaces'
    bl_label = 'Dissolve Faces'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Face mask')
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        out = []
        for vs, fs, mf in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get(), 
                              self.inputs['Face mask'].sv_get()):
            mesh = DCELMesh()
            mesh.from_sv_faces(vs, fs, face_mask=mf)
            mesh.dissolve_selected_faces()
            out.append(mesh.to_sv_mesh())
        out_v, out_f = zip(*out)
        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Faces'].sv_set(out_f)


def register():
    bpy.utils.register_class(SvDissolveFaces)


def unregister():
    bpy.utils.unregister_class(SvDissolveFaces)
