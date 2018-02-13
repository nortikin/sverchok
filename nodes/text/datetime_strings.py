# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

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

import datetime

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat


class SvDatetimeStrings(bpy.types.Node, SverchCustomTreeNode):
    ''' a SvDatetimeStrings f '''
    bl_idname = 'SvDatetimeStrings'
    bl_label = 'Datetime Strings'
    bl_icon = 'SORTTIME'

    date_pattern = bpy.props.StringProperty(default="%m/%d/%Y", description="date formatting information", name="Date Time String Formatter")
    time_offset = bpy.props.StringProperty(default="01/01/2018", description="for graphing purposes you might need to subtract a start date", name='offset')

    def sv_init(self, context):
        self.inputs.new("StringsSocket", "times")
        self.inputs.new("StringsSocket", "time offset").prop_name="time_offset"
        self.outputs.new("StringsSocket", "times")

    def draw_buttons(self, context, layout):
        layout.prop(self, "date_pattern", text="Format", icon="SQRTTIME")

    def process(self):

        V1 = self.inputs["times"].sv_get()
        V2 = self.inputs["time offset"].sv_get()

        if len(V1) == len(V2):
            # all times have an offset
            pass
        elif len(V1) == len(V2[0]):
            V2 = [[v] for v in V2[0]]
        elif len(V1) > len(V2) and len(V2):
            V1, V2 = match_long_repeat([V1, V2])
        else:
            print("see source code to show why execution is displaying this message")
            return

        VC_main = []
        for V, offset in zip(V1, V2):
            VC = []
            ordinal_offset = datetime.datetime.strptime(offset[0], self.date_pattern).toordinal()
            for value in V:
                t = datetime.datetime.strptime(value, self.date_pattern).toordinal()
                m = t - ordinal_offset
                VC.append(m)
            VC_main.append(VC)

        self.outputs['times'].sv_set(VC_main)


def register():
    bpy.utils.register_class(SvDatetimeStrings)


def unregister():
    bpy.utils.unregister_class(SvDatetimeStrings)
