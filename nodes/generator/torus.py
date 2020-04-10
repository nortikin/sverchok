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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from math import sin, cos, pi

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper

def sign(x): return 1 if x >= 0 else -1

epsilon = 1e-10  # used to avoid division by zero


def torus_verts(R, r, N1, N2, rPhase, sPhase, rExponent, sExponent, sTwist, Separate):
    '''
        R         : major radius
        r         : minor radius
        N1        : revolution sections around the torus center
        N2        : spin sections around the torus tube
        rPhase    : revolution phase
        sPhase    : spin phase
        rExponent : revolution exponent
        sExponent : spin exponent
        sTwist    : spin twist
    '''
    list_verts = []
    list_norms = []

    # angle increments (cached outside of the loop for performance)
    da1 = 2 * pi / N1
    da2 = 2 * pi / N2

    for n1 in range(N1):
        a1 = n1 * da1
        theta = a1 + rPhase  # revolution angle
        sin_theta = sin(theta)  # cached for performance
        cos_theta = cos(theta)  # cached for performance

        twist_angle = da2 * n1 / N1 * sTwist

        loop_verts = []
        add_vert = loop_verts.append
        for n2 in range(N2):
            a2 = n2 * da2
            phi = a2 + sPhase + twist_angle  # spin angle + twist
            sin_phi = sin(phi)  # cached for performance
            cos_phi = cos(phi)  # cached for performance

            pow_cos_phi = pow(abs(cos_phi), sExponent) * sign(cos_phi)
            pow_sin_phi = pow(abs(sin_phi), sExponent) * sign(sin_phi)
            pow_cos_theta = pow(abs(cos_theta), rExponent) * sign(cos_theta)
            pow_sin_theta = pow(abs(sin_theta), rExponent) * sign(sin_theta)

            x = (R + r * pow_cos_phi) * pow_cos_theta
            y = (R + r * pow_cos_phi) * pow_sin_theta
            z = r * pow_sin_phi

            # append vertex to loop
            add_vert([x, y, z])

            # append normal
            cx = R * cos_theta  # torus tube center
            cy = R * sin_theta  # torus tube center
            norm = [x - cx, y - cy, z]
            list_norms.append(norm)

        if Separate:
            list_verts.append(loop_verts)
        else:
            list_verts.extend(loop_verts)

    return list_verts, list_norms


def torus_edges(N1, N2, t):
    '''
        N1 : major sections - number of revolution sections around the torus center
        N2 : minor sections - number of spin sections around the torus tube
        t  : spin twist - number of twists (start-end vertex shift)
    '''
    list_edges = []
    add_edge = list_edges.append
    # spin loop EDGES : around the torus tube
    for n1 in range(N1):
        for n2 in range(N2 - 1):
            add_edge([N2 * n1 + n2, N2 * n1 + n2 + 1])
        add_edge([N2 * n1 + N2 - 1, N2 * n1 + 0])

    # revolution loop EDGES : around the torus center
    for n1 in range(N1 - 1):
        for n2 in range(N2):
            add_edge([N2 * n1 + n2, N2 * (n1 + 1) + n2])
    for n2 in range(N2):
        add_edge([N2 * (N1 - 1) + n2, N2 * 0 + (n2 + t) % N2])

    return list_edges


def torus_polygons(N1, N2, t):
    '''
        N1 : major sections - number of revolution sections around the torus center
        N2 : minor sections - number of spin sections around the torus tube
        t  : spin twist - number of twists (start-end vertex shift)
    '''
    list_polys = []
    add_poly = list_polys.append
    for n1 in range(N1 - 1):
        for n2 in range(N2 - 1):
            add_poly([N2 * n1 + n2, N2 * (n1 + 1) + n2, N2 * (n1 + 1) + n2 + 1, N2 * n1 + n2 + 1])
        add_poly([N2 * n1 + N2 - 1, N2 * (n1 + 1) + N2 - 1, N2 * (n1 + 1) + 0, N2 * n1 + 0])
    for n2 in range(N2 - 1):
        add_poly([N2 * (N1 - 1) + n2, N2 * 0 + (n2 + t) % N2, N2 * 0 + (n2 + 1 + t) % N2, N2 * (N1 - 1) + n2 + 1])
    add_poly([N2 * (N1 - 1) + N2 - 1, N2 * 0 + (N2 - 1 + t) % N2, N2 * 0 + (0 + t) % N2, N2 * (N1 - 1) + 0])

    return list_polys


