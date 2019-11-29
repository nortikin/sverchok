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
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.sv_KDT_utils import kdt_closest_path


class SvKDTreePathNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Nearest Verts Path
    Tooltip: Make a path (edges) verts joining each verts to the closest neighbor
    '''

    bl_idname = 'SvKDTreePathNode'
    bl_label = 'KDT Closest Path'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_KDT_PATH'

    mindist : FloatProperty(
        name='mindist', description='Minimum dist', min=0.0,
        default=0.1, update=updateNode)

    maxdist : FloatProperty(
        name='Max Distance', description='Maximum dist', min=0.0,
        default=2.0, update=updateNode)

    start_index : IntProperty(
        name='Start Index', description='Vertes Index to start path',
        default=0, min=0, update=updateNode)

    skip : IntProperty(
        name='skip', description='skip first n',
        default=0, min=0, update=updateNode)

    cycle : BoolProperty(
        name='Cyclic', description='Join first and last vertices',
        default=False, update=updateNode)

    list_match_global : EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match_local : EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'maxdist').prop_name = 'maxdist'
        self.inputs.new('SvStringsSocket', 'start_index').prop_name = 'start_index'

        self.outputs.new('SvStringsSocket', 'Edges')

    def draw_buttons(self, context, layout):
        layout.prop(self, "cycle", toggle=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "cycle", toggle=False)
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def get_data(self):
        '''get all data from sockets and match lengths'''
        si = self.inputs
        return list_match_func[self.list_match_global]([s.sv_get(default=[[]]) for s in si])

    def process(self):

        inputs = self.inputs
        outputs = self.outputs
        so = self.outputs
        si = self.inputs
        if not so[0].is_linked and si[0].is_linked:
            return

        result = []
        group = self.get_data()

        match_func = list_match_func[self.list_match_local]

        for verts, radius, start_indexes in zip(*group):
            verts, radius = match_func([verts, radius])
            for st in start_indexes:
                kdt_closest_path(verts, radius, st%len(verts), result, self.cycle)

        so[0].sv_set(result)


def register():
    bpy.utils.register_class(SvKDTreePathNode)


def unregister():
    bpy.utils.unregister_class(SvKDTreePathNode)
