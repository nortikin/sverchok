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
from bpy.props import BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode)
from sverchok.utils.geom import CubicSpline

from math import sin, cos, pi, sqrt

import numpy as np


def get_resample_profile(profile, samples, cycle):
    ''' Resample 1D array '''
    N = len(profile)
    v = [[n / (N - 1), p, 0] for n, p in enumerate(profile)]
    samples_array = np.array(samples).clip(0, 1)
    spline = CubicSpline(v, metric="POINTS", is_cyclic=cycle)
    out = spline.eval(samples_array)
    verts = out.tolist()

    resampled_profile = [v[1] for v in verts]

    return resampled_profile


def cylinder_verts(rt, rb, np, nm, h, t, ph, s, profile_p, profile_m, flags):
    """
    Generate cylinder vertices for the given parameters
        rt : top radius
        rb : bottom radius
        np : number of parallels
        nm : number of meridians
        h  : height
        t  : twist from bottom to top
        ph : phase
        s  : scale
    """
    separate, center, cyclic = flags

    rt = rt * s
    rb = rb * s
    h = h * s

    # resample PARALLELS profile
    resample_p = [m / nm for m in range(nm + 1)]
    resampled_profile_p = get_resample_profile(profile_p, resample_p, cyclic)
    # resample MERIDIANS profile
    resample_m = [p / np for p in range(np + 1)]
    resampled_profile_m = get_resample_profile(profile_m, resample_m, False)

    dA = 2.0 * pi / (nm)  # angle increment
    dH = h / (np - 1)  # height increment
    dT = t / (np - 1)  # twist increment
    dZ = - h / 2 if center else 0  # center offset

    vert_list = []
    addVerts = vert_list.append if separate else vert_list.extend
    for p in range(np):
        f = p / (np - 1)  # interpolation factor between rb and rt
        r = (rb * (1 - f) + rt * f)
        rp = r * resampled_profile_m[p]  # modulate radius by meridian profile
        z = dZ + dH * p
        phase = ph + dT * p  # paralle's total phase (phase + delta twist)

        verts = []
        for m in range(nm):
            rpm = rp * resampled_profile_p[m]  # modulate radius by parallel profile

            a = phase + dA * m
            x = rpm * cos(a)
            y = rpm * sin(a)
            verts.append([x, y, z])

        addVerts(verts)

    return vert_list


def cylinder_edges(P, M):
    """
    Generate cylinder edges for the given parameters
        P : number of parallels
        M : number of meridians
    """
    edge_list = []

    # generate PARALLELS edges (close loops)
    for i in range(P):
        for j in range(M - 1):
            edge_list.append([i * M + j, i * M + j + 1])
        edge_list.append([i * M + M - 1, i * M])  # close the loop

    # generate MERIDIANS edges
    for j in range(M):
        for i in range(P - 1):
            edge_list.append([i * M + j, (i + 1) * M + j])

    return edge_list


def cylinder_polys(P, M, cap_bottom, cap_top):
    """
    Generate cylinder polygons for the given parameters
        P : number of parallels
        M : number of meridians
    """
    poly_list = []

    for i in range(P - 1):
        for j in range(M - 1):
            poly_list.append([i * M + j, i * M + j + 1, (i + 1) * M + j + 1, (i + 1) * M + j])
        poly_list.append([(i + 1) * M - 1, i * M, (i + 1) * M, (i + 2) * M - 1])

    if cap_bottom:
        cap = []
        for i in reversed(range(M)):
            cap.append(i)
        poly_list.append(cap)

    if cap_top:
        cap = []
        for i in range(M):
            cap.append((P - 1) * M + i)
        poly_list.append(cap)

    return poly_list


class SvCylinderNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Cylinder '''
    bl_idname = 'SvCylinderNodeMK2'
    bl_label = 'Cylinder MK2'
    bl_icon = 'MESH_CYLINDER'

    radius_t = FloatProperty(
        name='Radius T', description="Top radius",
        default=1.0, update=updateNode)

    radius_b = FloatProperty(
        name='Radius B', description="Bottom radius",
        default=1.0, update=updateNode)

    parallels = IntProperty(
        name='Parallels', description="Number of parallels",
        default=2, min=2, update=updateNode)

    meridians = IntProperty(
        name='Meridians', description="Number of meridians",
        default=32, min=3, update=updateNode)

    height = FloatProperty(
        name='Height', description="The height of the cylinder",
        default=2.0, update=updateNode)

    twist = FloatProperty(
        name='Twist', description="The twist of the cylinder",
        default=0.0, update=updateNode)

    phase = FloatProperty(
        name='Phase', description="The phase of the cylinder",
        default=0.0, update=updateNode)

    scale = FloatProperty(
        name='Scale', description="The scale of the cylinder",
        default=1.0, update=updateNode)

    cap_bottom = BoolProperty(
        name='Cap Bottom', description="Generate bottom cap",
        default=True, update=updateNode)

    cap_top = BoolProperty(
        name='Cap Top', description="Generate top cap",
        default=True, update=updateNode)

    separate = BoolProperty(
        name='Separate', description='Separate UV coords',
        default=False, update=updateNode)

    center = BoolProperty(
        name='Center', description='Center cylinder around origin',
        default=True, update=updateNode)

    cyclic = BoolProperty(
        name='Cyclic', description='Parallels profile is cyclic',
        default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "RadiusT").prop_name = 'radius_t'
        self.inputs.new('StringsSocket', "RadiusB").prop_name = 'radius_b'
        self.inputs.new('StringsSocket', "Parallels").prop_name = 'parallels'
        self.inputs.new('StringsSocket', "Meridians").prop_name = 'meridians'
        self.inputs.new('StringsSocket', "Height").prop_name = 'height'
        self.inputs.new('StringsSocket', "Twist").prop_name = 'twist'
        self.inputs.new('StringsSocket', "Phase").prop_name = 'phase'
        self.inputs.new('StringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('StringsSocket', "Parallels Profile")
        self.inputs.new('StringsSocket', "Meridians Profile")

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")

    def draw_buttons(self, context, layout):
        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(self, "cap_bottom", text="Cap B", toggle=True)
        row.prop(self, "cap_top", text="Cap T", toggle=True)
        row = column.row(align=True)
        row.prop(self, "separate", toggle=True)
        row.prop(self, "center", toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "cyclic", toggle=True)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs

        # read inputs
        input_RT = inputs["RadiusT"].sv_get()[0]
        input_RB = inputs["RadiusB"].sv_get()[0]
        input_NP = inputs["Parallels"].sv_get()[0]
        input_NM = inputs["Meridians"].sv_get()[0]
        input_H = inputs["Height"].sv_get()[0]
        input_T = inputs["Twist"].sv_get()[0]
        input_PH = inputs["Phase"].sv_get()[0]
        input_S = inputs["Scale"].sv_get()[0]

        profile_p = inputs["Parallels Profile"].sv_get(default=[[1, 1]])[0]
        profile_m = inputs["Meridians Profile"].sv_get(default=[[1, 1]])[0]

        # sanitize inputs
        input_NP = list(map(lambda n: max(2, n), input_NP))
        input_NM = list(map(lambda m: max(3, m), input_NM))

        params = match_long_repeat([input_RT, input_RB,
                                    input_NP, input_NM,
                                    input_H, input_T,
                                    input_PH, input_S])

        flags = [self.separate, self.center, self.cyclic]

        verts_list = []
        edges_list = []
        polys_list = []
        for rt, rb, np, nm, h, t, ph, s in zip(*params):
            verts = cylinder_verts(rt, rb, np, nm, h, t, ph, s, profile_p, profile_m, flags)
            edges = cylinder_edges(np, nm)
            polys = cylinder_polys(np, nm, self.cap_bottom, self.cap_top)
            verts_list.append(verts)
            edges_list.append(edges)
            polys_list.append(polys)

        # outputs
        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(verts_list)

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(edges_list)

        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(polys_list)


def register():
    bpy.utils.register_class(SvCylinderNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvCylinderNodeMK2)
