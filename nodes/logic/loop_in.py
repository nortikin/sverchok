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
from bpy.props import IntProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_node_utils import frame_adjust

class SvCreateLoopOut(bpy.types.Operator):

    bl_idname = "node.create_loop_out"
    bl_label = "Create Loop Out"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]

        new_node =tree.nodes.new('SvLoopOutNode')
        new_node.parent = None
        new_node.location = (node.location.x + node.width + 400, node.location.y)
        tree.links.new(node.outputs[0], new_node.inputs[0])
        frame_adjust(node, new_node)
        return {'FINISHED'}

class SvLoopInNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: For Loop Start,
    Tooltip: Start node to define a nodes for-loop.
    """
    bl_idname = 'SvLoopInNode'
    bl_label = 'Loop In'
    bl_icon = 'FILE_REFRESH'

    def update_iterations(self, context):
        if self.iterations > self.max_iterations:
            self.iterations = self.max_iterations
        else:
            updateNode(self, context)
    iterations: IntProperty(
        name='Iterations', description='Times to repeat the loop (define maximum value on N-Panel properties)',
        default=1, min=0, update=update_iterations)

    def update_max_iterations(self, context):
        if self.iterations > self.max_iterations:
            self.iterations = self.max_iterations

    max_iterations: IntProperty(
        name='Max Iterations', description='Maximum allowed iterations',
        default=5, min=2, update=update_max_iterations)

    node_dict = {}

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = "iterations"
        self.inputs.new('SvStringsSocket', 'Data 0')

        self.outputs.new('SvLoopControlSocket', 'Loop Out')
        self.outputs["Loop Out"].link_limit = 1
        self.outputs.new('SvStringsSocket', 'Loop Number')
        self.outputs.new('SvStringsSocket', 'Total Loops')

    def draw_buttons(self,ctx, layout):
        if not (self.outputs[0].is_linked and self.outputs[0].links[0].to_socket.node.bl_idname=='SvLoopOutNode'):
            self.wrapper_tracked_ui_draw_op(layout, "node.create_loop_out", icon='CON_FOLLOWPATH', text="Create Loop Out")

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "max_iterations")

    def rclick_menu(self, context, layout):
        layout.prop(self, "max_iterations")


    def sv_update(self):

        # socket handling
        print("updating loopin")
        if self.inputs[-1].links:
            print("updating loopin adding inputs")
            name_input = 'Data '+str(len(self.inputs)-1)
            name_output = 'Data '+str(len(self.inputs)-2)
            self.inputs.new('SvStringsSocket', name_input)
            self.outputs.new('SvStringsSocket', name_output)
        else:
            while len(self.inputs) > 2 and not self.inputs[-2].links:
                self.inputs.remove(self.inputs[-1])
                self.outputs.remove(self.outputs[-1])
        # check number of connections and type match input socket n with output socket n
        count_inputs = 0
        count_outputs = 0
        for idx, socket in enumerate(self.inputs[1:]):
            if socket.name in self.outputs and self.outputs[socket.name].links:
                count_outputs += 1
            if socket.links:
                count_inputs += 1
                if type(socket.links[0].from_socket) != type(self.outputs[socket.name]):
                    self.outputs.remove(self.outputs[socket.name])
                    self.outputs.new(socket.links[0].from_socket.bl_idname, socket.name)
                    self.outputs.move(len(self.outputs)-1, idx+3)

    def process(self):


        self.outputs[0].sv_set([["Link to Loop Out node"]])
        self.outputs[1].sv_set([[0]])
        iterations = int(self.inputs['Iterations'].sv_get()[0][0])
        self.outputs['Total Loops'].sv_set([[min(iterations, self.max_iterations)]])
        for inp, outp in zip(self.inputs[1:-1], self.outputs[3:]):
            outp.sv_set(inp.sv_get(deepcopy=False, default=[]))



def register():
    bpy.utils.register_class(SvCreateLoopOut)
    bpy.utils.register_class(SvLoopInNode)


def unregister():
    bpy.utils.unregister_class(SvLoopInNode)
    bpy.utils.unregister_class(SvCreateLoopOut)
