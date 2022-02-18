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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode, get_edge_list, get_edge_loop)
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper

from math import sin, cos, pi, sqrt, gcd, acos, ceil
from mathutils import Quaternion, Matrix, Euler

from sverchok.utils.profile import profile

epsilon = 1e-5  # used to avoid division by zero

type_items = [("HYPO", "Hypo", ""), ("LINE", "Line", ""), ("EPI", "Epi", "")]

# name : [ preset index, type, radius1, radius2, distance, phase1, phase2, turns, resolution ]
trochoid_presets = {
    " ":                    (0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0),
    # GENERIC LINE, EPI and HYPO TYPES
    "CYCLOID":              (10, "LINE", 1.0, 1.0, 1.0, 0.0, 0.0, 3.0, 200),
    "CURTATE CYCLOID":      (11, "LINE", 1.0, 1.0, 0.5, 0.0, 0.0, 3.0, 200),
    "PROLATE CYCLOID":      (12, "LINE", 1.0, 1.0, 2.0, 0.0, 0.0, 3.0, 200),
    "EPI-CYCLOID":          (13, "EPI", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "CURTATE EPI-CYCLOID":  (14, "EPI", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200),
    "PROLATE EPI-CYCLOID":  (15, "EPI", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200),
    "HYPO CYCLOID":         (16, "HYPO", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "CURTATE HYPO-CYCLOID": (17, "HYPO", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200),
    "PROLATE HYPO-CYCLOID": (18, "HYPO", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200),
    # EPIs
    "CARDIOID":             (20, "EPI", 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "NEPHROID":             (21, "EPI", 2.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "RANUNCULOID":          (22, "EPI", 5.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    # HYPOs
    "DELTOID":              (30, "HYPO", 3.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "ASTROID":              (31, "HYPO", 4.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "ROSETTE":              (32, "HYPO", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300),
    # other somewhat interesting EPIs
    "E 6-1-5":              (40, "EPI", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300),
    "E 6-3-1":              (41, "EPI", 6.0, 3.0, 1.0, 0.0, 0.0, 1.0, 200),
    "E 10-1-9":             (42, "EPI", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500),
    "E 12-7-11":            (43, "EPI", 12.0, 7.0, 11.0, 0.0, 0.0, 7.0, 500),
    "E 7-2-2":              (44, "EPI", 7.0, 2.0, 2.0, 0.0, 0.0, 2.0, 300),
    # other somewhat interesting HYPOs
    "H 6-1-4":              (50, "HYPO", 6.0, 1.0, 4.0, 0.0, 0.0, 1.0, 500),
    "H 10-1-9":             (51, "HYPO", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500),
    "H 13-6-12":            (52, "HYPO", 13.0, 6.0, 12.0, 0.0, 0.0, 6.0, 200),
    "H 1-5-2":              (53, "HYPO", 1.0, 5.0, 2.0, 0.0, 0.0, 5.0, 200),
    "H 6-10-5":             (54, "HYPO", 6.0, 10.0, 5.0, 0.0, 0.0, 10.0, 100),
}


class SvTrochoidNode(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Cycloid, Spirograph
    Tooltip: Generate trochoid curves (cycloids & epi / hypo trochoids)
    """
    bl_idname = 'SvTrochoidNode'
    bl_label = 'Trochoid'
    sv_icon = 'SV_TROCHOID'

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.phase1 = self.phase1 * au
        self.phase2 = self.phase2 * au

    def update_normalize(self, context):
        self.update_sockets()
        updateNode(self, context)

    def update_demo(self, context):
        self.update_sockets()
        updateNode(self, context)

    def update_trochoid(self, context):
        if self.updating:
            return

        self.presets = " "  # clear the preset if any setting changes
        updateNode(self, context)

    def preset_items(self, context):
        return [(k, k.title(), "", "", s[0]) for k, s in sorted(trochoid_presets.items(), key=lambda k: k[1][0])]

    def update_presets(self, context):
        if self.presets == " ":
            return

        self.updating = True

        tt, r1, r2, d, p1, p2, t, n = trochoid_presets[self.presets][1:]
        self.trochoid_type = tt
        self.radius1 = r1
        self.radius2 = r2
        self.distance = d
        self.phase1 = p1
        self.phase2 = p2
        self.turns = t
        self.resolution = n
        self.scale = 1.0
        self.normalize_size = 1.0
        self.normalize = True
        self.swap = False

        self.updating = False

        updateNode(self, context)

    presets: EnumProperty(
        name="Presets", items=preset_items, update=update_presets)

    trochoid_type: EnumProperty(
        name="Type", items=type_items,
        description="Type of the trochoid: HYPO, LINE & EPI",
        default="EPI", update=update_trochoid)

    radius1: FloatProperty(
        name='Radius1', description='Radius of the static circle',
        default=6.0, min=0.0, update=update_trochoid)

    radius2: FloatProperty(
        name='Radius2', description='Radius of the moving circle',
        default=1.0, min=0.0, update=update_trochoid)

    distance: FloatProperty(
        name='Distance',
        description='Distance from the drawing point to the center of the moving circle',
        default=4.0, min=0.0, update=update_trochoid)

    phase1: FloatProperty(
        name='Phase1', description='Starting angle on the static circle',
        default=0.0, update=SvAngleHelper.update_angle)

    phase2: FloatProperty(
        name='Phase2', description='Starting angle on the moving circle',
        default=0.0, update=SvAngleHelper.update_angle)

    turns: FloatProperty(
        name='Turns', description='Number of turns the moving circle makes around the static circle',
        default=1.0, min=0.0, update=update_trochoid)

    shift: FloatProperty(
        name='Shift', description='Shift the starting point along the curve',
        default=0.0, update=update_trochoid)
        # default=0.0, min=0.0, max=1.0, update=update_trochoid)

    resolution: IntProperty(
        name='Resolution',
        description='Number of vertices in one full turn around the static circle',
        default=200, min=3, update=update_trochoid)

    scale: FloatProperty(
        name='Scale', description='Scale of the main parameters: radii and distance',
        default=1.0, min=0.0, update=update_trochoid)

    swap: BoolProperty(
        name='Swap', description='Swap radii and phases: R1<->R2 and P1<->P2',
        default=False, update=update_trochoid)

    normalize: BoolProperty(
        name='Normalize', description='Scale the curve to fit within normalized size',
        default=False, update=update_normalize)

    normalize_size: FloatProperty(
        name='Size', description='Normalized size of the curve',
        default=1.0, min=0.0, update=updateNode)

    turn_stretch: BoolProperty(
        name='Stretch Turn', description='Stretch the turns in order to close trochoid path',
        default=False, update=updateNode)

    demo_mode: BoolProperty(
        name='Demo Mode', description='Show extra outputs for demo purposes',
        default=False, update=update_demo)

    updating: BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.width = 170
        self.inputs.new('SvStringsSocket', "Radius1").prop_name = "radius1"
        self.inputs.new('SvStringsSocket', "Radius2",).prop_name = "radius2"
        self.inputs.new('SvStringsSocket', "Distance").prop_name = "distance"
        self.inputs.new('SvStringsSocket', "Turns").prop_name = "turns"
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = "resolution"
        self.inputs.new('SvStringsSocket', "Phase1").prop_name = "phase1"
        self.inputs.new('SvStringsSocket', "Phase2").prop_name = "phase2"
        self.inputs.new('SvStringsSocket', "Shift").prop_name = "shift"
        self.inputs.new('SvStringsSocket', "S").prop_name = "scale"

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")

        # demo mode sockets
        self.outputs.new('SvVerticesSocket', "Full Turns Vertices")
        self.outputs.new('SvStringsSocket', "Full Turns Edges")
        self.outputs.new('SvVerticesSocket', "Scaled r1 r2 d")
        self.outputs.new('SvMatrixSocket', "Moving Circle Transform")
        self.outputs.new('SvVerticesSocket', "Min Range")
        self.outputs.new('SvVerticesSocket', "Max Range")
        self.outputs.new('SvStringsSocket', "Normalized Scale")

        self.presets = "ROSETTE"
        self.update_sockets()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'presets', text="")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "trochoid_type", expand=True)
        row = col.row(align=True)
        row.prop(self, "normalize", text="Norm", toggle=True)
        row.prop(self, "swap", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_angle_units_buttons(context, layout)
        layout.prop(self, "turn_stretch")
        layout.prop(self, "demo_mode")

    def update_sockets(self):
        """
        Replace sockets based on currently selected mode
        """
        if self.normalize:
            socket = self.inputs[-1]
            socket.replace_socket("SvStringsSocket", "S").prop_name = "normalize_size"
        else:
            socket = self.inputs[-1]
            socket.replace_socket("SvStringsSocket", "S").prop_name = "scale"

        # demo mode sockets
        self.outputs["Full Turns Vertices"].hide_safe = not self.demo_mode
        self.outputs["Full Turns Edges"].hide_safe = not self.demo_mode
        self.outputs["Scaled r1 r2 d"].hide_safe = not self.demo_mode
        self.outputs["Min Range"].hide_safe = not self.demo_mode
        self.outputs["Max Range"].hide_safe = not self.demo_mode
        self.outputs["Moving Circle Transform"].hide_safe = not self.demo_mode
        self.outputs["Normalized Scale"].hide_safe = not self.demo_mode

    def scaling_factor(self, s, a, b, d):
        """
        Returns the scaling factor that keeps the curve to the given normalized size.

        Args:
            s : scale / size
            a : static circle radius
            b : moving circle radius
            d : distance

        Returns:
            The normalized scaling factor
        """
        if self.normalize:  # normalize ? => set scale to fit the normalize size
            if self.trochoid_type == "EPI":
                s = s / (abs(a + b) + d + epsilon)
            elif self.trochoid_type == "HYPO":
                s = s / (abs(a - b) + d + epsilon)
            else:  # LINE
                s = s / (2 * pi * a + d + epsilon)

        return s

    @profile
    def grid_range(self, r1, r2, d, p1, p2, t, s):
        """
        Get the min/max grid range (radial for EPI/HYPO and planar for LINE)
        """
        a, b = [r2, r1] if self.swap else [r1, r2]

        ss = self.scaling_factor(s, r1, r2, d)

        a = a * ss
        b = b * ss
        d = d * ss

        if self.trochoid_type == "EPI":
            min_r_range = abs(a + b - d)
            max_r_range = a + b + d
            min_range = [min_r_range, 0, 0]
            max_range = [max_r_range, 0, 0]

        elif self.trochoid_type == "HYPO":
            min_r_range = abs(abs(a - b) - d)
            max_r_range = abs(a - b) + d
            min_range = [min_r_range, 0, 0]
            max_range = [max_r_range, 0, 0]

        else:  # LINE
            min_y_range = b - d
            max_y_range = b + d
            # print("b=", b)
            # print("d=", d)
            # print("b/d=", b/d)
            k = min(1.0, abs(b/d))
            # f = p2 % (2*pi)
            a0 = acos(k)  # - f # angle at which P reaches min X position
            min_x_range = b * a0 - d * sin(a0)
            an = - acos(k) + 2 * pi * ceil(t+epsilon)
            max_x_range = b * an - d * sin(an)

            min_range = [min_x_range, min_y_range, 0]
            max_range = [max_x_range, max_y_range, 0]

        return min_range, max_range

    @profile
    def moving_circle_transform(self, r1, r2, d, p1, p2, t, n, s):

        a, b, p1, p2 = [r2, r1, p2, p1] if self.swap else [r1, r2, p1, p2]

        ts = b / gcd(int(a), int(b))
        t = t * ts if self.turn_stretch else t

        ss = self.scaling_factor(s, r1, r2, d)

        a = a * ss
        b = max(b * ss, epsilon)  # safeguard to avoid division by zero
        d = d * ss

        if self.trochoid_type == "EPI":
            sign = +1.0
        elif self.trochoid_type == "HYPO":
            sign = -1.0
        else:  # LINE
            t = 2 * pi * t

            m_t = Matrix().Identity(4)

            # translation
            m_t[0][3] = b * t
            m_t[1][3] = b
            m_t[2][3] = 0

            # rotation
            m_r = Euler((0, 0, -t + pi/2 - p2), "XYZ").to_quaternion().to_matrix().to_4x4()

            # composite matrix
            m = m_t @ m_r

            return m

        r = a + b * sign
        g = r / b
        t = 2 * pi * t

        m_t = Matrix().Identity(4)

        # translation
        m_t[0][3] = r * cos(t + p1)
        m_t[1][3] = r * sin(t + p1)
        m_t[2][3] = 0

        # rotation
        m_r = Euler((0, 0, sign * (g * t + p2)), "XYZ").to_quaternion().to_matrix().to_4x4()

        # composite matrix
        m = m_t @ m_r

        return m

    @profile
    def make_trochoid(self, r1, r2, d, p1, p2, t, n, f, s):
        """
        Generates the vertices and edges of the trochoid for the given parameters.

        r1 : radius1    = radius of the static circle
        r2 : radius2    = radius of the moving circle
        d  : distance   = drawing point distance to the center of the moving circle
        p1 : phase1     = starting angle for the static circle
        p2 : phase2     = starting angle for the moving circle
        t  : turns      = number of turns around the static circle
        n  : resolution = number of vertices in one full turn around the static circle
        f  : shift      = shift the starting point along the curve (percentage)
        s  : scale      = scale the main parameters (radii & distance)

        See documentation here for details:
          https://en.wikipedia.org/wiki/Trochoid
          https://en.wikipedia.org/wiki/Epitrochoid
          https://en.wikipedia.org/wiki/Hypotrochoid
        """
        verts = []
        edges = []

        a, b, p1, p2 = [r2, r1, p2, p1] if self.swap else [r1, r2, p1, p2]

        ts = b / gcd(int(a), int(b))
        t = t * ts if self.turn_stretch else t

        ss = self.scaling_factor(s, r1, r2, d)

        a = a * ss
        b = max(b * ss, epsilon)  # safeguard to avoid division by zero
        d = d * ss

        if self.trochoid_type == "EPI":
            r = a + b  # outer radius
            g = r / b  # outer "gear ratio"
            def fx(t): return r * cos(t + p1) - d * cos(g * t + p2)
            def fy(t): return r * sin(t + p1) - d * sin(g * t + p2)
        elif self.trochoid_type == "HYPO":
            r = a - b  # inner radius
            g = r / b  # inner "gear ratio"
            def fx(t): return r * cos(t + p1) + d * cos(g * t + p2)
            def fy(t): return r * sin(t + p1) - d * sin(g * t + p2)
        else:  # LINE
            def fx(t): return b * t - d * sin(t + p2)
            def fy(t): return b - d * cos(t + p2)

        def v(t): return [fx(t), fy(t), 0]

        n = max(3, int(t * n))  # total number of points in all turns
        dt = 2 * pi * t / n  # turn increment
        shift = 2 * pi * f * t

        verts = [v(shift + i * dt) for i in range(n + 1)]

        # close the curve if the first & last points overlap (remove duplicate)
        vf, vl = [verts[0], verts[n]]
        dx, dy, dz = [vl[0] - vf[0], vl[1] - vf[1], vl[2] - vf[2]]
        delta = sqrt(dx * dx + dy * dy + dz * dz)

        if delta < epsilon:  # close the curve
            del verts[-1]
            edges = get_edge_loop(n)
        else:  # keep the curve open
            edges = get_edge_list(n)

        return verts, edges

    @profile
    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_r1 = inputs["Radius1"].sv_get()[0]   # radius of static circle
        input_r2 = inputs["Radius2"].sv_get()[0]   # radius of moving circle
        input_d = inputs["Distance"].sv_get()[0]   # distance
        input_p1 = inputs["Phase1"].sv_get()[0]    # phase P1
        input_p2 = inputs["Phase2"].sv_get()[0]    # phase P2
        input_t = inputs["Turns"].sv_get()[0]      # turns
        input_n = inputs["Resolution"].sv_get()[0] # resolution
        input_f = inputs["Shift"].sv_get()[0]      # shift
        input_s = inputs["S"].sv_get()[0]          # scale

        # sanitize the inputs
        input_r1 = list(map(lambda x: max(0.0, x), input_r1))
        input_r2 = list(map(lambda x: max(0.0, x), input_r2))
        input_d = list(map(lambda x: max(0.0, x), input_d))
        input_t = list(map(lambda x: max(0.0, x), input_t))
        input_n = list(map(lambda x: max(3, int(x)), input_n))
        input_s = list(map(lambda x: max(0.0, x), input_s))

        parameters = match_long_repeat([input_r1, input_r2, input_d,
                                        input_p1, input_p2, input_t,
                                        input_n, input_f, input_s])

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        vert_list = []
        edge_list = []
        for r1, r2, d, p1, p2, t, n, f, s in zip(*parameters):
            verts, edges = self.make_trochoid(r1, r2, d, p1 * au, p2 * au, t, n, f, s)
            vert_list.append(verts)
            edge_list.append(edges)

        if outputs["Vertices"].is_linked:
            outputs["Vertices"].sv_set(vert_list)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edge_list)

        # demo mode sockets
        if self.demo_mode:
            matrix_list = []
            scaled_rrd_list = []
            max_range_list = []
            min_range_list = []
            normalized_scale_list = []
            v_list = []
            e_list = []
            for r1, r2, d, p1, p2, t, n, f, s in zip(*parameters):
                v, e = self.make_trochoid(r1, r2, d, p1 * au, p2 * au, self.turns, n, f, s)
                v_list.append(v)
                e_list.append(e)
                
                m = self.moving_circle_transform(r1, r2, d, p1 * au, p2 * au, t, n, s)
                matrix_list.append(m)

                ss = self.scaling_factor(s, r1, r2, d)
                scaled_rrd_list.append([r1*ss, r2*ss, d*ss if self.trochoid_type == "HYPO" else -d*ss])

                min_range, max_range = self.grid_range(r1, r2, d, p1 * au, p2 * au, t, s)
                min_range_list.append(min_range)
                max_range_list.append(max_range)

                normalized_scale_list.append(ss)
                
            if outputs["Full Turns Vertices"].is_linked:
                outputs["Full Turns Vertices"].sv_set(v_list)
            if outputs["Full Turns Edges"].is_linked:
                outputs["Full Turns Edges"].sv_set(e_list)
            if outputs["Scaled r1 r2 d"].is_linked:
                outputs["Scaled r1 r2 d"].sv_set([scaled_rrd_list])
            if outputs["Max Range"].is_linked:
                outputs["Max Range"].sv_set([max_range_list])
            if outputs["Min Range"].is_linked:
                outputs["Min Range"].sv_set([min_range_list])
            if outputs["Moving Circle Transform"].is_linked:
                outputs["Moving Circle Transform"].sv_set(matrix_list)
            if outputs["Normalized Scale"].is_linked:
                outputs["Normalized Scale"].sv_set([normalized_scale_list])
                

def register():
    bpy.utils.register_class(SvTrochoidNode)


def unregister():
    bpy.utils.unregister_class(SvTrochoidNode)
