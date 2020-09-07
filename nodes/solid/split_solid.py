# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvSolidFaceSurface, surface_to_freecad, is_solid_face_surface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSplitSolidNode', 'Split Solid by Face', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

def make_solids(solid, face_surfaces):
    faces = [face_surface.face for face_surface in face_surfaces]
    result, map = solid.generalFuse(faces)
    solids = map[0]
    if not solids:
        solids = result.Solids
    cut_faces = []
    for per_input_face in map[1:]:
        item = []
        for shape in per_input_face:
            if isinstance(shape, Part.Face):
                cut_face = SvSolidFaceSurface(shape).to_nurbs()
                item.append(cut_face)
        cut_faces.append(item)
    return solids, cut_faces

class SvSplitSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Split Solid Face
    Tooltip: Split one Solid into several Solids by cutting it with a Face
    """
    bl_idname = 'SvSplitSolidNode'
    bl_label = 'Split Solid by Face'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_SPLIT_SOLID'
    solid_catergory = "Operators"

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvSurfaceSocket', "SolidFace")
        self.outputs.new('SvSolidSocket', "Solids")
        self.outputs.new('SvSurfaceSocket', "CutFaces")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face_surfaces_s = self.inputs['SolidFace'].sv_get()
        face_surfaces_s = ensure_nesting_level(face_surfaces_s, 3, data_types=(SvSurface,))
        solids_s = self.inputs['Solid'].sv_get()
        solids_s = ensure_nesting_level(solids_s, 2, data_types=(Part.Shape,))

        solids_out = []
        cut_faces_out = []
        for solids, face_surfaces_i in zip_long_repeat(solids_s, face_surfaces_s):
            for solid, face_surfaces in zip_long_repeat(solids, face_surfaces_i):
                for i in range(len(face_surfaces)):
                    if not is_solid_face_surface(face_surfaces[i]):
                        face_surfaces[i] = surface_to_freecad(face_surfaces[i], make_face=True) # SvFreeCadNurbsSurface

                new_solids, cut_faces = make_solids(solid, face_surfaces)
                solids_out.append(new_solids)
                cut_faces_out.append(cut_faces)

        self.outputs['Solids'].sv_set(solids_out)
        if 'CutFaces' in self.outputs:
            self.outputs['CutFaces'].sv_set(cut_faces_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSplitSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSplitSolidNode)

