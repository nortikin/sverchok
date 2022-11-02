# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import map_recursive
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part


class SvIsSolidClosedNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Closed Solid
    Tooltip: Check if the Solid object is closed
    """
    bl_idname = 'SvIsSolidClosedNode'
    bl_label = 'Is Solid Closed'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvStringsSocket', "IsClosed")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get()

        def check(solid):
            return solid.isClosed()

        closed_out = map_recursive(check, solids_in, data_types=(Part.Shape,))

        self.outputs['IsClosed'].sv_set(closed_out)


def register():
    bpy.utils.register_class(SvIsSolidClosedNode)


def unregister():
    bpy.utils.unregister_class(SvIsSolidClosedNode)
