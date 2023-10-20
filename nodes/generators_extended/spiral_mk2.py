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
import numpy as np

from math import sin, cos, pi, sqrt, exp, atan, log
import re

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, get_edge_list
from sverchok.utils.sv_easing_functions import *
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper

PHI = (sqrt(5) + 1) / 2  # the golden ratio
PHIPI = 2 * log(PHI) / pi  # exponent for the Fibonacci (golden) spiral

spiral_type_items = [
    ("ARCHIMEDEAN", "Archimedean", "Generate an archimedean spiral.", 0),
    ("LOGARITHMIC", "Logarithmic", "Generate a logarithmic spiral.", 1),
    ("SPHERICAL", "Spherical", "Generate a spherical spiral.", 2),
    ("OVOIDAL", "Ovoidal", "Generate an ovoidal spiral.", 3),
    ("CORNU", "Cornu", "Generate a cornu spiral.", 4),
    ("EXO", "Exo", "Generate an exo spiral.", 5),
    ("SPIRANGLE", "Spirangle", "Generate a spirangle spiral.", 6)
]

# name : [ preset index, type, eR, iR, exponent, turns, resolution, scale, height ]
spiral_presets = {
    " ":            (0, "", 0.0, 0.0, 0.0, 0, 0, 0.0, 0.0),
    # archimedean spirals
    "ARCHIMEDEAN":  (10, "ARCHIMEDEAN", 1.0, 0.0, 1.0, 7, 100, 1.0, 0.0),
    "PARABOLIC":    (11, "ARCHIMEDEAN", 1.0, 0.0, 2.0, 5, 100, 1.0, 0.0),
    "HYPERBOLIC":   (12, "ARCHIMEDEAN", 1.0, 0.0, -1.0, 11, 100, 1.0, 0.0),
    "LITUUS":       (13, "ARCHIMEDEAN", 1.0, 0.0, -2.0, 11, 100, 1.0, 0.0),
    # logarithmic spirals
    "FIBONACCI":    (20, "LOGARITHMIC", 1.0, 0.5, PHIPI, 3, 100, 1.0, 0.0),
    # 3D spirals (mix type)
    "CONICAL":      (30, "ARCHIMEDEAN", 1.0, 0.0, 1.0, 7, 100, 1.0, 3.0),
    "HELIX":        (31, "LOGARITHMIC", 1.0, 0.0, 0.0, 7, 100, 1.0, 4.0),
    "SPHERICAL":    (32, "SPHERICAL", 1.0, 0.0, 0.0, 11, 55, 1.0, 0.0),
    "OVOIDAL":      (33, "OVOIDAL", 5.0, 1.0, 0.0, 7, 55, 1.0, 6.0),
    # spiral odities
    "CORNU":        (40, "CORNU", 1.0, 1.0, 1.0, 5, 55, 1.0, 0.0),
    "EXO":          (41, "EXO", 1.0, 0.1, PHI, 11, 101, 1.0, 0.0),
    # choppy spirals
    "SPIRANGLE SC": (50, "SPIRANGLE", 1.0, 0.0, 0.0, 8, 4, 1.0, 0.0),
    "SPIRANGLE HX": (51, "SPIRANGLE", 1.0, 0.0, 0.5, 7, 6, 1.0, 0.)
}

normalize_items = [
    ("ER", "eR", "Normalize spiral to the external radius.", 0),
    ("IR", "iR", "Normalize spiral to the internal radius.", 1)
]


