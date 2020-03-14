# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle, chain

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.mesh_structure.mesh import Mesh


class SvMeshIn(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvMeshIn'
    bl_label = 'Sv Mesh In'
    bl_icon = 'MOD_BOOLEAN'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Mesh')

    def process(self):
        if not self.inputs['Verts'].is_linked:
            return

        out = []
        for verts, edges, faces in zip(self.inputs['Verts'].sv_get(deepcopy=False),
                                    chain(self.inputs['Edges'].sv_get(default=[None], deepcopy=False), cycle([None])),
                                    chain(self.inputs['Faces'].sv_get(default=[None], deepcopy=False), cycle([None]))):
            me = Mesh()
            me.set(verts, edges, faces)
            out.append(me)
        self.outputs['Mesh'].sv_set(out)


def register():
    bpy.utils.register_class(SvMeshIn)


def unregister():
    bpy.utils.unregister_class(SvMeshIn)
