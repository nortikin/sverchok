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
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

ABC = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class SvMeshSwitchNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mesh, Switch, Select
    Tooltips: Switch among multiple Verts/Edge/Poly inputs
    """
    bl_idname = 'SvMeshSwitchNode'
    bl_label = 'Mesh Switch'

    selected = IntProperty(
        name="Selected", description="Selected Mesh",
        default=0, min=0, update=updateNode)

    def update(self):
        inputs = self.inputs
        if inputs[-2].links:  # last Verts socket linked ? => create more sockets
            name = ABC[int(len(inputs) / 2)]  # pick the next letter A to Z
            inputs.new("VerticesSocket", "Verts " + name)
            inputs.new("StringsSocket", "EdgePolys " + name)
        else:  # last Verts input unlinked ? => remove all but last unlinked
            # get the list of Verts socket labels (linked or unlinked)
            vertSockets = filter(lambda s: "Verts" in s.name, inputs)
            socketLabels = [s.name[-1] for s in vertSockets]  # (ABCD)
            # get the labels of last unlinked Verts sockets in reverse order
            unlinkedSocketLabels = []
            for label in socketLabels[::-1]:  # in reverse order (DCBA)
                if inputs["Verts " + label].is_linked:
                    break
                else:
                    unlinkedSocketLabels.append(label)
            # delete all unlinked V-EP inputs sockets (except the last ones)
            for label in unlinkedSocketLabels[:-1]:
                inputs.remove(inputs["Verts " + label])
                inputs.remove(inputs["EdgePolys " + label])

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Selected").prop_name = "selected"

        self.inputs.new('VerticesSocket', "Verts A")
        self.inputs.new('StringsSocket', "EdgePolys A")

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "EdgePolys")

    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs

        # get the list of labels of the linked Verts input sockets
        vertSockets = filter(lambda s: "Verts" in s.name and s.is_linked, inputs)
        socketLabels = [s.name[-1] for s in vertSockets]  # (ABCD)

        input_n = inputs["Selected"].sv_get()[0][0]
        num = max(1, len(socketLabels))
        n = max(0, int(input_n)) % num

        label = socketLabels[n]  # the label of the selected input

        if outputs["Verts"].is_linked:
            verts = inputs["Verts " + label].sv_get()
            outputs["Verts"].sv_set(verts)

        if outputs["EdgePolys"].is_linked:
            edgePolys = inputs["EdgePolys " + label].sv_get(default=[])
            outputs["EdgePolys"].sv_set(edgePolys)


def register():
    bpy.utils.register_class(SvMeshSwitchNode)


def unregister():
    bpy.utils.unregister_class(SvMeshSwitchNode)
