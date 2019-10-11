# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

GREEK_LABELS = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
    "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"]

GENERIC_SOCKET = "SvStringsSocket"
SEPARATOR_SOCKET = "SvSeparatorSocket"
MAX_SET_SIZE = 9
MAX_NUM_SWITCHES = 9

def get_indices_that_should_be_visible(node):
    """ instead this could be composed of multiple calls to 'get_indices_from_groupnum' function """
    socket_index = 1
    vis_dict = {}
    vis_dict[0] = True # selector always visible, first socket
    for group_index in range(node.max_groups):
        vis_dict[socket_index] = group_index < node.num_visible_groups
        socket_index += 1
        for set_item in range(node.max_items_per_group):
            vis_dict[socket_index] = (group_index < node.num_visible_groups and set_item < node.num_items_per_group) 
            socket_index += 1

    # g = "".join(["01"[k] for k in node.values()])
    # print(g)
    return vis_dict

def get_indices_for_groupnum(node, group_lookup):
    idx = 2 + ((node.max_items_per_group * group_lookup) + group_lookup)
    return list(range(idx, idx + node.num_items_per_group))


class SvInputSwitchNodeMOD(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sets, Switch, Select
    Tooltip: Switch among multiple input sets

    auto expanding feature:
        determined by "any_sockets_of_last_input_set_connected" till last visble is max groups
        
        if the node looks like:
            alpha 1
            alpha 2
            beta 1   <-   if any of these gets a linked socket, the next socket set is automatically generated
            beta 2   <-
            gamma 1
            gamma 2

    debug tools:   

        # (import inspect)
        # stick this line of code at the top of a function, and it will print the name of the function when called
        # print('doing', inspect.stack()[0][3])
    """

    bl_idname = 'SvInputSwitchNodeMOD'
    bl_label = 'Input Switch MOD'
    sv_icon = 'SV_INPUT_SWITCH'

    @property
    def interface_fully_initialized(self):
        return len(self.outputs) == MAX_SET_SIZE

    @property
    def not_already_maxed_out(self):
        return self.num_switches < MAX_NUM_SWITCHES

    @property
    def any_sockets_of_last_input_set_connected(self):
        indices = get_indices_for_groupnum(self.node_state, self.num_switches-1)
        return any([self.inputs[idx].is_linked for idx in indices])

    @property
    def node_state(self):
        state = lambda: None
        state.max_groups = MAX_NUM_SWITCHES
        state.num_visible_groups = self.num_switches
        state.max_items_per_group = MAX_SET_SIZE
        state.num_items_per_group = self.num_sockets_per_set
        return state

    def configure_sockets_for_switchnum(self, context):
        """ called when user adjust num sockets per set slider """
        self.set_hidestate_output_sockets_to_cope_with_switchnum()
        self.set_hidestate_input_sockets_to_cope_with_switchnum()

    num_sockets_per_set: IntProperty(
        name="Num Sockets per set", description="Num sockets per set",
        default=2, min=1, max=MAX_SET_SIZE, update=configure_sockets_for_switchnum)

    num_switches: IntProperty(
        name="Num Switches", description="Number of switch items (no update associated)",
        default=2, min=2, max=MAX_NUM_SWITCHES)

    num_available_switches: IntProperty(
        default=2, min=2, description='keep track of current state (no update associated)')

    selected: IntProperty(
        name="Selected", description="Selected Set",
        default=0, min=0, update=updateNode)


    def initialize_input_sockets(self):
        inew = self.inputs.new
        inew(GENERIC_SOCKET, "Selected").prop_name = "selected"
        for group in range(MAX_NUM_SWITCHES):
            socket = inew(SEPARATOR_SOCKET, f"Separator {group}")
            for set_item in range(MAX_SET_SIZE):
                inew(GENERIC_SOCKET, f"{GREEK_LABELS[group]} {set_item}")

    def initialize_output_sockets(self):
        for i in range(MAX_SET_SIZE): self.outputs.new(GENERIC_SOCKET, f"Data {i}")

    def replace_socket_if_needed(self, input_socket):
        if input_socket.bl_idname != input_socket.other.bl_idname:
            input_socket.replace_socket(input_socket.other.bl_idname)

    def adjust_input_socket_bl_idname_to_match_linked_input(self):
        for input_socket in self.inputs:
            if input_socket.is_linked:
                self.replace_socket_if_needed(input_socket)

    def adjust_output_sockets_bl_idname_to_match_selected_set(self, remap_indices):
        for out_idx, in_idx in enumerate(remap_indices):
            input_bl_idname = self.inputs[in_idx].bl_idname
            if input_bl_idname != self.outputs[out_idx].bl_idname:
                self.outputs[out_idx].replace_socket(input_bl_idname)

    def set_hidestate_input_sockets_to_cope_with_switchnum(self):
        tndict = get_indices_that_should_be_visible(self.node_state)
        for key, value in tndict.items():
            socket = self.inputs[key]
            desired_hide_state = not(value)
            if not socket.hide == desired_hide_state:
                socket.hide_safe = desired_hide_state

    def set_hidestate_output_sockets_to_cope_with_switchnum(self):
        for i in range(MAX_SET_SIZE):
            socket = self.outputs[i]
            desired_state = (i > (self.num_sockets_per_set - 1))
            if socket.hide != desired_state:
                socket.hide_safe = desired_state

    def interface_unhide_inputs_to_handle_new_set_if_needed(self):
        if self.not_already_maxed_out and self.any_sockets_of_last_input_set_connected:
            self.num_switches += 1
            self.set_hidestate_input_sockets_to_cope_with_switchnum()

    def draw_buttons(self, context, layout):
        layout.prop(self, "num_sockets_per_set")

    def update(self):
        if not self.interface_fully_initialized:
            return
        self.interface_unhide_inputs_to_handle_new_set_if_needed()

    def sv_init(self, context):
        self.initialize_input_sockets()
        self.set_hidestate_input_sockets_to_cope_with_switchnum()
        self.initialize_output_sockets()
        self.set_hidestate_output_sockets_to_cope_with_switchnum()

    def process(self):
        remap_indices = get_indices_for_groupnum(self.node_state, self.selected)
        self.adjust_input_socket_bl_idname_to_match_linked_input()
        self.adjust_output_sockets_bl_idname_to_match_selected_set(remap_indices)

        for output_idx, input_idx in enumerate(remap_indices):
            input_socket = self.inputs[input_idx]
            if input_socket.is_linked:
                A = input_socket.sv_get()
            else:
                A = [None]
            self.outputs[output_idx].sv_set(A)

    def get_local_function(self, named_function):
        if named_function in globals():
            return globals()[named_function]


classes = [SvInputSwitchNodeMOD]
register, unregister = bpy.utils.register_classes_factory(classes)
