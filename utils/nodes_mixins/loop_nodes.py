# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from typing import Optional

import bpy
if bpy.app.version[0] >= 5:
    from bpy.types import NodeSocket
else:
    from bpy_types import NodeSocket
from sverchok.core.update_system import SearchTree


class LoopNode:
    def repeat_last_socket(self,
                           search_tree: SearchTree,
                           min_input: int = 1):
        """It adds extra input socket if last socket is already connected.
        It removes last socket if it and socket above are not connected.

        :param min_input: number of to sockets which should be never removed
        """
        from_socket = search_tree.socket_from_input(self.inputs[-1])
        if from_socket is not None:
            from_node = search_tree.node_from_input(self.inputs[-1])
            new_label = from_node.label or from_node.name
            self.inputs[-1].label = new_label
            self.inputs.new('SvStringsSocket', 'Data')
            self.outputs.new('SvStringsSocket', 'Data').label = new_label
        else:
            while len(self.inputs) > min_input and not self.inputs[-2].is_linked:
                self.inputs.remove(self.inputs[-1])
                self.outputs.remove(self.outputs[-1])
            self.inputs[-1].label = ''

    def fix_output_types(self,
                         search_tree: SearchTree,
                         in_start: int = 0,
                         out_start: int = 0):
        """It checks type of socket connected to input one and if it does not
        fit to type of relevant output socket it changes its type.
        Also, it copies labels from input to output.

        :param in_start: position of input socket where to start the check
        :param out_start: position of output socket where to start the check
        """
        others = [search_tree.socket_from_input(s) for s in self.inputs[in_start:]]
        self.copy_sockets(others, self.outputs[out_start:], 'bl_idname')
        self.copy_sockets(self.inputs[in_start:], self.outputs[out_start:], 'label')

    @staticmethod
    def copy_sockets(from_socks: list[Optional[NodeSocket]],
                     to_socks: list[NodeSocket],
                     attr_name: str):
        """It copies the attribute from sockets to sockets"""
        if attr_name == 'bl_idname':
            for from_, to in zip(from_socks, to_socks):
                if from_ is None:
                    continue
                if from_.bl_idname != to.bl_idname:
                    to.replace_socket(from_.bl_idname)
        else:
            for from_, to in zip(from_socks, to_socks):
                if from_ is None:
                    continue
                setattr(to, attr_name, getattr(from_, attr_name))

    @staticmethod
    def fix_socket_number(socket_collection, request: int):
        """It makes length of given collection of sockets equal to request number"""
        current = len(socket_collection)
        if request > current:
            for _ in range(request - current):
                socket_collection.new('SvStringsSocket', 'Data')
        elif request < current:
            for _ in range(current - request):
                socket_collection.remove(socket_collection[-1])