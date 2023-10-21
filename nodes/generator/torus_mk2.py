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
from sverchok.data_structure import updateNode, list_match_modes, list_match_func
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper

import numpy as np

epsilon = 1e-10  # used to avoid division by zero

def torus_verts(R, r, N1, N2, rPhase, sPhase, rExponent, sExponent, sTwist, Separate, normals_is_linked):
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
    # angle increments (cached outside of the loop for performance)
    da1 = 2 * pi / N1
    da2 = 2 * pi / N2

    n1_i = np.arange(N1, dtype=np.int16)
    _n1 = np.repeat( [np.array(n1_i)], N2, axis = 0).T        # index n1
    n2_i = np.arange(N2, dtype=np.int16)
    _n2          = np.repeat( [np.array(n2_i)], N1, axis = 0) # index n2
    # revolution angle
    _theta       = _n1 * da1 + rPhase
    _sin_theta   = np.sin(_theta)
    _cos_theta   = np.cos(_theta)
    _twist_angle = da2 * _n1 / N1 * sTwist
    _phi         = da2 * _n2 + sPhase + _twist_angle
    _sin_phi     = np.sin(_phi)
    _cos_phi     = np.cos(_phi)
    if rExponent==1:
        _pow_sin_theta = _sin_theta
        _pow_cos_theta = _cos_theta
    elif rExponent==0:
        _pow_sin_theta = np.where(_sin_theta>=0, 1, -1)
        _pow_cos_theta = np.where(_cos_theta>=0, 1, -1)
    else:
        _pow_sin_theta = np.power(np.abs(_sin_theta), rExponent) * np.where(_sin_theta>=0, 1, -1)
        _pow_cos_theta = np.power(np.abs(_cos_theta), rExponent) * np.where(_cos_theta>=0, 1, -1)
    
    _cx = R * _cos_theta  # torus tube center
    _cy = R * _sin_theta  # torus tube center
    
    if sExponent==1:
        _pow_sin_phi = _sin_phi
        _pow_cos_phi = _cos_phi
    elif sExponent==0:
        _pow_sin_phi = np.where(_sin_phi>=0, 1, -1)
        _pow_cos_phi = np.where(_cos_phi>=0, 1, -1)
    else:
        _pow_sin_phi = np.power(np.abs(_sin_phi), sExponent) * np.where(_sin_phi>=0, 1, -1)
        _pow_cos_phi = np.power(np.abs(_cos_phi), sExponent) * np.where(_cos_phi>=0, 1, -1)

    # verices coordinates
    _x = (R + r * _pow_cos_phi) * _pow_cos_theta
    _y = (R + r * _pow_cos_phi) * _pow_sin_theta
    _z = r * _pow_sin_phi

    _verts = np.dstack( (_x, _y, _z) )
    _verts = _verts.reshape(-1,3)
    if Separate:
        # TODO: property do not work. Noting visible
        _verts = np.array(np.split(_verts, N1))
    _list_verts = _verts.tolist()

    _list_norms = []
    if normals_is_linked:
        _norm = np.dstack( (_x - _cx, _y - _cy, _z) )
        _list_norms = _norm.reshape(-1,3).tolist()

    return _list_verts, _list_norms


def torus_edges(N1, N2, t):
    '''
        N1 : major sections - number of revolution sections around the torus center
        N2 : minor sections - number of spin sections around the torus tube
        t  : spin twist - number of twists (start-end vertex shift)
    '''

    steps = np.arange(0, N1*N2)
    arr_verts = np.array(np.split(steps, N1))

    arr_verts   = np.vstack( (arr_verts, np.roll(arr_verts[:1], -t) ) ) # append first row to bottom to vertically circle with twist
    arr_verts   = np.hstack( (arr_verts, np.array([arr_verts[:,0]]).T ) ) # append first row to bottom to horizontal circle
    hspin_edges = np.dstack( (arr_verts[:N1,:N2], arr_verts[ :N1  ,1:N2+1] ))
    vspin_edges = np.dstack( (arr_verts[:N1,:N2], arr_verts[1:N1+1, :N2] ))
    hs_edges = np.concatenate( (hspin_edges,  vspin_edges ))
    hs_edges = np.concatenate( np.concatenate( (hspin_edges,  vspin_edges ), axis=0), axis=0) # remove exis

    hs_edges_list = hs_edges.tolist()
    return hs_edges_list