def make_archimedean_spiral(settings):
    '''
        eR       : exterior radius (end radius)
        iR       : interior radius (start radius)
        exponent : rate of growth (between iR and eR)
        turns    : number of turns in the spiral
        N        : curve resolution per turn
        scale    : overall scale of the curve
        height   : the height of the spiral along z
        phase    : phase the spiral around its center
        flip     : flip the spiral direction (default is CLOCKWISE)
    '''
    
    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = -1 if flip else 1  # flip direction ?

    max_phi = 2 * pi * turns * sign

    epsilon = 1e-5 if exponent < 0 else 0  # to avoid raising zero to negative power
    exponent = 1e-2 if exponent == 0 else exponent  # to avoid division by zero
    dR = eR - iR  # radius range : cached for performance
    ex = 1 / exponent  # inverse exponent : cached for performance

    N = N * turns  # total number of points in the spiral

    _n = np.arange(N, dtype=np.int32)
    _verts = np.empty((N,3), dtype=np.float32)
    _t = _n/N
    _phi = max_phi*_t+phase
    _r = (iR + dR * np.power(_t + epsilon, ex)) * scale  # essentially: r = a * t ^ (1/b)
    _verts[:,0] = _r*np.cos(_phi)
    _verts[:,1] = _r*np.sin(_phi)
    _verts[:,2] = height * _t
    _edges = np.zeros((N-1,2), dtype=np.int32)
    _edges[:,0] = _n[ :-1]
    _edges[:,1] = _n[1:  ]

    return _verts, _edges, []


def make_logarithmic_spiral(settings):
    '''
        eR       : exterior radius
        iR       : interior radius
        exponent : rate of growth
        turns    : number of turns in the spiral
        N        : curve resolution per turn
        scale    : overall scale of the curve
        height   : the height of the spiral along z
        phase    : phase the spiral around its center
        flip     : flip the spiral direction (default is CLOCKWISE)
    '''

    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = -1 if flip else 1  # flip direction ?

    max_phi = 2 * pi * turns

    N = N * turns  # total number of points in the spiral


    _n = np.arange(N, dtype=np.int32)
    _verts = np.empty((N,3), dtype=np.float32)
    _t = _n/N
    _phi = max_phi*_t
    _r = eR * scale * np.exp(exponent * _phi)
    _verts[:,0] = _r*np.sin(_phi*sign+phase)
    _verts[:,1] = _r*np.cos(_phi*sign+phase)
    _verts[:,2] = height * _t
    _edges = np.zeros((N-1,2), dtype=np.int32)
    _edges[:,0] = _n[ :-1]
    _edges[:,1] = _n[1:  ]
    return _verts, _edges, []

def make_spherical_spiral(settings):
    '''
        This is the approximate sperical spiral that has a finite length,
        where the phi & theta angles sweep their ranges at constant rates.

        eR       : exterior radius
        iR       : interior radius (UNUSED)
        exponent : rate of growth (sigmoid in & out)
        turns    : number of turns in the spiral
        N        : the curve resolution of one turn
        scale    : overall scale of the curve
        height   : the height of the spiral along z (UNUSED)
        phase    : phase the spiral around its center
        flip     : flip the spiral direction (default is CLOCKWISE)
    '''

    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = -1 if flip else 1  # flip direction ?

    max_phi = 2 * pi * turns * sign

    N = N * turns  # total number of points in the spiral
    es = prepareExponentialSettings(2, exponent + 1e-5)  # used for easing
    b, e, m, s = es

    _n = np.arange(N+1, dtype=np.int32)
    _verts = np.empty((N+1,3), dtype=np.float32)
    _t = _n/N
    _phi = max_phi*_t + phase
    _a = np.where(_t<0.5,                                                           # ExponentialEaseInOut
                      0.5 *      (np.power(b, e *      (2*_t - 1)   ) - m) * s,     # ExponentialEaseIn
                0.5 + 0.5 * (1 - (np.power(b, e * (1 - (2*_t - 1)-1)) - m) * s ) )  # ExponentialEaseOut
    _theta = -pi / 2 + pi * _a
    _RxCosTheta = (iR + eR * np.cos(_theta)) * scale 
    _verts[:,0] = np.cos(_phi) * _RxCosTheta
    _verts[:,1] = np.sin(_phi) * _RxCosTheta
    _verts[:,2] = eR * np.sin(_theta)

    _edges = np.zeros((N,2), dtype=np.int32)
    _edges[:,0] = _n[ :-1]
    _edges[:,1] = _n[1:  ]
    return _verts, _edges, []

