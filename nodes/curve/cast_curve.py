
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.geom import SphereEquation, CylinderEquation, PlaneEquation
from sverchok.utils.curve import SvCurve, SvCastCurveToPlane, SvCastCurveToSphere, SvCastCurveToCylinder, UnsupportedCurveTypeException
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import cast_nurbs_curve

class SvCastCurveNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: Cast Curve to Shape
        Tooltip: Cast (project) a curve to the plane, sphere or cylindrical surface
        """
        bl_idname = 'SvExCastCurveNode'
        bl_label = 'Cast Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_CAST_CURVE'

        coefficient : FloatProperty(
                name = "Coefficient",
                description="Casting effect coefficient. 0 means no effect, 1.0 means output the curve on the target form. Use other values for linear interpolation or linear extrapolation",
                default = 1.0,
                update=updateNode)

        radius : FloatProperty(
                name = "Radius",
                description="Radius of the sphere/cylinder",
                default = 1.0,
                update=updateNode)

        forms = [
            ('PLANE', "Plane", "Plane defined by point and normal vector", 0),
            ('SPHERE', "Sphere", "Sphere defined by center and radius", 1),
            ('CYLINDER', "Cylinder", "Cylinder defined by center, direction and radius", 2)
        ]

        def update_sockets(self, context):
            self.inputs['Direction'].hide_safe = self.form == 'SPHERE'
            self.inputs['Radius'].hide_safe = self.form == 'PLANE'
            updateNode(self, context)

        form : EnumProperty(
            name = "Target form",
            items = forms,
            default = 'PLANE',
            update = update_sockets)

        use_nurbs : BoolProperty(
            name = "Use control points",
            description = "Transform control points of NURBS curves. If checked, then for NURBS curves the node will project only control points of the curve, instead of projecting each point of the curve. For non-NURBS curves, the node will raise an error (become red), and processing will stop",
            default = False,
            update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            
            p = self.inputs.new('SvVerticesSocket', "Center")
            p.use_prop = True
            p.default_property = (0.0, 0.0, 0.0)

            p = self.inputs.new('SvVerticesSocket', "Direction")
            p.use_prop = True
            p.default_property = (0.0, 0.0, 1.0)

            self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
            self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
            self.outputs.new('SvCurveSocket', "Curve")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.label(text="Target form:")
            layout.prop(self, 'form', text='')
            layout.prop(self, 'use_nurbs')

        def _cast_generic(self, curve, center, direction, radius, coeff):
            if self.form == 'PLANE':
                new_curve = SvCastCurveToPlane(curve, center,
                                direction, coeff)
            elif self.form == 'SPHERE':
                new_curve = SvCastCurveToSphere(curve, center,
                                radius, coeff)
            elif self.form == 'CYLINDER':
                new_curve = SvCastCurveToCylinder(curve, center,
                                direction, radius, coeff)
            else:
                raise Exception("Unsupported target form")
            return new_curve

        def _cast_nurbs(self, curve, center, direction, radius, coeff):
            curve = SvNurbsCurve.to_nurbs(curve)
            if curve is None:
                raise UnsupportedCurveTypeException("Provided curve is not a NURBS")
            if self.form == 'PLANE':
                target = PlaneEquation.from_normal_and_point(direction, center)
            elif self.form == 'SPHERE':
                target = SphereEquation(center, radius)
            elif self.form == 'CYLINDER':
                target = CylinderEquation.from_point_direction_radius(center, direction, radius)
            else:
                raise Exception("Unsupported target form")

            return cast_nurbs_curve(curve, target, coeff=coeff)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            center_s = self.inputs['Center'].sv_get()
            direction_s = self.inputs['Direction'].sv_get()
            radius_s = self.inputs['Radius'].sv_get()
            coeff_s = self.inputs['Coefficient'].sv_get()

            if isinstance(curve_s[0], SvCurve):
                curve_s = [curve_s]
            center_s = ensure_nesting_level(center_s, 3)
            direction_s = ensure_nesting_level(direction_s, 3)
            radius_s = ensure_nesting_level(radius_s, 2)
            coeff_s = ensure_nesting_level(coeff_s, 2)

            curves_out = []
            for curves, centers, directions, radiuses, coeffs in zip_long_repeat(curve_s, center_s, direction_s, radius_s, coeff_s):
                for curve, center, direction, radius, coeff in zip_long_repeat(curves, centers, directions, radiuses, coeffs):
                    if self.use_nurbs:
                        new_curve = self._cast_nurbs(curve, np.array(center), np.array(direction), radius, coeff)
                    else:
                        new_curve = self._cast_generic(curve, np.array(center), np.array(direction), radius, coeff)
                    curves_out.append(new_curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvCastCurveNode)

def unregister():
    bpy.utils.unregister_class(SvCastCurveNode)

