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
from sverchok.data_structure import (zip_long_repeat, ensure_nesting_level,
                                     get_data_nesting_level, throttle_and_update_node)
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve, SvSolidEdgeCurve, curve_to_freecad_nurbs
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvFreeCadNurbsSurface, surface_to_freecad, is_solid_face_surface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvProjectCurveSurfaceNode', 'Project Curve to Surface (NURBS)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvProjectCurveSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Project Curve Surface NURBS
    Tooltip: Project a NURBS Curve onto a Face or Surface
    """
    bl_idname = 'SvProjectCurveSurfaceNode'
    bl_label = "Project Curve to Surface (NURBS)"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_PROJECT_CURVE'

    @throttle_and_update_node
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
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvSurfaceSocket', "Surface")
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.prop = (0.0, 0.0, -1.0)
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        self.outputs.new('SvCurveSocket', "Curves")
        self.outputs.new('SvCurveSocket', "TrimCurves")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text='Projection:')
        layout.prop(self, 'projection_type', text='')

    def get_trim(self, fc_face, fc_edge):
        trim, m, M = fc_face.curveOnSurface(fc_edge)
        trim = trim.toBSpline(m, M)
        trim = SvFreeCadNurbsCurve(trim, ndim=2)
        return trim

    def project(self, face_surface, sv_curve, point, vector):
        nurbs_curve = curve_to_freecad_nurbs(sv_curve)
        if nurbs_curve is None:
            raise Exception("Curve is not NURBS!")
        fc_curve = nurbs_curve.curve
        fc_edge = Part.Edge(fc_curve)
        # face_surface : SvFreeCadNurbsSurface
        fc_face = face_surface.face

        if self.projection_type == 'PARALLEL':
            vector = Base.Vector(*vector)
            projection = fc_face.makeParallelProjection(fc_edge, vector).Edges
        elif self.projection_type == 'PERSPECTIVE':
            point = Base.Vector(*point)
            projection = fc_face.makePerspectiveProjection(fc_edge, point).Edges
        else: # ORTHO
            projection = fc_face.project([fc_edge]).Edges

        if not projection:
            if self.projection_type == 'PARALLEL':
                words = f"along {vector}"
            elif self.projection_type == 'PERSPECTIVE':
                words = f"from {point}"
            else:
                words = ""
            raise Exception(f"Projection {words} of {sv_curve} onto {face_surface} is empty for some reason")

        trims = [self.get_trim(fc_face, edge) for edge in projection]
        edges = [SvSolidEdgeCurve(edge).to_nurbs() for edge in projection]

        return edges, trims

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        in_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        point_s = self.inputs['Point'].sv_get()
        point_s = ensure_nesting_level(point_s, 3)
        vector_s = self.inputs['Vector'].sv_get()
        vector_s = ensure_nesting_level(vector_s, 3)

        edges_out = []
        trims_out = []
        for curves, face_surfaces, points, vectors in zip_long_repeat(curve_s, surface_s, point_s, vector_s):
            new_edges = []
            new_trims = []
            for curve, face_surface, point, vector in zip_long_repeat(curves, face_surfaces, points, vectors):
                if not is_solid_face_surface(face_surface):
                    face_surface = surface_to_freecad(face_surface, make_face=True) # SvFreeCadNurbsSurface
                projection, trims = self.project(face_surface, curve, point, vector)
                new_edges.append(projection)
                new_trims.append(trims)

            if in_level == 1:
                edges_out.extend(new_edges)
                trims_out.extend(new_trims)
            else: # 2
                edges_out.append(new_edges)
                trims_out.append(new_trims)

        self.outputs['Curves'].sv_set(edges_out)
        self.outputs['TrimCurves'].sv_set(trims_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvProjectCurveSurfaceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvProjectCurveSurfaceNode)

