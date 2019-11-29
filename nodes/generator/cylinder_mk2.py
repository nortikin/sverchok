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
from sverchok.data_structure import (match_long_repeat, updateNode, get_edge_loop)
from sverchok.utils.geom import CubicSpline

from math import sin, cos, pi

import numpy as np

angle_unit_items = [
    ("RAD", "Rad", "Radians", "", 0),
    ("DEG", "Deg", 'Degrees', "", 1),
    ("UNI", "Uni", 'Unities', "", 2)
]

angle_conversion = {"RAD": 1.0, "DEG": pi / 180.0, "UNI": 2 * pi}


def resample_1D_array(profile, samples, cyclic):
    ''' Resample 1D array '''
    N = len(profile)
    v = [[n / (N - 1), p, 0] for n, p in enumerate(profile)]
    samples_array = np.array(samples).clip(0, 1)
    spline = CubicSpline(v, metric="POINTS", is_cyclic=cyclic)
    out = spline.eval(samples_array)
    verts = out.tolist()

    resampled_profile = [v[1] for v in verts]

    return resampled_profile


def make_verts(rt, rb, np, nm, h, t, ph, s, profile_p, profile_m, flags):
    """
    Generate cylinder vertices for the given parameters
        rt : top radius
        rb : bottom radius
        np : number of parallels (= number of points in a meridian)
        nm : number of meridians (= number of points in a parallel)
        h  : height
        t  : twist (rotate parallel verts by this angle around Z from bottom to top)
        ph : phase (rotate all verts by this angle around Z axis)
        s  : scale the entire mesh (radii & height)
        profile_p : parallels profile
        profile_m : meridians profile
    """
    separate, center, cyclic = flags

    rt = rt * s
    rb = rb * s
    h = h * s

    if len(profile_p) < 2:  # no profile given (make profile all ones)
        resampled_profile_p = [1] * nm
    else: # resample PARALLELS profile to nm parallel points [0-1]
        samples = [m / nm for m in range(nm + 1)]
        resampled_profile_p = resample_1D_array(profile_p, samples, cyclic)

    if len(profile_m) < 2:  # no profile given (make profile all ones)
        resampled_profile_m = [1] * np
    else: # resample MERIDIANS profile to np meridian points [0-1)
        samples = [p / (np - 1) for p in range(np)]
        resampled_profile_m = resample_1D_array(profile_m, samples, False)

    dA = 2.0 * pi / nm  # angle increment from one meridian to the next
    dH = h / (np - 1)  # height increment from one parallel to the next
    dT = t / (np - 1)  # twist increment from one parallel to the next
    dZ = - h / 2 if center else 0  # center offset

    vert_list = []
    add_verts = vert_list.append if separate else vert_list.extend
    for p in range(np):  # for every point on a meridian (traverse the parallels)
        f = p / (np - 1)  # interpolation factor between rb and rt
        r = rb * (1 - f) + rt * f  # interpolated radius between bottom and top radii
        rp = r * resampled_profile_m[p]  # modulate radius by meridian profile
        z = dZ + dH * p
        phase = ph + dT * p  # parallel's total phase (phase + delta twist)

        verts = []
        for m in range(nm):  # for every point on a parallel (traverse the meridians)
            rpm = rp * resampled_profile_p[m]  # modulate radius by parallel profile
            a = phase + dA * m
            x = rpm * cos(a)
            y = rpm * sin(a)
            verts.append([x, y, z])

        add_verts(verts)

    return vert_list


def make_edges(P, M, separate):
    """
    Generate the cylinder edges for the given parameters
        P : number of parallels (= number of points in a meridian)
        M : number of meridians (= number of points in a parallel)
        separate: split the parallels into separate edge lists
    """
    edge_list = []

    if separate:  # replicate edges in one parallel for every meridian point
        edge_list = [get_edge_loop(M)] * P
    else:
        add_edge = edge_list.append
        # generate PARALLELS edges (close paths)
        for i in range(P):  # for every point on a meridian
            for j in range(M - 1):  # for every point on a parallel (minus last)
                add_edge([i * M + j, i * M + j + 1])
            add_edge([(i + 1) * M - 1, i * M])  # close the path

        # generate MERIDIANS edges (open paths)
        for j in range(M):  # for every point on a parallel
            for i in range(P - 1):  # for every point on a meridian (minus last)
                add_edge([i * M + j, (i + 1) * M + j])

    return edge_list


