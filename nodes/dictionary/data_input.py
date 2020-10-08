# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

import bpy
from bpy.types import Operator, Node, PropertyGroup
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.nodes.dictionary.dictionary_in import SvDict

SUPPORTED_TYPES = [
        ('float', "Float", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('int', "Integer", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('str', "String", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('bool', "Boolean", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('vector', "Vector", 'SvVerticesSocket', 'SvVectorColumnHandler')
    ]

supported_type_items = [(id, name, name) for id, name, sock, cls in SUPPORTED_TYPES]

type_handlers = dict([(id, cls) for id, name, sock, cls in SUPPORTED_TYPES])

type_sockets = dict([(id, sock) for id, name, sock, cls in SUPPORTED_TYPES])

class SvColumnDescriptor(PropertyGroup):
    name : StringProperty(name="Name")
    data_type : EnumProperty(name = "Type",
                    items = supported_type_items,
                    default = supported_type_items[0][0]
                )

class SvSpreadsheetValue(PropertyGroup):
    int_value : IntProperty(name="Value")
    float_value : FloatProperty(name="Value")
    str_value : StringProperty(name="Value")
    bool_value : BoolProperty(name="Value")
    vector_value : FloatVectorProperty(
            name = "Value", size=3)
    
    def get_value(self, data_type):
        prop_name = f"{data_type}_value"
        handler_name = type_handlers[data_type]
        handler = globals()[handler_name]
        value = getattr(self, prop_name)
        return handler.get_data(value)

class SvSpreadsheetRow(PropertyGroup):
    name : StringProperty(name="Name")
    items : CollectionProperty(name = "Columns", type=SvSpreadsheetValue)

    def get_data(self, column_descriptions):
        data = SvDict()
        for column, item in zip(column_descriptions, self.items):
            data.inputs[column.name] = {
                    'type' : type_sockets[column.data_type],
                    'name' : column.name,
                    'nest' : None
                }
            data[column.name] = item.get_value(column.data_type)
        return data

class SvSpreadsheetAddRow(bpy.types.Operator):
    bl_label = "Add spreadsheet row"
    bl_idname = "sverchok.spreadsheet_row_add"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    columns : CollectionProperty(name = "Columns", type=SvColumnDescriptor)

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        data_row = node.spreadsheet.data.add()
        for column in self.columns:
            data_row.items.add()
        updateNode(node, context)
        return {'FINISHED'}

class SvSpreadsheetData(PropertyGroup):
    columns : CollectionProperty(name = "Columns", type=SvColumnDescriptor)
    data : CollectionProperty(name = "Data", type=SvSpreadsheetRow)
    selected : IntProperty()
    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def draw(self, layout):
        n = len(self.columns)
        grid = layout.grid_flow(row_major=True, columns=n+1, align=True)
        grid.label(text="Item name")
        for column in self.columns:
            grid.label(text=column.name)
        for data_row in self.data:
            grid.prop(data_row, 'name', text='')
            for column, item in zip(self.columns, data_row.items):
                prop_type = column.data_type
                prop_name = f"{prop_type}_value"
                handler_name = type_handlers[prop_type]
                handler = globals()[handler_name]
                handler.draw(grid, item, prop_name, column.name)

        row = layout.row(align=True)
        add = row.operator(SvSpreadsheetAddRow.bl_idname, text='', icon='ADD')
        add.nodename = self.nodename
        add.treename = self.treename

        for column in self.columns:
            c = add.columns.add()
            c.name = column.name
            c.data_type = column.data_type

    def get_data(self):
        data = SvDict()
        for data_row in self.data:
            data[data_row.name] = data_row.get_data(self.columns)
            data.inputs[data_row.name] = {
                        'type': 'SvDictionarySocket',
                        'name': data_row.name,
                        'nest': data[data_row.name].inputs
                    }

        return data

class UI_UL_SvColumnDescriptorsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        row.prop(item, 'name', text='')
        row.prop(item, 'data_type', text='')

class SvSpreadsheetAddColumn(bpy.types.Operator):
    bl_label = "Add spreadsheet column"
    bl_idname = "sverchok.spreadsheet_column_add"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.spreadsheet.columns.add()
        for data_row in node.spreadsheet.data:
            data_row.items.add()
        updateNode(node, context)
        return {'FINISHED'}

class SvDefaultColumnHandler(object):
    @classmethod
    def draw(cls, layout, item, prop_name, prop_title):
        layout.prop(item, prop_name, text='')

    @classmethod
    def get_data(cls, data):
        return data

class SvVectorColumnHandler(object):
    @classmethod
    def draw(cls, layout, item, prop_name, prop_title):
        layout.template_component_menu(item, prop_name, name=prop_title)

    @classmethod
    def get_data(cls, data):
        return tuple(data)

class SvDataInputNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: spreadsheet data input
    Tooltip: Input data with spreadsheet-like interface
    """

    bl_idname = 'SvDataInputNode'
    bl_label = "Data Input"
    bl_icon = 'MATERIAL'

    spreadsheet : PointerProperty(type=SvSpreadsheetData)

    def sv_init(self, context):
        self.width = 600
        self.outputs.new('SvDictionarySocket', "Data")

    def sv_update(self):
        self.spreadsheet.nodename = self.name
        self.spreadsheet.treename = self.id_data.name

    def draw_buttons(self, context, layout):
        self.spreadsheet.draw(layout)

    def draw_buttons_ext(self, context, layout):
        layout.template_list("UI_UL_SvColumnDescriptorsList", "columns", self.spreadsheet, "columns", self.spreadsheet, "selected")

        row = layout.row(align=True)
        add = row.operator(SvSpreadsheetAddColumn.bl_idname, text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        data = self.spreadsheet.get_data()
        self.outputs['Data'].sv_set([data])

classes = [
        SvColumnDescriptor, SvSpreadsheetValue,
        SvSpreadsheetRow, SvSpreadsheetData,
        UI_UL_SvColumnDescriptorsList,
        SvSpreadsheetAddColumn, SvSpreadsheetAddRow,
        SvDataInputNode
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

