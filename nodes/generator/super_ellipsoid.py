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

from math import sin, cos, pi


def sign(x): return 1 if x >= 0 else -1

epsilon = 1e-10  # used to eliminate vertex overlap at the South/North poles

# name : [ sx, sy, sz, xp, xm, np, nm ]
super_presets = {
    " ":                [0.0, 0.0, 0.0, 0.0, 0.0, 0, 0],
    "SPHERE":           [1.0, 1.0, 1.0, 1.0, 1.0, 24, 24],
    "CUBE":             [1.0, 1.0, 1.0, 0.0, 0.0, 3, 5],
    "CYLINDER":         [1.0, 1.0, 1.0, 1.0, 0.0, 4, 32],
    "OCTOHEDRON":       [1.0, 1.0, 1.0, 1.0, 1.0, 3, 4],
    "SPINNING TOP":     [1.0, 1.0, 1.0, 1.0, 3.0, 24, 24],
    "STAR":             [1.0, 1.0, 1.0, 4.0, 4.0, 32, 32],
    "ROUNDED BIN":      [1.0, 1.0, 1.0, 0.5, 0.0, 32, 32],
    "ROUNDED CUBE":     [1.0, 1.0, 1.0, 0.2, 0.2, 32, 32],
    "ROUNDED CYLINDER": [1.0, 1.0, 1.0, 1.0, 0.1, 32, 32],
}


def make_verts(sx, sy, sz, xp, xm, np, nm):
    """
    Generate the super ellipsoid vertices for the given parameters
        sx : scale along x
        sx : scale along y
        sx : scale along z
        xp : parallel exponent
        xm : meridian exponent
        np : number of parallels
        nm : number of meridians
    """
    verts = []
    for p in range(np):
        a = (pi / 2 - epsilon) * (2 * p / (np - 1) - 1)
        cosA = cos(a)
        sinA = sin(a)
        powCA = pow(abs(cosA), xm) * sign(cosA)
        powSA = pow(abs(sinA), xm) * sign(sinA)
        for m in range(nm):
            b = pi * (2 * m / nm - 1)
            cosB = cos(b)
            sinB = sin(b)
            powCB = pow(abs(cosB), xp) * sign(cosB)
            powSB = pow(abs(sinB), xp) * sign(sinB)

            x = sx * powCA * powCB
            y = sy * powCA * powSB
            z = sz * powSA
            verts.append([x, y, z])

    return verts


def make_edges(P, M):
    """
    Generate the super ellipsoid edges for the given parameters
        P : number of parallels
        M : number of meridians
    """
    edge_list = []

    for i in range(P):
        for j in range(M - 1):
            edge_list.append([i * M + j, i * M + j + 1])
        edge_list.append([(i + 1) * M - 1, i * M])

    for i in range(P):
        for j in range(M):
            edge_list.append([i * M + j, (i + 1) * M + j])

    return edge_list


def make_polys(P, M, cap_top, cap_bottom):
    """
    Generate the super ellipsoid polygons for the given parameters
        P : number of parallels
        M : number of meridians
    """
    poly_list = []

    for i in range(P - 1):
        for j in range(M - 1):
            poly_list.append([i * M + j, i * M + j + 1, (i + 1) * M + j + 1, (i + 1) * M + j])
        poly_list.append([(i + 1) * M - 1, i * M, (i + 1) * M, (i + 2) * M - 1])

    if cap_top:
        cap = []
        for j in range(M):
            cap.append(M * (P - 1) + j)
        poly_list.append(cap)

    if cap_bottom:
        cap = []
        for j in reversed(range(M)):
            cap.append(j)
        poly_list.append(cap)

    return poly_list


class SvSuperEllipsoidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sphere Cube Cylinder Octohedron Star
    Tooltip: Generate various Super Ellipsoid shapes.
    """
    bl_idname = 'SvSuperEllipsoidNode'
    bl_label = 'Super Ellipsoid'

    def update_ellipsoid(self, context):
        if self.updating:
            return

        self.presets = " "
        updateNode(self, context)

    def update_presets(self, context):
        self.updating = True

        if self.presets == " ":
            self.updating = False
            return

        sx, sy, sz, xp, xm, np, nm = super_presets[self.presets]
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

    preset_items = [(k, k.title(), "", "", i) for i, (k, v) in enumerate(sorted(super_presets.items()))]

    presets = EnumProperty(
        name="Presets", items=preset_items,
        update=update_presets)

    scale_x = FloatProperty(
        name='Scale X', description="Scale along X",
        default=1.0, update=update_ellipsoid)

    scale_y = FloatProperty(
        name='Scale Y', description="Scale along Y",
        default=1.0, update=update_ellipsoid)

    scale_z = FloatProperty(
        name='Scale Z', description="Scale along Z",
        default=1.0, update=update_ellipsoid)

    exponent_parallels = FloatProperty(
        name='P Exponent', description="Parallel exponent",
        default=1.0, min=0.0, update=update_ellipsoid)

    exponent_meridians = FloatProperty(
        name='M Exponent', description="Meridian exponent",
        default=1.0, min=0.0, update=update_ellipsoid)

    number_parallels = IntProperty(
        name='Parallels', description="Number of parallels",
        default=10, min=3, update=update_ellipsoid)

    number_meridians = IntProperty(
        name='Meridians', description="Number of meridians",
        default=10, min=3, update=update_ellipsoid)

    cap_top = BoolProperty(
        name='Cap Top', description="Generate top cap",
        default=True, update=updateNode)

    cap_bottom = BoolProperty(
        name='Cap Bottom', description="Generate bottom cap",
        default=True, update=updateNode)

    updating = BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "SX").prop_name = 'scale_x'
        self.inputs.new('StringsSocket', "SY").prop_name = 'scale_y'
        self.inputs.new('StringsSocket', "SZ").prop_name = 'scale_z'
        self.inputs.new('StringsSocket', "XP").prop_name = 'exponent_parallels'
        self.inputs.new('StringsSocket', "XM").prop_name = 'exponent_meridians'
        self.inputs.new('StringsSocket', "NP").prop_name = 'number_parallels'
        self.inputs.new('StringsSocket', "NM").prop_name = 'number_meridians'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")

        self.presets = "ROUNDED CUBE"

    def draw_buttons(self, context, layout):
        if not self.inputs["XP"].is_linked and not self.inputs["XM"].is_linked:
            layout.prop(self, "presets", text="")

    def draw_buttons_ext(self, context, layout):
        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(self, "cap_top", text="Cap T", toggle=True)
        row.prop(self, "cap_bottom", text="Cap B", toggle=True)

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
        input_np = list(map(lambda a: max(3, a), input_np))
        input_nm = list(map(lambda a: max(3, a), input_nm))

        params = match_long_repeat([input_sx, input_sy, input_sz,
                                    input_xp, input_xm,
                                    input_np, input_nm])

        verts_list = []
        edges_list = []
        polys_list = []
        for sx, sy, sz, xp, xm, np, nm in zip(*params):
            verts = make_verts(sx, sy, sz, xp, xm, np, nm)
            edges = make_edges(np, nm)
            polys = make_polys(np, nm, self.cap_top, self.cap_bottom)
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
    bpy.utils.register_class(SvSuperEllipsoidNode)


def unregister():
    bpy.utils.unregister_class(SvSuperEllipsoidNode)
