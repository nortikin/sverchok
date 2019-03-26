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

from sverchok.utils.logging import debug
from sverchok.utils.profile import profile


swich_off_debug = lambda _: None
debug_process = swich_off_debug
#debug = swich_off_debug

list_debugs = [debug, debug_process]
if False:
    for d in list_debugs:
        d = swich_off_debug


class UpdateDataStructure:
    def __init__(self):
        self._node_has_changed = dict()
        self._sock_has_changed = dict()
        self._prop_has_changed = dict()
        self._sock_cache = dict()
        self._prop_cache = dict()
        self._root_nodes = dict()
        self._ani_nodes = dict()

    @staticmethod
    def _get_id(obj, prop=None):
        if prop:
            return str(hash(obj.id_data.name + obj.name + prop))
        elif isinstance(obj, bpy.types.NodeSocket):
            # avoiding the same names of input and output sockets
            position = 'output' if obj.is_output else 'input'
            return str(hash(obj.id_data.name + obj.node.name + position + obj.identifier))
        elif isinstance(obj, bpy.types.Node):
            return str(hash(obj.id_data.name + obj.name))
        else:
            raise TypeError

    @staticmethod
    def get_node_props(node):
        main = {k: v for k, v in node.items()}
        if hasattr(node, 'additional_properties'):
            main.update(node.additional_properties())
        return main

    def _update_sock_cache(self, sock):
        cache = self._sock_cache
        status = self._sock_has_changed
        id = self._get_id(sock)
        if not sock.is_output and sock.is_linked:
            if id not in cache:
                cache[id] = sock.other.node.name
                status[id] = True
                debug('Sock "{}" in node "{}" was linked'.format(sock.name, sock.node.name))
            elif cache[id] == sock.other.node.name:
                status[id] = False
            else:
                cache[id] = sock.other.node.name
                status[id] = True
                debug('Sock "{}" in node "{}" was relinked'.format(sock.name, sock.node.name))
        elif not sock.is_output:
            if id not in cache:
                status[id] = False
            elif cache[id] == '':
                status[id] = False
            else:
                cache[id] = ''
                status[id] = True
                debug('Sock "{}" in node "{}" was unlinked'.format(sock.name, sock.node.name))

    def _update_prop_cache(self, node):
        # updating prop_cache and status of properties
        cache = self._prop_cache
        status = self._prop_has_changed
        props = self.get_node_props(node)

        def assign_value(cache, id, value):
            try:
                cache[id] = value[:]
            except TypeError:
                cache[id] = value

        for k in props:
            v = props[k]
            id = self._get_id(node, k)
            if id not in cache:
                status[id] = True
                assign_value(cache, id, v)
                debug('Prop "{}" in node "{}" was changed (init)'.format(k, node.name))
            else:
                # iterable objects of blender props should be compared one by one
                try:
                    equal = True
                    for nested_v, nested_c in zip(v, cache[id]):
                        if nested_v != nested_c:
                            equal = False
                            break
                except TypeError:
                    equal = v == cache[id]
                finally:
                    if equal:
                        status[id] = False
                    else:
                        status[id] = True
                        assign_value(cache, id, v)
                        debug('Prop "{}" in node "{}" was changed'.format(k, node.name))

    def has_changed(self, obj, prop=None):
        id = self._get_id(obj, prop)
        if prop == 'ANY':
            prop_names = [k for k in self.get_node_props(obj)]
            return True in [self._prop_has_changed[self._get_id(obj, pn)] for pn in prop_names]
        elif prop:
            return self._prop_has_changed[id]
        elif isinstance(obj, bpy.types.NodeSocket):
            return self._sock_has_changed[id]
        elif isinstance(obj, bpy.types.Node):
            return self._node_has_changed.setdefault(id, False)
        else:
            raise TypeError

    def _set_has_changed(self, obj, change=False, prop=None):
        id = self._get_id(obj, prop)
        if prop:
            self._prop_has_changed[id] = change
        elif isinstance(obj, bpy.types.NodeSocket):
            self._sock_has_changed[id] = change
        elif isinstance(obj, bpy.types.Node):
            self._node_has_changed[id] = change
        else:
            raise TypeError


