
from math import sqrt

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvEllipse

class SvEllipseCurveNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Ellipse Curve
    Tooltip: Generate ellipse curve
    """
    bl_idname = 'SvEllipseCurveNodeMK2'
    bl_label = 'Ellipse (Curve)'
    sv_icon = 'SV_ELLIPSE'

    mode_items = [("AB", "a b", "Major Radius / Minor Radius", 1),
                  ("AE", "a e", "Major Radius / Eccentricity", 2),
                  ("AC", "a c", "Major Radius / Focal Length", 3)]

    centering_items = [(SvEllipse.F1, "F1", "Ellipse focal point 1", 1),
                       (SvEllipse.CENTER, "C", "Ellipse center point", 2),
                       (SvEllipse.F2, "F2", "Ellipse focal point 2", 3)]

    def update_sockets(self, context):
        self.inputs['Minor Radius'].enabled = (self.mode == "AB")
        self.inputs['Eccentricity'].enabled = (self.mode == "AE")
        self.inputs['Focal Length'].enabled = (self.mode == "AC")

        updateNode(self, context)

    mode: EnumProperty(
        name="Mode", items=mode_items,
        description="Ellipse definition mode",
        default="AB", update=update_sockets)

    centering: EnumProperty(
        name="Centering", items=centering_items,
        description="Center the ellipse around F1, C or F2",
        default=SvEllipse.CENTER,
        update=update_sockets)

    major_radius: FloatProperty(
        name='Major Radius', description='Ellipse major radius (semiaxis)',
        default=1.0, min=0.0, update=update_sockets)

    minor_radius: FloatProperty(
        name='Minor Radius', description='Ellipse minor radius (semiaxis)',
        default=0.8, min=0.0, update=update_sockets)

    eccentricity: FloatProperty(
        name='Eccentricity', description='Ellipse eccentricity',
        default=0.6, min=0.0, max=1.0, update=update_sockets)

    focal_length: FloatProperty(
        name='Focal Length', description='Ellipse focal length. Distance from ellipse’s center to it’s focal points',
        default=0.6, min=0.0, update=update_sockets)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "mode", expand=True)
        row = col.row(align=True)
        row.prop(self, "centering", expand=True)

    def sv_init(self, context):
        self.width = 160
        self.inputs.new('SvStringsSocket', "Major Radius").prop_name = "major_radius" # 0
        self.inputs.new('SvStringsSocket', "Minor Radius").prop_name = "minor_radius" # 1
        self.inputs.new("SvStringsSocket", "Eccentricity").prop_name = "eccentricity"
        self.inputs.new("SvStringsSocket", "Focal Length").prop_name = "focal_length"
        self.inputs.new('SvMatrixSocket', "Matrix") # 2

        self.outputs.new('SvCurveSocket', "Ellipse")
        self.outputs.new('SvVerticesSocket', "F1")
        self.outputs.new('SvVerticesSocket', "F2")
        
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        major_radius_s = self.inputs['Major Radius'].sv_get(deepcopy=False)
        if self.mode == 'AB':
            input2_s = self.inputs["Minor Radius"].sv_get(deepcopy=False)
        elif self.mode == 'AE':
            input2_s = self.inputs["Eccentricity"].sv_get(deepcopy=False)
        else:
            input2_s = self.inputs["Focal Length"].sv_get(deepcopy=False)

        matrices_s = self.inputs['Matrix'].sv_get(default = [[Matrix()]])

        major_radius_s = ensure_nesting_level(major_radius_s, 2)
        input2_s = ensure_nesting_level(input2_s, 2)
        matrices_s = ensure_nesting_level(matrices_s, 2, data_types=(Matrix,))

        curves_out = []
        f1_out = []
        f2_out = []
        for major_radius_i, input2_i, matrices_i in zip_long_repeat(major_radius_s, input2_s, matrices_s):
            new_curves = []
            new_f1 = []
            new_f2 = []
            for major_radius, input2, matrix in zip_long_repeat(major_radius_i, input2_i, matrices_i):
                if self.mode == 'AB':
                    minor_radius = input2
                elif self.mode == 'AE':
                    e = input2
                    minor_radius = major_radius * sqrt(1 - e*e)
                else: # AC
                    c = input2
                    a = major_radius
                    minor_radius = sqrt(a*a - c*c)

                ellipse = SvEllipse(matrix, major_radius, minor_radius, center_type = self.centering)
                f1, f2 = ellipse.to_equation().focal_points()
                new_f1.append(f1)
                new_f2.append(f2)
                new_curves.append(ellipse)

            curves_out.append(new_curves)
            f1_out.append(new_f1)
            f2_out.append(new_f2)

        self.outputs['Ellipse'].sv_set(curves_out)
        self.outputs['F1'].sv_set(f1_out)
        self.outputs['F2'].sv_set(f2_out)

def register():
    bpy.utils.register_class(SvEllipseCurveNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvEllipseCurveNodeMK2)

