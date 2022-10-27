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


class SvRefineSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Refine Solid
    Tooltip: Refine Solid by removing unnecessary edges
    """
    bl_idname = 'SvRefineSolidNode'
    bl_label = 'Refine Solid'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvSolidSocket', "Solid")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get()

        def refine(solid):
            return solid.removeSplitter()

        solids_out = map_recursive(refine, solids_in, data_types=(Part.Shape,))

        self.outputs['Solid'].sv_set(solids_out)


def register():
    bpy.utils.register_class(SvRefineSolidNode)


def unregister():
    bpy.utils.unregister_class(SvRefineSolidNode)
