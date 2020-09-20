# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode, get_data_nesting_level
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSolidFromFacesNode', 'Solid from Faces', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidFromFacesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid from Faces
    Tooltip: Make a Solid from it's faces (they must constitute a closed shell)
    """
    bl_idname = 'SvSolidFromFacesNode'
    bl_label = 'Solid from Faces'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_EXTRUDE_FACE'
    solid_catergory = "Input"

    tolerance : FloatProperty(
            name = "Tolerance",
            default = 0.001,
            precision = 6,
            update = updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'tolerance')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "SolidFaces")
        self.outputs.new('SvSolidSocket', "Solid")

    def make_solid(self, surfaces):
        faces = [face.face for face in surfaces]
        shell = Part.makeShell(faces)
        shape = Part.makeSolid(shell)
        ok = shape.isValid()
        if not ok:
            self.debug("Constructed solid is not valid, will try to fix it")
            ok = shape.fix(self.tolerance, self.tolerance, self.tolerance)
            if not ok:
                raise Exception("Constructed Solid object is not valid and can't be fixed automatically")
        if not shape.isClosed():
            raise Exception("Constructed Solid object is not closed")
        return shape

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face_surfaces_s = self.inputs['SolidFaces'].sv_get()
        input_level = get_data_nesting_level(face_surfaces_s, data_types=(SvSurface,))
        face_surfaces_s = ensure_nesting_level(face_surfaces_s, 3, data_types=(SvSurface,))

        solids_out = []
        for surfaces_i in face_surfaces_s:
            new_solids = []
            for surfaces in surfaces_i:
                for i in range(len(surfaces)):
                    if not is_solid_face_surface(surfaces[i]):
                        surfaces[i] = surface_to_freecad(surfaces[i], make_face=True)
                solid = self.make_solid(surfaces)
                new_solids.append(solid)
            if input_level > 2:
                solids_out.append(new_solids)
            else:
                solids_out.extend(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFromFacesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFromFacesNode)

