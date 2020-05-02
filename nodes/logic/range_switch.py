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
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

MODE_INSIDE_ON = "INSIDE ON"
MODE_INSIDE_OFF = "INSIDE OFF"
MODE_PASS_THROUGH = "PASS THROUGH"

switch_mode_items = [(MODE_INSIDE_ON, "Inside ON", "", 1),
                     (MODE_INSIDE_OFF, "Inside OFF", "", 2),
                     (MODE_PASS_THROUGH, "Pass Through", "", 3)]


class SvSwitchOperatorCallback(bpy.types.Operator):
    ''' Callbacks to the main node '''
    bl_idname = "nodes.sv_switcher_callback"
    bl_label = "Sv Ops Switcher callback"

    function_name: StringProperty()  # what function to call

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(context)
        return {"FINISHED"}


class SvRangeSwitchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Switch, Range
    Tooltip: Switches state for a value relative to a value range.
    """
    bl_idname = 'SvRangeSwitchNode'
    bl_label = 'Range Switch'
    bl_icon = "SNAP_INCREMENT"

    """
    (-) ----[0]---outside---[b1]---inside---[b2]---outside ---> (+)

    INSIDE ON mode:

    OFF      |b1|    ON     |b2|    OFF     # inside ON,  outside OFF

    INSIDE OFF mode:

    ON       |b1|    OFF    |b2|    ON      # inside OFF, outside ON

    PASS THROUGH mode:

    ON  ->   |b1|  - ON ->  |b2| -> OFF     # pass through switches state
    ON  <-   |b1| <- OFF -  |b2| <- OFF     #
    """
    mode: EnumProperty(
        name="Mode", description="Select a switch behavior",
        items=switch_mode_items,
        default=MODE_PASS_THROUGH,
        update=updateNode)

    range_val: FloatProperty(
        name="Value", description="Value",
        default=0.0,
        update=updateNode)

    range_b1: FloatProperty(
        name="Boundary 1", description="First boundary of the range",
        default=1.0,
        update=updateNode)

    range_b2: FloatProperty(
        name="Boundary 2", description="Second boundary of the range",
        default=2.0,
        update=updateNode)

    state: BoolProperty(
        name="State", description="Current state of the switch",
        default=False)

    last_zone: IntProperty(
        name="Last Zone", description="Last zone number (1,2,3)",
        default=1)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text="")

        if self.mode == MODE_PASS_THROUGH:
            cb = SvSwitchOperatorCallback.bl_idname
            button = layout.operator(cb, text='Toggle Switch')
            button.function_name = "toggle_state"

    def toggle_state(self, context):
        self.state = not self.state
        updateNode(self, context)

    def get_zone(self, val, minB, maxB):
        if val < minB:
            return 1
        elif val < maxB:
            return 2
        else:  # val > maxB
            return 3

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('SvStringsSocket', "val").prop_name = 'range_val'
        self.inputs.new('SvStringsSocket', "b1").prop_name = 'range_b1'
        self.inputs.new('SvStringsSocket', "b2").prop_name = 'range_b2'

        self.outputs.new('SvStringsSocket',  "State")
        self.outputs.new('SvStringsSocket',  "Zone")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_val = self.inputs["val"].sv_get()[0][0]
        input_b1 = self.inputs["b1"].sv_get()[0][0]
        input_b2 = self.inputs["b2"].sv_get()[0][0]

        input_val = abs(input_val)
        input_b1 = abs(input_b1)
        input_b2 = abs(input_b2)

        val = input_val
        minB = min(input_b1, input_b2)
        maxB = max(input_b1, input_b2)

        zone = self.get_zone(val, minB, maxB)

        if self.mode == MODE_INSIDE_ON:
            if zone == 2:
                self.state = True
            else:
                self.state = False

        elif self.mode == MODE_INSIDE_OFF:
            if zone == 2:
                self.state = False
            else:
                self.state = True

        else:  # PASS through switch ON->OFF, OFF->ON
            if self.last_zone == 1:
                if zone == 3:
                    self.last_zone = zone
                    self.state = not self.state

            elif self.last_zone == 3:
                if zone == 1:
                    self.last_zone = zone
                    self.state = not self.state

        self.outputs["State"].sv_set([[self.state]])
        self.outputs["Zone"].sv_set([[zone]])


def register():
    bpy.utils.register_class(SvSwitchOperatorCallback)
    bpy.utils.register_class(SvRangeSwitchNode)


def unregister():
    bpy.utils.unregister_class(SvRangeSwitchNode)
    bpy.utils.unregister_class(SvSwitchOperatorCallback)
