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
from sverchok.utils.nodes_mixins.loop_nodes import LoopNode

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


class SvLoopOutNode(LoopNode, SverchCustomTreeNode, bpy.types.Node):
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

    def change_mode(self, loop_in_node):
        if loop_in_node.mode == 'For_Each':
            name = 'Data '+str(len(self.inputs)-2)
            self.inputs.new('SvStringsSocket', name)
        self.mode = loop_in_node.mode

    def sv_update(self):
        """It is update in Loop in node"""

    @property
    def loop_in_node(self):
        """Should be called only from process method"""
        from_node = UpdateTree.get(self.id_data).node_from_input(self.inputs[0])
        if from_node is not None:
            return from_node if from_node.bl_idname == 'SvLoopInNode' else None
        return from_node

    @staticmethod
    def check_bad_inner_loops(intersection):
        inner_loops_out, inner_loops_in = [], []
        for node in intersection:
            if node.bl_idname == 'SvLoopOutNode':
                inner_loops_out.append(node)
            if node.bl_idname == 'SvLoopInNode':
                inner_loops_in.append(node)
        for node in inner_loops_out:
            inner_loop_in_node = node.loop_in_node
            if inner_loop_in_node is None:
                raise RuntimeError(f'"{node.name}" does not connect to a Loop in node')
            if inner_loop_in_node not in inner_loops_in:
                raise RuntimeError(f'"{inner_loop_in_node.name}" should inside the loop')
            inner_loops_in.remove(inner_loop_in_node)

        if inner_loops_in:
            loop_in_names = ', '.join(f'"{n.name}"' for n in inner_loops_in)
            is_are = "is" if len(inner_loops_in) == 1 else "are"
            raise RuntimeError(f'{loop_in_names} {is_are} not connected to Loop'
                               f' out node inside the main loop')

    def process(self):
        loop_in_node = self.loop_in_node

        if not self.inputs[0].is_linked:
            return
        if loop_in_node is None:
            raise RuntimeError("Connection to Loop In Node is expected")

        self.inputs[1].label = socket_labels[loop_in_node.mode]
        if loop_in_node.mode == 'Range':
            self.range_mode(loop_in_node)
        else:
            self.for_each_mode(loop_in_node)

    def for_each_mode(self, loop_in_node):
        list_match = list_match_func[loop_in_node.list_match]
        params = list_match([inp.sv_get(deepcopy=False, default=[]) for inp in loop_in_node.inputs[1:-1]])

        tree = UpdateTree.get(self.id_data)
        from_nodes = tree.nodes_from([loop_in_node])
        to_nodes = tree.nodes_to([self])
        loop_nodes = from_nodes.intersection(to_nodes)
        self.check_bad_inner_loops((n for n in loop_nodes))

        if len(params[0]) == 1:
            if not self.inputs['Break'].sv_get(deepcopy=False, default=[[False]])[0][0]:
                for inp, outp in zip(self.inputs[2:], self.outputs):
                    outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
            else:
                for outp in self.outputs:
                    outp.sv_set([])
        else:
            sort_loop_nodes = tree.sort_nodes(loop_nodes)
            break_socket = tree.previous_sockets(self)[1]
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

        tree = UpdateTree.get(self.id_data)
        from_nodes = tree.nodes_from([loop_in_node])
        to_nodes = tree.nodes_to([self])
        loop_nodes = from_nodes.intersection(to_nodes)
        self.check_bad_inner_loops((n for n in loop_nodes))

        if iterations == 0:
            for inp, outp in zip(loop_in_node.inputs[1:-1], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))

        elif iterations == 1:

            for inp, outp in zip(self.inputs[2:], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
        else:
            sort_loop_nodes = tree.sort_nodes(loop_nodes)
            break_socket = tree.previous_sockets(self)[1]
            do_print = loop_in_node.print_to_console

            # the nodes should be cleared out from last loop data
            for node in sort_loop_nodes[:-1]:
                tree.update_node(node)

            for i in range(iterations-1):
                if break_socket and break_socket.sv_get(default=[[False]])[0][0]:
                    break
                for j, socket in enumerate(tree.previous_sockets(self)[2:]):
                    if socket is None:
                        continue
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
                if inp is None:
                    continue
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
