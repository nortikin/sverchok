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
from sverchok.data_structure import (match_long_repeat, updateNode)
import numpy as np

from math import sin, cos, pi


def sign(x): return 1 if x >= 0 else -1

epsilon = 1e-10  # used to eliminate vertex overlap at the South/North poles

# name : [ sx, sy, sz, xp, xm, np, nm ]
super_presets = {
    "_":                [0.0, 0.0, 0.0, 0.0, 0.0, 0, 0],
    "SPHERE":           [1.0, 1.0, 1.0, 1.0, 1.0, 32, 32],
    "CUBE":             [1.0, 1.0, 1.0, 0.0, 0.0, 3, 5],
    "CYLINDER":         [1.0, 1.0, 1.0, 1.0, 0.0, 4, 32],
    "OCTOHEDRON":       [1.0, 1.0, 1.0, 1.0, 1.0, 3, 4],
    "SPINNING_TOP":     [1.0, 1.0, 1.0, 1.0, 4.0, 32, 32],
    "CUBIC_CONE":       [1.0, 1.0, 1.0, 1.0, 2.0, 32, 32],
    "CUBIC_BALL":       [1.0, 1.0, 1.0, 2.0, 1.0, 32, 32],
    "CUSHION":          [1.0, 1.0, 0.2, 2.0, 1.0, 32, 32],
    "STAR_BALL":        [1.0, 1.0, 1.0, 4.0, 1.0, 32, 64],
    "STAR":             [1.0, 1.0, 1.0, 4.0, 4.0, 64, 64],
    "ROUNDED_BIN":      [1.0, 1.0, 1.0, 0.5, 0.0, 32, 32],
    "ROUNDED_CUBE":     [1.0, 1.0, 1.0, 0.2, 0.2, 32, 32],
    "ROUNDED_CYLINDER": [1.0, 1.0, 1.0, 1.0, 0.1, 32, 32],
}


def make_verts(sx, sy, sz, xp, xm, npar, nm):
    """
    Generate the super-ellipsoid vertices for the given parameters
        sx : scale along x
        sx : scale along y
        sx : scale along z
        xp : parallel exponent
        xm : meridian exponent
        np : number of parallels (= number of points in a meridian)
        nm : number of meridians (= number of points in a parallel)
    """
    
    n1_i  = np.arange(npar, dtype=np.int16)
    _p = np.repeat( [np.array(n1_i)], nm, axis = 0).T        # index n1
    n2_i  = np.arange(nm, dtype=np.int16)
    _m    = np.repeat( [np.array(n2_i)], npar, axis = 0) # index n2
    _a = (pi / 2 - epsilon) * (2 * _p / (npar - 1) - 1)
    _cos_a = np.cos(_a)
    _sin_a = np.sin(_a)
    _pow_ca = np.power(np.abs(_cos_a), xm) * np.where(_cos_a>=0, 1, -1)
    _pow_sa = np.power(np.abs(_sin_a), xm) * np.where(_sin_a>=0, 1, -1)

    _b = pi * (2 * _m / nm - 1)
    _cos_b = np.cos(_b)
    _sin_b = np.sin(_b)
    _pow_cb = np.power(np.abs(_cos_b), xp) * np.where(_cos_b>=0, 1, -1)
    _pow_sb = np.power(np.abs(_sin_b), xp) * np.where(_sin_b>=0, 1, -1)
    _x = sx * _pow_ca * _pow_cb
    _y = sy * _pow_ca * _pow_sb
    _z = sz * _pow_sa
    _verts = np.dstack( (_x, _y, _z) )
    _verts = _verts.reshape(-1,3)
    _list_verts = _verts.tolist()

    return _list_verts