def make_polys(P, M, cap_bottom, cap_top, separate):
    """
    Generate the cylinder polygons for the given parameters
        P : number of parallels (= number of points in a meridian)
        M : number of meridians (= number of points in a parallel)
        cap_bottom : turn on/off the bottom cap generation
        cap_top    : turn on/off the top cap generation
        separate: split the parallels into separate poly lists
    """
    poly_list = []

    if separate:
        poly_list = [[list(range(M))]] * P
    else:
        add_poly = poly_list.append
        for i in range(P - 1):
            for j in range(M - 1):
                add_poly([i * M + j, i * M + j + 1, (i + 1) * M + j + 1, (i + 1) * M + j])
            add_poly([(i + 1) * M - 1, i * M, (i + 1) * M, (i + 2) * M - 1])

        if cap_bottom:
            cap = [j for j in reversed(range(M))]
            add_poly(cap)

        if cap_top:
            offset = (P - 1) * M
            cap = [offset + j for j in range(M)]
            add_poly(cap)

    return poly_list


class SvCylinderNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Cylinder, Tube
    Tooltip: Generate cylinder based meshes
    """
    bl_idname = 'SvCylinderNodeMK2'
    bl_label = 'Cylinder'
    bl_icon = 'MESH_CYLINDER'

    def update_angles(self, context):
        """ Convert angle values to selected angle units """
        if self.last_angle_units == "RAD":
            if self.angle_units == "RAD":
                au = 1.0  # RAD -> RAD
            elif self.angle_units == "DEG":
                au = 180.0 / pi  # RAD -> DEG
            elif self.angle_units == "UNI":
                au = 0.5 / pi  # RAD -> UNI

        elif self.last_angle_units == "DEG":
            if self.angle_units == "RAD":
                au = pi / 180  # DEG -> RAD
            elif self.angle_units == "DEG":
                au = 1.0  # DEG -> DEG
            elif self.angle_units == "UNI":
                au = 1.0 / 360  # DEG -> UNI

        elif self.last_angle_units == "UNI":
            if self.angle_units == "RAD":
                au = 2 * pi  # UNI -> RAD
            elif self.angle_units == "DEG":
                au = 360  # UNI -> DEG
            elif self.angle_units == "UNI":
                au = 1.0  # UNI -> UNI

        self.last_angle_units = self.angle_units

        self.updating = True  # inhibit update calls

        self.twist = au * self.twist  # convert to current angle units
        self.phase = au * self.phase  # convert to current angle units

        self.updating = False
        updateNode(self, context)

    def update_cylinder(self, context):
        if self.updating:
            return

        updateNode(self, context)

    angle_units: EnumProperty(
        name="Angle Units", description="Angle units (radians/degrees/unities)",
        default="RAD", items=angle_unit_items, update=update_angles)

    last_angle_units: EnumProperty(
        name="Last Angle Units", description="Last angle units (radians/degrees/unities)",
        default="RAD", items=angle_unit_items)  # used for updates when changing angle units

    radius_t: FloatProperty(
        name='Radius T', description="Top radius",
        default=1.0, update=updateNode)

    radius_b: FloatProperty(
        name='Radius B', description="Bottom radius",
        default=1.0, update=updateNode)

    parallels: IntProperty(
        name='Parallels', description="Number of parallels",
        default=2, min=2, update=updateNode)

    meridians: IntProperty(
        name='Meridians', description="Number of meridians",
        default=32, min=3, update=updateNode)

    height: FloatProperty(
        name='Height', description="The height of the cylinder",
        default=2.0, update=updateNode)

    twist: FloatProperty(
        name='Twist', description="The twist of the cylinder",
        default=0.0, update=update_cylinder)

    phase: FloatProperty(
        name='Phase', description="The phase of the cylinder",
        default=0.0, update=update_cylinder)

    scale: FloatProperty(
        name='Scale', description="The scale of the cylinder",
        default=1.0, update=updateNode)

    cap_bottom: BoolProperty(
        name='Cap Bottom', description="Generate bottom cap",
        default=True, update=updateNode)

    cap_top: BoolProperty(
        name='Cap Top', description="Generate top cap",
        default=True, update=updateNode)

    separate: BoolProperty(
        name='Separate', description='Separate UV coords',
        default=False, update=updateNode)

    center: BoolProperty(
        name='Center', description='Center cylinder around origin',
        default=True, update=updateNode)

    cyclic: BoolProperty(
        name='Cyclic', description='Parallels profile is cyclic',
        default=True, update=updateNode)

    updating: BoolProperty(
        name="Updating", description="Flag to inhibit updating", default=False)

    def migrate_from(self, old_node):
        self.separate = old_node.Separate
        self.cap_bottom = old_node.cap_
        self.cap_top = old_node.cap_
        self.center = False
        self.parallels = old_node.subd_ + 2

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "RadiusT").prop_name = 'radius_t'
        self.inputs.new('SvStringsSocket', "RadiusB").prop_name = 'radius_b'
        self.inputs.new('SvStringsSocket', "Parallels").prop_name = 'parallels'
        self.inputs.new('SvStringsSocket', "Meridians").prop_name = 'meridians'
        self.inputs.new('SvStringsSocket', "Height").prop_name = 'height'
        self.inputs.new('SvStringsSocket', "Twist").prop_name = 'twist'
        self.inputs.new('SvStringsSocket', "Phase").prop_name = 'phase'
        self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('SvStringsSocket', "Parallels Profile")
        self.inputs.new('SvStringsSocket', "Meridians Profile")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(self, "cap_bottom", text="Cap B", toggle=True)
        row.prop(self, "cap_top", text="Cap T", toggle=True)
        row = column.row(align=True)
        row.prop(self, "separate", toggle=True)
        row.prop(self, "center", toggle=True)
        row = layout.row(align=True)
        row.prop(self, "angle_units", expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "cyclic", toggle=True)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs

        # read inputs
        input_rt = inputs["RadiusT"].sv_get()[0]
        input_rb = inputs["RadiusB"].sv_get()[0]
        input_np = inputs["Parallels"].sv_get()[0]
        input_nm = inputs["Meridians"].sv_get()[0]
        input_h = inputs["Height"].sv_get()[0]
        input_t = inputs["Twist"].sv_get()[0]
        input_ph = inputs["Phase"].sv_get()[0]
        input_s = inputs["Scale"].sv_get()[0]

        profile_p = inputs["Parallels Profile"].sv_get(default=[[]])[0]
        profile_m = inputs["Meridians Profile"].sv_get(default=[[]])[0]

        # sanitize inputs
        input_np = list(map(lambda n: max(2, n), input_np))
        input_nm = list(map(lambda m: max(3, m), input_nm))

        params = match_long_repeat([input_rt, input_rb,
                                    input_np, input_nm,
                                    input_h, input_t,
                                    input_ph, input_s])

        flags = [self.separate, self.center, self.cyclic]

        au = angle_conversion[self.angle_units] # angle conversion to radians

        verts_output_linked = self.outputs['Vertices'].is_linked
        edges_output_linked = self.outputs['Edges'].is_linked
        polys_output_linked = self.outputs['Polygons'].is_linked

        verts_list = []
        edges_list = []
        polys_list = []
        for rt, rb, np, nm, h, t, ph, s in zip(*params):
            if verts_output_linked:
                verts = make_verts(rt, rb, np, nm, h, t * au, ph * au, s, profile_p, profile_m, flags)
                verts_list.append(verts)
            if edges_output_linked:
                edges = make_edges(np, nm, self.separate)
                edges_list.append(edges)
            if polys_output_linked:
                polys = make_polys(np, nm, self.cap_bottom, self.cap_top, self.separate)
                polys_list.append(polys)

        # outputs
        if verts_output_linked:
            self.outputs['Vertices'].sv_set(verts_list)

        if edges_output_linked:
            self.outputs['Edges'].sv_set(edges_list)

        if polys_output_linked:
            self.outputs['Polygons'].sv_set(polys_list)


def register():
    bpy.utils.register_class(SvCylinderNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvCylinderNodeMK2)
