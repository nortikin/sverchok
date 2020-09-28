# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSolidPolygonFaceNode', 'Polygon Face (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidPolygonFaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Face Polygon
    Tooltip: Make a Face of a Solid from each polygon of the mesh
    """
    bl_idname = 'SvSolidPolygonFaceNode'
    bl_label = "Polygon Face (Solid)"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_POLYGON_FACE'
    solid_catergory = "Inputs"

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvSurfaceSocket', "SolidFaces")

    def make_faces(self, verts, face_idxs):
        result = []
        for face_i in face_idxs:
            face_i.append(face_i[0])
            verts = [verts[idx] for idx in face_i]
            verts = [Base.Vector(*vert) for vert in verts]
            wire = Part.makePolygon(verts)
            face = Part.Face(wire)
            surface = SvSolidFaceSurface(face)#.to_nurbs()
            result.append(surface)
        return result

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        verts_s = ensure_nesting_level(verts_s, 3)
        faces_s = self.inputs['Faces'].sv_get()
        faces_s = ensure_nesting_level(faces_s, 3)

        solids_out = []
        for verts, faces in zip_long_repeat(verts_s, faces_s):
            surfaces = self.make_faces(verts, faces)
            solids_out.append(surfaces)

        self.outputs['SolidFaces'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidPolygonFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidPolygonFaceNode)

