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
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
    "Zeta", "Eta", "Theta", "Iota", "Kappa", "Lambda",
    "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho", "Sigma",
    "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"]

GENERIC_SOCKET = "SvStringsSocket"
SEPARATOR_SOCKET = "SvSeparatorSocket"
MAX_SET_SIZE = 9
MAX_NUM_SWITCHES = 9

class SvInputSwitchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sets, Switch, Select
    Tooltip: Switch among multiple input sets
    """
    bl_idname = 'SvInputSwitchNode'
    bl_label = 'Input Switch'
    sv_icon = 'SV_INPUT_SWITCH'

    def label_of_set(self, index):
        return GREEK_LABELS[index]

    def update_node_sockets_per_set(self, context):
        print('doing', inspect.stack()[0][3])
        for i in range(MAX_SET_SIZE):
            self.outputs[i].hide_safe = (i > (self.num_sockets_per_set-1))

        # [ ] for any input set that doesn't make self.num_sockets_per_set, insert n.
        #     do this from highest to lowest set, so insert will be stable
        pass


    num_sockets_per_set: IntProperty(
        name="Num Sockets per set", description="Number of inputs in a set",
        default=2, min=1, max=MAX_SET_SIZE, update=update_node_sockets_per_set)

    num_switches: IntProperty(
        name="Num Switches", description="Number of switch items",
        default=2, min=2, max=MAX_NUM_SWITCHES)

    selected: IntProperty(
        name="Selected", description="Selected Set",
        default=0, min=0, update=updateNode)


    def add_new_sockets_for_new_empty_set(self):
        inew = self.inputs.new
        onew = self.outputs.new
        
        self.num_switches += 1
        inew(SEPARATOR_SOCKET, f"Separator {self.num_switches}")
        for i in range(self.num_sockets_per_set):
            inew(GENERIC_SOCKET, f"{self.label_of_set(self.num_switches)} {i + 1}")

    def last_setnum_input_sockets_connected(self):
        """ if the node looks like:
            alpha 1
            alpha 2
            beta 1   <-   if any of these gets a linked socket, the next socket set is automatically generated
            beta 2   <-
            gamma 1
            gamma 2
        """
        last_index = len(self.inputs) 
        first_index = last_index - self.num_sockets_per_set
        return [self.inputs[idx].is_linked for idx in range(first_index, last_index)]

    def not_already_maxed_out(self):
        return self.num_switches < MAX_NUM_SWITCHES

    def insert_input_sockets_to_all_sets(self):
        pass

    def remove_input_sockets_from_all_sets(self):
        pass

    def update(self):
        """ Update the input sockets when sockets are connected/disconnected """
        
        # fully initialized ?
        if not len(self.outputs) == MAX_SET_SIZE:
            return

        # should the extend the outputs
        if any(self.last_setnum_input_sockets_connected()) and self.not_already_maxed_out():
            self.add_new_sockets_for_new_empty_set()
            return

        # [ ] if none of the last two sets are connected, then drop the last set
        pass

    def draw_buttons(self, context, layout):
        layout.prop(self, "num_sockets_per_set")

    def sv_init(self, context):
        inew = self.inputs.new
        onew = self.outputs.new
        
        inew(GENERIC_SOCKET, "Selected").prop_name = "selected"
        inew(SEPARATOR_SOCKET, "Separator main")

        for j in range(self.num_switches):
            for i in range(self.num_sockets_per_set):
                inew(GENERIC_SOCKET, f"{self.label_of_set(j)} {i + 1}")
            if j < (self.num_switches - 1):
                inew(SEPARATOR_SOCKET, f"Separator {j}")

        # make all output sockets, and hide non used
        for i in range(MAX_SET_SIZE):
            sock = onew(GENERIC_SOCKET, f"Data {i + 1}")
            if i > 1:
                sock.hide_safe = True

    def replace_socket_if_needed(self, input_socket):
        if (input_socket.bl_idname == input_socket.other.bl_idname):
            return
        input_socket.replace_socket(input_socket.other.bl_idname)

    def adjust_input_socket_bl_idname_to_match_linked_input(self):
        for input_socket in self.inputs:
            if input_socket.is_linked:
                self.replace_socket_if_needed(input_socket)

    def process(self):
        print('doing', inspect.stack()[0][3])

        # [x] if any of the connected input sockets don't match the output socket type, replace bl_idname
        self.adjust_input_socket_bl_idname_to_match_linked_input()
        
        # [ ] match the output socket types with the input sockets being passed through.
        # [ ] make mapping of input sockets, associated with each switch
        # [ ] 

        pass


def register(): bpy.utils.register_class(SvInputSwitchNode)
def unregister(): bpy.utils.unregister_class(SvInputSwitchNode)
