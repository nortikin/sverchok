# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvMirrorLiteBMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: mirror lite
    Tooltip:  a basic mirror using bmesh.ops.mirror
    
    """

    bl_idname = 'SvMirrorLiteBMeshNode'
    bl_label = 'Mirror Lite (bm.ops)'
    bl_icon = 'GREASEPENCIL'

    def sv_init(self, context):
        ...

    def draw_buttons(self, context, layout):
        ...

    def process(self):
        ...


classes = [SvMirrorLiteBMeshNode]
register, unregister = bpy.utils.register_classes_factory(classes)
