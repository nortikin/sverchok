# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import inspect

import bpy
from bpy.props import IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from collections import OrderedDict

GREEK_LABELS = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
    "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"]

GENERIC_SOCKET = "SvStringsSocket"
SEPARATOR_SOCKET = "SvSeparatorSocket"
MAX_SET_SIZE = 9
MAX_NUM_SWITCHES = 9

def get_indices_that_should_be_visible(max_groups, num_visible_groups, max_items_per_group, num_items_per_group):
    socket_index = 1
    node = {}
    node[0] = True # selector always visible, first socket
    for group_index in range(max_groups):
        node[socket_index] = group_index < num_visible_groups
        socket_index += 1
        for set_item in range(max_items_per_group):
            node[socket_index] = (group_index < num_visible_groups and set_item < num_items_per_group) 
            socket_index += 1

    g = "".join(["01"[k] for k in node.values()])
    print(g)
    return node

class SvInputSwitchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sets, Switch, Select
    Tooltip: Switch among multiple input sets
    """

    bl_idname = 'SvInputSwitchNode'
    bl_label = 'Input Switch'
    sv_icon = 'SV_INPUT_SWITCH'

    def interface_fully_initialized(self):
        return len(self.outputs) == MAX_SET_SIZE

    def replace_socket_if_needed(self, input_socket):
        if input_socket.bl_idname != input_socket.other.bl_idname:
            input_socket.replace_socket(input_socket.other.bl_idname)

    def update_node_sockets_per_set(self, context):
        print('doing', inspect.stack()[0][3])

        # reconfigure _ output _ sockets
        for i in range(MAX_SET_SIZE):
            socket = self.outputs[i]
            desired_state = (i > (self.num_sockets_per_set - 1))
            if socket.hide != desired_state:
                socket.hide_safe = desired_state

        # reconfigure _ input _ sockets
        pass

    def adjust_input_socket_bl_idname_to_match_linked_input(self):
        for input_socket in self.inputs:
            if input_socket.is_linked:
                self.replace_socket_if_needed(input_socket)

    def adjust_output_sockets_bl_idname_to_match_selected_set(self, remap_indices):
        for out_idx, in_idx in enumerate(remap_indices):
            input_bl_idname = self.inputs[in_idx].bl_idname
            if input_bl_idname != self.outputs[out_idx].bl_idname:
                self.outputs[out_idx].replace_socket(input_bl_idname)

    @property
    def not_already_maxed_out(self):
        return self.num_switches < MAX_NUM_SWITCHES

    @property
    def any_sockets_of_last_input_set_connected(self):
        """ if the node looks like:
            alpha 1
            alpha 2
            beta 1   <-   if any of these gets a linked socket, the next socket set is automatically generated
            beta 2   <-
            gamma 1
            gamma 2
        """
        last_index = len(self.inputs)  # should reflect 
        first_index = last_index - self.num_sockets_per_set
        # [ ] get indices of last visible input set

        return any([self.inputs[idx].is_linked for idx in range(first_index, last_index)])

    def initialize_input_sockets(self):
        inew = self.inputs.new
        inew(GENERIC_SOCKET, "Selected").prop_name = "selected"
        for group in range(MAX_NUM_SWITCHES):
            socket = inew(SEPARATOR_SOCKET, f"Separator {group}")
            for set_item in range(MAX_SET_SIZE):
                inew(GENERIC_SOCKET, f"{GREEK_LABELS[group]} {set_item}")
        
    def initialize_output_sockets(self):
        """ create all needed output sockets, but hide beyond set size """
        onew = self.outputs.new
        for i in range(MAX_SET_SIZE):
            sock = onew(GENERIC_SOCKET, f"Data {i}")
            if i >= self.num_sockets_per_set:
                sock.hide_safe = True

    def collect_input_indices_to_map(self):
        """ which input socket indices are associated with the selected set """
        print('doing', inspect.stack()[0][3])
        return [2, 3]

    def unhide_sockets_to_cope_with_switchnum(self):
        tndict = get_indices_that_should_be_visible(MAX_NUM_SWITCHES, self.num_switches, MAX_SET_SIZE, self.num_sockets_per_set)
        for key, value in tndict.items():
            socket = self.inputs[key]
            desired_hide_state = not(value)
            if not socket.hide == desired_hide_state:
                socket.hide_safe = desired_hide_state

    def interface_unhide_inputs_to_handle_new_set_if_needed(self):
        if self.not_already_maxed_out and self.any_sockets_of_last_input_set_connected:
            self.num_switches += 1
            self.unhide_sockets_to_cope_with_switchnum()

    num_sockets_per_set: IntProperty(
        name="Num Sockets per set", description="Number of inputs in a set",
        default=2, min=1, max=MAX_SET_SIZE, update=update_node_sockets_per_set)

    num_switches: IntProperty(
        name="Num Switches", description="Number of switch items (no update associated)",
        default=2, min=2, max=MAX_NUM_SWITCHES)

    num_available_switches: IntProperty(
        default=2, min=2, description='keep track of current state (no update associated)')

    selected: IntProperty(
        name="Selected", description="Selected Set",
        default=0, min=0, update=updateNode)


    def draw_buttons(self, context, layout):
        layout.prop(self, "num_sockets_per_set")

    def update(self):
        if not self.interface_fully_initialized():
            return

        # self.interface_unhide_inputs_to_handle_new_set_if_needed()

    def sv_init(self, context):
        self.initialize_input_sockets()
        self.unhide_sockets_to_cope_with_switchnum()
        self.initialize_output_sockets()

    def process(self):
        print('num_switches (from process func)', self.num_switches)

        remap_indices = self.collect_input_indices_to_map() 
        self.adjust_input_socket_bl_idname_to_match_linked_input()
        self.adjust_output_sockets_bl_idname_to_match_selected_set(remap_indices)

        for output_idx, input_idx in enumerate(remap_indices):
            input_socket = self.inputs[input_idx]
            if input_socket.is_linked:
                A = input_socket.sv_get()
                self.outputs[output_idx].sv_set(A)


def register(): bpy.utils.register_class(SvInputSwitchNode)
def unregister(): bpy.utils.unregister_class(SvInputSwitchNode)
