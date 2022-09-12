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
from sverchok.core.update_system import UpdateTree, SearchTree
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_4, numpy_list_match_modes
from sverchok.utils.sv_node_utils import frame_adjust
from sverchok.utils.nodes_mixins.loop_nodes import LoopNode


class SvCreateLoopOut(bpy.types.Operator):

    bl_idname = "node.create_loop_out"
    bl_label = "Create Loop Out"

    def execute(self, context):

        node = context.node
        tree = node.id_data
        new_node = tree.nodes.new('SvLoopOutNode')
        new_node.parent = None
        new_node.location = (node.location.x + node.width + 400, node.location.y)
        tree.links.new(node.outputs[0], new_node.inputs[0])
        frame_adjust(node, new_node)
        return {'FINISHED'}

class SvUpdateLoopInSocketLabels(bpy.types.Operator):
    '''Update Loop In socket Labels'''
    bl_idname = "node.update_loop_in_socket_labels"
    bl_label = "Update Loop In Socket Labels"

    def execute(self, context):
        node = context.node
        for inp, outp in zip(node.inputs[1:], node.outputs[3:]):
            outp.label = inp.label
        if node.mode == 'Range' and node.outputs[0].is_linked:
            if node.outputs[0].links[0].to_socket.node.bl_idname == 'SvLoopOutNode':
                loop_out_node = node.outputs[0].links[0].to_socket.node
                for inp, self_inp, self_outp in zip(node.inputs[1:], loop_out_node.inputs[2:], loop_out_node.outputs):
                    self_outp.label = inp.label
                    self_inp.label = inp.label
        return {'FINISHED'}


class SvLoopInNode(LoopNode, SverchCustomTreeNode, bpy.types.Node):
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

    linked_to_loop_out: BoolProperty(
        name='linked_to_loop_out', description='Maximum allowed iterations',
        default=False)

    print_to_console: BoolProperty(
        name='Print progress in console', description='Maximum allowed iterations',
        default=False)

    def update_mode(self, context):
        self.inputs['Iterations'].hide_safe = self.mode == "For_Each"
        if self.mode == "For_Each":
            self.outputs[1].label = 'Item Number'
            self.outputs[2].label = 'Total Items'
        else:
            self.outputs[1].label = 'Loop Number'
            self.outputs[2].label = 'Total Loops'
        self.sv_update()
        updateNode(self, context)

    mode: EnumProperty(
        name='Mode', description='Maximum allowed iterations',
        items=enum_item_4(['Range', 'For Each']), default='Range',
        update=update_mode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = "iterations"
        self.inputs.new('SvStringsSocket', 'Data 0')

        self.outputs.new('SvLoopControlSocket', 'Loop Out')
        self.outputs["Loop Out"].link_limit = 1
        self.outputs.new('SvStringsSocket', 'Loop Number')
        self.outputs.new('SvStringsSocket', 'Total Loops')

    def draw_buttons(self, ctx, layout):
        if not self.linked_to_loop_out:
            layout.operator("node.create_loop_out", icon='CON_FOLLOWPATH', text="Create Loop Out")
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, 'mode', expand=True)
        if self.mode == "Range":
            layout.prop(self, "max_iterations")
        else:
            layout.prop(self, "list_match")
        layout.prop(self, 'print_to_console')
        socket_labels = layout.box()
        socket_labels.label(text="Socket Labels")
        for socket in self.inputs[1:]:
            socket_labels.prop(socket, "label", text=socket.name)
        socket_labels.operator("node.update_loop_in_socket_labels", icon='CON_FOLLOWPATH', text="Update Socket Labels")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, 'mode')
        if self.mode == "Range":
            layout.prop(self, "max_iterations")
        else:
            layout.prop_menu_enum(self, 'list_match')

    def sv_update(self):
        in_util_socks = 1
        out_util_socks = 3
        search_tree = SearchTree(self.id_data)  # can be invalid after replacing sockets
        self.repeat_last_socket(search_tree, min_input=in_util_socks+1)
        self.fix_output_types(search_tree, in_start=in_util_socks, out_start=out_util_socks)

        loop_outs = search_tree.nodes_from_socket(self.outputs[0])
        self.linked_to_loop_out = bool(loop_outs)
        if not loop_outs or loop_outs[0].bl_idname != 'SvLoopOutNode':
            return

        # fix Loop Out node
        loop_out = loop_outs[0]
        in_util_socks_other = 2
        if loop_out.mode != self.mode:
            loop_out.change_mode(self)
        if self.mode == 'Range':
            data_socks = len(self.inputs) - in_util_socks
            self.fix_socket_number(loop_out.inputs, data_socks+in_util_socks_other-1)
            self.fix_socket_number(loop_out.outputs, data_socks-1)
            other_socks = [search_tree.socket_from_input(s) for s in self.inputs[in_util_socks:]]
            self.copy_sockets(other_socks, loop_out.inputs[in_util_socks_other:], 'bl_idname')
            self.copy_sockets(other_socks, loop_out.outputs, 'bl_idname')
            self.copy_sockets(self.inputs[in_util_socks:], loop_out.outputs, 'label')
            self.copy_sockets(self.inputs[in_util_socks:],
                              loop_out.inputs[in_util_socks_other:],
                              'label')
        else:
            loop_out.repeat_last_socket(search_tree, min_input=in_util_socks_other+1)
            loop_out.fix_output_types(search_tree, in_start=in_util_socks_other)

    @property
    def loop_out_nodes(self):
        """Should be called only from process method"""
        # the support of several Loop Out nodes is not intentional.
        # It's possible to overcome the limitation of connection to
        # Loop Out socket by copying Loop Out node with links (Ctrl+Shift+D)
        # or by using reroutes
        nodes = UpdateTree.get(self.id_data).nodes_from_socket(self.outputs[0])
        return [n for n in nodes if n.bl_idname == 'SvLoopOutNode']

    def process(self):
        if len(self.loop_out_nodes) > 1:
            raise RuntimeError("The node can be connected to one Loop Out node only")

        self.outputs[0].sv_set([["Link to Loop Out node"]])
        self.outputs[1].sv_set([[0]])
        if self.mode == 'Range':
            iterations = int(self.inputs['Iterations'].sv_get()[0][0])
            self.outputs['Total Loops'].sv_set([[min(iterations, self.max_iterations)]])
            for inp, outp in zip(self.inputs[1:-1], self.outputs[3:]):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
        else:
            lens = []
            for inp, outp in zip(self.inputs[1:-1], self.outputs[3:]):
                data = inp.sv_get(deepcopy=False, default=[])
                lens.append(len(data))
                outp.sv_set([data[0]])
            self.outputs[2].sv_set([[max(lens)]])


def register():
    bpy.utils.register_class(SvCreateLoopOut)
    bpy.utils.register_class(SvUpdateLoopInSocketLabels)
    bpy.utils.register_class(SvLoopInNode)


def unregister():
    bpy.utils.unregister_class(SvLoopInNode)
    bpy.utils.unregister_class(SvUpdateLoopInSocketLabels)
    bpy.utils.unregister_class(SvCreateLoopOut)
