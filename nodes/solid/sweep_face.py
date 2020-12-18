# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.freecad import curve_to_freecad_nurbs
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSweepSolidFaceNode', 'Sweep Face (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base
    from Part import BRepOffsetAPI 

class SvSweepSolidFaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Face Revolution
    Tooltip: Make a Solid by sweeping a Face along Curve
    """
    bl_idname = 'SvSweepSolidFaceNode'
    bl_label = 'Sweep Face (Solid)'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_SWEEP_FACE'
    solid_catergory = "Operators"

    use_frenet : BoolProperty(
            name = "Frenet",
            description = "Use Frenet frame of the curve to define the rotation of the face",
            default = True,
            update = updateNode)

    move_face : BoolProperty(
            name = "Align Face Location",
            description = "Align the face location to the beginning of the curve",
            default = True,
            update = updateNode)

    rotate_face : BoolProperty(
            name = "Align Face Rotation",
            description = "Align the face rotation so that it is perpendicular to the curve",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'use_frenet', toggle=True)
        layout.prop(self, 'move_face', toggle=True)
        layout.prop(self, 'rotate_face', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Profile")
        self.inputs.new('SvCurveSocket', "Path")
        self.outputs.new('SvSolidSocket', "Solid")

    def make_solid(self, face, path):
        path_edge = Part.Edge(path)
        path_wire = Part.Wire([path_edge])
        api = BRepOffsetAPI.MakePipeShell(path_wire)
        api.setFrenetMode(self.use_frenet)
        if not face.Surface.isPlanar():
            self.warning("The profile face is not planar; FreeCAD probably will not be able to generate a Solid object")
        section = face.OuterWire
        if not section.isClosed():
            raise Exception("Face's outer wire is not closed")
        api.add(section, self.move_face, self.rotate_face)
        if not api.isReady():
            raise Exception("Unexpected: API object is not ready")
        api.build()
        if not api.makeSolid():
            raise Exception("Can not build a Solid object")
        return api.shape()

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face_surface_s = self.inputs['Profile'].sv_get()
        face_surface_s = ensure_nesting_level(face_surface_s, 2, data_types=(SvSurface,))
        curve_s = self.inputs['Path'].sv_get()
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))

        solid_out = []
        for face_surfaces, curves in zip_long_repeat(face_surface_s, curve_s):
            for face_surface, curve in zip_long_repeat(face_surfaces, curves):
                if not is_solid_face_surface(face_surface):
                    face_surface = surface_to_freecad(face_surface, make_face=True)
                curve = curve_to_freecad_nurbs(curve)
                if curve is None:
                    raise Exception("Path curve is not a NURBS!")

                solid = self.make_solid(face_surface.face, curve.curve)
                solid_out.append(solid)

        self.outputs['Solid'].sv_set(solid_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSweepSolidFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSweepSolidFaceNode)

