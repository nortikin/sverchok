# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations
from typing import TYPE_CHECKING, Union, Tuple, Any

import bpy
from sverchok.utils.sv_node_utils import recursive_framed_location_finder

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONFormat01:
    """It's only know about Sverchok JSON structure nad can fill it"""
    def __init__(self):
        self._json_data = {
            "export_version": "0.10",
            "framed_nodes": dict(),
            "groups": dict(),
            "nodes": dict(),
            "update_lists": []
        }

    def get_dict(self):
        return self._json_data

    @classmethod
    def create_from_tree(cls, node_group: SverchCustomTree, save_defaults: bool = False) -> JSONFormat01:
        sv_json = cls()
        for node in node_group.nodes:
            sv_json.add_node(node)
            sv_json.add_node_in_frame(node)
        for link in node_group.links:
            sv_json.add_link(link)
        return sv_json

    @classmethod
    def create_from_nodes(cls, nodes: list, save_defaults: bool = False) -> JSONFormat01: ...

    def add_node(self, node: SverchCustomTreeNode) -> NodeFormat:
        json_node = NodeFormat.create_from_node(node)
        self._json_data['nodes'][node.name] = json_node.get_dict()

    def add_link(self, link: bpy.types.NodeLink):
        if hasattr(link.from_socket, 'index') and hasattr(link.to_socket, 'index'):
            # there are normal nodes from both sides of the link, get their indexes
            self._json_data['update_lists'].append([
                link.from_node.name, link.from_socket.index, link.to_node.name, link.to_socket.index
            ])
        else:
            # from one side or both there are reroute nodes, get socket names instead
            # it is strange solution but it is how current exporter works
            # potentially it can bring troubles in case if normal node has several sockets with equal names
            # what is not forbidden by Blender API
            self._json_data['update_lists'].append([
                link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name
            ])

    def add_node_in_frame(self, node: SverchCustomTreeNode):
        if node.parent:
            self._json_data["framed_nodes"][node.name] = node.parent.name

    def add_monad_tree(self, monad_name, magic_string): ...


class NodeFormat:
    def __init__(self):
        self._json_data = {
            "bl_idname": "",
            "height": None,
            "width": None,
            "label": '',
            "hide": False,
            "location": (0, 0),
            "params": dict(),
            "custom_socket_props": dict()
        }

    def get_dict(self):
        return self._json_data

    @classmethod
    def create_from_node(cls, node: SverchCustomTreeNode) -> NodeFormat:
        json_node = cls()
        json_node.add_mandatory_attributes(node)
        json_node.add_node_properties(node)
        json_node.add_socket_properties(node)
        return json_node

    def add_mandatory_attributes(self, node: SverchCustomTreeNode):
        # todo different for reroutes and frames and monads
        self._json_data['bl_idname'] = node.bl_idname
        self._json_data['height'] = node.height
        self._json_data['width'] = node.width
        self._json_data['label'] = node.label
        self._json_data['hide'] = node.hide
        self._json_data['location'] = recursive_framed_location_finder(node, node.location[:])

        if node.use_custom_color:
            self._json_data['color'] = node.color[:]
            self._json_data['use_custom_color'] = True

    def add_node_properties(self, node: SverchCustomTreeNode):
        for prop_name in node.keys():
            prop = BPYProperty(node, prop_name)
            if prop.is_to_export():
                self._json_data["params"][prop.name] = prop.value

    def add_socket_properties(self, node: SverchCustomTreeNode):
        # output sockets does not have anything worth exporting
        for i, sock in enumerate(node.inputs):
            sock_props = dict()
            for prop_name in sock.keys():
                prop = BPYProperty(sock, prop_name)
                if prop.is_to_export():
                    sock_props[prop.name] = prop.value
            if sock_props:
                self._json_data['custom_socket_props'][str(i)] = sock_props


class BPYProperty:
    def __init__(self, data, prop_name: str):
        self.name = prop_name
        self._data = data

    def is_to_export(self) -> bool:
        if not self.is_to_save:
            return False
        elif self.type == 'POINTER':
            return False  # pointers does not supported know
        elif self.default_value == self.value:
            return False  # the value will be loaded from code
        else:
            return True

    @property
    def value(self) -> Any:
        if self.is_array:
            return getattr(self._data, self.name)[:]  # convert to tuple
        else:
            return getattr(self._data, self.name)

    @property
    def type(self) -> str:
        return self._data.bl_rna.properties[self.name].type

    @property
    def default_value(self) -> Any:
        return self._data.bl_rna.properties[self.name].default

    @property
    def is_to_save(self) -> bool:
        return not self._data.bl_rna.properties[self.name].is_skip_save

    @property
    def is_array(self) -> bool:
        if self.type in {'BOOL', 'FLOAT', 'INT'}:
            return self._data.bl_rna.properties[self.name].is_array
        else:
            # other properties does not have is_array attribute
            return False
