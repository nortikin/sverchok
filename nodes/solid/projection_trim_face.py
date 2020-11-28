# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, throttle_and_update_node
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve, SvFreeCadCurve, SvSolidEdgeCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvFreeCadNurbsSurface, surface_to_freecad, is_solid_face_surface
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

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['Point'].hide_safe = self.projection_type != 'PERSPECTIVE'
        self.inputs['Vector'].hide_safe = self.projection_type != 'PARALLEL'

    projection_types = [
            ('PARALLEL', "Parallel", "Use parallel projection along given vector", 0),
            ('PERSPECTIVE', "Perspective", "Use perspective projection from given pont", 1),
            ('ORTHO', "Orthogonal", "Use orthogonal projection", 2),
            ('UV', "UV Trim", "Trim surface by curve(s) in surface's UV space", 3)
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
        self.outputs.new('SvCurveSocket', "Edges")
        self.outputs.new('SvCurveSocket', "UVCurves")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text='Projection:')
        layout.prop(self, 'projection_type', text='')

    def cut(self, face_surface, sv_curves, point, vector):
        # face_surface : SvFreeCadNurbsSurface
        nurbs = [SvNurbsCurve.to_nurbs(curve) for curve in sv_curves]
        if any(c is None for c in nurbs):
            raise Exception("One of curves is not a NURBS!")
        fc_nurbs_curves = [SvFreeCadNurbsCurve.from_any_nurbs(c) for c in nurbs]
        fc_nurbs = [c.curve for c in fc_nurbs_curves]
        if self.projection_type in {'PARALLEL', 'PERSPECTIVE', 'ORTHO'}:
            try:
                fc_edges = [Part.Edge(c) for c in fc_nurbs]
            except Exception as e:
                raise Exception(f"Can't build edges from {fc_nurbs}: {e}")
        fc_face = Part.Face(face_surface.surface)

        if self.projection_type == 'PARALLEL':
            vector = Base.Vector(*vector)
            projections = [fc_face.makeParallelProjection(edge, vector) for edge in fc_edges]
            projections = [p.Edges for p in projections]
        elif self.projection_type == 'PERSPECTIVE':
            point = Base.Vector(*point)
            projections = [fc_face.makePerspectiveProjection(edge, point).Edges for edge in fc_edges]
        elif self.projection_type == 'ORTHO':
            projections = [fc_face.project(fc_edges).Edges]
        else: # UV
            uv_curves = [c.to_2d() for c in fc_nurbs_curves]
            fc_nurbs_2d = [c.curve for c in uv_curves]
            projections = [[c.toShape(face_surface.surface) for c in fc_nurbs_2d]]

        projections = sum(projections, [])
        if not projections:
            words = f"along {vector}" if self.projection_type == 'PARALLEL' else f"from {point}"
            raise Exception(f"Projection {words} of {sv_curves} onto {face_surface} is empty for some reason")
        try:
            wire = Part.Wire(projections)
        except Exception as e:
            ps = [SvFreeCadNurbsCurve(p.Curve) for p in projections]
            raise Exception(f"Can't make a valid Wire out of curves {sv_curves} projected onto {face_surface}:\n{e}\nProjections are: {ps}")

        cut_fc_face = Part.Face(face_surface.surface, wire)
        cut_face_surface = SvFreeCadNurbsSurface(face_surface.surface, face=cut_fc_face) 

        if self.projection_type != 'UV':
            uv_curves = []
            for edge in cut_fc_face.OuterWire.Edges:
                trim,m,M = cut_fc_face.curveOnSurface(edge)
                trim = SvFreeCadCurve(trim, (m,M), ndim=2)
                uv_curves.append(trim)

        projections = [SvSolidEdgeCurve(p) for p in projections]
        return uv_curves, projections, cut_face_surface

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
        trim_out = []
        edges_out = []
        for surfaces, curves_i, points, vectors in zip_long_repeat(surface_s, curve_s, point_s, vector_s):
            new_faces = []
            new_trim = []
            new_edges = []
            for surface, curves, point, vector in zip_long_repeat(surfaces, curves_i, points, vectors):
                if is_solid_face_surface(surface):
                    face_surface = surface
                else:
                    face_surface = surface_to_freecad(surface) # SvFreeCadNurbsSurface
                if curves:
                    trims, edges, face = self.cut(face_surface, curves, point, vector)
                else:
                    face = face_surface
                    trims = []
                    edges = []
                new_faces.append(face)
                new_trim.append(trims)
                new_edges.append(edges)

            faces_out.append(new_faces)
            trim_out.append(new_trim)
            edges_out.append(new_edges)

        self.outputs['SolidFace'].sv_set(faces_out)
        if 'UVCurves' in self.outputs:
            self.outputs['UVCurves'].sv_set(trim_out)
        if 'Edges' in self.outputs:
            self.outputs['Edges'].sv_set(edges_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvProjectTrimFaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvProjectTrimFaceNode)


