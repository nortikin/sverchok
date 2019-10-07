# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvMeshBeautify(bpy.types.Node, SverchCustomTreeNode):

    """
    Triggers: beauty existing fill
    Tooltip: rearrange faces with bmesh operator
    
    useful for typography converted to geometry.
    """

    bl_idname = 'SvMeshBeautify'
    bl_label = 'Mesh Beautify'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Verts')
        self.inputs.new('StringsSocket', 'Faces')
        self.outputs.new('VerticesSocket', 'Verts')
        self.outputs.new('StringsSocket', 'Faces')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return

        in_verts = self.inputs['Verts'].sv_get()
        in_faces = self.inputs['Faces'].sv_get()

        out_verts, out_faces = [], []

        if in_verts and in_faces:
            fill = bmesh.ops.beautify_fill
            for verts, faces in zip(in_verts, in_faces):
                bm = bmesh_from_pydata(verts, [], faces)
                bm.verts.ensure_lookup_table()
                fill(bm, faces=bm.faces[:], edges=bm.edges[:], use_restrict_tag=False, method=0)
                nv, ne, nf = pydata_from_bmesh(bm)
                out_verts.append(nv)
                out_faces.append(nf)

        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)


def register():
    bpy.utils.register_class(SvMeshBeautify)


def unregister():
    bpy.utils.unregister_class(SvMeshBeautify)
