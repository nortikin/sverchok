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

from sverchok.node_tree import SverchCustomTreeNode


from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.data_structure import list_match_func


class SvLoopOutNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: For Loop End,
    Tooltip: End node to define a nodes for-loop.
    """
    bl_idname = 'SvLoopOutNode'
    bl_label = 'Loop Out'
    bl_icon = 'CON_FOLLOWPATH'



    def sv_init(self, context):
        self.inputs.new('SvLoopControlSocket', 'Loop In')
        self.inputs.new('SvStringsSocket', 'Data 0')
        self.inputs.new('SvStringsSocket', 'Data 1')
        self.outputs.new('SvStringsSocket', 'Data 0')
        self.outputs.new('SvStringsSocket', 'Data 1')


    def sv_update(self):


        if not self.inputs[0].is_linked:
            return

        loop_in_node = self.inputs[0].links[0].from_socket.node
        if not loop_in_node.bl_idname == 'SvLoopInNode':
            return

        print("updating loopout")


        while len(loop_in_node.inputs)-1 > len(self.inputs):
            print("updating loopout adding inputs")
            name = 'Data '+str(len(self.inputs)-1)

            self.inputs.new('SvStringsSocket', name)
            self.outputs.new('SvStringsSocket', name)
        while len(loop_in_node.inputs)-1 < len(self.inputs):
            print("updating loopout removing inputs")
            self.inputs.remove(self.inputs[-1])
            self.outputs.remove(self.outputs[-1])
        if loop_in_node.inputs[-1].links:
            name = 'Data '+str(len(self.inputs)-1)
            self.inputs.new('SvStringsSocket', name)
            self.outputs.new('SvStringsSocket', name)
        # check number of connections and type match input socket n with output socket n
        count_inputs = 0
        count_outputs = 0
        for idx, socket in enumerate(loop_in_node.inputs):
            if socket.name in self.outputs and self.outputs[socket.name].links:
                count_outputs += 1
            if socket.links:
                count_inputs += 1
                if type(socket.links[0].from_socket) != type(self.outputs[socket.name]):
                    self.inputs.remove(self.inputs[socket.name])
                    self.inputs.new(socket.links[0].from_socket.bl_idname, socket.name)
                    self.inputs.move(len(self.inputs)-1, idx)
                    self.outputs.remove(self.outputs[socket.name])
                    self.outputs.new(socket.links[0].from_socket.bl_idname, socket.name)
                    self.outputs.move(len(self.outputs)-1, idx-1)

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
            else:
                inner_loops_in.remove(inner_loop_in_node.name)
        if inner_loops_in:
            return True

        return False

    def get_affected_nodes(self, loop_in_node):
        nodes_to_loop_out = make_tree_from_nodes([self.name], self.id_data, down=False)
        nodes_from_loop_in = make_tree_from_nodes([loop_in_node.name], self.id_data, down=True)
        nodes_from_loop_out = make_tree_from_nodes([self.name], self.id_data, down=True)

        set_nodes_from_loop_in = frozenset(nodes_from_loop_in)
        set_nodes_from_loop_out = frozenset(nodes_from_loop_out)
        # set_nodes_to_loop_out = frozenset(nodes_to_loop_out)

        intersection = [x for x in nodes_to_loop_out if x in set_nodes_from_loop_in]
        related_nodes = [x for x in nodes_from_loop_in if x not in set_nodes_from_loop_out and x not in intersection]

        return intersection, related_nodes

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
        if loop_in_node.mode == 'Range':
            self.range_mode(loop_in_node)
        else:
            self.for_each_mode(loop_in_node)

    def for_each_mode(self, loop_in_node):
        list_match = list_match_func[loop_in_node.list_match]
        params = list_match([inp.sv_get(deepcopy=False, default=[]) for inp in loop_in_node.inputs[1:-1]])
        if len(params[0]) == 1:

            for inp, outp in zip(self.inputs[1:], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
        else:
            intersection, related_nodes = self.get_affected_nodes(loop_in_node)
            if self.bad_inner_loops(intersection):
                raise Exception("Loops inside not well connected")

            tree_nodes = self.id_data.nodes
            do_update(intersection[:-1], tree_nodes)
            idx = 0
            out_data = [[] for inp in  self.inputs[1:]]
            for inp, out in zip(self.inputs[1:], out_data):
                out.append(inp.sv_get(deepcopy=False, default=[])[0])
            for item_params in zip(*params):
                if idx == 0:
                    idx += 1
                    continue
                for j, data in enumerate(item_params):
                    loop_in_node.outputs[j+3].sv_set([data])
                loop_in_node.outputs['Loop Number'].sv_set([[idx]])
                idx += 1
                for node_name in intersection[1:-1]:
                    tree_nodes[node_name].process()
                for inp, out in zip(self.inputs[1:], out_data):
                    out.append(inp.sv_get(deepcopy=False, default=[])[0])


            for inp, outp in zip(out_data, self.outputs):
                outp.sv_set(inp)

            do_update(related_nodes, self.id_data.nodes)

    def range_mode(self, loop_in_node):
        if loop_in_node.iterations == 0:
            for inp, outp in zip(loop_in_node.inputs[1:-1], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))

        elif loop_in_node.iterations == 1:

            for inp, outp in zip(self.inputs[1:], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))
        else:

            intersection, related_nodes = self.get_affected_nodes(loop_in_node)
            if self.bad_inner_loops(intersection):
                raise Exception("Loops inside not well connected")


            iterations = min(int(loop_in_node.inputs['Iterations'].sv_get()[0][0]), loop_in_node.max_iterations)
            tree_nodes = self.id_data.nodes
            do_update(intersection[:-1], tree_nodes)
            for i in range(iterations-1):

                for j, socket in enumerate(self.inputs[1:]):
                    data = socket.sv_get(deepcopy=False, default=[])
                    loop_in_node.outputs[j+3].sv_set(data)
                loop_in_node.outputs['Loop Number'].sv_set([[i+1]])
                for node_name in intersection[1:-1]:
                    tree_nodes[node_name].process()


            for inp, outp in zip(self.inputs[1:], self.outputs):
                outp.sv_set(inp.sv_get(deepcopy=False, default=[]))

            do_update(related_nodes, self.id_data.nodes)




def register():
    bpy.utils.register_class(SvLoopOutNode)


def unregister():
    bpy.utils.unregister_class(SvLoopOutNode)
