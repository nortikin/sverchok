# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.freecad import curve_to_freecad_nurbs, SvSolidEdgeCurve
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    try:
        import Part as PartModule
    except ImportError:
        PartModule = Part
    from FreeCAD import Base

class SvProjectSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Project Point or Curve onto Solid
    Tooltip: Project a point or a NURBS curve onto Solid object
    """
    bl_idname = 'SvProjectSolidNode'
    bl_label = "Project to Solid"
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_PROJECT_CURVE'
    sv_dependencies = {'FreeCAD'}

    def update_sockets(self, context):
        self.inputs['Point'].hide_safe = self.projection_type != 'PERSPECTIVE'
        self.inputs['Vector'].hide_safe = self.projection_type != 'PARALLEL'
        updateNode(self, context)

    projection_types = [
            ('PARALLEL', "Parallel", "Use parallel projection along given vector", 0),
            ('PERSPECTIVE', "Perspective", "Use perspective projection from given point", 1),
            ('ORTHO', "Orthogonal", "Use orthogonal projection", 2)
        ]
    
    projection_type : EnumProperty(
            name = "Projection",
            description = "Used projection type",
            items = projection_types,
            default = 'PARALLEL',
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvCurveSocket', "Curve")
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.prop = (0.0, 0.0, -1.0)
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text='Projection:')
        layout.prop(self, 'projection_type', text='')

    def project(self, solid, sv_object, point, vector):
        nurbs_curve = curve_to_freecad_nurbs(sv_object)
        if nurbs_curve is None:
            raise Exception("Curve is not NURBS!")
        fc_curve = nurbs_curve.curve
        fc_shape = PartModule.Edge(fc_curve)

        if self.projection_type == 'PARALLEL':
            vector = Base.Vector(*vector)
            projection = solid.makeParallelProjection(fc_shape, vector)
        elif self.projection_type == 'PERSPECTIVE':
            point = Base.Vector(*point)
            projection = solid.makePerspectiveProjection(fc_shape, point)
        else: # ORTHO
            projection = solid.project([fc_shape])

        if not projection:
            if self.projection_type == 'PARALLEL':
                words = f"along {vector}"
            elif self.projection_type == 'PERSPECTIVE':
                words = f"from {point}"
            else:
                words = ""
            raise Exception(f"Projection {words} of {sv_object} onto {solid} is empty for some reason")

        return [SvSolidEdgeCurve(edge).to_nurbs() for edge in projection.Edges]

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solid_s = self.inputs['Solid'].sv_get()
        in_level = get_data_nesting_level(solid_s, data_types=(PartModule.Shape,))
        solid_s = ensure_nesting_level(solid_s, 2, data_types=(PartModule.Shape,))
        nested_output = in_level > 1
        curve_s = self.inputs['Curve'].sv_get()
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        point_s = self.inputs['Point'].sv_get()
        point_s = ensure_nesting_level(point_s, 3)
        vector_s = self.inputs['Vector'].sv_get()
        vector_s = ensure_nesting_level(vector_s, 3)

        curve_out = []
        for params in zip_long_repeat(solid_s, curve_s, point_s, vector_s):
            new_curves = []
            new_vertices = []
            for solid, curve, point, vector in zip_long_repeat(*params):
                curve = self.project(solid, curve, point, vector)
                new_curves.append(curve)
            if nested_output:
                curve_out.append(new_curves)
            else:
                curve_out.extend(new_curves)
        
        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvProjectSolidNode)


def unregister():
    bpy.utils.unregister_class(SvProjectSolidNode)

