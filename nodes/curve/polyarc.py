
from mathutils import Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.geom import circle_by_start_end_tangent
from sverchok.utils.curve import SvCircle, SvLine, SvConcatCurve

class SvPolyArcNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Arc Start, End, Tangent
    Tooltip: Generate an arc from Start point, End point and Tangent vector
    """
    bl_idname = 'SvPolyArcNode'
    bl_label = 'Poly Arc'
    bl_icon = 'SPHERECURVE'
    sv_icon = 'SV_ARC_SED'

    concat : BoolProperty(
            name = "Concatenate",
            description = "Concatenate arc segments into single curve",
            default = True,
            update = updateNode)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            description = "Make the curve cyclic (closed)",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvVerticesSocket', "Tangent")
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvMatrixSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")
        self.outputs.new('SvStringsSocket', "Angle")

    def draw_buttons(self, context, layout):
        layout.prop(self, "concat", toggle=True)
        layout.prop(self, "is_cyclic", toggle=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        tangent_s = self.inputs['Tangent'].sv_get(default = [[[]]])
        have_tangent = self.inputs['Tangent'].is_linked

        verts_s = ensure_nesting_level(verts_s, 3)
        tangent_s = ensure_nesting_level(tangent_s, 3)
        tangent_s = tangent_s[0] # We can use only one tangent per curve, but let's support a spare pair of []

        curve_out = []
        center_out = []
        radius_out = []
        angle_out = []
        for verts, tangent in zip_long_repeat(verts_s, tangent_s):
            new_curves = []
            new_centers = []
            new_radius = []
            new_angles = []

            if not have_tangent:
                start_tangent = Vector(verts[1]) - Vector(verts[0])
                if self.is_cyclic:
                    end_tangent = Vector(verts[-1]) - Vector(verts[-2])
                    tangent = 0.5*(start_tangent + end_tangent)
                else:
                    tangent = start_tangent
            elif not isinstance(tangent, Vector):
                tangent = Vector(tangent)

            if self.is_cyclic:
                verts = verts + [verts[0]]

            for start, end in zip(verts, verts[1:]):
                start = Vector(start)
                end = Vector(end)
                diff = end - start
                if diff.angle(tangent) < 1e-8:
                    curve = SvLine.from_two_points(start, end)
                else:
                    eq = circle_by_start_end_tangent(start, end, tangent)
                    curve = SvCircle.from_equation(eq)
                    _, angle = curve.get_u_bounds()
                    tangent = Vector(curve.tangent(angle))
                    new_centers.append(curve.matrix)
                    new_radius.append(curve.radius)
                    new_angles.append(angle)
                new_curves.append(curve)

            if self.concat:
                new_curves = [SvConcatCurve(new_curves)]
            curve_out.append(new_curves)
            center_out.append(new_centers)
            radius_out.append(new_radius)
            angle_out.append(new_angles)

        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['Center'].sv_set(center_out)
        self.outputs['Radius'].sv_set(radius_out)
        self.outputs['Angle'].sv_set(angle_out)

def register():
    bpy.utils.register_class(SvPolyArcNode)

def unregister():
    bpy.utils.unregister_class(SvPolyArcNode)