class SvTorusNode(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Torus, Donut
    Tooltip: Generate toroidal meshes
    """
    bl_idname = 'SvTorusNode'
    bl_label = 'Torus'
    bl_icon = 'MESH_TORUS'

    def update_mode(self, context):
        # switch radii input sockets (R,r) <=> (eR,iR)
        if self.mode == 'EXT_INT':
            self.inputs['R'].prop_name = "torus_eR"
            self.inputs['r'].prop_name = "torus_iR"
        else:
            self.inputs['R'].prop_name = "torus_R"
            self.inputs['r'].prop_name = "torus_r"

        updateNode(self, context)

    # keep the equivalent radii pair in sync (eR,iR) => (R,r)
    def external_internal_radii_changed(self, context):
        if self.mode == "EXT_INT":
            self.torus_R = (self.torus_eR + self.torus_iR) * 0.5
            self.torus_r = (self.torus_eR - self.torus_iR) * 0.5
            updateNode(self, context)

    # keep the equivalent radii pair in sync (R,r) => (eR,iR)
    def major_minor_radii_changed(self, context):
        if self.mode == "MAJOR_MINOR":
            self.torus_eR = self.torus_R + self.torus_r
            self.torus_iR = self.torus_R - self.torus_r
            updateNode(self, context)

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.torus_rP = self.torus_rP * au
        self.torus_sP = self.torus_sP * au

    # TORUS DIMENSIONS options
    mode: EnumProperty(
        name="Torus Dimensions",
        items=(("MAJOR_MINOR", "R : r",
                "Use the Major/Minor radii for torus dimensions."),
               ("EXT_INT", "eR : iR",
                "Use the Exterior/Interior radii for torus dimensions.")),
        update=update_mode)

    torus_R: FloatProperty(
        name="Major Radius",
        min=0.00, max=100.0,
        default=1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Radius from the torus origin to the center of the cross section",
        update=major_minor_radii_changed)

    torus_r: FloatProperty(
        name="Minor Radius",
        min=0.00, max=100.0,
        default=.25,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Radius of the torus' cross section",
        update=major_minor_radii_changed)

    torus_iR: FloatProperty(
        name="Interior Radius",
        min=0.00, max=100.0,
        default=.75,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Interior radius of the torus (closest to the torus center)",
        update=external_internal_radii_changed)

    torus_eR: FloatProperty(
        name="Exterior Radius",
        min=0.00, max=100.0,
        default=1.25,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Exterior radius of the torus (farthest from the torus center)",
        update=external_internal_radii_changed)

    # TORUS RESOLUTION options
    torus_n1: IntProperty(
        name="Revolution Sections",
        default=32,
        min=3, soft_min=3,
        description="Number of sections around the torus center",
        update=updateNode)

    torus_n2: IntProperty(
        name="Spin Sections",
        default=16,
        min=3, soft_min=3,
        description="Number of sections around the torus tube",
        update=updateNode)

    # TORUS Phase Options
    torus_rP: FloatProperty(
        name="Revolution Phase",
        default=0.0,
        description="Phase the revolution sections by this angle amount",
        update=SvAngleHelper.update_angle)

    torus_sP: FloatProperty(
        name="Spin Phase",
        default=0.0,
        description="Phase the spin sections by this angle amount",
        update=SvAngleHelper.update_angle)

    torus_rE: FloatProperty(
        name="Revolution Exponent",
        default=1.0, min = 0.0,
        description="Exponent of the revolution profile",
        update=updateNode)

    torus_sE: FloatProperty(
        name="Spin Exponent",
        default=1.0, min = 0.0,
        description="Exponent of the spin profile",
        update=updateNode)

    torus_sT: IntProperty(
        name="Spin Twist",
        default=0,
        description="Twist the spin sections by this number of increments",
        update=updateNode)

    # OTHER options
    Separate: BoolProperty(
        name='Separate',
        description='Separate UV coords',
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.width = 175
        self.inputs.new('SvStringsSocket', "R").prop_name = 'torus_R'
        self.inputs.new('SvStringsSocket', "r").prop_name = 'torus_r'
        self.inputs.new('SvStringsSocket', "n1").prop_name = 'torus_n1'
        self.inputs.new('SvStringsSocket', "n2").prop_name = 'torus_n2'
        self.inputs.new('SvStringsSocket', "rP").prop_name = 'torus_rP'
        self.inputs.new('SvStringsSocket', "sP").prop_name = 'torus_sP'
        self.inputs.new('SvStringsSocket', "rE").prop_name = 'torus_rE'
        self.inputs.new('SvStringsSocket', "sE").prop_name = 'torus_sE'
        self.inputs.new('SvStringsSocket', "sT").prop_name = 'torus_sT'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket',  "Edges")
        self.outputs.new('SvStringsSocket',  "Polygons")
        self.outputs.new('SvVerticesSocket', "Normals")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate")
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_angle_units_buttons(context, layout)

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_RR = self.inputs["R"].sv_get()[0]   # list of MAJOR or EXTERIOR radii
        input_rr = self.inputs["r"].sv_get()[0]   # list of MINOR or INTERIOR radii
        input_n1 = self.inputs["n1"].sv_get()[0]  # list of REVOLUTION sections
        input_n2 = self.inputs["n2"].sv_get()[0]  # list of SPIN sections
        input_rP = self.inputs["rP"].sv_get()[0]  # list of REVOLUTION phases
        input_sP = self.inputs["sP"].sv_get()[0]  # list of SPIN phases
        input_rE = self.inputs["rE"].sv_get()[0]  # list of REVOLUTION exponents
        input_sE = self.inputs["sE"].sv_get()[0]  # list of SPIN exponents
        input_sT = self.inputs["sT"].sv_get()[0]  # list of SPIN twists

        # bound check the list values
        input_RR = list(map(lambda x: max(0, x), input_RR))
        input_rr = list(map(lambda x: max(0, x), input_rr))
        input_n1 = list(map(lambda x: max(3, int(x)), input_n1))
        input_n2 = list(map(lambda x: max(3, int(x)), input_n2))
        input_rE = list(map(lambda x: max(0, x), input_rE))
        input_sE = list(map(lambda x: max(0, x), input_sE))

        # convert input radii values to MAJOR/MINOR, based on selected mode
        if self.mode == 'EXT_INT':
            # convert radii from EXTERIOR/INTERIOR to MAJOR/MINOR
            # (extend radii lists to a matching length before conversion)
            input_RR, input_rr = match_long_repeat([input_RR, input_rr])
            input_R = list(map(lambda x, y: (x + y) * 0.5, input_RR, input_rr))
            input_r = list(map(lambda x, y: (x - y) * 0.5, input_RR, input_rr))
        else:  # values already given as MAJOR/MINOR radii
            input_R = input_RR
            input_r = input_rr

        parameters = match_long_repeat([input_R, input_r,
                                        input_n1, input_n2,
                                        input_rP, input_sP,
                                        input_rE, input_sE,
                                        input_sT])

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        if self.outputs['Vertices'].is_linked or self.outputs['Normals'].is_linked:
            verts_list = []
            norms_list = []
            for R, r, n1, n2, rP, sP, rE, sE, sT in zip(*parameters):
                verts, norms = torus_verts(R, r, n1, n2, rP * au, sP * au, rE, sE, sT, self.Separate)
                verts_list.append(verts)
                norms_list.append(norms)
            self.outputs['Vertices'].sv_set(verts_list)
            self.outputs['Normals'].sv_set(norms_list)

        if self.outputs['Edges'].is_linked:
            edges_list = []
            for _, _, n1, n2, _, _, _, _, sT in zip(*parameters):
                edges = torus_edges(n1, n2, sT)
                edges_list.append(edges)
            self.outputs['Edges'].sv_set(edges_list)

        if self.outputs['Polygons'].is_linked:
            polys_list = []
            for _, _, n1, n2, _, _, _, _, sT in zip(*parameters):
                polys = torus_polygons(n1, n2, sT)
                polys_list.append(polys)
            self.outputs['Polygons'].sv_set(polys_list)


def register():
    bpy.utils.register_class(SvTorusNode)


def unregister():
    bpy.utils.unregister_class(SvTorusNode)
