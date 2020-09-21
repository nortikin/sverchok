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
from sverchok.utils.handle_blender_data import BPYProperty

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONImporter:
    """It's only know about Sverchok JSON structure nad can fill it"""
    @classmethod
    def create_from_tree(cls, tree: SverchCustomTree, save_defaults: bool = False) -> dict:
        root_tree_importer = TreeImporter01()
        return root_tree_importer.import_tree(tree)

    @classmethod
    def create_from_nodes(cls, nodes: list, save_defaults: bool = False) -> JSONImporter: ...

    def _add_monad_tree(self, monad_name, magic_string): ...


class TreeImporter01:
    def __init__(self):
        self._structure = {
            "export_version": "0.10",
            "framed_nodes": dict(),
            "groups": dict(),
            "nodes": dict(),
            "update_lists": []
        }

    def import_tree(self, tree: SverchCustomTree) -> dict:
        for node in tree.nodes:
            self._add_node(node)
            self._add_node_in_frame(node)
        for link in tree.links:
            self._add_link(link)
        return self._structure

    def _add_node(self, node: SverchCustomTreeNode) -> NodeFormat:
        json_node = NodeFormat.create_from_node(node)
        self._structure['nodes'][node.name] = json_node.get_dict()

    def _add_link(self, link: bpy.types.NodeLink):
        if hasattr(link.from_socket, 'index') and hasattr(link.to_socket, 'index'):
            # there are normal nodes from both sides of the link, get their indexes
            self._structure['update_lists'].append([
                link.from_node.name, link.from_socket.index, link.to_node.name, link.to_socket.index
            ])
        else:
            # from one side or both there are reroute nodes, get socket names instead
            # it is strange solution but it is how current exporter works
            # potentially it can bring troubles in case if normal node has several sockets with equal names
            # what is not forbidden by Blender API
            self._structure['update_lists'].append([
                link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name
            ])

    def _add_node_in_frame(self, node: SverchCustomTreeNode):
        if node.parent:
            self._structure["framed_nodes"][node.name] = node.parent.name


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
        # todo different for monads
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
            if self._is_property_to_export(prop):
                if prop.type == 'COLLECTION':
                    self._json_data["params"][prop_name] = prop.filter_collection_values()
                else:
                    self._json_data["params"][prop.name] = prop.value

    def add_socket_properties(self, node: SverchCustomTreeNode):
        # output sockets does not have anything worth exporting
        for i, sock in enumerate(node.inputs):
            sock_props = dict()
            for prop_name in sock.keys():
                prop = BPYProperty(sock, prop_name)
                if self._is_property_to_export(prop):
                    if prop.type == 'COLLECTION':
                        sock_props[prop_name] = prop.filter_collection_values()
                    else:
                        sock_props[prop.name] = prop.value
            if sock_props:
                self._json_data['custom_socket_props'][str(i)] = sock_props

    @staticmethod
    def _is_property_to_export(prop: BPYProperty) -> bool:
        if not prop.is_valid:
            return False  # deprecated property
        elif not prop.is_to_save:
            return False
        elif prop.type == 'POINTER':
            return False  # pointers does not supported know
        elif prop.default_value == prop.value:
            return False  # the value will be loaded from code
        else:
            return True
