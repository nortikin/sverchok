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
from bpy.props import IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from collections import OrderedDict

GREEK_LABELS = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon",
                "Zeta", "Eta", "Theta", "Iota", "Kappa", "Lambda",
                "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho", "Sigma",
                "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"]

LATIN_LABELS = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class SvInputSwitchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sets, Switch, Select
    Tooltip: Switch among multiple input sets
    """
    bl_idname = 'SvInputSwitchNode'
    bl_label = 'Input Switch'
    sv_icon = 'SV_INPUT_SWITCH'

    def label_of_set(self, index):
        return GREEK_LABELS[index] if self.greek_labels else LATIN_LABELS[index]

    def update_socket_types(self):
        """ Update output socket types to match selected set input socket types"""
        self.inhibit_update_calls = True  # inhibit calls to update()

        inputs = self.inputs
        outputs = self.outputs

        num_linked_sets = self.number_of_linked_sets()
        if inputs["Selected"].is_linked or num_linked_sets == 0:
            # set all output types to StringSocket when selected socket is connected or no sets are connected
            for i in range(self.set_size):
                out_label = "Data " + str(i + 1)
                if out_label in outputs:
                    socket = outputs[out_label]
                    socket.replace_socket("StringsSocket")

        else:  # set output socket types to match selected SET input socket types
            n = inputs["Selected"].sv_get()[0][0] % num_linked_sets
            # find the label of the n'th connected set
            linked_sets_labels = [self.label_of_set(i) for i in range(self.number_of_sets()) if self.is_set_linked(i)]
            selected_set_label = linked_sets_labels[n]
            for i in range(self.set_size):
                in_label = selected_set_label + " " + str(i + 1)
                out_label = "Data " + str(i + 1)
                out_socket_type = "StringsSocket"
                if in_label in inputs and inputs[in_label].is_linked:
                    link = inputs[in_label].links[0]
                    in_socket_type = link.from_socket.bl_idname
                    out_socket_type = in_socket_type
                else:
                    out_socket_type = "StringsSocket"

                if out_label in outputs:
                    socket = outputs[out_label]
                    socket.replace_socket(out_socket_type)

        self.inhibit_update_calls = False

        self.socket_types_outdated = False

    def update_selected(self, context):
        self.update_socket_types()
        updateNode(self, context)

    def update_set_sockets(self, context):
        """
        Update the input/output sockets in the sets whenever:
         * the size of the set changes
         * the labels are switched from greek to latin
         * the separators are shown/hidden
        """

        self.id_data.freeze(hard=True)  # inhibit calls to process()
        self.inhibit_update_calls = True  # inhibit calls to update()

        inputs = self.inputs

        # RECORD the previous links to the SET input sockets
        in_link_map = OrderedDict()
        in_set_sockets = [s for s in inputs if s.name != "Selected"]

        # the size of the set prior to this update (needed to find input/set location)
        set_size = self.last_set_size + 1 if self.last_show_separators else self.last_set_size
        self.last_set_size = self.set_size
        self.last_show_separators = self.show_separators

        new_set_index = -1
        last_set_index = -1
        for i, s in enumerate(in_set_sockets):
            this_set_index = int(i / set_size)
            if s.is_linked:
                if this_set_index != last_set_index:
                    last_set_index = this_set_index
                    new_set_index = new_set_index + 1
                new_num = s.name[-1:]  # extract the number from the label
                new_label = self.label_of_set(new_set_index) + " " + new_num
                in_link_map[new_label] = [link.from_socket for link in s.links]

        # REMOVE the old SET's inputs sockets
        in_socket_names = [s.name for s in inputs if s.name != "Selected"]
        for name in in_socket_names:
            inputs.remove(inputs[name])

        # CREATE the SET of input sockets
        for n in range(new_set_index + 2):
            if self.show_separators:
                inputs.new("SvSeparatorSocket", self.label_of_set(n) + " 0")
            for i in range(self.set_size):  # create the first SET inputs
                label = self.label_of_set(n) + " " + str(i + 1)
                inputs.new("StringsSocket", label)

        # RECONNECT previously linked SET input sockets (if they still exist)
        for sn, from_socket_list in in_link_map.items():
            if sn in inputs:
                for from_socket in from_socket_list:
                    links = inputs[sn].id_data.links
                    links.new(from_socket, inputs[sn])

        outputs = self.outputs

        # RECORD the previous links to the SET's output sockets
        out_link_map = OrderedDict()
        for s in outputs:
            if s.is_linked:
                out_link_map[s.name] = [link.to_socket for link in s.links]

        # REMOVE the old SET's output sockets
        out_socket_names = [s.name for s in outputs]
        for name in out_socket_names:
            outputs.remove(outputs[name])

        # CREATE new output sockets
        for i in range(self.set_size):  # create the SET outputs
            label = "Data " + str(i + 1)
            outputs.new("StringsSocket", label)

        # RECONNECT previously linked SET output sockets (if they still exist)
        for sn, to_socket_list in out_link_map.items():
            if sn in outputs:
                for to_socket in to_socket_list:
                    links = outputs[sn].id_data.links
                    links.new(outputs[sn], to_socket)

        self.inhibit_update_calls = False
        self.id_data.unfreeze(hard=True)

        self.update_socket_types()

    set_size = IntProperty(
        name="Set Size", description="Number of inputs in a set",
        default=2, min=1, max=9, update=update_set_sockets)

    last_set_size = IntProperty(
        name="Last Set Size", description="Last Number of inputs in a set",
        default=2, min=1, max=9)

    selected = IntProperty(
        name="Selected", description="Selected Set",
        default=0, min=0, update=update_selected)

    show_separators = BoolProperty(
        name="Show Separators", description="Show separators between sets",
        default=True, update=update_set_sockets)

    last_show_separators = BoolProperty(
        name="Last Show Separators", description="Last Show separators between sets",
        default=True)

    greek_labels = BoolProperty(
        name="Greek Labels", description="Use Greek letters for set input socket labels",
        default=True, update=update_set_sockets)

    inhibit_update_calls = BoolProperty(
        name="Skip Update", description="Flag to inhibit update calls when setting sockets",
        default=False)

    socket_types_outdated = BoolProperty(
        name="Needs Socket Type Update",
        description="Flag to mark when (output) socket types need to be updated",
        default=False)

    def get_set_size(self):
        return self.set_size + 1 if self.show_separators else self.set_size

    def number_of_sets(self):
        return int((len(self.inputs) - 1) / self.get_set_size())  # exclude "Selected" input

    def number_of_linked_sets(self):
        num_linked_sets = 0
        for n in range(self.number_of_sets()):
            if self.is_set_linked(n):
                num_linked_sets = num_linked_sets + 1
        return num_linked_sets

    def is_set_linked(self, index):
        return any(s.is_linked for s in self.inputs_in_set(index))

    def inputs_in_set(self, index):
        set_size = self.get_set_size()
        i1 = 1 + set_size * index
        i2 = 1 + set_size * (index + 1)
        return self.inputs[i1:i2]

    def update(self):
        """ Update the input sockets when sockets are connected/disconnected """

        if self.inhibit_update_calls:
            return

        # only needs update if the node has all its initial sockets created
        set_size = self.get_set_size()
        if len(self.inputs) < set_size + 1:
            return

        self.id_data.freeze(hard=True)  # inhibit calls to process()
        self.inhibit_update_calls = True  # inhibit calls to update()

        inputs = self.inputs

        # disconnect any separator socket in case any is connected
        _ = [s.remove_links() for s in inputs if s.bl_idname == "SvSeparatorSocket"]

        n = self.number_of_sets()

        # is the last set linked ? => create an extra set
        if self.is_set_linked(n - 1):
            new_set_label = self.label_of_set(n)
            # create sockets for the new set with the next label: Alpha to Omega
            if self.show_separators:
                inputs.new("SvSeparatorSocket", new_set_label + " 0")
            for i in range(self.set_size):
                inputs.new("StringsSocket", new_set_label + " " + str(i + 1))

        else:  # last set is unlinked ? => remove last unconnected sets except the last
            m = n - 1  # start with the last set
            while m != 0:  # one set must always exist
                if self.is_set_linked(m - 1):  # previous set connected ? done
                    break
                else:  # previous set not connected => remove this set
                    names = [s.name for s in self.inputs_in_set(m)]
                    for name in names:
                        inputs.remove(inputs[name])
                    m = m - 1

        self.inhibit_update_calls = False
        self.id_data.unfreeze(hard=True)

        self.socket_types_outdated = True  # prompt socket type update

    def draw_buttons(self, context, layout):
        layout.prop(self, "set_size")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "show_separators")
        layout.prop(self, "greek_labels")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Selected").prop_name = "selected"
        if self.show_separators:
            self.inputs.new("SvSeparatorSocket", self.label_of_set(0) + " 0")
        for i in range(self.set_size):  # create the first SET inputs & outputs
            self.inputs.new("StringsSocket", self.label_of_set(0) + " " + str(i + 1))
            self.outputs.new("StringsSocket", "Data " + str(i + 1))

    def process(self):

        if self.socket_types_outdated:
            self.update_socket_types()

        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs

        # get the list of LABELS of the LINKED sets (Alpha, Beta...)
        linked_set_labels = [self.label_of_set(n) for n in range(self.number_of_sets()) if self.is_set_linked(n)]
        num_linked_sets = len(linked_set_labels)  # number of linked sets

        if num_linked_sets == 0:  # no set to output if no input sets are connected
            return

        input_n = inputs["Selected"].sv_get()[0]
        selected_sets = [max(0, int(n)) % num_linked_sets for n in input_n]

        # get the sequence of LABELS of the sets selected to be output
        sequence_labels = [linked_set_labels[i] for i in selected_sets]
        # get the list of UNIQUE LABELS of the sets selected to be output
        output_labels = list(set(sequence_labels))

        for i in range(self.set_size):
            out_label = "Data " + str(i + 1)
            if outputs[out_label].is_linked:
                # read ONCE all the inputs which are going to be output
                in_dict = {label: inputs[label + " " + str(i + 1)].sv_get()[0] for label in output_labels}
                # create output list based on read inputs and the selected sequence
                data_list = [in_dict[label] for label in sequence_labels]
                outputs[out_label].sv_set(data_list)


def register():
    bpy.utils.register_class(SvInputSwitchNode)


def unregister():
    bpy.utils.unregister_class(SvInputSwitchNode)