class UpdateSystemMem(UpdateDataStructure):
    def _get_root_nodes(self, node_tree):
        if node_tree.name in self._root_nodes:
            return self._root_nodes[node_tree.name]
        else:
            root_nodes = []
            for node in node_tree.nodes:
                if True not in [soc.is_linked for soc in node.inputs]:
                    root_nodes.append(node)
            self._root_nodes[node_tree.name] = root_nodes
            return root_nodes

    def _get_animate_nodes(self, node_tree):
        if node_tree.name in self._ani_nodes:
            return self._ani_nodes[node_tree.name]
        else:
            ani_nodes = [node for node in node_tree.nodes if node.bl_idname == 'SvFrameInfoNodeMK2']
            self._ani_nodes[node_tree.name] = ani_nodes
            return ani_nodes

    @staticmethod
    def _get_next_nodes(node):
        next_nodes = []
        for soc in node.outputs:
            for link in soc.links:
                next_nodes.append(link.to_node)
        return next_nodes

    def _update_prop_soc_status(self, node_tree):
        for node in node_tree.nodes:
            self._update_prop_cache(node)
            for sock in node.inputs:
                self._update_sock_cache(sock)

    def _update_nodes_status(self, start_nodes):
        root_nodes = start_nodes[:]  # input was not changed, check only property
        was_changed_nodes = []  # input was changed
        check_nodes = []  # ready for check, should get through all tests
        done = set()  # if node not in so node was not checked yet

        def set_changed_nodes(node):
            nonlocal was_changed_nodes, done, self
            next_nodes = [nn for nn in self._get_next_nodes(node) if nn.name not in done]
            self._set_has_changed(node, True)
            [self._set_has_changed(sock, True) for sock in node.outputs]
            was_changed_nodes.extend(next_nodes)
            done.add(node.name)

        def set_check_nodes(node):
            nonlocal check_nodes, done, self
            next_nodes = [nn for nn in self._get_next_nodes(node) if nn.name not in done]
            self._set_has_changed(node, False)
            [self._set_has_changed(sock, False) for sock in node.outputs]
            check_nodes.extend(next_nodes)
            done.add(node.name)

        def should_node_changed(node):
            nonlocal self
            for sock in node.inputs:
                if self.has_changed(sock):
                    debug('"{}" is changed - input sock - "{}" - was relinked'.format(node.name, sock.name))
                    return True
            if self.has_changed(node, prop='ANY'):
                debug('"{}" is changed - a prop was changed'.format(node.name))
                return True
            for sock in node.inputs:
                if sock.other and self.has_changed(sock.other):
                    debug('"{}" is changed - data of "{}" - was changed'.format(node.name, sock.other.node.name))
                    return True
            for sock in node.outputs:
                for link in sock.links:
                    if self.has_changed(link.to_socket):
                        debug('"{}" is changed - output sock - "{}" - was relinked'.format(node.name, sock.name))
                        return True
            return False

        while was_changed_nodes or check_nodes or root_nodes:
            if was_changed_nodes:
                node = was_changed_nodes.pop()
                set_changed_nodes(node)
                debug('Changed - "{}" - input was changed'.format(node.name))
            elif check_nodes:
                node = check_nodes.pop()
                if False in [soc.other.node.name in done for soc in node.inputs if soc.other]:
                    debug('Cant decide - "{}" - input is undefined'.format(node.name))
                    continue
                else:
                    if not should_node_changed(node):
                        set_check_nodes(node)
                        debug('Remain - "{}"'.format(node.name))
                    else:
                        set_changed_nodes(node)

            elif root_nodes:
                node = root_nodes.pop()
                if should_node_changed(node):
                    set_changed_nodes(node)
                else:
                    set_check_nodes(node)
                    debug('Remain - "{}"'.format(node.name))

    def _process_nodes_hard(self, start_nodes):
        debug_process('==========Start process nodes==========')
        next_nodes = start_nodes[:]
        done = set()
        while next_nodes:
            debug_process('Next nodes in process - "{}"'.format([node.name for node in next_nodes]))
            node = next_nodes.pop()
            next_nodes.extend([nn for nn in self._get_next_nodes(node) if nn not in done])
            if self.has_changed(node) and hasattr(node, 'process'):
                previous_nodes = [sock.other.node for sock in node.inputs if sock.other]
                if True not in [self.has_changed(node) for node in previous_nodes]:
                    debug_process('Process - "{}"'.format(node.name))
                    node.process()
                elif False in [node.name in done for node in previous_nodes]:
                    debug_process('Node "{}" is skipped -  input is undefined'.format(node.name))
                else:
                    debug_process('Process - "{}"'.format(node.name))
                    node.process()
            done.add(node.name)

    def _process_nodes_easy(self, start_nodes):
        next_nodes = start_nodes[:]
        done = set()
        while next_nodes:
            node = next_nodes.pop()
            next_nodes.extend([nn for nn in self._get_next_nodes(node) if nn not in done])
            self._set_has_changed(node, change=True)
            if hasattr(node, 'process'):
                node.process()
            done.add(node.name)

    def _update_color_nodes(self, node_tree):
        for node in node_tree.nodes:
            if self.has_changed(node):
                node.set_color((1, 0, 0))
            else:
                node.set_color()

    def _update_tree(self, node_tree):
        self._root_nodes.pop(node_tree.name, None)
        self._ani_nodes.pop(node_tree.name, None)
        self._update_prop_soc_status(node_tree)
        root_nodes = self._get_root_nodes(node_tree)
        self._update_nodes_status(root_nodes)
        self._process_nodes_hard(root_nodes)

    def _update_from_node(self, node):
         self._update_prop_cache(node)
         self._process_nodes_easy([node])

    def _update_from_nodes(self, nodes):
        [self._update_prop_cache(node) for node in nodes]
        self._process_nodes_easy(nodes)

    @profile
    def update(self, obj=None, props=None):
        sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
        node_trees = list(ng for ng in bpy.data.node_groups if ng.bl_idname in sv_types and ng.nodes)
        self._node_has_changed.clear()
        if props == 'ANIMATE':
            debug('===========Start animation update================')
            ani_nodes = []
            for ng in node_trees:
                if ng.sv_process and ng.sv_animate:
                    ani_nodes.extend([node for node in self._get_animate_nodes(ng)])
            debug('Next animate nodes was found - {}'.format([node.name for node in ani_nodes]))
            self._update_from_nodes(ani_nodes)
        elif props:
            raise ValueError
        elif obj is None:
            debug('=============Start all trees update===============')
            [self._update_tree(ng) for ng in node_trees if ng.sv_process]
        elif isinstance(obj, bpy.types.NodeTree):
            debug('=============Start "{}" tree update==============='.format(obj.name))
            if obj.sv_process:
                self._update_tree(obj)
        elif isinstance(obj, bpy.types.Node):
            debug('=============Start "{}" node update==============='.format(obj.name))
            if obj.id_data.sv_process:
                self._update_from_node(obj)
        else:
            raise TypeError
        [self._update_color_nodes(ng) for ng in node_trees]


tree_updater = UpdateSystemMem()
