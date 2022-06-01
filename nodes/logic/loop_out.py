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
from bpy.props import EnumProperty
from sverchok.core.update_system import UpdateTree

from sverchok.node_tree import SverchCustomTreeNode


from sverchok.data_structure import list_match_func, enum_item_4


socket_labels = {'Range': 'Break', 'For_Each': 'Skip'}

class SvUpdateLoopOutSocketLabels(bpy.types.Operator):
    '''Update Loop Out socket Labels'''
    bl_idname = "node.update_loop_out_socket_labels"
    bl_label = "Update Loop Out Socket Labels"

    def execute(self, context):
        node = context.node
        for inp, outp in zip(node.inputs[2:], node.outputs):
            outp.label = inp.label

        return {'FINISHED'}

class SvLoopOutNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: For Loop End,
    Tooltip: End node to define a nodes for-loop.
    """
    bl_idname = 'SvLoopOutNode'
    bl_label = 'Loop Out'
    bl_icon = 'CON_FOLLOWPATH'

    mode: EnumProperty(
        name='Mode', description='Maximum allowed iterations',
        items=enum_item_4(['Range', 'For Each']), default='Range',
        )

    def sv_init(self, context):
        self.inputs.new('SvLoopControlSocket', 'Loop In')
        self.inputs.new('SvStringsSocket', 'Break')
        self.inputs.new('SvStringsSocket', 'Data 0')

        self.outputs.new('SvStringsSocket', 'Data 0')

    def draw_buttons_ext(self, context, layout):
        if self.mode == 'For_Each':
            socket_labels_box = layout.box()
            socket_labels_box.label(text="Socket Labels")
            for socket in self.inputs[2:]:
                socket_labels_box.prop(socket, "label", text=socket.name)
            socket_labels_box.operator("node.update_loop_out_socket_labels", icon='CON_FOLLOWPATH', text="Update Socket Labels")

    def update_sockets_range_mode(self, loop_in_node):
        while len(loop_in_node.inputs) > len(self.inputs):
            name = 'Data '+str(len(self.inputs)-2)
            self.inputs.new('SvStringsSocket', name)
            self.outputs.new('SvStringsSocket', name)
        while len(loop_in_node.inputs) < len(self.inputs):
            self.inputs.remove(self.inputs[-1])
            self.outputs.remove(self.outputs[-1])

        # in case the loop_in has not been updated yet
        if loop_in_node.inputs[-1].links:
            name = 'Data '+str(len(self.inputs)-2)
            self.inputs.new('SvStringsSocket', name)
            self.outputs.new('SvStringsSocket', name)

        # dynamic sockets
        for idx, socket in enumerate(loop_in_node.inputs):
            if idx==0:
                continue

            if socket.links:
                if type(socket.links[0].from_socket) != type(self.outputs[socket.name]):
                    self.inputs.remove(self.inputs[socket.name])
                    self.inputs.new(socket.links[0].from_socket.bl_idname, socket.name)
                    self.inputs.move(len(self.inputs)-1, idx+1)
                    self.outputs.remove(self.outputs[socket.name])
                    self.outputs.new(socket.links[0].from_socket.bl_idname, socket.name)
                    self.outputs.move(len(self.outputs)-1, idx-1)
        for inp, self_inp, self_outp in zip(loop_in_node.inputs[1:], self.inputs[2:], self.outputs):
            self_outp.label = inp.label
            self_inp.label = inp.label


    def update_sockets_for_each_mode(self):
        # socket handling
        if len(self.outputs)+3 > len(self.inputs):
            self.outputs.remove(self.outputs[-1])
        if self.inputs[-1].links:
            name_input = 'Data '+str(len(self.inputs)-2)
            name_output = 'Data '+str(len(self.inputs)-3)
            other_socket = self.inputs[-1].other
            new_label = other_socket.label if other_socket.label else other_socket.name
            self.inputs[-1].label = new_label
            self.inputs.new('SvStringsSocket', name_input)
            self.outputs.new('SvStringsSocket', name_output)
        else:
            while len(self.inputs) > 3 and not self.inputs[-2].links:
                self.inputs.remove(self.inputs[-1])
                self.outputs.remove(self.outputs[-1])


        # match input socket n with output socket n
        for idx, socket in enumerate(self.inputs[2:]):

            if socket.links:

                if type(socket.links[0].from_socket) != type(self.outputs[socket.name]):
                    self.outputs.remove(self.outputs[socket.name])
                    self.outputs.new(socket.links[0].from_socket.bl_idname, socket.name)
                    self.outputs.move(len(self.outputs)-1, idx)
        for inp, outp in zip(self.inputs[2:-1], self.outputs):
            outp.label = inp.label

    def change_mode(self, loop_in_node):
        if loop_in_node.mode == 'For_Each':
            name = 'Data '+str(len(self.inputs)-2)
            self.inputs.new('SvStringsSocket', name)
        self.mode = loop_in_node.mode

    def sv_update(self):

        if not self.inputs[0].is_linked:
            return

        loop_in_node = self.inputs[0].links[0].from_socket.node
        if not loop_in_node.bl_idname == 'SvLoopInNode':
            return

        if loop_in_node.mode != self.mode:
            self.change_mode(loop_in_node)

        if loop_in_node.mode == 'Range':
            self.update_sockets_range_mode(loop_in_node)
        else:
            self.update_sockets_for_each_mode()

    def bad_inner_loops(self, intersection):
        inner_loops_out, inner_loops_in = [],[]
        ng = self.id_data
        for node in intersection:
            if ng.nodes[node].bl_idname == 'SvLoopOutNode':
                inner_loops_out.append(node)
            if ng.nodes[node].bl_idname == 'SvLoopInNode':
                inner_loops_in.append(node)
        for node in inner_loops_out:
            if not ng.nodes[node].ready():
                return True

            inner_loop_in_node = ng.nodes[node].inputs[0].links[0].from_socket.node
            if not inner_loop_in_node.name in inner_loops_in:
                print("Inner Loop not well connected")
                return True
            inner_loops_in.remove(inner_loop_in_node.name)

        if inner_loops_in:
            return True

        return False

    def ready(self):
        if not self.inputs[0].is_linked:
            print("Inner Loop not connected")
            return False
        if not any([socket.is_linked for socket in self.outputs]):
            return False
        loop_in_node = self.inputs[0].links[0].from_socket.node
        if not loop_in_node.bl_idname == 'SvLoopInNode':
            print("Inner Loop not well connected")
            return False
        return True

    def process(self):
        if not self.ready():
            return

        loop_in_node = self.inputs[0].links[0].from_socket.node

        self.inputs[1].label = socket_labels[loop_in_node.mode]
        if loop_in_node.mode == 'Range':
            self.range_mode(loop_in_node)
        else:
            self.for_each_mode(loop_in_node)

    def for_each_mode(self, loop_in_node):
        list_match = list_match_func[loop_in_node.list_match]
        params = list_match([inp.sv_get(deepcopy=False, default=[]) for inp in loop_in_node.inputs[1:-1]])

        if len(params[0]) == 1:
            if not self.inputs['Break'].sv_get(deepcopy=False, default=[[False]])[0][0]:
                for inp, outp in zip(self.inputs[2:], self.outputs):
                    outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
            else:
                for outp in self.outputs:
                    outp.sv_set([])
        else:
            tree = UpdateTree.get(self.id_data)
            from_nodes = tree.nodes_from([loop_in_node])
            to_nodes = tree.nodes_to([self])
            loop_nodes = from_nodes.intersection(to_nodes)
            sort_loop_nodes = tree.sort_nodes(loop_nodes)
            break_socket = tree.previous_sockets(self)[1]

            if self.bad_inner_loops((n.name for n in loop_nodes)):
                raise Exception("Loops inside not well connected")

            do_print = loop_in_node.print_to_console
            idx = 0
            out_data = [[] for inp in self.inputs[2:]]

            # the nodes should be cleared out from last loop data
            for node in sort_loop_nodes[:-1]:
                tree.update_node(node)

            if not break_socket or not break_socket.sv_get(default=[[False]])[0][0]:
                for inp, out in zip(tree.previous_sockets(self)[2:len(self.outputs) + 2], out_data):
                    if inp is not None:
                        out.append(inp.sv_get()[0])
                    else:
                        out.append([])

            for item_params in zip(*params):
                if idx == 0:
                    idx += 1
                    continue
                for j, data in enumerate(item_params):
                    loop_in_node.outputs[j+3].sv_set([data])
                loop_in_node.outputs['Loop Number'].sv_set([[idx]])
                idx += 1
                if do_print:
                    print(f"Looping Object Number {idx}")
                for node in sort_loop_nodes[1:-1]:
                    try:
                        tree.update_node(node, suppress=False)
                    except Exception:
                        raise Exception(f"Element: {idx}")

                if not break_socket or not break_socket.sv_get(default=[[False]])[0][0]:
                    for inp, out in zip(tree.previous_sockets(self)[2:len(self.outputs) + 2], out_data):
                        if inp is not None:
                            out.append(inp.sv_get()[0])
                        else:
                            out.append([])

            for inp, outp in zip(out_data, self.outputs):
                outp.sv_set(inp)

            from_out_nodes = tree.nodes_from([self])
            side_loop_nodes = from_nodes - from_out_nodes - loop_nodes
            for node in tree.sort_nodes(side_loop_nodes):
                tree.update_node(node)

    def range_mode(self, loop_in_node):
        iterations = min(int(loop_in_node.inputs['Iterations'].sv_get()[0][0]), loop_in_node.max_iterations)
        if iterations == 0:
            for inp, outp in zip(loop_in_node.inputs[1:-1], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))

        elif iterations == 1:

            for inp, outp in zip(self.inputs[2:], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
        else:
            tree = UpdateTree.get(self.id_data)
            from_nodes = tree.nodes_from([loop_in_node])
            to_nodes = tree.nodes_to([self])
            loop_nodes = from_nodes.intersection(to_nodes)
            sort_loop_nodes = tree.sort_nodes(loop_nodes)
            break_socket = tree.previous_sockets(self)[1]

            if self.bad_inner_loops((n.name for n in loop_nodes)):  # todo pass real nodes
                raise Exception("Loops inside not well connected")

            do_print = loop_in_node.print_to_console

            # the nodes should be cleared out from last loop data
            for node in sort_loop_nodes[:-1]:
                tree.update_node(node)

            for i in range(iterations-1):
                if break_socket and break_socket.sv_get(default=[[False]])[0][0]:
                    break
                for j, socket in enumerate(tree.previous_sockets(self)[2:]):
                    data = socket.sv_get(deepcopy=False, default=[])
                    loop_in_node.outputs[j+3].sv_set(data)
                loop_in_node.outputs['Loop Number'].sv_set([[i+1]])
                if do_print:
                    print(f"Looping iteration Number {i+1}")
                for node in sort_loop_nodes[1:-1]:
                    try:
                        tree.update_node(node, suppress=False)
                    except Exception:
                        raise Exception(f"Iteration number: {i+1}")

            for inp, outp in zip(tree.previous_sockets(self)[2:], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))

            from_out_nodes = tree.nodes_from([self])
            side_loop_nodes = from_nodes - from_out_nodes - loop_nodes
            for node in tree.sort_nodes(side_loop_nodes):
                tree.update_node(node)


def register():
    bpy.utils.register_class(SvUpdateLoopOutSocketLabels)
    bpy.utils.register_class(SvLoopOutNode)


def unregister():
    bpy.utils.unregister_class(SvLoopOutNode)
    bpy.utils.unregister_class(SvUpdateLoopOutSocketLabels)
