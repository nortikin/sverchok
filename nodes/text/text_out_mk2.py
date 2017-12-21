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

# made by: Linus Yng, haxed by zeffii to mk2
# pylint: disable=c0326

import io
import csv
import json
import itertools
import pprint
import sverchok

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import node_id, multi_socket, updateNode

from sverchok.utils.sv_text_io_common import (
    FAIL_COLOR, READY_COLOR, TEXT_IO_CALLBACK,
    get_socket_type,
    new_output_socket,
    name_dict,
    text_modes
)


class SvTextOutNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Text Output Node '''
    bl_idname = 'SvTextOutNodeMK2'
    bl_label = 'Text out+'
    bl_icon = 'OUTLINER_OB_EMPTY'

    sv_modes = [
        ('compact',     'Compact',      'Using str()',        1),
        ('pretty',      'Pretty',       'Using pretty print', 2)]

    json_modes = [
        ('compact',     'Compact',      'Minimal',            1),
        ('pretty',      'Pretty',       'Indent and order',   2)]

    csv_dialects = [
        ('excel',       'Excel',        'Standard excel',     1),
        ('excel-tab',   'Excel tabs',   'Excel tab format',   2),
        ('unix',        'Unix',         'Unix standard',      3)]

    def change_mode(self, context):
        self.inputs.clear()

        if self.text_mode == 'CSV':
            self.inputs.new('StringsSocket', 'Col 0')
            self.base_name = 'Col '
        elif self.text_mode == 'JSON':
            self.inputs.new('StringsSocket', 'Data 0')
            self.base_name = 'Data '
        elif self.text_mode == 'SV':
            self.inputs.new('StringsSocket', 'Data')

    text = StringProperty()

    text_mode = EnumProperty(items=text_modes, default='CSV', update=change_mode)
    csv_dialect = EnumProperty(items=csv_dialects, default='excel')
    sv_mode = EnumProperty(items=sv_modes, default='compact')
    json_mode = EnumProperty(items=json_modes, default='pretty')

    append = BoolProperty(default=False, description="Append to output file")
    base_name = StringProperty(name='base_name', default='Col ')
    multi_socket_type = StringProperty(name='multi_socket_type', default='StringsSocket')

    autodump = BoolProperty(default=False, description="autodump")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Col 0', 'Col 0')

    def draw_buttons(self, context, layout):

        addon = context.user_preferences.addons.get(sverchok.__name__)
        over_sized_buttons = addon.preferences.over_sized_buttons

        col = layout.column(align=True)
        col.prop(self, 'autodump', "auto dump", toggle=True)
        row = col.row(align=True)
        row.prop_search(self, 'text', bpy.data, 'texts', text="Output to")

        row = col.row(align=True)
        row.prop(self, 'text_mode', "Text format", expand=True)

        row = col.row(align=True)
        if self.text_mode == 'CSV':
            row.prop(self, 'csv_dialect', "Dialect")
        elif self.text_mode == 'SV':
            row.prop(self, 'sv_mode', "Format", expand=True)
        elif self.text_mode == 'JSON':
            row.prop(self, 'json_mode', "Format", expand=True)

        col2 = col.column(align=True)
        row = col2.row(align=True)
        if not self.autodump:
            row.scale_y = 4.0 if over_sized_buttons else 1
            row.operator(TEXT_IO_CALLBACK, text='D U M P').fn_name = 'dump'
            col2.prop(self, 'append', "Append")

    def update_socket(self, context):
        self.update()

    def process(self):
        if self.text_mode in {'CSV', 'JSON'}:
            multi_socket(self, min=1)

        if self.autodump:
            self.append = False
            self.dump()

    # build a string with data from sockets
    def dump(self):
        out = self.get_data()
        if len(out) == 0:
            return False

        if not self.append:
            bpy.data.texts[self.text].clear()
        bpy.data.texts[self.text].write(out)
        self.color = READY_COLOR

        return True

    def get_data(self):
        out = ""
        if self.text_mode == 'CSV':
            data_out = []
            for socket in self.inputs:
                if socket.is_linked:

                    tmp = socket.sv_get(deepcopy=False)
                    if tmp:
                        # flatten list
                        data_out.extend(list(itertools.chain.from_iterable([tmp])))

            csv_str = io.StringIO()
            writer = csv.writer(csv_str, dialect=self.csv_dialect)
            for row in zip(*data_out):
                writer.writerow(row)

            out = csv_str.getvalue()

        elif self.text_mode == 'JSON':
            data_out = {}

            for socket in self.inputs:
                if socket.is_linked:
                    tmp = socket.sv_get(deepcopy=False)
                    if tmp:
                        tmp_name = socket.links[0].from_node.name+':'+socket.links[0].from_socket.name
                        name = tmp_name
                        j = 1
                        while name in data_out:
                            name = tmp_name+str(j)
                            j += 1

                        data_out[name] = (get_socket_type(self, socket.name), tmp)

            if self.json_mode == 'pretty':
                out = json.dumps(data_out, indent=4)
            else:
                out = json.dumps(data_out, separators=(',', ':'))

        elif self.text_mode == 'SV':
            if self.inputs['Data'].links:
                data = self.inputs['Data'].sv_get(deepcopy=False)
                if self.sv_mode == 'pretty':
                    out = pprint.pformat(data)
                else:  # compact
                    out = str(data)
        return out


def register():
    bpy.utils.register_class(SvTextOutNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvTextOutNodeMK2)
