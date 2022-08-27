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
from bpy.props import FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.geom import distance_line_line


class SvDistancetLineLineNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Intersect, Trim
    Tooltip: Distance Line to line and closest points in the lines
    '''
    bl_idname = 'SvDistancetLineLineNode'
    bl_label = 'Distance Line Line'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DISTANCE_LINE_LINE'

    tolerance : FloatProperty(
        name="tolerance", description='intersection tolerance',
        default=1.0e-6, min=0.0, precision=6,
        update=updateNode)

    list_match_global : EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('SvVerticesSocket', "Verts Line A")
        sinw('SvVerticesSocket', "Verts Line B")

        sonw('SvStringsSocket', "Distance")
        sonw('SvStringsSocket', "Intersect")
        sonw('SvVerticesSocket', "Closest Point A")
        sonw('SvVerticesSocket', "Closest Point B")
        sonw('SvStringsSocket', "A in segment")
        sonw('SvStringsSocket', "B in segment")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "tolerance")
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop(self, "tolerance")
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")

    def get_data(self):
        '''get all data from sockets and match lengths'''
        si = self.inputs
        return list_match_func[self.list_match_global]([s.sv_get(default=[[]], deepcopy=False) for s in si])

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        si = self.inputs
        if not (any(s.is_linked for s in so) and all(s.is_linked for s in si)):
            return

        result = [[] for socket in so]
        gates = [socket.is_linked for socket in so]

        group = self.get_data()

        for line_a, line_b in zip(*group):
            distance_line_line(line_a, line_b, result, gates, self.tolerance)

        for i, res in enumerate(result):
            if gates[i]:
                so[i].sv_set(res)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvDistancetLineLineNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvDistancetLineLineNode)
