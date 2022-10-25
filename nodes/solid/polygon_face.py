# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part
    from FreeCAD import Base


class SvSolidPolygonFaceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Solid Face Polygon
    Tooltip: Make a Face of a Solid from each polygon of the mesh
    """
    bl_idname = 'SvSolidPolygonFaceNode'
    bl_label = "Polygon Face (Solid)"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_POLYGON_FACE'
    sv_category = "Solid Inputs"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvSurfaceSocket', "SolidFaces")

    accuracy : IntProperty(
            name = "Accuracy",
            description = "Tolerance parameter for checking if ends of edges coincide",
            default = 8,
            min = 1,
            update = updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'accuracy')

    def make_faces(self, verts, face_idxs):
        tolerance = 10 ** (-self.accuracy)

        result = []
        fc_vector = Base.Vector
        for face_i in face_idxs:
            face_i = list(face_i)
            face_i.append(face_i[0])
            fc_verts = [verts[idx] for idx in face_i]
            fc_verts = [fc_vector(*vert) for vert in fc_verts]
            wire = Part.makePolygon(fc_verts)
            wire.fixTolerance(tolerance)
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
    bpy.utils.register_class(SvSolidPolygonFaceNode)


def unregister():
    bpy.utils.unregister_class(SvSolidPolygonFaceNode)
