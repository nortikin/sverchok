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
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty, CollectionProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.logging import debug

MODE_INSIDE_ON = "INSIDE ON"
MODE_INSIDE_OFF = "INSIDE OFF"
MODE_PASS_THROUGH = "PASS THROUGH"

ZONE_BELOW = 1
ZONE_INSIDE = 2
ZONE_ABOVE = 3

switch_mode_items = [(MODE_INSIDE_ON, "Inside ON", "", 1),
                     (MODE_INSIDE_OFF, "Inside OFF", "", 2),
                     (MODE_PASS_THROUGH, "Pass Through", "", 3)]


class SvSwitchOperatorCallback(bpy.types.Operator):
    ''' Callbacks to the main node '''
    bl_idname = "nodes.sv_switch_callback"
    bl_label = "Sv Ops Switch callback"

    function_name: StringProperty()  # what function to call

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(context)
        return {"FINISHED"}


class SvSwitchPropertyGroup(bpy.types.PropertyGroup):
    ''' Switch class used by the node to keep track of multiple switches '''

    switch_state: BoolProperty(
        name="State", description="Current state of the switch",
        default=False)

    switch_zone: IntProperty(
        name="Zone", description="Zone number the value is in relative to the range (1,2,3)",
        default=ZONE_BELOW)

    switch_last_zone: IntProperty(
        name="Last Zone", description="Last zone number (1,2,3)",
        default=ZONE_BELOW)

    @property
    def state(self):
        return self.switch_state

    @property
    def zone(self):
        return self.switch_zone

    def toggle_state(self):
        self.switch_state = not self.switch_state

    def update_switch(self, mode, val, minB, maxB):
        if val < minB:
            self.switch_zone = ZONE_BELOW
        elif val <= maxB:
            self.switch_zone = ZONE_INSIDE
        else:  # val > maxB
            self.switch_zone = ZONE_ABOVE

        if mode == MODE_INSIDE_ON:
            if self.switch_zone == ZONE_INSIDE:
                self.switch_state = True
            else:
                self.switch_state = False

        elif mode == MODE_INSIDE_OFF:
            if self.switch_zone == ZONE_INSIDE:
                self.switch_state = False
            else:
                self.switch_state = True

        elif mode == MODE_PASS_THROUGH:
            if self.switch_last_zone == ZONE_BELOW:
                if self.switch_zone == ZONE_ABOVE:
                    self.switch_last_zone = self.switch_zone
                    self.switch_state = not self.switch_state

            elif self.switch_last_zone == ZONE_ABOVE:
                if self.switch_zone == ZONE_BELOW:
                    self.switch_last_zone = self.switch_zone
                    self.switch_state = not self.switch_state
        else:
            raise Exception("Unknown mode: {}".format(mode))


class SvRangeSwitchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Switch, Range
    Tooltip: Switches state based on a value relative to a value range.
    """
    bl_idname = 'SvRangeSwitchNode'
    bl_label = 'Range Switch'
    bl_icon = "SNAP_INCREMENT"

    switches: CollectionProperty(name="Switches", type=SvSwitchPropertyGroup)

    """
    [0]-- outside -->[b1]<-- inside -->[b2]<-- outside --> (+)

    INSIDE ON mode:

    OFF ---> |b1| <-- ON --> |b2| <--- OFF   # inside ON,  outside OFF

    INSIDE OFF mode:

    ON  ---> |b1| <-- OFF --> |b2| <--- ON   # inside OFF, outside ON

    PASS THROUGH mode:

    ON  ---> |b1| -- ON --> |b2| ---> OFF    # pass through range switches state
    ON  <--- |b1| <- OFF -- |b2| <--- OFF    #
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

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text="")

        if self.mode == MODE_PASS_THROUGH:
            cb = SvSwitchOperatorCallback.bl_idname
            button = layout.operator(cb, text='Toggle Switch')
            button.function_name = "toggle_state"

    def toggle_state(self, context):
        for switch in self.switches:
            switch.toggle_state()

        updateNode(self, context)

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('SvStringsSocket', "val").prop_name = 'range_val'
        self.inputs.new('SvStringsSocket', "b1").prop_name = 'range_b1'
        self.inputs.new('SvStringsSocket', "b2").prop_name = 'range_b2'

        self.outputs.new('SvStringsSocket', "State")
        self.outputs.new('SvStringsSocket', "Zone")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_val = self.inputs["val"].sv_get()[0]
        input_b1 = self.inputs["b1"].sv_get()[0]
        input_b2 = self.inputs["b2"].sv_get()[0]

        parameters = match_long_repeat([input_val, input_b1, input_b2])

        # update the numberr of switches based on number of inputs
        old_switch_count = len(self.switches)
        new_switch_count = len(parameters[0])

        # did the number of switches change ? => add or remove switches
        if old_switch_count != new_switch_count:
            if new_switch_count > old_switch_count:  # add new switches
                for n in range(old_switch_count, new_switch_count):
                    debug("creating new switch")
                    switch = self.switches.add()
            else:  # remove old switches
                while len(self.switches) > new_switch_count:
                    n = len(self.switches) - 1
                    debug("removing old switch")
                    self.switches.remove(n)

        # update switches
        state_list = []
        zone_list = []
        for i, params in enumerate(zip(*parameters)):
            val, b1, b2 = params
            minB = min(b1, b2)
            maxB = max(b1, b2)

            switch = self.switches[i]
            switch.update_switch(self.mode, val, minB, maxB)

            state_list.append(switch.state)
            zone_list.append(switch.zone)

        self.outputs["State"].sv_set([state_list])
        self.outputs["Zone"].sv_set([zone_list])


classes = [SvSwitchPropertyGroup, SvSwitchOperatorCallback, SvRangeSwitchNode]


def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(classes)]
