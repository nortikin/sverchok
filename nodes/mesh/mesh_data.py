# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import chain

import numpy as np

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from .line import Mesh


class SvMeshDataNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: mesh line
    Tooltip: Generate simple line
    """
    bl_idname = 'SvMeshDataNode'
    bl_label = 'Mesh Data'

    def sv_init(self, context):
        self.inputs.new('SvMeshSocket', "Mesh")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        # No vectorization here
        me: Mesh = self.inputs["Mesh"].sv_get(deepcopy=False, default=None)

        if me is not None:
            self.outputs["Vertices"].sv_set([me.verts])


def register():
    bpy.utils.register_class(SvMeshDataNode)


def unregister():
    bpy.utils.unregister_class(SvMeshDataNode)
