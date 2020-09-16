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
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSolidFaceSolidifyNode', 'Solidify Face (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidFaceSolidifyNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Soldify Solid Face Offset Thickness
    Tooltip: Make a Solid by offsetting (adding thickness, solidifying) a Face of a Solid
    """
    bl_idname = 'SvSolidFaceSolidifyNode'
    bl_label = 'Solidify Face (Solid)'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_SOLIDIFY_FACE'
    solid_catergory = "Operators"

    refine_solid: BoolProperty(
            name="Refine Solid",
            description="Removes redundant edges (may slow the process)",
            default=False,
            update=updateNode)

    offset : FloatProperty(
            name = "Offset",
            description = "Thickness value",
            default = 0.1,
            update=updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            description = "precision of approximation",
            default = 0.01,
            precision=6,
            update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "SolidFace")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'
        self.outputs.new('SvSolidSocket', "Solid")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face_surfaces_s = self.inputs['SolidFace'].sv_get()
        face_surfaces_s = ensure_nesting_level(face_surfaces_s, 2, data_types=(SvSurface,))
        offset_s = self.inputs['Offset'].sv_get()
        offset_s = ensure_nesting_level(offset_s, 2)
        tolerance_s = self.inputs['Tolerance'].sv_get()
        tolerance_s = ensure_nesting_level(tolerance_s, 2)

        solids_out = []
        for face_surfaces, offsets, tolerances in zip_long_repeat(face_surfaces_s, offset_s, tolerance_s):
            #new_solids = []
            for face_surface, offset, tolerance in zip_long_repeat(face_surfaces, offsets, tolerances):
                if not is_solid_face_surface(face_surface):
                    # face_surface is an instance of SvSurface,
                    # but not a instance of SvFreeCadNurbsSurface
                    self.debug("Surface %s is not a face of a solid, will convert automatically", face_surface)
                    face_surface = surface_to_freecad(face_surface, make_face=True) # SvFreeCadNurbsSurface

                continuity = face_surface.get_min_continuity()
                if continuity >= 0 and continuity < 1:
                    raise Exception("This node requires at least C1 continuity of the surface; only C0 is guaranteed by surface's knotvector")
                fc_face = face_surface.face
                shape = fc_face.makeOffsetShape(offset, tolerance, fill=True)
                solids_out.append(shape)
            #solids_out.append(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFaceSolidifyNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFaceSolidifyNode)

