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
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty

from sverchok.data_structure import updateNode
from sverchok.utils.dictionary import SvDict
from sverchok.utils.modules.eval_formula import get_variables
from sverchok.utils.modules.spreadsheet.evaluator import eval_spreadsheet, SvSpreadsheetAccessor

SUPPORTED_TYPES = [
        ('float', "Float", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('int', "Integer", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('str', "String", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('bool', "Boolean", 'SvStringsSocket', 'SvDefaultColumnHandler'),
        ('vector', "Vector", 'SvVerticesSocket', 'SvVectorColumnHandler'),
        ('formula', "Formula", 'SvStringsSocket', 'SvDefaultColumnHandler')
    ]

supported_type_items = [(id, name, name) for id, name, sock, cls in SUPPORTED_TYPES]

type_handlers = dict([(id, cls) for id, name, sock, cls in SUPPORTED_TYPES])

type_sockets = dict([(id, sock) for id, name, sock, cls in SUPPORTED_TYPES])

class SvColumnDescriptor(PropertyGroup):
    def update_column(self, context):
        if hasattr(context, 'node'):
            context.node.on_update_column(context)
        else:
            pass

    name : StringProperty(name="Name", update=update_column)
    data_type : EnumProperty(name = "Type",
                    items = supported_type_items,
                    default = supported_type_items[0][0],
                    update = update_column
                )

class SvSpreadsheetValue(PropertyGroup):

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def update_value(self, context):
        if hasattr(context, 'node'):
            node = context.node
        else:
            node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.on_update_value(context)

    int_value : IntProperty(name="Value", update=update_value)
    float_value : FloatProperty(name="Value", update=update_value)
    str_value : StringProperty(name="Value", update=update_value)
    bool_value : BoolProperty(name="Value", update=update_value)
    vector_value : FloatVectorProperty(
            name = "Value", size=3,
            update=update_value)
    formula_value : StringProperty(name="Formula", update=update_value)
    
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

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.add_row()
        updateNode(node, context)
        return {'FINISHED'}

class SvSpreadsheetRemoveRow(bpy.types.Operator):
    bl_label = "Remove spreadsheet row"
    bl_idname = "sverchok.spreadsheet_row_remove"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = self.item_index
        node.spreadsheet.data.remove(idx)
        updateNode(node, context)
        return {'FINISHED'}

class SvSpreadsheetMoveRow(bpy.types.Operator):
    bl_label = "Move spreadsheet row"
    bl_idname = "sverchok.spreadsheet_row_shift"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')
    shift : IntProperty(name='shift')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        selected_index = self.item_index
        node.move_row(self.item_index, self.shift, context)
        return {'FINISHED'}

class SvSpreadsheetData(PropertyGroup):
    columns : CollectionProperty(name = "Columns", type=SvColumnDescriptor)
    data : CollectionProperty(name = "Data", type=SvSpreadsheetRow)
    selected : IntProperty()
    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def draw(self, layout):
        n = len(self.columns)
        grid = layout.grid_flow(row_major=True, columns=n+4, align=True)
        grid.label(text="Item name")
        for column in self.columns:
            grid.label(text=column.name)
        grid.separator()
        grid.separator()
        grid.separator()
        for index, data_row in enumerate(self.data):
            grid.prop(data_row, 'name', text='')
            for column, item in zip(self.columns, data_row.items):
                prop_type = column.data_type
                prop_name = f"{prop_type}_value"
                handler_name = type_handlers[prop_type]
                handler = globals()[handler_name]
                handler.draw(grid, item, prop_name, column.name)

            up = grid.operator(SvSpreadsheetMoveRow.bl_idname, text='', icon='TRIA_UP')
            up.nodename = self.nodename
            up.treename = self.treename
            up.item_index = index
            up.shift = -1

            down = grid.operator(SvSpreadsheetMoveRow.bl_idname, text='', icon='TRIA_DOWN')
            down.nodename = self.nodename
            down.treename = self.treename
            down.item_index = index
            down.shift = 1

            remove = grid.operator(SvSpreadsheetRemoveRow.bl_idname, text='', icon='REMOVE')
            remove.nodename = self.nodename
            remove.treename = self.treename
            remove.item_index = index

        row = layout.row(align=True)
        add = row.operator(SvSpreadsheetAddRow.bl_idname, text='', icon='ADD')
        add.nodename = self.nodename
        add.treename = self.treename

    def set_node(self, node):
        self.treename = node.id_data.name
        self.nodename = node.name
        for data_row in self.data:
            for item in data_row.items:
                item.treename = self.treename
                item.nodename = self.nodename

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

    def get_formula_cols(self):
        formula_cols = [col.name for col in self.columns if col.data_type == 'formula']
        return formula_cols

    def evaluate(self, input_data, variables):
        formula_cols = self.get_formula_cols()
        src_dict = self.get_data()
        if not formula_cols:
            return src_dict
        else:
            row_names = list(src_dict.keys())
            variables = variables.copy()
            variables['Input'] = SvSpreadsheetAccessor(input_data)
            return eval_spreadsheet(src_dict, row_names, formula_cols, variables)

    def get_variables(self):
        src_dict = self.get_data()
        formula_cols = self.get_formula_cols()
        variables = set()
        for data_row in src_dict.values():
            for col_name in formula_cols:
                formula = data_row[col_name]
                vs = get_variables(formula)
                variables.update(vs)

        row_names = set()
        for data_row in self.data:
            row_names.add(data_row.name)
        variables.difference_update(row_names)
        if 'Input' in variables:
            variables.remove('Input')
        return variables

class UI_UL_SvColumnDescriptorsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        row.prop(item, 'name', text='')
        row.prop(item, 'data_type', text='')

        # data is SvSpreadsheetData here
        up = row.operator(SvSpreadsheetMoveColumn.bl_idname, text='', icon='TRIA_UP')
        up.nodename = data.nodename
        up.treename = data.treename
        up.item_index = index
        up.shift = -1

        down = row.operator(SvSpreadsheetMoveColumn.bl_idname, text='', icon='TRIA_DOWN')
        down.nodename = data.nodename
        down.treename = data.treename
        down.item_index = index
        down.shift = 1

        remove = row.operator(SvSpreadsheetRemoveColumn.bl_idname, text='', icon='REMOVE')
        remove.nodename = data.nodename
        remove.treename = data.treename
        remove.item_index = index

class SvSpreadsheetAddColumn(bpy.types.Operator):
    bl_label = "Add spreadsheet column"
    bl_idname = "sverchok.spreadsheet_column_add"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.add_column()
        updateNode(node, context)
        return {'FINISHED'}

class SvSpreadsheetRemoveColumn(bpy.types.Operator):
    bl_label = "Remove spreadsheet column"
    bl_idname = "sverchok.spreadsheet_column_remove"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = self.item_index
        node.remove_column(idx)
        updateNode(node, context)
        return {'FINISHED'}

class SvSpreadsheetMoveColumn(bpy.types.Operator):
    bl_label = "Move spreadsheet column"
    bl_idname = "sverchok.spreadsheet_column_shift"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')
    shift : IntProperty(name='shift')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        selected_index = self.item_index
        node.move_column(self.item_index, self.shift, context)
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

