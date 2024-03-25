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


class SvSolidCenterOfMassNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Center of Mass (Solid)
    Tooltip: Calculate center of mass (barycenter) of a Solid object
    """
    bl_idname = 'SvSolidCenterOfMassNode'
    bl_label = 'Center of Mass (Solid)'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvVerticesSocket', "Center")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get()

        def calc(solid):
            if not isinstance(solid, Part.Solid):
                solid = Part.makeSolid(solid)
            c = solid.CenterOfMass
            return tuple(c)

        centers_out = map_recursive(calc, solids_in, data_types=(Part.Shape,))

        self.outputs['Center'].sv_set(centers_out)


def register():
    bpy.utils.register_class(SvSolidCenterOfMassNode)


def unregister():
    bpy.utils.unregister_class(SvSolidCenterOfMassNode)
