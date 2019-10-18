# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode


class SvMergeMesh2DLight(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Planar edgenet to polygons
    Tooltip: Something like fill holes node

    Only X and Y dimensions of input points will be taken for work.
    """
    bl_idname = 'SvMergeMesh2DLight'
    bl_label = 'Some node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vers')
        self.inputs.new('SvStringsSocket', "Edgs")
        self.outputs.new('SvVerticesSocket', 'Vers')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        pass


def register():
    bpy.utils.register_class(SvMergeMesh2DLight)


def unregister():
    bpy.utils.unregister_class(SvMergeMesh2DLight)
