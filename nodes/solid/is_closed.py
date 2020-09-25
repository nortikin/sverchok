# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, map_recursive
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvIsSolidClosedNode', 'Validate Solid', 'FreeCAD')
else:
    import Part

class SvIsSolidClosedNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Closed Solid
    Tooltip: Check if the Solid object is closed
    """
    bl_idname = 'SvIsSolidClosedNode'
    bl_label = 'Is Solid Closed'
    bl_icon = 'OUTLINER_OB_EMPTY'
    solid_catergory = "Operators"

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
    if FreeCAD is not None:
        bpy.utils.register_class(SvIsSolidClosedNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvIsSolidClosedNode)

