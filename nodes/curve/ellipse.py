
import numpy as np
from math import pi, sqrt

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok.utils.curve import SvEllipse

class SvEllipseCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ellipse Curve
    Tooltip: Generate ellipse curve
    """
    bl_idname = 'SvEllipseCurveNode'
    bl_label = 'Ellipse (Curve)'
    sv_icon = 'SV_ELLIPSE'

    mode_items = [("AB", "a b", "Major Radius / Minor Radius", 1),
                  ("AE", "a e", "Major Radius / Eccentricity", 2),
                  ("AC", "a c", "Major Radius / Focal Length", 3)]

    @throttled
    def update_mode(self, context):
        ''' Update the ellipse parameters of the new mode based on previous mode ones'''

        if self.mode == self.last_mode:
            return

        #               from            to
        switch_state = (self.last_mode, self.mode)

        a = self.major_radius
        e = self.eccentricity
        c = self.focal_length

        self.updating = True

        if switch_state == ("AE", "AB"):
            self.minor_radius = a * sqrt(1 - e * e)

        elif switch_state == ("AC", "AB"):
            c = min(a, c)
            self.minor_radius = sqrt(a * a - c * c)

        elif switch_state == ("AB", "AE"):
            b = min(a, self.minor_radius)
            self.eccentricity = sqrt(1 - (b * b) / (a * a))

        elif switch_state == ("AC", "AE"):
            self.eccentricity = c / a

        elif switch_state == ("AB", "AC"):
            b = min(a, self.minor_radius)
            self.focal_length = sqrt(a * a - b * b)

        elif switch_state == ("AE", "AC"):
            self.focal_length = a * e

        self.updating = False

        self.last_mode = self.mode
        self.update_sockets()

    def update_ellipse(self, context):
        if self.updating:
            return

        updateNode(self, context)

    def update_sockets(self):
        if self.mode == "AB":
            socket2 = self.inputs[1]
            socket2.replace_socket("SvStringsSocket", "Minor Radius").prop_name = "minor_radius"
        elif self.mode == "AE":
            socket2 = self.inputs[1]
            socket2.replace_socket("SvStringsSocket", "Eccentricity").prop_name = "eccentricity"
        else:  # AC
            socket2 = self.inputs[1]
            socket2.replace_socket("SvStringsSocket", "Focal Length").prop_name = "focal_length"

    mode: EnumProperty(
        name="Mode", items=mode_items,
        description="Ellipse definition mode",
        default="AB", update=update_mode)

    last_mode: EnumProperty(
        name="Mode", items=mode_items,
        description="Ellipse definition last mode",
        default="AB")

    major_radius: FloatProperty(
        name='Major Radius', description='Ellipse major radius',
        default=1.0, min=0.0, update=update_ellipse)

    minor_radius: FloatProperty(
        name='Minor Radius', description='Ellipse minor radius',
        default=0.8, min=0.0, update=update_ellipse)

    eccentricity: FloatProperty(
        name='Eccentricity', description='Ellipse eccentricity',
        default=0.6, min=0.0, max=1.0, update=update_ellipse)

    focal_length: FloatProperty(
        name='Focal Length', description='Ellipse focal length',
        default=0.6, min=0.0, update=update_ellipse)

    updating: BoolProperty(default=False)  # used for disabling update callback

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "mode", expand=True)

    def sv_init(self, context):
        self.width = 160
        self.inputs.new('SvStringsSocket', "Major Radius").prop_name = "major_radius" # 0
        self.inputs.new('SvStringsSocket', "Minor Radius").prop_name = "minor_radius" # 1
        self.inputs.new('SvMatrixSocket', "Matrix") # 2

        self.outputs.new('SvCurveSocket', "Ellipse")
        self.outputs.new('SvVerticesSocket', "F1")
        self.outputs.new('SvVerticesSocket', "F2")

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        major_radius_s = self.inputs['Major Radius'].sv_get()
        input2_s = self.inputs[1].sv_get()# minor radius, eccentricity or focal length
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

                ellipse = SvEllipse(matrix, major_radius, minor_radius)
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
    bpy.utils.register_class(SvEllipseCurveNode)

def unregister():
    bpy.utils.unregister_class(SvEllipseCurveNode)

