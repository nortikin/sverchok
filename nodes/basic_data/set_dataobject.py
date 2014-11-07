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

import parser
import mathutils
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode, VerticesSocket
from sverchok.data_structure import (updateNode, 
                                     SvGetSocketAnyType, match_long_repeat)


class SvSetDataObjectNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Set Object Props '''
    bl_idname = 'SvSetDataObjectNode'
    bl_label = 'set_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("location",   "Location",   "", 1),
        ("scale",   "Scale",   "", 2),
        ("rotation_euler",   "Rotation_Euler",   "", 3),
        ("delta_location",   "Delta_Location",   "", 4),
        ("delta_scale",   "Delta_Scale",   "", 5),
        ("delta_rotation_euler",   "Delta_Rotation_Euler",   "", 6),
        ("custom",   "Custom",   "", 7)
    ]

    formula = StringProperty(name='formula',
                             description='property to asign value',
                             default='select', update=updateNode)

    Modes = EnumProperty(name="property modes", description="Objects property",
                         default="location", items=modes, update=updateNode)

    def draw_buttons(self, context, layout):
        if self.Modes == 'custom':
            layout.prop(self,  "formula", text="")
        row = layout.row(align=True)
        layout.prop(self, "Modes", "Objects property")

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Objects')
        self.inputs.new('VerticesSocket', 'values')

    def process(self):
        SGSAT = SvGetSocketAnyType
        if self.inputs['Objects'].links and self.inputs['values'].links:

            ObjectID = SGSAT(self, self.inputs['Objects'])[0]
            if isinstance(SGSAT(self, self.inputs['values'])[0][0],(tuple)):
                Val = [Vector(i) for i in SGSAT(self, self.inputs['values'])[0]]
            else:
                Val = SGSAT(self, self.inputs['values'])[0]

            temp = match_long_repeat([ObjectID, Val])
            ObjectID, Val = temp[0], temp[1]

            if self.Modes != 'custom':
                Prop = self.Modes
            else:
                Prop = self.formula

            g = 0
            while g != len(ObjectID):
                if ObjectID[g] != None:
                    exec("ObjectID[g]."+Prop+"= Val[g]")
                g = g+1

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvSetDataObjectNode)


def unregister():
    bpy.utils.unregister_class(SvSetDataObjectNode)
