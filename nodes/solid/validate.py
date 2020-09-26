# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, map_unzip_recursirve
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidValidateNode', 'Validate & Fix Solid', 'FreeCAD')
else:
    import Part

class SvSolidValidateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Validate Fix Solid
    Tooltip: Validate or fix Solid objects
    """
    bl_idname = 'SvSolidValidateNode'
    bl_label = 'Validate & Fix Solid'
    bl_icon = 'OUTLINER_OB_EMPTY'
    solid_catergory = "Operators"

    precision : FloatProperty(
        name = "Precision",
        default = 0.001,
        precision = 6,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'precision')

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvSolidSocket', "FixedSolid")
        self.outputs.new('SvStringsSocket', "IsValid")

    def _process(self, solid):
        try:
            valid = solid.isValid()
        except:
            valid = False
        if valid:
            fixed = solid
        elif self.outputs['FixedSolid'].is_linked:
            fixed = solid.copy()
            ok = fixed.fix(self.precision, self.precision, self.precision)
            if not ok:
                raise Exception("The provided Solid is not valid and can not be fixed automatically")
        else:
            fixed = None
        return fixed, valid

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get()

        solids_out, valid_out = map_unzip_recursirve(self._process, solids_in, data_types=(Part.Shape,))

        self.outputs['FixedSolid'].sv_set(solids_out)
        self.outputs['IsValid'].sv_set(valid_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidValidateNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidValidateNode)

