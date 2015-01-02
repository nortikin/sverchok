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
from bpy.props import EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class SvSortObjsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Sort Objects '''
    bl_idname = 'SvSortObjsNode'
    bl_label = 'sort_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("xax",   "X Axis",   "", 1),
        ("yax",   "Y Axis",   "", 2),
        ("zax",   "Z Axis",   "", 3),
        ("cust",   "Custom Value",   "", 4),
    ]

    Modes = EnumProperty(name="sortmodes", description="Sorting Objects modes",
                         default="xax", items=modes, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('StringsSocket', 'CustomValue')
        self.outputs.new('SvObjectSocket', 'Object')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Modes", "Sort Objs")

    def process(self):
        siob = self.inputs['Object']
        SM = self.Modes
        if siob.is_linked or siob.object_ref:
            X = siob.sv_get()
            if SM == "xax":
                Y = [i.location.x for i in X]
            elif SM == "yax":
                Y = [i.location.y for i in X]
            elif SM == "zax":
                Y = [i.location.z for i in X]
            elif SM == "cust":
                if self.inputs['CustomValue'].is_linked:
                    Y = self.inputs['CustomValue'].sv_get()[0]
                else:
                    return

            X.sort(key=dict(zip(X, Y)).get)

        self.outputs['Object'].sv_set(X)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvSortObjsNode)


def unregister():
    bpy.utils.unregister_class(SvSortObjsNode)
