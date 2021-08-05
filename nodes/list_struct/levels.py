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
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty, BoolVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, describe_data_shape_by_level, list_levels_adjust, SIMPLE_DATA_TYPES,\
    changable_sockets
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.dependencies import FreeCAD
from sverchok.utils.logging import info
ALL_TYPES = SIMPLE_DATA_TYPES + (SvCurve, SvSurface)
if FreeCAD is not None:
    import Part
    ALL_TYPES = ALL_TYPES + (Part.Shape,)

class SvNestingLevelEntry(bpy.types.PropertyGroup):
    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            info("Node is not defined in this context, so will not update the node.")

    description : StringProperty(options = {'SKIP_SAVE'}, default="?")
    flatten : BoolProperty(
                name = "Flatten",
                description = "Concatenate all child lists into one list",
                default=False,
                update=update_entry)
    wrap : BoolProperty(
                name = "Wrap",
                description = "Wrap data into additional pair of square brackets []",
                default=False,
                update=update_entry)

class SvListLevelsNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: List Levels
    Tooltip: List nesting levels manipulation
    '''
    bl_idname = 'SvListLevelsNode'
    bl_label = 'List Levels'
    bl_icon = 'OUTLINER'

    levels_config : CollectionProperty(type=SvNestingLevelEntry)
    prev_nesting_level : IntProperty(default = 0, options = {'SKIP_SAVE'})
    flatten_mem: BoolVectorProperty(size=32, default=[False for i in range(32)])
    wrap_mem: BoolVectorProperty(size=32, default=[False for i in range(32)])

    def draw_buttons(self, context, layout):
        n = len(self.levels_config)
        if not n:
            layout.label(text="No data passed")
            return
        grid = layout.grid_flow(row_major=True, columns=5, align=True)

        grid.label(text='Depth')
        grid.label(text='Nesting')
        grid.label(text='Shape')
        grid.label(text='Flatten')
        grid.label(text='Wrap')

        for i, entry in enumerate(self.levels_config):
            nesting = n-i-1
            level_str = str(i)
            if i == 0:
                level_str += " (outermost)"
            elif nesting == 0:
                level_str += " (innermost)"
            grid.label(text=level_str)
            grid.label(text=str(nesting))
            grid.label(text=entry.description)
            if nesting < 2:
                grid.label(icon='X', text='')
            else:
                grid.prop(entry, 'flatten', text='')
            grid.prop(entry, 'wrap', text='')

    def sv_update(self):
        self.update_buttons(False)

    def update_buttons(self, update_during_process):
        try:
            data = self.inputs['Data'].sv_get(default=[])
        except LookupError:
            data = []
        if not data:
            self.prev_nesting_level = 0
            for i, l in enumerate(self.levels_config):
                self.flatten_mem[i] = l.flatten
                self.wrap_mem[i] = l.wrap

            self.levels_config.clear()
            return


        changable_sockets(self, 'Data', ['Data', ])
        nesting, descriptions = describe_data_shape_by_level(data, include_numpy_nesting=False)
        rebuild_list = self.prev_nesting_level != nesting
        self.prev_nesting_level = nesting

        if rebuild_list:
            self.levels_config.clear()
            for i, descr in enumerate(descriptions):
                l = self.levels_config.add()
                l.description = descr
                l.flatten = self.flatten_mem[i]
                l.wrap = self.wrap_mem[i]

        else:
            for entry, descr in zip(self.levels_config, descriptions):
                entry.description = descr

    def sv_init(self, context):
        self.width = 300
        self.inputs.new('SvStringsSocket', 'Data')
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_copy(self, original):
        self.prev_nesting_level = 0

    def process(self):
        if not self.inputs['Data'].is_linked:
            return
        self.update_buttons(True)
        if not self.outputs['Data'].is_linked:
            return

        data = self.inputs['Data'].sv_get(default=[], deepcopy=False)
        result = list_levels_adjust(data, self.levels_config, data_types=ALL_TYPES)

        self.outputs['Data'].sv_set(result)

classes = [SvNestingLevelEntry, SvListLevelsNode]

def register():
    for name in classes:
        bpy.utils.register_class(name)

def unregister():
    for name in reversed(classes):
        bpy.utils.unregister_class(name)
