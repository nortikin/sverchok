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
from math import radians
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes, sv_zip
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.modules.vertex_utils import center
from sverchok.utils.listutils import lists_flat

from sverchok.utils.pentagon_geom import generate_penta_grid, generate_penta_tiles


GRID_TYPE_ITEMS = [
    ("PENTAGON1", "Pentagon 1", "", custom_icon("SV_PENTAGON_1"), 4),
    ("PENTAGON2", "Pentagon 2", "", custom_icon("SV_PENTAGON_2"), 5),
    ("PENTAGON3", "Pentagon 3", "", custom_icon("SV_PENTAGON_3"), 6),
    ("PENTAGON4", "Pentagon 4", "", custom_icon("SV_PENTAGON_4"), 7),
    ("PENTAGON5", "Pentagon 5", "", custom_icon("SV_PENTAGON_5"), 8)]

ALIGN_ITEMS = [
    ("X", "X", "Align tile primitives to X axis", custom_icon("SV_PENTAGON_X_ROT"), 0),
    ("Y", "Y", "Align tile primitives to Y axis", custom_icon("SV_PENTAGON_Y_ROT"), 1),
    ("P", "Pentagon", "Align tile primitives to pentagon", custom_icon("SV_PENTAGON_P_ROT"), 2)
]
ANGLE_UNITS_ITEMS = [
    ("RAD", "Radians", "Define angles in radians", 0),
    ("DEG", "Degrees", "Define angles in degrees", 1),
]
PENTAGON_SOCKETS = {
    "PENTAGON1": "ABabcd",
    "PENTAGON2": "ACabd",
    "PENTAGON3": "ADab",
    "PENTAGON4": "BCbc",
    "PENTAGON5": "Cbd",
}

class SvPentagonTilerNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Hexagonal, Triangular, Ortogonal,
    Tooltip: Create polygon array assambled to fill the plane. Triangles, Hexagons and Squares
    """
    bl_idname = 'SvPentagonTilerNode'
    bl_label = 'Pentagon Tiler'
    sv_icon = 'SV_PENTAGON_5'

    def update_layout(self, context):
        self.update_sockets()
        updateNode(self, context)

    grid_type: EnumProperty(
        name="Type",
        description="Polygon Type",
        default="PENTAGON2", items=GRID_TYPE_ITEMS,
        update=update_layout)

    numx: IntProperty(
        name="NumX", description="Number of tile primitives along X",
        default=7, min=1, update=updateNode)

    numy: IntProperty(
        name="NumY", description="Number of tile primitives along Y",
        default=6, min=1, update=updateNode)

    angle: FloatProperty(
        name="Angle", description="Angle to rotate the grid and tiles",
        default=0.0, update=updateNode)
    angle_mode: EnumProperty(
        name="Angle", description="Angle units",
        default="DEG", items=ANGLE_UNITS_ITEMS,
        update=updateNode)
    center: BoolProperty(
        name="Center", description="Center grid around origin",
        default=True, update=updateNode)

    align: EnumProperty(
        name="Rotation", description="Base angle mode",
        default="P", items=ALIGN_ITEMS,
        update=updateNode)
    separate: BoolProperty(
        name="Separate", description="Separate tiles primitives",
        default=False, update=updateNode)
    angle_a: FloatProperty(
        name="A", description="Scale of the polygon tile",
        default=80.0, min=0.0, update=updateNode)
    angle_b: FloatProperty(
        name="B", description="Scale of the polygon tile",
        default=100.0, min=0.0, update=updateNode)
    angle_c: FloatProperty(
        name="C", description="Scale of the polygon tile",
        default=135.0, min=0.0, update=updateNode)
    angle_d: FloatProperty(
        name="D", description="Scale of the polygon tile",
        default=100.0, min=0.0, update=updateNode)

    side_a: FloatProperty(
        name="a", description="Scale of the polygon tile",
        default=1.0, min=0.0, update=updateNode)
    side_b: FloatProperty(
        name="b", description="Scale of the polygon tile",
        default=2.0, min=0.0, update=updateNode)
    side_c: FloatProperty(
        name="c", description="Scale of the polygon tile",
        default=2.5, min=0.0, update=updateNode)
    side_d: FloatProperty(
        name="d", description="Scale of the polygon tile",
        default=0.5, min=0.0, update=updateNode)

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)

    def sv_init(self, context):
        self.width = 170

        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.inputs.new('SvStringsSocket', "NumX").prop_name = 'numx'
        self.inputs.new('SvStringsSocket', "NumY").prop_name = 'numy'
        self.inputs.new('SvStringsSocket', "A").prop_name = 'angle_a'
        self.inputs.new('SvStringsSocket', "B").prop_name = 'angle_b'
        self.inputs.new('SvStringsSocket', "C").prop_name = 'angle_c'
        self.inputs.new('SvStringsSocket', "D").prop_name = 'angle_d'
        self.inputs.new('SvStringsSocket', "a").prop_name = 'side_a'
        self.inputs.new('SvStringsSocket', "b").prop_name = 'side_b'
        self.inputs.new('SvStringsSocket', "c").prop_name = 'side_c'
        self.inputs.new('SvStringsSocket', "d").prop_name = 'side_d'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

        self.update_layout(context)

    def update_sockets(self):
        inputs = self.inputs
        inputs_n = 'ABCDabcd'
        for socket in inputs_n:
            if socket in PENTAGON_SOCKETS[self.grid_type]:
                if inputs[socket].hide_safe:
                    inputs[socket].hide_safe = False
            else:
                inputs[socket].hide_safe = True

    def draw_buttons(self, context, layout):
        layout.prop(self, 'grid_type', expand=False)
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop(self, 'align', expand=False)
        row = layout.row(align=True)
        row.prop(self, 'separate', toggle=True)
        row.prop(self, 'center', toggle=True)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, 'grid_type', expand=False)
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop(self, 'align', expand=False)
        row = layout.row(align=True)
        row.prop(self, 'separate', toggle=True)
        row.prop(self, 'center', toggle=True)
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "grid_type", text="Mode")
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop_menu_enum(self, 'align')
        layout.prop_menu_enum(self, "angle_mode", text="Angle Units")
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def pentagon_tiler(self, params):
        params[1:3] = [list(map(lambda x: max(1, x), num)) for num in  params[1:3]]
        if self.angle_mode == 'DEG':
            params[0] = list(map(lambda x: radians(x), params[0]))
            params[3:7] = [list(map(lambda x: radians(x), ang)) for ang in params[3:7]]
        params = list_match_func[self.list_match_local](params)

        vert_list, edge_list, poly_list = [[], [], []]
        for par in zip(*params):
            grid = generate_penta_grid(self.grid_type, self.align, par)
            verts, edges, polys = generate_penta_tiles(par, grid, self.separate, self.grid_type)

            vert_list.extend(verts)
            edge_list.extend(edges)
            poly_list.extend(polys)

        if self.center:
            vert_list = center(vert_list)

        if self.separate:
            vert_list, edge_list, poly_list = lists_flat([vert_list, edge_list, poly_list])

        return vert_list, edge_list, poly_list

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return
        # input values lists
        params = [s.sv_get() for s in self.inputs]
        params = list_match_func[self.list_match_global](params)

        vert_list, edge_list, poly_list = [], [], []

        if  self.flat_output:
            v_add, e_add, p_add = vert_list.extend, edge_list.extend, poly_list.extend
        else:
            v_add, e_add, p_add = vert_list.append, edge_list.append, poly_list.append

        for par in sv_zip(*params):
            verts, edges, polys = self.pentagon_tiler(par)
            v_add(verts)
            e_add(edges)
            p_add(polys)

        self.outputs['Vertices'].sv_set(vert_list)
        self.outputs['Edges'].sv_set(edge_list)
        self.outputs['Polygons'].sv_set(poly_list)


def register():
    bpy.utils.register_class(SvPentagonTilerNode)


def unregister():
    bpy.utils.unregister_class(SvPentagonTilerNode)
