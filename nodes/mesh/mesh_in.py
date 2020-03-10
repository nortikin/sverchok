# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle, chain

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.mesh_structure import Mesh
from sverchok.utils.mesh_structure.check_input import set_safe_attr


class SvMeshIn(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvMeshIn'
    bl_label = 'Sv Mesh In'
    bl_icon = 'MOD_BOOLEAN'

    def sv_init(self, context):
        self.inputs.new('SvDictionarySocket', 'Object')
        self.inputs.new('SvDictionarySocket', 'Faces')
        self.inputs.new('SvDictionarySocket', 'Edges')
        self.inputs.new('SvDictionarySocket', 'Verts')
        self.inputs.new('SvDictionarySocket', 'Loops')
        self.outputs.new('SvStringsSocket', 'Mesh')

    def process(self):
        if not any([s.is_linked for s in self.inputs]):
            return

        max_len = max([len(s.sv_get(default=[], deepcopy=False)) for s in self.inputs])
        data = [chain(s.sv_get(default=([None]), deepcopy=False), cycle([None])) for s in self.inputs]
        out = []
        for i, layer in zip(range(max_len), zip(*data)):
            me = Mesh()
            for element, attrs in zip([me, me.faces, me.edges, me.verts, me.loops], layer):
                if attrs:
                    [set_safe_attr(element, key, values) for key, values in attrs.items()]
            out.append(me)
        self.outputs['Mesh'].sv_set(out)


def register():
    bpy.utils.register_class(SvMeshIn)


def unregister():
    bpy.utils.unregister_class(SvMeshIn)
