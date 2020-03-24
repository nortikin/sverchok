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

# This node is based on blender's built-in TorusKnot+ add-on

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from math import sin, cos, pi, sqrt, gcd
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, get_edge_loop


def make_torus_knot(flags, settings, link_index=0):
    '''
        Make a Torus Knot (link)

        flags =
        compute_normals    : compute normal vectors
        compute_tangents   : compute tangent vectors
        normalize_normals  : normalize normal vectors
        normalize_tangents : normalize tangent vectors

        settings =
        R         : major radius of the torus
        r         : minor radius of the torus
        p         : number of REVOLUTIONS around the torus hole
        q         : number of SPINS through the torus hole
        u         : p multiplier
        v         : q multiplier
        h         : height (scale along Z)
        s         : scale (radii scale factor)
        r_phase   : user defined REVOLUTION phase
        s_phase   : user defined SPIN phase
        shift     : shift the points along the curve (0-1)
        flip_p    : flip REVOLUTION direction (P)
        flip_q    : flip SPIN direction (Q)
        N         : number of vertices in the curve (per link)

        link_index : link index in a multiple-link knot (when q & p are not co-primes)
    '''

    compute_normals, compute_tangents, normalize_normals, normalize_tangents = flags
    R, r, p, q, u, v, h, s, r_phase, s_phase, shift, flip_p, flip_q, N = settings

    # scale the radii
    R = R * s
    r = r * s

    # number of decoupled links when (p,q) are NOT co-primes
    links = gcd(p, q)  # = 1 when (p,q) are co-primes

    # parametrized angle increment (cached outside of the loop for performance)
    # NOTE: the total angle is divided by number of decoupled links to ensure
    #       the curve does not overlap with itself when (p,q) are not co-primes
    a = 2 * pi / links
    da = a / N

    # link phase : each decoupled link is phased equally around the torus center
    # NOTE: link_index value is in [0, links-1]
    link_phase = 2 * pi / q * link_index  # = 0 when there is just ONE link

    r_phase += link_phase  # total revolution phase of the current link

    # flip directions ? NOTE: flipping both is equivalent to no flip
    if flip_p:
        p *= -1
    if flip_q:
        q *= -1

    # apply multipliers
    p *= u
    q *= v

    # add the point shift along the curve (shift = [0-1])
    r_phase += 2 * pi * p * shift
    s_phase += 2 * pi * q * shift

    # create the list of verts, edges, normals and tangents for the current link
    verts = []
    edges = []
    norms = []
    tangs = []

    for n in range(N):
        # t = 2*pi / links * n/N with: da = 2*pi/links/N => t = n * da
        t = n * da
        theta = p * t + r_phase  # revolution angle
        phi = q * t + s_phase  # spin angle

        # cache values to improve performance
        sin_theta = sin(theta)
        cos_theta = cos(theta)
        sin_phi = sin(phi)
        cos_phi = cos(phi)

        # compute vertex coordinates
        x = (R + r * cos_phi) * cos_theta
        y = (R + r * cos_phi) * sin_theta
        z = r * sin_phi * h

        # append VERTEX
        verts.append([x, y, z])

        # append NORMAL
        if compute_normals:
            nx = x - R * cos_theta
            ny = y - R * sin_theta
            nz = z
            if normalize_normals:
                nn = sqrt(nx * nx + ny * ny + nz * nz)
                if nn == 0:
                    norm = [nx, ny, nz]
                else:
                    norm = [nx / nn, ny / nn, nz / nn]  # normalize the normal
            else:
                norm = [nx, ny, nz]

            norms.append(norm)

        # append TANGENT
        if compute_tangents:
            qxr, pxr, pxR = [q * r, p * r, p * R]  # cached for performance
            tx = a * (- qxr * sin_phi * cos_theta
                      - pxr * cos_phi * sin_theta
                      - pxR * sin_theta)
            ty = a * (- qxr * sin_phi * sin_theta
                      + pxr * cos_phi * cos_theta
                      + pxR * cos_theta)
            tz = a * qxr * h * cos_phi
            if normalize_tangents:
                tn = sqrt(tx * tx + ty * ty + tz * tz)
                if tn == 0:
                    tang = [tx, ty, tz]
                else:
                    tang = [tx / tn, ty / tn, tz / tn]  # normalize the tangent
            else:
                tang = [tx, ty, tz]

            tangs.append(tang)

    # generate the EDGEs
    edges = get_edge_loop(N)

    return verts, edges, norms, tangs


class SvTorusKnotNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Torus Knot '''
    bl_idname = 'SvTorusKnotNodeMK2'
    bl_label = 'Torus Knot'
    bl_icon = 'MESH_TORUS'
    sv_icon = 'SV_TORUS_KNOT'

    # switch radii input sockets (R,r) <=> (eR,iR)
    def update_mode(self, context):
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

    # TORUS KNOT Options
    torus_p: IntProperty(
        name="p",
        default=2, min=1, soft_min=1,
        description="Number of REVOLUTIONs around the torus hole before closing the knot",
        update=updateNode)

    torus_q: IntProperty(
        name="q",
        default=3, min=1, soft_min=1,
        description="Number of SPINs through the torus hole before closing the knot",
        update=updateNode)

    flip_p: BoolProperty(
        name="Flip p",
        default=False,
        description="Flip REVOLUTION direction",
        update=updateNode)

    flip_q: BoolProperty(
        name="Flip q",
        default=False,
        description="Flip SPIN direction",
        update=updateNode)

    multiple_links: BoolProperty(
        name="Multiple Links",
        default=True,
        description="Generate ALL links or just ONE link when p and q are not co-primes",
        update=updateNode)

    torus_u: IntProperty(
        name="p multiplier",
        default=1, min=1, soft_min=1,
        description="p multiplier",
        update=updateNode)

    torus_v: IntProperty(
        name="q multiplier",
        default=1, min=1, soft_min=1,
        description="q multiplier",
        update=updateNode)

    torus_rP: FloatProperty(
        name="Revolution Phase",
        default=0.0,
        description="Phase the revolutions by this radian amount",
        update=updateNode)

    torus_sP: FloatProperty(
        name="Spin Phase",
        default=0.0,
        description="Phase the spins by this radian amount",
        update=updateNode)

    torus_sh: FloatProperty(
        name="Shift",
        default=0.0,
        description="Shift the points along the curve (0-1)",
        update=updateNode)

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
        default=1.0, min=0.0, soft_min=0.0,
        subtype='DISTANCE', unit='LENGTH',
        description="Radius from the torus origin to the center of the cross section",
        update=major_minor_radii_changed)

    torus_r: FloatProperty(
        name="Minor Radius",
        default=.25, min=0.0, soft_min=0.0,
        subtype='DISTANCE', unit='LENGTH',
        description="Radius of the torus' cross section",
        update=major_minor_radii_changed)

    torus_iR: FloatProperty(
        name="Interior Radius",
        default=.75, min=0.0, soft_min=0.0,
        subtype='DISTANCE', unit='LENGTH',
        description="Interior radius of the torus (closest to the torus center)",
        update=external_internal_radii_changed)

    torus_eR: FloatProperty(
        name="Exterior Radius",
        default=1.25, min=0.0, soft_min=0.0,
        subtype='DISTANCE', unit='LENGTH',
        description="Exterior radius of the torus (farthest from the torus center)",
        update=external_internal_radii_changed)

    torus_s: FloatProperty(
        name="Scale",
        default=1.0, min=0.01,
        description="Scale factor to multiply the radii",
        update=updateNode)

    torus_h: FloatProperty(
        name="Height",
        default=1.0, min=0.0, soft_min=0.0,
        description="Scale along the local Z axis",
        update=updateNode)

    # CURVE options
    torus_res: IntProperty(
        name="Curve Resolution",
        default=100, min=3, soft_min=3,
        description="Number of vertices in the curve (per link)",
        update=updateNode)

    adaptive_resolution: BoolProperty(
        name="Adaptive Resolution",
        default=False,
        description="Auto adjust the curve resolution based on TK length",
        update=updateNode)

    # VECTORS options
    normalize_normals: BoolProperty(
        name="Normalize Normals",
        default=True,
        description="Normalize the normal vectors",
        update=updateNode)

    normalize_tangents: BoolProperty(
        name="Normalize Tangents",
        default=True,
        description="Normalize the tangent vectors",
        update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('SvStringsSocket', "R").prop_name = 'torus_R'
        self.inputs.new('SvStringsSocket', "r").prop_name = 'torus_r'
        self.inputs.new('SvStringsSocket', "p").prop_name = 'torus_p'
        self.inputs.new('SvStringsSocket', "q").prop_name = 'torus_q'
        self.inputs.new('SvStringsSocket', "n").prop_name = 'torus_res'
        self.inputs.new('SvStringsSocket', "rP").prop_name = 'torus_rP'
        self.inputs.new('SvStringsSocket', "sP").prop_name = 'torus_sP'
        self.inputs.new('SvStringsSocket', "sh").prop_name = 'torus_sh'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket',  "Edges")
        self.outputs.new('SvVerticesSocket', "Normals")
        self.outputs.new('SvVerticesSocket', "Tangents")

    def draw_buttons_ext(self, context, layout):
        layout.column().label(text="Curve")
        box = layout.box()
        box.prop(self, 'adaptive_resolution')
        box.prop(self, 'multiple_links')
        layout.column().label(text="Flipping")
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "flip_p")
        row.prop(self, "flip_q")
        layout.column().label(text="Multipliers")
        box = layout.box()
        box.prop(self, "torus_u")
        box.prop(self, "torus_v")
        layout.column().label(text="Geometry")
        box = layout.box()
        box.prop(self, "torus_h")
        box.prop(self, "torus_s")
        layout.column().label(text="Vectors")
        box = layout.box()
        box.prop(self, "normalize_normals")
        box.prop(self, "normalize_tangents")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_RR = inputs["R"].sv_get()[0]  # list of MAJOR or EXTERIOR radii
        input_rr = inputs["r"].sv_get()[0]  # list of MINOR or INTERIOR radii
        input_p = inputs["p"].sv_get()[0]  # list of REVOLUTION turns
        input_q = inputs["q"].sv_get()[0]  # list of SPIN turns
        input_n = inputs["n"].sv_get()[0]  # list of curve resolutions
        input_rP = inputs["rP"].sv_get()[0]  # list of REVOLUTION phases
        input_sP = inputs["sP"].sv_get()[0]  # list of SPIN phases
        input_sh = inputs["sh"].sv_get()[0]  # list of SHIFT values

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

        # extra parameters
        u = self.torus_u  # p multiplier
        v = self.torus_v  # q multiplier
        h = self.torus_h  # height (scale along Z)
        s = self.torus_s  # scale (radii scale factor)
        fp = self.flip_p  # flip REVOLUTION direction (P)
        fq = self.flip_q  # flip SPIN direction (Q)

        # computation flags
        compute_normals = outputs["Normals"].is_linked
        compute_tangents = outputs["Tangents"].is_linked
        normalize_normals = self.normalize_normals
        normalize_tangents = self.normalize_tangents
        flags = [compute_normals, compute_tangents, normalize_normals, normalize_tangents]

        parameters = match_long_repeat([input_R, input_r, input_p, input_q, input_n, input_rP, input_sP, input_sh])

        verts_list = []
        edges_list = []
        norms_list = []
        tangs_list = []

        for R, r, p, q, n, rP, sP, sh in zip(*parameters):

            if self.adaptive_resolution:
                # adjust curve resolution automatically based on (p,q,R,r) values
                links = gcd(p, q)
                # get an approximate length of the whole TK curve [see URL below for details]
                # https://math.stackexchange.com/questions/1523388/tight-approximation-of-a-torus-knot-length
                maxTKLen = 2 * pi * sqrt(p * p * (R + r) * (R + r) + q * q * r * r)  # upper bound approximation
                minTKLen = 2 * pi * sqrt(p * p * (R - r) * (R - r) + q * q * r * r)  # lower bound approximation
                avgTKLen = (minTKLen + maxTKLen) / 2  # average approximation
                n = int(max(3, avgTKLen / links * 10))  # x N factor = control points per unit length

            if self.multiple_links:
                links = gcd(p, q)
            else:
                links = 1

            settings = [R, r, p, q, u, v, h, s, rP, sP, sh, fp, fq, n]  # link settings

            for l in range(links):
                verts, edges, norms, tangs = make_torus_knot(flags, settings, l)
                verts_list.append(verts)
                edges_list.append(edges)
                norms_list.append(norms)
                tangs_list.append(tangs)

        self.outputs['Vertices'].sv_set(verts_list)
        self.outputs['Edges'].sv_set(edges_list)
        self.outputs['Normals'].sv_set(norms_list)
        self.outputs['Tangents'].sv_set(tangs_list)


def register():
    bpy.utils.register_class(SvTorusKnotNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvTorusKnotNodeMK2)