def make_ovoidal_spiral(settings):
    '''
        eR       : exterior radius (vertical cross section circles)
        iR       : interior radius (horizontal cross section circle)
        exponent : rate of growth (sigmoid in & out)
        turns    : number of turns in the spiral
        N        : the curve resolution of one turn
        scale    : overall scale of the curve
        height   : the height of the spiral along z
        phase    : phase the spiral around its center
        flip     : flip the spiral direction (default is CLOCKWISE)
    '''

    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = -1 if flip else 1  # flip direction ?

    max_phi = 2 * pi * turns * sign

    # derive eR based on iR and height (the main parameters)
    # eR = [iR - (H/2)^2/iR]/2 ::: H = 2 * sqrt(2*iR*eR - iR*iR)
    eR = 0.5 * (iR + 0.25 * height * height / iR)
    eR2 = eR * eR  # cached for performance
    dR = eR - iR  # cached for performance

    N = N * turns  # total number of points in the spiral

    es = prepareExponentialSettings(2, exponent + 1e-5)  # used for easing

    b, e, m, s = es

    _n = np.arange(N+1, dtype=np.int32)
    _verts = np.empty((N+1,3), dtype=np.float32)
    _t = _n/N
    _phi = max_phi*_t + phase

    _a = np.where(_t<0.5,                                                           # ExponentialEaseInOut
                      0.5 *      (np.power(b, e *      (2*_t - 1)   ) - m) * s,     # ExponentialEaseIn
                0.5 + 0.5 * (1 - (np.power(b, e * (1 - (2*_t - 1)-1)) - m) * s ) )  # ExponentialEaseOut
    _theta = -pi / 2 + pi * _a
    _h = 0.5 * height * np.sin(_theta) # [-H/2, +H/2]
    _r = np.sqrt(eR2 - _h * _h) - dR   # [0 -> iR -> 0]
    _verts[:,0] = _r * np.cos(_phi) * scale
    _verts[:,1] = _r * np.sin(_phi) * scale
    _verts[:,2] = _h * scale

    _edges = np.zeros((N,2), dtype=np.int32)
    _edges[:,0] = _n[ :-1]
    _edges[:,1] = _n[1:  ]
    return _verts, _edges, []

def make_cornu_spiral(settings):
    '''
        L     : length
        N     : resolution
        S     : scale
        M     :

        x(t) = s * Integral(0,t) { cos(pi*u*u/2) du }
        y(t) = s * Integral(0,t) { sin(pi*u*u/2) du }

        TODO : refine the math (smoother curve, adaptive res, faster computation)
    '''
    
    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = -1 if flip else 1  # flip direction ?

    N = N * turns  # total number of points in the spiral
    L = iR * turns  # length
    S = eR * scale  # overall scale

    cos_phase = cos(phase)
    sin_phase = sin(phase)

    _n     = np.arange(N+1, dtype=np.int32)
    _verts = np.empty((N+1,3), dtype=np.float32)
    _t     = _n/N
    _a     = _t * (2 - _t)                          # a = ExponentialEaseOut(t, es)
    _M     = 100 + (100*_a).astype(dtype=np.int32)  # integral steps (pricise of integral calculation)
    _l     = L * _a                                 # l = [0, +L]
    _l1    = np.roll(_l, 1)
    _l1[0] = 0
    _du    = (_l - _l1) / _M
    
    # # integral from l1 to l2
    # It is just ariphmetic progression. Can be numpify with vectorize
    # u = l1
    # du = (l - l1) / M
    # for m in range(M + 1):
    #     u = u + du  # u = [l1, l2]
    #     phi = u * u * pi / 2
    #     x = x + cos(phi) * du
    #     y = y + sin(phi) * du

    def integral_l12(M, u, du0):
        pi_2 = pi/2
        _arr_n = np.arange(M+1, dtype=np.float32)
        _arr_u = _arr_n*du0+u
        _arr_phi = _arr_u*_arr_u * pi_2
        _cos_phi = np.cos(_arr_phi)*du0
        _sin_phi = np.sin(_arr_phi)*du0
        sum_cos = np.sum(_cos_phi)
        sum_sin = np.sum(_sin_phi)

        return sum_cos, sum_sin
    
    integral_l12_vect = np.vectorize(integral_l12)
    _dx, _dy = integral_l12_vect(_M, _l1, _du)
    _cumsum_x = np.cumsum(_dx)
    _cumsum_y = np.cumsum(_dy)
    
    # scale and flip
    _xx = _cumsum_x * S
    _yy = _cumsum_y * S * sign

    # rotate by phase amount
    _px = _xx * cos_phase - _yy * sin_phase
    _py = _xx * sin_phase + _yy * cos_phase
    _pz = height * _t

    _p1 = np.dstack( (_px, _py, _pz) ).reshape(-1, 3) # positive spiral verts
    _verts = np.concatenate( (np.flip(-_p1, axis=0), _p1))
    _verts = _verts.reshape(-1,3)

    _edges = np.zeros((N,2), dtype=np.int32)
    _edges[:,0] = _n[ :-1]
    _edges[:,1] = _n[1:  ]

    return _verts, _edges, []

