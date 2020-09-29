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
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface, SvSolidFaceSurface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvShrinkExpandSolidFaceNode', 'Shrink / Expand Solid Face', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvShrinkExpandSolidFaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Shrink / Expand Solid Face
    Tooltip: Shrink / Expand Solid Face
    """
    bl_idname = 'SvShrinkExpandSolidFaceNode'
    bl_label = 'Shrink / Expand Solid Face'
    bl_icon = 'EDGESEL'
    solid_catergory = "Operators"

    offset : FloatProperty(
                name = "Offset",
                description = "Edges offset. Use negative values to shrink the face, or positive values to expand it",
                default = 0.1,
                update = updateNode)

    join_types = [
            ('0', "Arcs", "Arcs", 0),
            #('1', "Tangent", "Tangent", 1), # Causes crashes for me
            ('2', "Intersection", "Intersection", 2)
        ]

    join_type : EnumProperty(
            name = "Join type",
            items = join_types,
            default = '0',
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join_type')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "SolidFace")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        self.outputs.new('SvSurfaceSocket', "SolidFace")

    def _process(self, face_surface, offset):
        fc_face = face_surface.face
        new_fc_face = fc_face.makeOffset2D(offset,
                        join = int(self.join_type)
                        #fill = False,
                        #openResult = False,
                        #intersection = True
                    )
        surface = SvSolidFaceSurface(new_fc_face)
        return surface

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face_surfaces_s = self.inputs['SolidFace'].sv_get()
        face_surfaces_s = ensure_nesting_level(face_surfaces_s, 2, data_types=(SvSurface,))
        offset_s = self.inputs['Offset'].sv_get()
        offset_s = ensure_nesting_level(offset_s, 2)

        surface_out = []
        for inputs in zip_long_repeat(face_surfaces_s, offset_s):
            new_surfaces = []
            for face_surface, offset in zip_long_repeat(*inputs):
                if not is_solid_face_surface(face_surface):
                    face_surface = surface_to_freecad(face_surface, make_face=True)
                surface = self._process(face_surface, offset)
                new_surfaces.append(surface)
            surface_out.append(new_surfaces)

        self.outputs['SolidFace'].sv_set(surface_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvShrinkExpandSolidFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvShrinkExpandSolidFaceNode)

