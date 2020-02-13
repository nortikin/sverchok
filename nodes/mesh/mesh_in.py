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


def fix_input_data(attrs_dict: dict) -> None:
    # should be in data structure
    for key, val in attrs_dict.items():
        if key == 'name':
            if not isinstance(val, str):
                if not isinstance(val, list) or not isinstance(val[0], str):
                    raise ValueError(f"Name attribute expect string value or list of strings, {val} got instead")
            if isinstance(val, list):
                attrs_dict[key] = val[0]


class SvMeshIn(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvMeshIn'
    bl_label = 'Sv Mesh In'
    bl_icon = 'MOD_BOOLEAN'

    def sv_init(self, context):
        self.inputs.new('SvDictionarySocket', 'Verts')
        self.inputs.new('SvDictionarySocket', 'Edges')
        self.inputs.new('SvDictionarySocket', 'Faces')
        self.inputs.new('SvDictionarySocket', 'Loops')
        self.inputs.new('SvDictionarySocket', 'Object')
        self.outputs.new('SvStringsSocket', 'Mesh')

    def process(self):
        if not any([s.is_linked for s in self.inputs]):
            return

        max_len = max([len(s.sv_get(default=[])) for s in self.inputs])
        data = [chain(s.sv_get(default=([None]), deepcopy=False), cycle([None])) for s in self.inputs]
        out = []
        for i, layer in zip(range(max_len), zip(*data)):
            me = Mesh()
            for element, attrs in zip([me.verts, me.edges, me.faces, me.loops, me], layer):
                if attrs:
                    fix_input_data(attrs)
                    [setattr(element, key, values) for key, values in attrs.items()]
            out.append(me)
        self.outputs['Mesh'].sv_set(out)


def register():
    bpy.utils.register_class(SvMeshIn)


def unregister():
    bpy.utils.unregister_class(SvMeshIn)