def make_exo_spiral(settings):
    '''
        This is an exponential in & out between two circles

        eR       : exterior radius
        iR       : interior radius
        exponent : rate of growth (SIGMOID : exponential in & out)
        turns    : number of turns in the spiral
        N        : the curve resolution of one turn
        scale    : overall scale of the curve
        height   : the height of the spiral along z
        phase    : phase the spiral around its center
        flip     : flip the spiral direction (default is CLOCKWISE)
    '''

    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = 1 if flip else -1  # flip direction ?

    max_phi = 2 * pi * turns * sign

    N = N * turns  # total number of points in the spiral

    es = prepareExponentialSettings(11, exponent + 1e-5)  # used for easing

    b, e, m, s = es

    _n = np.arange(N+1, dtype=np.int32)
    _verts = np.empty((N+1,3), dtype=np.float32)
    _t = _n/N
    _a = np.where(_t<0.5,                                                           # ExponentialEaseInOut
                      0.5 *      (np.power(b, e *      (2*_t - 1)   ) - m) * s,     # ExponentialEaseIn
                0.5 + 0.5 * (1 - (np.power(b, e * (1 - (2*_t - 1)-1)) - m) * s ) )  # ExponentialEaseOut
    _r = (iR + (eR - iR) * _a) * scale
    _phi = max_phi*_t + phase
    _verts[:,0] = _r * np.cos(_phi)
    _verts[:,1] = _r * np.sin(_phi)
    _verts[:,2] = height * _t

    _edges = np.zeros((N,2), dtype=np.int32)
    _edges[:,0] = _n[ :-1]
    _edges[:,1] = _n[1:  ]
    return _verts, _edges, []


def make_spirangle_spiral(settings):
    '''
        eR       : exterior radius (end radius)
        iR       : interior radius (start radius)
        exponent : rate of growth
        turns    : number of turns in the spiral
        N        : curve resolution per turn
        scale    : overall scale of the curve
        height   : the height of the spiral along z
        phase    : phase the spiral around its center
        flip     : flip the spiral direction (default is CLOCKWISE)
    '''
    # TODO: numpify

    eR, iR, exponent, turns, N, scale, height, phase, flip = settings

    sign = -1 if flip else 1  # flip direction ?

    deltaA = 2 * pi / N * sign  # angle increment
    deltaE = exponent / N  # exponent increment
    deltaR = (eR + iR)  # radius increment
    deltaZ = height / (N * turns)  # z increment
    e = 0
    r = iR
    phi = phase
    x, y, z = [0, 0, -deltaZ]

    N = N * turns  # total number of points in the spiral

    verts = []
    norms = []
    add_vert = verts.append
    add_norm = norms.append
    for n in range(N + 1):
        x = x + r * cos(phi) * scale
        y = y + r * sin(phi) * scale
        z = z + deltaZ
        e = e + deltaE
        r = r + deltaR * exp(e)
        phi = phi + deltaA
        add_vert([x, y, z])

    edges = get_edge_list(N)

    return verts, edges, norms


def normalize_spiral(verts, normalize_eR, eR, iR, scale):
    '''
        Normalize the spiral (XY) to either exterior or interior radius
    '''
    _verts = np.array(verts, dtype = np.float64)
    if normalize_eR:  # normalize to exterior radius (ending radius)
        psx = verts[-1][0] # x coordinate of the last point in the spiral
        psy = verts[-1][1] # y coordinate of the last point in the spiral
        r = sqrt(psx * psx + psy * psy)
        ss = eR / r * scale if eR != 0 else 1
    else:  # normalize to interior radius (starting radius)
        psx = verts[0][0] # x coordinate of the first point in the spiral
        psy = verts[0][1] # y coordinate of the first point in the spiral
        r = sqrt(psx * psx + psy * psy)
        ss = iR / r * scale if iR != 0 else 1

    _verts = _verts * ss
    return _verts