def make_edges_polys(is_edges, is_polys, P, M, cap_bottom, cap_top):
    """
    Generate the super-ellipsoid edges and polygons for the given parameters
        is_edges: generate edges
        is_polys: generate polys
        P : number of parallels (= number of points in a meridian)
        M : number of meridians (= number of points in a parallel)
        cap_bottom : turn on/off the bottom cap generation
        cap_top    : turn on/off the top cap generation
    """
    list_edges = None
    list_polys = None

    N1 = P
    N2 = M

    steps       = np.arange(0, N1*N2)  # generate array of indices
    arr_verts   = np.array(np.split(steps, N1))  # split array of indices by parallels
    arr_verts   = np.hstack( (arr_verts, np.array([arr_verts[:,0]]).T ) ) # append first column to the left to horizontal circle of edges and faces

    if is_edges:
        hspin_edges = np.dstack( (arr_verts[:N1  ,:N2], arr_verts[ :N1,1:N2+1] ))
        vspin_edges = np.dstack( (arr_verts[:N1-1,:N2], arr_verts[1:N1, :N2] ))
        hs_edges    = np.concatenate( (hspin_edges,  vspin_edges ), axis=0)  # combine horisontal end vertical edges
        hs_edges    = hs_edges.reshape(-1,2)
        list_edges  = hs_edges.tolist()

    if is_polys:
        arr_faces          = np.zeros((N1-1, N2, 4), 'i' )
        arr_faces[:, :, 0] = arr_verts[ :-1, 1:  ]
        arr_faces[:, :, 1] = arr_verts[1:  , 1:  ]
        arr_faces[:, :, 2] = arr_verts[1:  ,  :-1]
        arr_faces[:, :, 3] = arr_verts[ :-1,  :-1]
        hs_faces           = arr_faces.reshape(-1,4) # remove exis
        list_polys         = hs_faces.tolist()
        if cap_bottom:
            cap_b = np.flip( np.arange(M) )
            cap_b = cap_b.tolist()
            list_polys.append(cap_b)

        if cap_top:
            cap_t = np.arange(M)+(N1-1)*N2
            cap_t = cap_t.tolist()
            list_polys.append(cap_t)

    return list_edges, list_polys

def make_edges(P, M):
    """
    Generate the super-ellipsoid edges for the given parameters
        P : number of parallels (= number of points in a meridian)
        M : number of meridians (= number of points in a parallel)
    """

    N1 = P
    N2 = M
    steps = np.arange(0, N1*N2)
    arr_verts = np.array(np.split(steps, N1))

    #arr_verts   = np.vstack( (arr_verts, np.roll(arr_verts[:1], -t) ) ) # append first row to bottom to vertically circle with twist
    arr_verts   = np.hstack( (arr_verts, np.array([arr_verts[:,0]]).T ) ) # append first column to the left to horizontal circle
    hspin_edges = np.dstack( (arr_verts[:N1  ,:N2], arr_verts[ :N1,1:N2+1] ))
    vspin_edges = np.dstack( (arr_verts[:N1-1,:N2], arr_verts[1:N1, :N2] ))
    hs_edges = np.concatenate( (hspin_edges,  vspin_edges ))
    hs_edges = np.concatenate( np.concatenate( (hspin_edges,  vspin_edges ), axis=0), axis=0) # remove exis

    hs_edges_list = hs_edges.tolist()
    
    return hs_edges_list

def make_polys(P, M, cap_bottom, cap_top):
    """
    Generate the super-ellipsoid polygons for the given parameters
        P : number of parallels (= number of points in a meridian)
        M : number of meridians (= number of points in a parallel)
        cap_bottom : turn on/off the bottom cap generation
        cap_top    : turn on/off the top cap generation
    """

    N1 = P
    N2 = M
    
    arr_faces = np.zeros((N1-1, N2, 4), 'i' )

    steps = np.arange(0, N1*N2)
    arr_verts = np.array(np.split(steps, N1))
    arr_verts = np.hstack( (arr_verts, np.array([arr_verts[:,0]]).T ) ) # append first column to the left to horizontal circle
    
    arr_faces[:, :, 0] = arr_verts[ :-1, 1:  ]
    arr_faces[:, :, 1] = arr_verts[1:  , 1:  ]
    arr_faces[:, :, 2] = arr_verts[1:  ,  :-1]
    arr_faces[:, :, 3] = arr_verts[ :-1,  :-1]
    hs_faces = arr_faces.reshape(-1,4) # remove exis
    hs_faces_list = hs_faces.tolist()
    if cap_bottom:
        cap_b = np.flip( np.arange(M) )
        hs_faces_list.append(cap_b)

    if cap_top:
        cap_t = np.arange(M)+(N1-1)*N2
        hs_faces_list.append(cap_t)

    return hs_faces_list

class SvSuperEllipsoidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Sphere Cube Cylinder Octahedron Star
    Tooltip: Generate various Super-Ellipsoid shapes.\n\tIn: Scale X/Y/Z, Exponent P/M, Parallels, Meridians\n\tExtra: Cap Bottom/Top\n\tOut: Vertices, Edges, Polygons
    """
    bl_idname = 'SvSuperEllipsoidNode'
    bl_label = 'Super Ellipsoid'
    sv_icon = 'SV_SUPER_ELLIPSE'

    def update_ellipsoid(self, context):
        if self.updating:
            return

        self.presets = "_"
        updateNode(self, context)

    def update_presets(self, context):
        self.updating = True

        if self.presets == "_":
            self.updating = False
            return

        sx, sy, sz, xp, xm, np, nm = super_presets[self.presets.replace(" ", "_")]
        self.scale_x = sx
        self.scale_y = sy
        self.scale_z = sz
        self.exponent_parallels = xp
        self.exponent_meridians = xm
        self.number_parallels = np
        self.number_meridians = nm
        self.cap_bottom = True
        self.cap_top = True

        self.updating = False
        updateNode(self, context)

    preset_items = [(k, k.replace("_", " ").title(), "", "", i) for i, (k, v) in enumerate(sorted(super_presets.items()))]

    presets: EnumProperty(
        name="Presets", items=preset_items, description="Various presets",
        update=update_presets)

    scale_x: FloatProperty(
        name='Scale X', description="Scale along X",
        default=1.0, update=update_ellipsoid)

    scale_y: FloatProperty(
        name='Scale Y', description="Scale along Y",
        default=1.0, update=update_ellipsoid)

    scale_z: FloatProperty(
        name='Scale Z', description="Scale along Z",
        default=1.0, update=update_ellipsoid)

    exponent_parallels: FloatProperty(
        name='P Exponent', description="Parallel exponent",
        default=1.0, min=0.0, update=update_ellipsoid)

    exponent_meridians: FloatProperty(
        name='M Exponent', description="Meridian exponent",
        default=1.0, min=0.0, update=update_ellipsoid)

    number_parallels: IntProperty(
        name='Parallels', description="Number of parallels",
        default=10, min=3, update=update_ellipsoid)

    number_meridians: IntProperty(
        name='Meridians', description="Number of meridians",
        default=10, min=3, update=update_ellipsoid)

    cap_bottom: BoolProperty(
        name='Cap Bottom', description="Generate bottom cap",
        default=True, update=updateNode)

    cap_top: BoolProperty(
        name='Cap Top', description="Generate top cap",
        default=True, update=updateNode)

    updating: BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('SvStringsSocket', "SX").prop_name = 'scale_x'
        self.inputs.new('SvStringsSocket', "SY").prop_name = 'scale_y'
        self.inputs.new('SvStringsSocket', "SZ").prop_name = 'scale_z'
        self.inputs.new('SvStringsSocket', "XP").prop_name = 'exponent_parallels'
        self.inputs.new('SvStringsSocket', "XM").prop_name = 'exponent_meridians'
        self.inputs.new('SvStringsSocket', "NP").prop_name = 'number_parallels'
        self.inputs.new('SvStringsSocket', "NM").prop_name = 'number_meridians'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

        self.presets = "ROUNDED_CUBE"

    def draw_buttons(self, context, layout):
        if not self.inputs["XP"].is_linked and not self.inputs["XM"].is_linked:
            layout.prop(self, "presets", text="")

    def draw_buttons_ext(self, context, layout):
        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(self, "cap_bottom", text="Cap B", toggle=True)
        row.prop(self, "cap_top", text="Cap T", toggle=True)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs

        # read inputs
        input_sx = inputs["SX"].sv_get()[0]
        input_sy = inputs["SY"].sv_get()[0]
        input_sz = inputs["SZ"].sv_get()[0]
        input_xp = inputs["XP"].sv_get()[0]
        input_xm = inputs["XM"].sv_get()[0]
        input_np = inputs["NP"].sv_get()[0]
        input_nm = inputs["NM"].sv_get()[0]

        # sanitize inputs
        input_xp = list(map(lambda a: max(0.0, a), input_xp))
        input_xm = list(map(lambda a: max(0.0, a), input_xm))
        input_np = list(map(lambda a: max(3, int(a)), input_np))
        input_nm = list(map(lambda a: max(3, int(a)), input_nm))

        params = match_long_repeat([input_sx, input_sy, input_sz,
                                    input_xp, input_xm,
                                    input_np, input_nm])

        verts_output_linked = self.outputs['Vertices'].is_linked
        edges_output_linked = self.outputs['Edges'].is_linked
        polys_output_linked = self.outputs['Polygons'].is_linked

        verts_list = []
        edges_list = []
        polys_list = []
        for sx, sy, sz, xp, xm, np, nm in zip(*params):
            if verts_output_linked:
                verts = make_verts(sx, sy, sz, xp, xm, np, nm)
                verts_list.append(verts)
            
            if edges_output_linked or polys_output_linked:
                edges, polys = make_edges_polys(edges_output_linked, polys_output_linked, np, nm, self.cap_bottom, self.cap_top)

                if edges_output_linked:
                    edges_list.append(edges)
                if polys_output_linked:
                    polys_list.append(polys)

        # outputs
        if verts_output_linked:
            self.outputs['Vertices'].sv_set(verts_list)

        if edges_output_linked:
            self.outputs['Edges'].sv_set(edges_list)

        if polys_output_linked:
            self.outputs['Polygons'].sv_set(polys_list)


def register():
    bpy.utils.register_class(SvSuperEllipsoidNode)


def unregister():
    bpy.utils.unregister_class(SvSuperEllipsoidNode)
