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


class SvSolidAreaNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Area Solid
    Tooltip: Calculate total area of all faces of a Solid object
    """
    bl_idname = 'SvSolidAreaNode'
    bl_label = 'Solid Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvStringsSocket', "Area")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get()

        def calc(solid):
            if not isinstance(solid, Part.Solid):
                solid = Part.makeSolid(solid)
            c = solid.Area
            return [c]

        area_out = map_recursive(calc, solids_in, data_types=(Part.Shape,))

        self.outputs['Area'].sv_set(area_out)


def register():
    bpy.utils.register_class(SvSolidAreaNode)


def unregister():
    bpy.utils.unregister_class(SvSolidAreaNode)
