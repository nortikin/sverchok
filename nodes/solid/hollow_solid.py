# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode, repeat_last_for_length
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvSolidFaceSurface, surface_to_freecad, is_solid_face_surface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvHollowSolidNode', 'Hollow Solid', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvHollowSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Hollow Solid
    Tooltip: Make a hollow solid shell out a solid body
    """
    bl_idname = 'SvHollowSolidNode'
    bl_label = 'Hollow Solid'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_SPLIT_SOLID'
    solid_catergory = "Operators"

    thickness : FloatProperty(
            name = "Thickness",
            description = "Thickness value",
            default = 0.1,
            update=updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            default = 0.01,
            precision=6,
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'tolerance')

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvStringsSocket', "Thickness").prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', "EdgeMask")
        self.outputs.new('SvSolidSocket', "Solid")

    def make_solid(solid, thickness, mask):
        mask = repeat_last_for_length(mask, len(solid.Faces))
        faces = [face for c, face in zip(mask, solid.Faces) if c]
        shape = solid.makeThickness(faces, thickness, self.tolerance)
        return shape

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_s = self.inputs['Solid'].sv_get()
        solids_s = ensure_nesting_level(solids_s, 2, data_types=(Part.Shape,))
        thickness_s = self.inputs['Thickness'].sv_get()
        thickness_s = ensure_nesting_level(thickness_s, 2)
        mask_s = self.inputs['EdgeMask'].sv_get()
        mask_s = ensure_nesting_level(mask_s, 3)

        solids_out = []
        for params in zip_long_repeat(solids_s, thickness_s, mask_s):
            new_solids = []
            for solid, thickness, mask in zip_long_repeat(*params):
                new_solid = self.make_solid(solid, thickness, mask)
                new_solids.append(new_solid)
            solids_out.append(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvHollowSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvHollowSolidNode)

