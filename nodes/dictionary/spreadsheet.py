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

from collections import defaultdict

import bpy
from bpy.props import CollectionProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat, zip_long_repeat
from sverchok.utils.logging import info, debug
from sverchok.utils.modules.spreadsheet.ui import *

class SvSpreadsheetNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: spreadsheet data input
    Tooltip: Input data with spreadsheet-like interface
    """

    bl_idname = 'SvSpreadsheetNode'
    bl_label = "Spreadsheet"
    bl_icon = 'MATERIAL'

    spreadsheet : PointerProperty(type=SvSpreadsheetData)

    def sv_init(self, context):
        self.width = 500
        self.inputs.new('SvDictionarySocket', "Input")
        self.outputs.new('SvDictionarySocket', "Data")
        self.outputs.new('SvDictionarySocket', "Rows")
        self.outputs.new('SvDictionarySocket', "Columns")

        column = self.add_column()
        column.name = "Value"

        row = self.add_row()
        row.name = "Item"

    def sv_update(self):
        self.spreadsheet.set_node(self)
        self.adjust_sockets()

    def draw_buttons(self, context, layout):
        self.spreadsheet.draw(layout)

    def draw_buttons_ext(self, context, layout):
        layout.template_list("UI_UL_SvColumnDescriptorsList", "columns", self.spreadsheet, "columns", self.spreadsheet, "selected")

        row = layout.row(align=True)
        add = row.operator(SvSpreadsheetAddColumn.bl_idname, text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name

    def adjust_sockets(self):
        variables = self.spreadsheet.get_variables()
        for key in self.inputs.keys():
            if (key not in variables) and key not in ['Input']:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

        formula_cols = self.spreadsheet.get_formula_cols()
        self.inputs['Input'].hide_safe = len(formula_cols) == 0

    @throttled
    def on_update_value(self, context):
        self.adjust_sockets()

    @throttled
    def on_update_column(self, context):
        self.adjust_sockets()
        
    def add_row(self):
        data_row = self.spreadsheet.data.add()
        for column in self.spreadsheet.columns:
            item = data_row.items.add()
            item.treename = self.id_data.name
            item.nodename = self.name
        return data_row

    def move_row(self, selected_index, shift, context):
        next_index = selected_index + shift
        if (0 <= selected_index < len(self.spreadsheet.data)) and (0 <= next_index < len(self.spreadsheet.data)):
            self.spreadsheet.data.move(selected_index, next_index)
            updateNode(self, context)

    def add_column(self):
        column = self.spreadsheet.columns.add()
        for data_row in self.spreadsheet.data:
            item = data_row.items.add()
            item.treename = self.id_data.name
            item.nodename = self.name
        return column

    def remove_column(self, idx):
        self.spreadsheet.columns.remove(idx)
        for data_row in self.spreadsheet.data:
            data_row.items.remove(idx)

    def move_column(self, selected_index, shift, context):
        next_index = selected_index + shift
        if (0 <= selected_index < len(self.spreadsheet.columns)) and (0 <= next_index < len(self.spreadsheet.columns)):
            self.spreadsheet.columns.move(selected_index, next_index)
            for data_row in self.spreadsheet.data:
                data_row.items.move(selected_index, next_index)
            updateNode(self, context)

    def get_input(self):
        variables = self.spreadsheet.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()
        return inputs

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        input_data_s = self.inputs['Input'].sv_get(default = [None])

        var_names = self.spreadsheet.get_variables()
        inputs = self.get_input()
        input_values = [inputs.get(name, [[0]]) for name in var_names]
        if var_names:
            parameters = match_long_repeat([input_data_s] + input_values)
        else:
            parameters = [input_data_s]

        data_out = []
        rows_out = []
        columns_out = []
        for input_data, *objects in zip(*parameters):
            if var_names:
                var_values_s = zip_long_repeat(*objects)
            else:
                var_values_s = [[]]
            for var_values in var_values_s:
                variables = dict(zip(var_names, var_values))
            
                data = self.spreadsheet.evaluate(input_data, variables)
                data_out.append(data)

                rows = list(data.values())
                rows_out.extend(rows)

                columns = defaultdict(dict)
                for row_key, row in data.items():
                    for col_key, item in row.items():
                        columns[col_key][row_key] = item
                columns = list(columns.values())
                columns_out.extend(columns)

        self.outputs['Data'].sv_set(data_out)
        self.outputs['Rows'].sv_set(rows_out)
        self.outputs['Columns'].sv_set(columns_out)

classes = [
        SvColumnDescriptor, SvSpreadsheetValue,
        SvSpreadsheetRow, SvSpreadsheetData,
        UI_UL_SvColumnDescriptorsList,
        SvSpreadsheetAddColumn, SvSpreadsheetRemoveColumn, SvSpreadsheetMoveColumn,
        SvSpreadsheetAddRow, SvSpreadsheetRemoveRow, SvSpreadsheetMoveRow,
        SvSpreadsheetNode
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