def torus_polygons(N1, N2, t):
    '''
        N1 : major sections - number of revolution sections around the torus center
        N2 : minor sections - number of spin sections around the torus tube
        t  : spin twist - number of twists (start-end vertex shift)
    '''
    arr_faces = np.zeros((N1, N2, 4), 'i' )

    steps = np.arange(0, N1*N2)
    arr_verts = np.array(np.split(steps, N1))
    arr_verts = np.vstack( (arr_verts, np.roll(arr_verts[:1], -t) ) ) # append first row to bottom to vertically circle
    arr_verts = np.hstack( (arr_verts, np.array([arr_verts[:,0]]).T ) ) # append first column to right to horizontal circle
    
    arr_faces[:, :, 0] = arr_verts[ :-1,  :-1]
    arr_faces[:, :, 1] = arr_verts[1:  ,  :-1]
    arr_faces[:, :, 2] = arr_verts[1:  , 1:  ]
    arr_faces[:, :, 3] = arr_verts[ :-1, 1:  ]
    hs_faces = arr_faces.reshape(-1,4) # remove exis
    hs_edges_list = hs_faces.tolist()

    return hs_edges_list



class SvTorusNodeMK2(SverchCustomTreeNode, bpy.types.Node, SvAngleHelper):
    """
    Triggers: Torus, Donut
    Tooltip: Generate toroidal meshes. [default]\n\tDims [R:r]/eR:iR\n\tMajor/Minor Radius: [1.0/.25]\n\tRevolution Sections: [32]\n\tSpin Sections: [16]\n\tRevolution/Spin Phase: [0]\n\tRevolution/Spin Exponent: [1.0]\n\tSpin Twist[0]
    """
    bl_idname = 'SvTorusNodeMK2'
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

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
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
        layout.prop(self, "list_match")

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
            input_RR, input_rr = list_match_func[self.list_match]([input_RR, input_rr])
            input_R = list(map(lambda x, y: (x + y) * 0.5, input_RR, input_rr))
            input_r = list(map(lambda x, y: (x - y) * 0.5, input_RR, input_rr))
        else:  # values already given as MAJOR/MINOR radii
            input_R = input_RR
            input_r = input_rr

        parameters = list_match_func[self.list_match]([input_R, input_r,
                                        input_n1, input_n2,
                                        input_rP, input_sP,
                                        input_rE, input_sE,
                                        input_sT])

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        if self.outputs['Vertices'].is_linked or self.outputs['Normals'].is_linked:
            verts_list = []
            norms_list = []
            verts_cache = dict()
            normals_is_linked = self.outputs['Normals'].is_linked
            for R, r, n1, n2, rP, sP, rE, sE, sT in zip(*parameters):
                if (R, r, n1, n2, rP, sP, rE, sE, sT) in verts_cache:
                    verts, norms = verts_cache[(R, r, n1, n2, rP, sP, rE, sE, sT)]
                else:
                    verts, norms = verts_cache[(R, r, n1, n2, rP, sP, rE, sE, sT)] = torus_verts(R, r, n1, n2, rP * au, sP * au, rE, sE, sT, self.Separate, normals_is_linked)
                verts_list.append(verts)
                if normals_is_linked:
                    norms_list.append(norms)
            verts_cache.clear()
            self.outputs['Vertices'].sv_set(verts_list)
            if normals_is_linked:
                self.outputs['Normals'].sv_set(norms_list)

        if self.outputs['Edges'].is_linked:
            edges_list = []
            edges_cache = dict()
            for _, _, n1, n2, _, _, _, _, sT in zip(*parameters):
                if (n1, n2, sT) in edges_cache:
                    edges = edges_cache[(n1, n2, sT)]
                else:
                    edges = edges_cache[(n1, n2, sT)] = torus_edges(n1, n2, sT)
                edges_list.append(edges)
            edges_cache.clear()
            self.outputs['Edges'].sv_set(edges_list)

        if self.outputs['Polygons'].is_linked:
            polys_list = []
            polys_cache = dict()
            for _, _, n1, n2, _, _, _, _, sT in zip(*parameters):
                if (n1, n2, sT) in polys_cache:
                    polys = polys_cache[(n1, n2, sT)]
                else:
                    polys = polys_cache[(n1, n2, sT)] = torus_polygons(n1, n2, sT)
                polys_list.append(polys)
            polys_cache.clear()
            self.outputs['Polygons'].sv_set(polys_list)


def register():
    bpy.utils.register_class(SvTorusNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvTorusNodeMK2)
