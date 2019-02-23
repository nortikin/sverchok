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

indentSize = 0


class SvTestingNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Testing
    Tooltip: Testing stuff
    """
    bl_idname = 'SvTestingNode'
    bl_label = 'Testing Node'

    def update_socket_types(self):
        indent = self.set_indent(True)
        print("")
        print(indent, "TIC update_socket_types")

        self.id_data.freeze(hard=True)
        self.update = True

        inputs = self.inputs
        outputs = self.outputs

        for i in range(self.set_size):
            outLabel = "Data " + str(i + 1)
            outSockeType = "StringsSocket" if self.set_size % 2 else "VerticesSocket"

            if outLabel in outputs:
                print(indent, "TIC replacing:", i + 1, " of ", self.set_size)
                print(indent, "replace :", outLabel)
                print(indent, "replacing out socket type with: ", outSockeType)
                socket = outputs[outLabel]
                socket.replace_socket(outSockeType)
                print(indent, "TOC replacing:", i + 1, " of ", self.set_size)

        self.update = False
        self.id_data.unfreeze(hard=True)

        print(indent, "TOC update_socket_types")
        print("")
        self.set_indent(False)

    def update_set_sockets(self, context):
        indent = self.set_indent(True)
        print("")
        print(indent, "TIC update_set_sockets")

        self.id_data.freeze(hard=True)
        self.updating = True  # inhibit the calls to update()

        inputs = self.inputs
        outputs = self.outputs

        # INPUT SOCKETS ========================================================

        # RECORD the previous links to the SET's inputs sockets
        iLinkMap = OrderedDict()
        for s in inputs:
            if s.is_linked:
                iLinkMap[s.name] = [link.from_socket for link in s.links]

        # REMOVE the old SET's input sockets
        inSocketNames = [s.name for s in inputs]
        for name in inSocketNames:
            print(indent, "TIC: remove input socket:", name)
            inputs.remove(inputs[name])
            print(indent, "TOC: remove input socket:", name)

        # CREATE new input sockets
        for i in range(self.set_size):  # create the SET inputs
            label = "Alpha " + str(i + 1)
            print(indent, "TIC: add input socket:", label)
            inputs.new("StringsSocket", label)
            print(indent, "TOC: add input socket:", label)

        # RECONNECT previously linked SET input sockets (if they still exist)
        for sn, fromSocketList in iLinkMap.items():
            if sn in inputs:
                for fromSocket in fromSocketList:
                    print(indent, "TIC: link input socket:", sn)
                    links = inputs[sn].id_data.links
                    links.new(fromSocket, inputs[sn])
                    print(indent, "TOC: link input socket:", sn)

        # OUTPUT SOCKETS =======================================================

        # RECORD the previous links to the SET's output sockets
        oLinkMap = OrderedDict()
        for s in outputs:
            if s.is_linked:
                oLinkMap[s.name] = [link.to_socket for link in s.links]

        # REMOVE the old SET's output sockets
        outSocketNames = [s.name for s in outputs]
        for name in outSocketNames:
            print(indent, "TIC: remove output socket:", name)
            outputs.remove(outputs[name])
            print(indent, "TOC: remove output socket:", name)

        # CREATE new output sockets
        for i in range(self.set_size):  # create the SET outputs
            label = "Data " + str(i + 1)
            print(indent, "TIC: add output socket:", label)
            outputs.new("StringsSocket", label)
            print(indent, "TOC: add output socket:", label)

        # RECONNECT previously linked SET output sockets (if they still exist)
        for sn, toSocketList in oLinkMap.items():
            if sn in outputs:
                for toSocket in toSocketList:
                    print(indent, "TIC: link output socket:", sn)
                    links = outputs[sn].id_data.links
                    links.new(outputs[sn], toSocket)
                    print(indent, "TOC: link output socket:", sn)

        self.updating = False
        self.id_data.unfreeze(hard=True)

        self.update_socket_types()

        print(indent, "TOC update_set_sockets")
        print("")
        self.set_indent(False)

    set_size = IntProperty(
        name="Set Size", description="Number of inputs in a set",
        default=2, min=1, max=9, update=update_set_sockets)

    updating = BoolProperty(
        name="Updating", description="Flag to inhibit update calls when setting sockets",
        default=False)

    def set_indent(self, plus):
        global indentSize
        if plus:
            indentSize = indentSize + 2
        else:
            indentSize = indentSize - 2

        return '+' * indentSize

    def update(self):
        """ Update the input sockets when sockets are connected/disconnected """
        indent = self.set_indent(True)
        print("")
        print(indent, "TIC update")

        if self.updating:
            print(indent, "TOC update : already updating")
            print("")
            self.set_indent(False)
            return

        self.id_data.freeze(hard=True)
        self.updating = True

        inputs = self.inputs

        self.updating = False
        self.id_data.unfreeze(hard=True)

        self.update_socket_types()

        print(indent, "TOC update")
        print("")
        self.set_indent(False)

    def draw_buttons(self, context, layout):
        layout.prop(self, "set_size")

    def sv_init(self, context):
        for i in range(self.set_size):  # create the first SET inputs & outputs
            self.inputs.new("StringsSocket", "Alpha" + " " + str(i + 1))
            self.outputs.new("StringsSocket", "Data " + str(i + 1))

    def process(self):
        return


def register():
    bpy.utils.register_class(SvTestingNode)


def unregister():
    bpy.utils.unregister_class(SvTestingNode)
