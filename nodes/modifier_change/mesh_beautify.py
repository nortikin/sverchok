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
from sverchok.data_structure import enum_item_4, updateNode

class SvMeshBeautify(bpy.types.Node, SverchCustomTreeNode):

    """
    Triggers: beauty existing fill
    Tooltip: rearrange faces with bmesh operator

    useful for typography converted to geometry.
    """

    bl_idname = 'SvMeshBeautify'
    bl_label = 'Mesh Beautify'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MESH_BEAUTIFY'

    beautify_mode: bpy.props.EnumProperty(
        name='Beautify', items=enum_item_4(['AREA', 'ANGLE']), default="AREA", update=updateNode
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'beautify_mode', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Faces')

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
                fill(bm, faces=bm.faces[:], edges=bm.edges[:], use_restrict_tag=False, method=self.beautify_mode)
                nv, ne, nf = pydata_from_bmesh(bm)
                out_verts.append(nv)
                out_faces.append(nf)

        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)


def register():
    bpy.utils.register_class(SvMeshBeautify)


def unregister():
    bpy.utils.unregister_class(SvMeshBeautify)