class SvSpiralNodeMK2(SverchCustomTreeNode, bpy.types.Node, SvAngleHelper):
    """
    Triggers: Spiral
    Tooltip: Generate spiral curves.\n\tIn: Radiuses, Exponent, Turns/Resolution, Scale, Height, Phase, Arms\n\tOut: Vertices, Edges
    """
    bl_idname = 'SvSpiralNodeMK2'
    bl_label = 'Spiral'
    sv_icon = "SV_SPIRAL"

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.phase = self.phase * au

    def update_spiral(self, context):
        if self.updating:
            return

        self.presets = " "
        updateNode(self, context)

    preset_items = [
        (k, k.title(), "", "", s[0])
        for k, s in sorted(spiral_presets.items(), key=lambda k: k[1][0])]

    def update_presets(self, context):
        self.updating = True

        if self.presets == " ":
            self.updating = False
            return

        _, sT, eR, iR, e, t, N, s, h = spiral_presets[self.presets]
        self.sType = sT
        self.eRadius = eR
        self.iRadius = iR
        self.exponent = e
        self.turns = t
        self.resolution = N
        self.scale = s
        self.height = h
        self.phase = 0.0
        self.arms = 1
        self.flip = False
        self.separate = False

        self.updating = False
        updateNode(self, context)

    presets: EnumProperty(
        name="Presets", items=preset_items,
        update=update_presets)

    sType: EnumProperty(
        name="Type", items=spiral_type_items,
        default="ARCHIMEDEAN", update=update_spiral)

    normalize: EnumProperty(
        name="Normalize Radius", items=normalize_items,
        default="ER", update=update_spiral)

    iRadius: FloatProperty(
        name="Interior Radius", description="Interior radius",
        default=1.0, min=0.0, update=update_spiral)

    eRadius: FloatProperty(
        name="Exterior Radius", description="Exterior radius",
        default=2.0, min=0.0, update=update_spiral)

    turns: IntProperty(
        name="Turns", description="Number of turns",
        default=11, min=1, update=update_spiral)

    arms: IntProperty(
        name="Arms", description="Number of spiral arms",
        default=1, min=1, update=update_spiral)

    flip: BoolProperty(
        name="Flip Direction", description="Flip spiral direction",
        default=False, update=update_spiral)

    scale: FloatProperty(
        name="Scale", description="Scale spiral vertices",
        default=1.0, update=update_spiral)

    height: FloatProperty(
        name="Height", description="Height of the spiral along z",
        default=0.0, update=update_spiral)

    phase: FloatProperty(
        name="Phase", description="Phase amount around spiral center",
        default=0.0, update=SvAngleHelper.update_angle)

    exponent: FloatProperty(
        name="Exponent", description="Exponent attenuator",
        default=2.0, update=update_spiral)

    resolution: IntProperty(
        name="Turn Resolution", description="Number of vertices in one turn in the spiral",
        default=100, min=3, update=update_spiral)

    separate: BoolProperty(
        name="Separate arms",
        description="Separate the spiral arms",
        default=False, update=update_spiral)

    updating: BoolProperty(default=False)  # used for disabling update callback

    def migrate_from(self, old_node):
        ''' Migration from old nodes '''
        if old_node.bl_idname == "SvSpiralNode":
            self.sType = old_node.stype
            self.last_angle_units = AngleUnits.RADIANS
            self.angle_units = AngleUnits.RADIANS

    def sv_init(self, context):
        self.width = 170
        self.inputs.new('SvStringsSocket', "R").prop_name = 'eRadius'
        self.inputs.new('SvStringsSocket', "r").prop_name = 'iRadius'
        self.inputs.new('SvStringsSocket', "e").prop_name = 'exponent'
        self.inputs.new('SvStringsSocket', "t").prop_name = 'turns'
        self.inputs.new('SvStringsSocket', "n").prop_name = 'resolution'
        self.inputs.new('SvStringsSocket', "s").prop_name = 'scale'
        self.inputs.new('SvStringsSocket', "h").prop_name = 'height'
        self.inputs.new('SvStringsSocket', "p").prop_name = 'phase'
        self.inputs.new('SvStringsSocket', "a").prop_name = 'arms'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")

        self.presets = "ARCHIMEDEAN"

    def draw_buttons(self, context, layout):
        layout.prop(self, 'presets')
        layout.prop(self, 'sType', text="")
        col = layout.column(align=True)
        if self.sType in ("LOGARITHMIC", "ARCHIMEDEAN", "SPIRANGLE"):
            row = col.row(align=True)
            row.prop(self, 'normalize', expand=True)
        row = col.row(align=True)
        row.prop(self, 'flip', text="Flip", toggle=True)
        row.prop(self, 'separate', text="Separate", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_angle_units_buttons(context, layout)

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_R = inputs["R"].sv_get()[0]  # list of exterior radii
        input_r = inputs["r"].sv_get()[0]  # list of interior radii
        input_e = inputs["e"].sv_get()[0]  # list of exponents
        input_t = inputs["t"].sv_get()[0]  # list of turns
        input_n = inputs["n"].sv_get()[0]  # list of curve resolutions
        input_s = inputs["s"].sv_get()[0]  # list of scales
        input_h = inputs["h"].sv_get()[0]  # list of heights (z)
        input_p = inputs["p"].sv_get()[0]  # list of phases
        input_a = inputs["a"].sv_get()[0]  # list of arms

        # sanitize the input
        input_R = list(map(lambda x: max(0.0, x), input_R))
        input_r = list(map(lambda x: max(0.0, x), input_r))
        input_t = list(map(lambda x: max(1, int(x)), input_t))
        input_n = list(map(lambda x: max(3, int(x)), input_n))
        input_a = list(map(lambda x: max(1, int(x)), input_a))

        # extra parameters
        f = self.flip  # flip direction

        parameters = match_long_repeat([input_R, input_r, input_e, input_t,
                                        input_n, input_s, input_h, input_p, input_a])

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        make_spiral = eval("make_" + self.sType.lower() + "_spiral")

        verts_list = []
        edges_list = []
        for R, r, e, t, n, s, h, p, a in zip(*parameters):
            p = p * au
            if self.separate:
                _arm_verts = np.empty((0,0,3), dtype=np.int32)
                _arm_edges = np.empty((0,0,2), dtype=np.int32)
            else:
                _arm_verts = np.empty((0,3), dtype=np.int32)
                _arm_edges = np.empty((0,2), dtype=np.int32)
            for i in range(a):  # generate each arm
                pa = p + 2 * pi / a * i
                settings = [R, r, e, t, n, s, h, pa, f]  # spiral settings

                verts, edges, norms = make_spiral(settings)

                if self.sType in ("LOGARITHMIC", "ARCHIMEDEAN", "SPIRANGLE"):
                    normalize_spiral(verts, self.normalize == "ER", R, r, s)

                if self.separate:
                    # unvisibled (4 levels. Visible is 3 levels)
                    _arm_verts = np.concatenate( (_arm_verts, verts[np.newaxis, :,:] ) ) if _arm_verts.size else verts[np.newaxis, :,:]
                    _arm_edges = np.concatenate( (_arm_edges, edges[np.newaxis, :,:] ) ) if _arm_edges.size else edges[np.newaxis, :,:]
                else:  # join the arms
                    o = len(_arm_verts)
                    edges = np.array(edges)
                    edges = edges+o
                    _arm_verts = np.vstack((_arm_verts, verts))
                    _arm_edges = np.vstack((_arm_edges, edges))

            _list_arm_verts = _arm_verts.tolist()
            _list_arm_edges = _arm_edges.tolist()
            verts_list.append(_list_arm_verts)
            edges_list.append(_list_arm_edges)

        self.outputs['Vertices'].sv_set(verts_list)
        self.outputs['Edges'].sv_set(edges_list)


def register():
    bpy.utils.register_class(SvSpiralNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvSpiralNodeMK2)
