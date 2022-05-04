# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import chain
from copy import copy

import numpy as np

import bpy
from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import numpy_full_list
from .line import Mesh


class SvSetPositionMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: mesh line
    Tooltip: Generate simple line
    """
    bl_idname = 'SvSetPositionMeshNode'
    bl_label = 'Set Position'

    def sv_init(self, context):
        self.inputs.new('SvMeshSocket', "Mesh")
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvMeshSocket', "Mesh")

    def process(self):
        me: Mesh = self.inputs["Mesh"].sv_get(deepcopy=False, default=None)
        v = np.asarray(self.inputs["Vertices"].sv_get(deepcopy=False, default=[[]])[0], dtype=np.float32)

        if me is None:
            return

        me = copy(me)
        if len(v) > 0:
            me.verts = numpy_full_list(v, len(me.verts))

        self.outputs["Mesh"].sv_set(me)


def register():
    bpy.utils.register_class(SvSetPositionMeshNode)


def unregister():
    bpy.utils.unregister_class(SvSetPositionMeshNode)
