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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty
from add_mesh_extra_objects.add_mesh_solid import createSolid
from mathutils import Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat
from sverchok.utils.modules.geom_utils import interp_v3_v3v3, normalize, add_v3_v3v3, sub_v3_v3v3
from sverchok.nodes.modifier_change.polygons_to_edges import pols_edges
## This node is a port to the  add_mesh_extra_objects.add_mesh_solid createSolid

class SvRegularSolid(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Platonic, Archimedean or Catalan solids.
    Tooltip: Add one of the Platonic, Archimedean or Catalan solids.
    """
    bl_idname = 'SvRegularSolid'
    bl_label = 'Regular Solid'
    bl_icon = 'GRIP'
    sv_icon = 'SV_REGULAR_SOLID'


    def reset_preset(self, context):
        if self.changing_preset:
            return
        if self.preset != "0":
            self.preset = "0"
        else:
            updateNode(self, context)

    source: EnumProperty(
                    items=(("4", "Tetrahedron", ""),
                            ("6", "Hexahedron", ""),
                            ("8", "Octahedron", ""),
                            ("12", "Dodecahedron", ""),
                            ("20", "Icosahedron", "")),
                    name="Source",
                    description="Starting point of your solid",
                    update=reset_preset
                    )
    size: FloatProperty(
                    name="Size",
                    description="Radius of the sphere through the vertices",
                    min=0.01,
                    soft_min=0.01,
                    max=100,
                    soft_max=100,
                    default=1.0,
                    update=updateNode
                    )
    vTrunc: FloatProperty(
                    name="Vertex Truncation",
                    description="Amount of vertex truncation",
                    min=0.0,
                    soft_min=0.0,
                    max=2.0,
                    soft_max=2.0,
                    default=0.0,
                    precision=3,
                    step=0.5,
                    update=reset_preset
                    )
    eTrunc: FloatProperty(
                    name="Edge Truncation",
                    description="Amount of edge truncation",
                    min=0.0,
                    soft_min=0.0,
                    max=1.0,
                    soft_max=1.0,
                    default=0.0,
                    precision=3,
                    step=0.2,
                    update=reset_preset
                    )
    snub: EnumProperty(
                    items=(("None", "No Snub", ""),
                           ("Left", "Left Snub", ""),
                           ("Right", "Right Snub", "")),
                    name="Snub",
                    description="Create the snub version",
                    update=reset_preset
                    )
    dual: BoolProperty(
                    name="Dual",
                    description="Create the dual of the current solid",
                    default=False,
                    update=reset_preset
                    )
    keepSize: BoolProperty(
                    name="Keep Size",
                    description="Keep the whole solid at a constant size",
                    default=False,
                    update=updateNode
                    )
    changing_preset: BoolProperty(
                    name="changing_preset",
                    description="changing_preset",
                    default=False,
                    )
    def updatePreset(self, context):
        if self.preset != "0":
            # if preset, set preset
            if self.previousSetting != self.preset:
                self.changing_preset = True
                using = self.p[self.preset]
                self.source = using[0]
                self.vTrunc = using[1]
                self.eTrunc = using[2]
                self.dual = using[3]
                self.snub = using[4]

        self.changing_preset = False
        updateNode(self, context)

    preset: EnumProperty(
                    items=(("0", "Custom", ""),
                           ("t4", "Truncated Tetrahedron", ""),
                           ("r4", "Cuboctahedron", ""),
                           ("t6", "Truncated Cube", ""),
                           ("t8", "Truncated Octahedron", ""),
                           ("b6", "Rhombicuboctahedron", ""),
                           ("c6", "Truncated Cuboctahedron", ""),
                           ("s6", "Snub Cube", ""),
                           ("r12", "Icosidodecahedron", ""),
                           ("t12", "Truncated Dodecahedron", ""),
                           ("t20", "Truncated Icosahedron", ""),
                           ("b12", "Rhombicosidodecahedron", ""),
                           ("c12", "Truncated Icosidodecahedron", ""),
                           ("s12", "Snub Dodecahedron", ""),
                           ("dt4", "Triakis Tetrahedron", ""),
                           ("dr4", "Rhombic Dodecahedron", ""),
                           ("dt6", "Triakis Octahedron", ""),
                           ("dt8", "Tetrakis Hexahedron", ""),
                           ("db6", "Deltoidal Icositetrahedron", ""),
                           ("dc6", "Disdyakis Dodecahedron", ""),
                           ("ds6", "Pentagonal Icositetrahedron", ""),
                           ("dr12", "Rhombic Triacontahedron", ""),
                           ("dt12", "Triakis Icosahedron", ""),
                           ("dt20", "Pentakis Dodecahedron", ""),
                           ("db12", "Deltoidal Hexecontahedron", ""),
                           ("dc12", "Disdyakis Triacontahedron", ""),
                           ("ds12", "Pentagonal Hexecontahedron", "")),
                    name="Presets",
                    description="Parameters for some hard names",
                    update=updatePreset
                    )

    # actual preset values
    p = {"t4": ["4", 2 / 3, 0, 0, "None"],
         "r4": ["4", 1, 1, 0, "None"],
         "t6": ["6", 2 / 3, 0, 0, "None"],
         "t8": ["8", 2 / 3, 0, 0, "None"],
         "b6": ["6", 1.0938, 1, 0, "None"],
         "c6": ["6", 1.0572, 0.585786, 0, "None"],
         "s6": ["6", 1.0875, 0.704, 0, "Left"],
         "r12": ["12", 1, 0, 0, "None"],
         "t12": ["12", 2 / 3, 0, 0, "None"],
         "t20": ["20", 2 / 3, 0, 0, "None"],
         "b12": ["12", 1.1338, 1, 0, "None"],
         "c12": ["20", 0.921, 0.553, 0, "None"],
         "s12": ["12", 1.1235, 0.68, 0, "Left"],
         "dt4": ["4", 2 / 3, 0, 1, "None"],
         "dr4": ["4", 1, 1, 1, "None"],
         "dt6": ["6", 2 / 3, 0, 1, "None"],
         "dt8": ["8", 2 / 3, 0, 1, "None"],
         "db6": ["6", 1.0938, 1, 1, "None"],
         "dc6": ["6", 1.0572, 0.585786, 1, "None"],
         "ds6": ["6", 1.0875, 0.704, 1, "Left"],
         "dr12": ["12", 1, 0, 1, "None"],
         "dt12": ["12", 2 / 3, 0, 1, "None"],
         "dt20": ["20", 2 / 3, 0, 1, "None"],
         "db12": ["12", 1.1338, 1, 1, "None"],
         "dc12": ["20", 0.921, 0.553, 1, "None"],
         "ds12": ["12", 1.1235, 0.68, 1, "Left"]}

    # previous preset, for User-friendly reasons
    previousSetting = ""

    def sv_init(self, context):
        si = self.inputs
        si.new('SvStringsSocket', "size").prop_name = 'size'
        si.new('SvStringsSocket', "vTrunc").prop_name = 'vTrunc'
        si.new('SvStringsSocket', "eTrunc").prop_name = 'eTrunc'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        col = layout.column(align=False)
        col.prop(self, "preset", expand=False)
        col.prop(self, "source", expand=False)
        col.prop(self, "snub", expand=False)
        row = layout.row(align=True)
        row.prop(self, "dual", toggle=True)
        row.prop(self, "keepSize", toggle=True)

    def get_data(self):
        size = self.inputs["size"].sv_get()
        vTrunc = self.inputs["vTrunc"].sv_get()
        eTrunc = self.inputs["eTrunc"].sv_get()
        params = [size, vTrunc, eTrunc]
        return match_long_repeat(params)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        verts_out, edges_out, polys_out = [], [], []

        params = self.get_data()
        get_edges = self.outputs['Edges'].is_linked

        for p in zip(*params):
            p = match_long_repeat(p)
            for p2 in zip(*p):
                size, vTrunc, eTrunc = p2

                verts, faces = createSolid(self.source,
                                       vTrunc,
                                       eTrunc,
                                       self.dual,
                                       self.snub
                                       )

                # resize to normal size, or if keepSize, make sure all verts are of length 'size'
                if self.keepSize:
                    rad = size / verts[-1 if self.dual else 0].length
                else:
                    rad = size
                verts = [list(i * rad) for i in verts]

                verts_out.append(verts)
                polys_out.append(faces)
                if get_edges:
                    edges_out.append(pols_edges([faces], unique_edges=True)[0])

        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(verts_out)
        if get_edges:
            self.outputs['Edges'].sv_set(edges_out)
        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(polys_out)


def register():
    bpy.utils.register_class(SvRegularSolid)


def unregister():
    bpy.utils.unregister_class(SvRegularSolid)
