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
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, get_data_nesting_level, updateNode
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvFreeCadNurbsSurface, surface_to_freecad
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvProjectTrimFaceNode', 'Face from Surface (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvProjectTrimFaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Face Trim Surface
    Tooltip: Make a Face of a Solid by trimming a Surface with projected Curve(s)
    """
    bl_idname = 'SvProjectTrimFaceNode'
    bl_label = "Face from Surface (Solid)"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_PROJECT_CUT_FACE'
    solid_catergory = "Inputs"

    @throttled
    def update_sockets(self, context):
        self.inputs['Point'].hide_safe = self.projection_type != 'PERSPECTIVE'
        self.inputs['Vector'].hide_safe = self.projection_type != 'PARALLEL'

    projection_types = [
            ('PARALLEL', "Parallel", "Use parallel projection along given vector", 0),
            ('PERSPECTIVE', "Perspective", "Use perspective projection from given pont", 1),
            ('ORTHO', "Orthogonal", "Use orthogonal projection", 2)
        ]
    
    projection_type : EnumProperty(
            name = "Projection",
            description = "Used projection type",
            items = projection_types,
            default = 'PARALLEL',
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        # Named it "Cut", to do not confuse with "Trim" curves, which are
        # usually in surface's UV space
        self.inputs.new('SvCurveSocket', "Cut") 
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.prop = (0.0, 0.0, -1.0)
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        self.outputs.new('SvSurfaceSocket', "SolidFace")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text='Projection:')
        layout.prop(self, 'projection_type', text='')

    def cut(self, face_surface, sv_curves, point, vector):
        # face_surface : SvFreeCadNurbsSurface
        nurbs = [SvNurbsCurve.to_nurbs(curve) for curve in sv_curves]
        if any(c is None for c in nurbs):
            raise Exception("One of curves is not a NURBS!")
        fc_nurbs = [SvFreeCadNurbsCurve.from_any_nurbs(c).curve for c in nurbs]
        fc_edges = [Part.Edge(c) for c in fc_nurbs]
        fc_face = Part.Face(face_surface.surface)

        if self.projection_type == 'PARALLEL':
            vector = Base.Vector(*vector)
            projections = [fc_face.makeParallelProjection(edge, vector) for edge in fc_edges]
            projections = [p.Edges for p in projections]
        elif self.projection_type == 'PERSPECTIVE':
            point = Base.Vector(*point)
            projections = [fc_face.makePerspectiveProjection(edge, point).Edges for edge in fc_edges]
        else: # ORTHO
            projections = [fc_face.project(fc_edges).Edges]

        projections = sum(projections, [])
        if not projections:
            words = f"along {vector}" if self.projection_type == 'PARALLEL' else f"from {point}"
            raise Exception(f"Projection {words} of {sv_curves} onto {face_surface} is empty for some reason")
        try:
            wire = Part.Wire(projections)
        except Part.OCCError as e:
            ps = [SvFreeCadNurbsCurve(p.Curve) for p in projections]
            raise Exception(f"Can't make a valid Wire out of curves {sv_curves} projected onto {face_surface}:\n{e}\nProjections are: {ps}")

        cut_fc_face = Part.Face(face_surface.surface, wire)
        cut_face_surface = SvFreeCadNurbsSurface(face_surface.surface, face=cut_fc_face) 

        return cut_face_surface

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        if self.inputs['Cut'].is_linked:
            curve_s = self.inputs['Cut'].sv_get()
            # List of curves per surface
            curve_s = ensure_nesting_level(curve_s, 3, data_types=(SvCurve,))
        else:
            curve_s = [[[]]]
        point_s = self.inputs['Point'].sv_get()
        point_s = ensure_nesting_level(point_s, 3)
        vector_s = self.inputs['Vector'].sv_get()
        vector_s = ensure_nesting_level(vector_s, 3)

        faces_out = []
        for surfaces, curves_i, points, vectors in zip_long_repeat(surface_s, curve_s, point_s, vector_s):
            new_faces = []
            new_trim = []
            new_edges = []
            for surface, curves, point, vector in zip_long_repeat(surfaces, curves_i, points, vectors):
                face_surface = surface_to_freecad(surface) # SvFreeCadNurbsSurface
                if curves:
                    face = self.cut(face_surface, curves, point, vector)
                else:
                    face = face_surface
                new_faces.append(face)
            faces_out.append(new_faces)

        self.outputs['SolidFace'].sv_set(faces_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvProjectTrimFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvProjectTrimFaceNode)


