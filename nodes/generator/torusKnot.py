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

from math import sin, cos, pi, sqrt, radians, gcd
from random import random
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, SvSetSocketAnyType

DEBUG=False

options_plus=True


########################################################################
####################### Knot Definitions ###############################
########################################################################
def Torus_Knot(R, r, p, q, u, v, h, s, rPhase, sPhase, flipP, flipQ, N, linkIndex=0):
    '''
        R         : major radius of the torus
        r         : minor radius of the torus
        p         : number of REVOLUTIONS around the torus hole
        q         : number of SPINS through the torus hole
        u         : p multiplier
        v         : q multiplier
        h         : height (scale along Z)
        s         : scale (radii scale factor)
        rPhase    : user defined REVOLUTION phase
        sPhase    : user defined SPIN phase
        flipP     : flip REVOLUTION direction (P)
        flipQ     : flip SPIN direction (Q)
        N         : number of vertices in the curve (per link)
        linkIndex : link index in a multiple link knot (when q & p are not co-primes)
    '''
    if DEBUG:
        start = time.time()

    # use plus options only when they are enabled
    if not options_plus:
        u = 1
        v = 1
        h = 1
        s = 1

    # scale the radii
    R = R * s
    r = r * s

    # number of decoupled links when (p,q) are NOT co-primes
    links = gcd(p, q)  # = 1 when (p,q) are co-primes

    # parametrized angle increment (cached outside of the loop for performance)
    # NOTE: the total angle is divided by number of decoupled links to ensure
    #       the curve does not overlap with itself when (p,q) are not co-primes
    da = 2*pi/links/(N-1)

    # link phase : each decoupled link is phased equally around the torus center
    # NOTE: linkIndex value is in [0, links-1]
    linkPhase = 2*pi/q * linkIndex  # = 0 when there is just ONE link

    # user defined phasing
    if not options_plus:
        rPhase = 0
        sPhase = 0

    rPhase += linkPhase  # total revolution phase of the current link

    # flip directions ? NOTE: flipping both is equivalent to no flip
    if flipP:
        p *= -1
    if flipQ:
        q *= -1

    # create the list of verts, edges and norms for the current link
    listVerts = []
    listEdges = []
    listNorms = []
    for n in range(N-1):
        # t = 2*pi / links * n/(N-1) with: da = 2*pi/links/(N-1) => t = n * da
        t = n * da
        theta = p*t*u + rPhase  # revolution angle
        phi   = q*t*v + sPhase  # spin angle

        # cache values to improve performance
        sin_theta = sin(theta)
        cos_theta = cos(theta)
        sin_phi = sin(phi)
        cos_phi = cos(phi)

        # compute vertex coordinates
        x = (R + r*cos_phi) * cos_theta
        y = (R + r*cos_phi) * sin_theta
        z = r*sin_phi * h

        # append vertex
        listVerts.append([x, y, z])

        # append edge
        if n != N-2:
            listEdges.append([n, n+1])
        else: # closing the loop
            listEdges.append([n, 0])

        # append normal
        cx = R * cos_theta # torus tube center at theta
        cy = R * sin_theta # torus tube center at theta
        norm = [x-cx, y-cy, z]
        listNorms.append(norm)

    if DEBUG:
        end = time.time()
        print("Torus Link Time: ", end - start)

    return listVerts, listEdges, listNorms


class SvTorusKnotNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Torus Knot '''
    bl_idname = 'SvTorusKnotNode'
    bl_label = 'Torus Knot'
    bl_icon = 'MESH_TORUS'

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
            self.torus_R = (self.torus_eR + self.torus_iR)*0.5
            self.torus_r = (self.torus_eR - self.torus_iR)*0.5
            updateNode(self, context)

    # keep the equivalent radii pair in sync (R,r) => (eR,iR)
    def major_minor_radii_changed(self, context):
        if self.mode == "MAJOR_MINOR":
            self.torus_eR = self.torus_R + self.torus_r
            self.torus_iR = self.torus_R - self.torus_r
            updateNode(self, context)

    # GENERAL options
    options_plus = BoolProperty(
        name="Extra Options",
        default=False,
        description="Show more options (the plus part)",
        update=updateNode)

    # TORUS KNOT Options
    torus_p = IntProperty(
        name="p",
        default=2,
        min=1, soft_min=1,
        description="Number of REVOLUTIONs around the torus hole before closing the knot",
        update=updateNode)

    torus_q = IntProperty(
        name="q",
        default=3,
        min=1, soft_min=1,
        description="Number of SPINs through the torus hole before closing the knot",
        update=updateNode)

    flip_p = BoolProperty(
        name="Flip p",
        default=False,
        description="Flip REVOLUTION direction",
        update=updateNode)

    flip_q = BoolProperty(
        name="Flip q",
        default=False,
        description="Flip SPIN direction",
        update=updateNode)

    multiple_links = BoolProperty(
        name="Multiple Links",
        default=True,
        description="Generate ALL links or just ONE link when q and q are not co-primes",
        update=updateNode)

    torus_u = IntProperty(
        name="p multiplier",
        default=1,
        min=1, soft_min=1,
        description="p multiplier",
        update=updateNode)

    torus_v = IntProperty(
        name="q multiplier",
        default=1,
        min=1, soft_min=1,
        description="q multiplier",
        update=updateNode)

    torus_rP = FloatProperty(
        name="Revolution Phase",
        default=0.0,
        min=0.0, soft_min=0.0,
        description="Phase revolutions by this radian amount",
        update=updateNode)

    torus_sP = FloatProperty(
        name="Spin Phase",
        default=0.0,
        min=0.0, soft_min=0.0,
        description="Phase spins by this radian amount",
        update=updateNode)

    # TORUS DIMENSIONS options
    mode = EnumProperty(
        name="Torus Dimensions",
        items=(("MAJOR_MINOR", "Major/Minor",
                "Use the Major/Minor radii for torus dimensions."),
                ("EXT_INT", "Exterior/Interior",
                "Use the Exterior/Interior radii for torus dimensions.")),
        update=update_mode)

    torus_R = FloatProperty(
        name="Major Radius",
        min=0.00, max=100.0,
        default=1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Radius from the torus origin to the center of the cross section",
        update=major_minor_radii_changed)

    torus_r = FloatProperty(
        name="Minor Radius",
        min=0.00, max=100.0,
        default=.25,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Radius of the torus' cross section",
        update=major_minor_radii_changed)

    torus_iR = FloatProperty(
        name="Interior Radius",
        min=0.00, max=100.0,
        default=.75,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Interior radius of the torus (closest to the torus center)",
        update=external_internal_radii_changed)

    torus_eR = FloatProperty(
        name="Exterior Radius",
        min=0.00, max=100.0,
        default=1.25,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Exterior radius of the torus (farthest from the torus center)",
        update=external_internal_radii_changed)

    torus_s = FloatProperty(
        name="Scale",
        min=0.01, max=100.0,
        default=1.00,
        description="Scale factor to multiply the radii",
        update=updateNode)

    torus_h = FloatProperty(
        name="Height",
        default=1.0,
        min=0.0, max=100.0,
        description="Scale along the local Z axis",
        update=updateNode)

    # CURVE options
    torus_res = IntProperty(
        name="Curve Resolution",
        default=100,
        min=3, soft_min=3,
        description="Number of vertices in the curve (per link)",
        update=updateNode)

    adaptive_resolution = BoolProperty(
        name="Adaptive Resolution",
        default=False,
        description="Auto adjust curve resolution based on TK length",
        update=updateNode)


    def sv_init(self, context):
        self.inputs.new('StringsSocket', "R").prop_name = 'torus_R'
        self.inputs.new('StringsSocket', "r").prop_name = 'torus_r'
        self.inputs.new('StringsSocket', "p").prop_name = 'torus_p'
        self.inputs.new('StringsSocket', "q").prop_name = 'torus_q'
        self.inputs.new('StringsSocket', "n").prop_name = 'torus_res'
        self.inputs.new('StringsSocket', "rP").prop_name = 'torus_rP'
        self.inputs.new('StringsSocket', "sP").prop_name = 'torus_sP'

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket',  "Edges")
        self.outputs.new('VerticesSocket', "Normals")


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


    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)


    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_RR = self.inputs["R"].sv_get()[0]  # list of MAJOR or EXTERIOR radii
        input_rr = self.inputs["r"].sv_get()[0]  # list of MINOR or INTERIOR radii
        input_p  = self.inputs["p"].sv_get()[0]  # list of REVOLUTION turns
        input_q  = self.inputs["q"].sv_get()[0]  # list of SPIN turns
        input_n  = self.inputs["n"].sv_get()[0]  # list of curve resolutions
        input_rP = self.inputs["rP"].sv_get()[0] # list of REVOLUTION phases
        input_sP = self.inputs["sP"].sv_get()[0] # list of SPIN phases

        # convert input radii values to MAJOR/MINOR, based on selected mode
        if self.mode == 'EXT_INT':
            # convert radii from EXTERIOR/INTERIOR to MAJOR/MINOR
            # (extend radii lists to a matching length before conversion)
            input_RR, input_rr = match_long_repeat([input_RR, input_rr])
            input_R = list(map(lambda x,y: (x+y)*0.5, input_RR, input_rr))
            input_r = list(map(lambda x,y: (x-y)*0.5, input_RR, input_rr))
        else: # values already given as MAJOR/MINOR radii
            input_R = input_RR
            input_r = input_rr

        # extra parameters
        u = self.torus_u  # p multiplier
        v = self.torus_v  # q multiplier
        h = self.torus_h  # height (scale along Z)
        s = self.torus_s  # scale (radii scale factor)
        fp = self.flip_p  # flip REVOLUTION direction (P)
        fq = self.flip_q  # flip SPIN direction (Q)

        parameters = match_long_repeat([input_R, input_r, input_p, input_q, input_n, input_rP, input_sP])

        torusVerts = []
        torusEdges = []
        torusNorms = []

        for R, r, p, q, n, rP, sP in zip(*parameters):

            if self.adaptive_resolution:
                # adjust curve resolution automatically based on (p,q,R,r) values
                links = gcd(p, q)
                # get an approximate length of the whole TK curve
                maxTKLen = 2*pi*sqrt(p*p*(R+r)*(R+r) + q*q*r*r)  # upper bound approximation
                minTKLen = 2*pi*sqrt(p*p*(R-r)*(R-r) + q*q*r*r)  # lower bound approximation
                avgTKLen = (minTKLen + maxTKLen)/2  # average approximation
                if DEBUG:
                    print("Approximate average TK length = %.2f" % avgTKLen)
                n = int(max(3, avgTKLen/links * 8))  # x N factor = control points per unit length

            if self.multiple_links:
                links=gcd(p,q)
            else:
                links=1

            for l in range(links):
                verts, edges, norms = Torus_Knot(R,r,p,q,u,v,h,s,rP,sP,fp,fq,n,l)
                torusVerts.append(verts)
                torusEdges.append(edges)
                torusNorms.append(norms)

        self.outputs['Vertices'].sv_set(torusVerts)
        self.outputs['Edges'].sv_set(torusEdges)
        self.outputs['Normals'].sv_set(torusNorms)


def register():
    bpy.utils.register_class(SvTorusKnotNode)


def unregister():
    bpy.utils.unregister_class(SvTorusKnotNode)

if __name__ == '__main__':
    register()
