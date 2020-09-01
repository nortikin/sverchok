# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, get_data_nesting_level, updateNode
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSolidSurfaceFaceNode', 'Face from Surface (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidSurfaceFaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Face Surface
    Tooltip: Make a Face of a Solid from a Surface object
    """
    bl_idname = 'SvSolidSurfaceFaceNode'
    bl_label = "Face from Surface (Solid)"
    bl_icon = 'EDGESEL'
    solid_catergory = "Inputs"

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvSurfaceSocket', "SolidFace")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))

        faces_out = []
        for surfaces in surface_s:
            new_faces = []
            for surface in surfaces:
                fc_surface = surface_to_freecad(surface)
                face = Part.Face(fc_surface.surface)
                fc_surface.face = face
                new_faces.append(fc_surface)
            faces_out.append(new_faces)

        self.outputs['SolidFace'].sv_set(faces_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidSurfaceFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidSurfaceFaceNode)

