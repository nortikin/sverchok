# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import (match_long_repeat, updateNode, get_edge_loop)
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper

from math import sin, cos, pi, sqrt

centering_items = [("F1", "F1", "Ellipse focal point 1", 1),
                   ("C", "C", "Ellipse center point", 2),
                   ("F2", "F2", "Ellipse focal point 2", 3)]

mode_items = [("AB", "a b", "Major Radius / Minor Radius", 1),
              ("AE", "a e", "Major Radius / Eccentricity", 2),
              ("AC", "a c", "Major Radius / Focal Length", 3)]


class SvEllipseNodeMK2(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Ellipse
    Tooltip: Generate ellipses
    """
    bl_idname = 'SvEllipseNodeMK2'
    bl_label = 'Ellipse'
    sv_icon = 'SV_ELLIPSE'

    @throttled
    def update_mode(self, context):
        ''' Update the ellipse parameters of the new mode based on previous mode ones'''

        if self.mode == "AB":
            if self.last_mode == "AE":  # ae => ab
                a = self.major_radius
                e = self.eccentricity
                self.minor_radius = a * sqrt(1 - e * e)
            elif self.last_mode == "AC":  # ac => ab
                a = self.major_radius
                c = min(a, self.focal_length)
                self.minor_radius = sqrt(a * a - c * c)

        elif self.mode == "AE":
            if self.last_mode == "AB":  # ab => ae
                a = self.major_radius
                b = min(a, self.minor_radius)
                self.eccentricity = sqrt(1 - (b * b) / (a * a))
            if self.last_mode == "AC":  # ac => ae
                a = self.major_radius
                c = self.focal_length
                self.eccentricity = c / a

        elif self.mode == "AC":
            if self.last_mode == "AB":  # ab => ac
                a = self.major_radius
                b = min(a, self.minor_radius)
                self.focal_length = sqrt(a * a - b * b)
            if self.last_mode == "AE":  # ae => ac
                a = self.major_radius
                e = self.eccentricity
                self.focal_length = a * e

        if self.mode != self.last_mode:
            self.last_mode = self.mode
            self.update_sockets()

        # there's an automatic updateNode call from the decorator at the.
        # people aren't going to be repeatedly pressing the same mode enum 


    def update_ellipse(self, context):
        if self.updating:
            return

        updateNode(self, context)

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.phase = self.phase * au
        self.rotation = self.rotation * au

    centering: EnumProperty(
        name="Centering", items=centering_items,
        description="Center the ellipse around F1, C or F2",
        default="C", update=updateNode)

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

    num_verts: IntProperty(
        name='Num Verts', description='Number of vertices in the ellipse',
        default=36, min=3, update=updateNode)

    phase: FloatProperty(
        name='Phase', description='Phase ellipse vertices around the center by this angle amount',
        default=0.0, update=SvAngleHelper.update_angle)

    rotation: FloatProperty(
        name='Rotation', description='Rotate ellipse vertices around the centering point by this angle amount',
        default=0.0, update=SvAngleHelper.update_angle)

    scale: FloatProperty(
        name='Scale', description='Scale ellipse radii by this amount',
        default=1.0, min=0.0, update=updateNode)

    updating: BoolProperty(default=False)  # used for disabling update callback

    def migrate_from(self, old_node):
        ''' Migration from old nodes '''
        if old_node.bl_idname == "SvEllipseNode":
            self.angle_units = AngleUnits.RADIANS
            self.last_angle_units = AngleUnits.RADIANS

    def sv_init(self, context):
        self.width = 160
        self.inputs.new('SvStringsSocket', "Major Radius").prop_name = "major_radius"
        self.inputs.new('SvStringsSocket', "Minor Radius").prop_name = "minor_radius"
        self.inputs.new('SvStringsSocket', "Num Verts").prop_name = "num_verts"
        self.inputs.new('SvStringsSocket', "Phase").prop_name = "phase"
        self.inputs.new('SvStringsSocket', "Rotation").prop_name = "rotation"
        self.inputs.new('SvStringsSocket', "Scale").prop_name = "scale"

        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polys")
        self.outputs.new('SvVerticesSocket', "F1")
        self.outputs.new('SvVerticesSocket', "F2")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "mode", expand=True)
        row = col.row(align=True)
        row.prop(self, "centering", expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_angle_units_buttons(context, layout)

    def update_sockets(self):
        socket2 = self.inputs[1]
        if self.mode == "AB":
            socket2.replace_socket("SvStringsSocket", "Minor Radius").prop_name = "minor_radius"
        elif self.mode == "AE":
            socket2.replace_socket("SvStringsSocket", "Eccentricity").prop_name = "eccentricity"
        else:  # AC
            socket2.replace_socket("SvStringsSocket", "Focal Length").prop_name = "focal_length"

    def make_ellipse(self, a, b, N, phase, rotation, scale):
        '''
        Make an Ellipse (verts, edges and polys)

        a         : major radius of the ellipse
        b         : minor radius of the ellipse
        N         : number of vertices in the curve
        phase     : shift the points along the curve by this angle amount
        rotation  : rotate the ellipse in plane by this angle amount
        scale     : scale the major & minor radii by this factor
        '''
        verts = []
        edges = []
        polys = []

        a = a * scale
        b = b * scale

        if a > b:
            dx = sqrt(a * a - b * b)
            dy = 0
        else:
            dx = 0
            dy = sqrt(b * b - a * a)

        if self.centering == "F1":
            cx = -dx
            cy = -dy
        elif self.centering == "F2":
            cx = +dx
            cy = +dy
        else:  # "C"
            cx = 0
            cy = 0

        sins = sin(rotation)  # cached for performance
        coss = cos(rotation)  # cached for performance

        f1x = -cx - dx
        f1y = -cy - dy
        f2x = -cx + dx
        f2y = -cy + dy
        f1xx = f1x * coss - f1y * sins
        f1yy = f1x * sins + f1y * coss
        f2xx = f2x * coss - f2y * sins
        f2yy = f2x * sins + f2y * coss

        f1 = [f1xx, f1yy, 0]
        f2 = [f2xx, f2yy, 0]

        delta = 2 * pi / N  # cached for performance

        add_vert = verts.append
        for n in range(N):
            theta = delta * n + phase
            x = -cx + a * cos(theta)
            y = -cy + b * sin(theta)
            # apply inplane rotation
            xx = x * coss - y * sins
            yy = x * sins + y * coss
            add_vert((xx, yy, 0))

        edges = get_edge_loop(N)
        polys = [list(range(N))]

        return verts, edges, polys, f1, f2

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_v1 = inputs[0].sv_get()[0]  # major radius
        input_v2 = inputs[1].sv_get()[0]  # minor radius, eccentricity or focal length
        input_N = inputs["Num Verts"].sv_get()[0]
        input_p = inputs["Phase"].sv_get()[0]
        input_r = inputs["Rotation"].sv_get()[0]
        input_s = inputs["Scale"].sv_get()[0]

        # convert main input parameters to major/minor radii (and sanitize inputs)
        if self.mode == "AB":
            input_a, input_b = match_long_repeat([input_v1, input_v2])
            input_a = list(map(lambda a: max(0.0, a), input_a))
            input_b = list(map(lambda a, b: max(0.0, min(a, b)), input_a, input_b))
        elif self.mode == "AE":
            input_a, input_e = match_long_repeat([input_v1, input_v2])
            input_a = list(map(lambda a: max(0.0, a), input_a))
            input_e = list(map(lambda e: max(0.0, min(1.0, e)), input_e))
            input_b = list(map(lambda a, e: a * sqrt(1 - e * e), input_a, input_e))
        else:  # "AC"
            input_a, input_c = match_long_repeat([input_v1, input_v2])
            input_a = list(map(lambda a: max(0.0, a), input_a))
            input_c = list(map(lambda a, c: max(0.0, min(a, c)), input_a, input_c))
            input_b = list(map(lambda a, c: sqrt(a * a - c * c), input_a, input_c))

        # sanitize the input
        input_N = list(map(lambda n: max(3, int(n)), input_N))

        parameters = match_long_repeat([input_a, input_b, input_N, input_p, input_r, input_s])

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        verts_list = []
        edges_list = []
        polys_list = []
        f1_list = []
        f2_list = []
        for a, b, N, p, r, s in zip(*parameters):
            verts, edges, polys, f1, f2 = self.make_ellipse(a, b, N, p * au, r * au, s)
            verts_list.append(verts)
            edges_list.append(edges)
            polys_list.append(polys)
            f1_list.append(f1)
            f2_list.append(f2)

        outputs["Verts"].sv_set(verts_list)
        outputs["Edges"].sv_set(edges_list)
        outputs["Polys"].sv_set(polys_list)

        outputs["F1"].sv_set([f1_list])
        outputs["F2"].sv_set([f2_list])


def register():
    bpy.utils.register_class(SvEllipseNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvEllipseNodeMK2)
