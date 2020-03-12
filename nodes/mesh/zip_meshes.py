# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle, chain

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import repeat_last, updateNode
from sverchok.core.mesh_structure import Mesh, MeshGroup, FacesGroup, EdgesGroup, VertsGroup, LoopsGroup
from sverchok.utils.mesh_structure.check_input import set_safe_attr


class SvZipMeshes(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvZipMeshes'
    bl_label = 'Zip Meshes'
    bl_icon = 'MOD_BOOLEAN'

    mesh_name: bpy.props.StringProperty(default="SvMesh", update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mesh_name', text='')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Mesh1')
        self.inputs.new('SvStringsSocket', 'Mesh2')
        self.outputs.new('SvStringsSocket', 'Mesh')

    def process(self):
        pass


def register():
    bpy.utils.register_class(SvZipMeshes)


def unregister():
    bpy.utils.unregister_class(SvZipMeshes)