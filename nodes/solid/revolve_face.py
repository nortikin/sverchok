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
    add_dummy('SvSolidFaceRevolveNode', 'Revolve Face (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidFaceRevolveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Face Revolution
    Tooltip: Make a Solid of revolution from a Face
    """
    bl_idname = 'SvSolidFaceRevolveNode'
    bl_label = 'Revolve Face (Solid)'
    bl_icon = 'EDGESEL'
    solid_catergory = "Operators"

    refine_solid: BoolProperty(
            name="Refine Solid",
            description="Removes redundant edges (may slow the process)",
            default=False,
            update=updateNode)

    angle : FloatProperty(
            name = "Angle",
            description = "Revolution angle",
            default = 360,
            update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "SolidFace")
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.prop = (0.0, 0.0, 1.0)
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.outputs.new('SvSolidSocket', "Solid")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face_surfaces_s = self.inputs['SolidFace'].sv_get()
        face_surfaces_s = ensure_nesting_level(face_surfaces_s, 2, data_types=(SvSurface,))
        angle_s = self.inputs['Angle'].sv_get()
        angle_s = ensure_nesting_level(angle_s, 2)
        point_s = self.inputs['Point'].sv_get()
        point_s = ensure_nesting_level(point_s, 3)
        direction_s = self.inputs['Direction'].sv_get()
        direction_s = ensure_nesting_level(direction_s, 3)

        solids_out = []
        for face_surfaces, angles, points, directions in zip_long_repeat(face_surfaces_s, angle_s, point_s, direction_s):
            #new_solids = []
            for face_surface, angle, point, direction in zip_long_repeat(face_surfaces, angles, points, directions):
                if not is_solid_face_surface(face_surface):
                    # face_surface is an instance of SvSurface,
                    # but not a instance of SvFreeCadNurbsSurface
                    self.debug("Surface %s is not a face of a solid, will convert automatically", face_surface)
                    face_surface = surface_to_freecad(face_surface, make_face=True) # SvFreeCadNurbsSurface

                fc_face = face_surface.face
                fc_point = Base.Vector(*point)
                fc_direction = Base.Vector(*direction)
                shape = fc_face.revolve(fc_point, fc_direction, angle)
                solids_out.append(shape)
            #solids_out.append(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFaceRevolveNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFaceRevolveNode)

