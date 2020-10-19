# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from typing import TYPE_CHECKING, Union, List, Generator

import bpy
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.handle_blender_data import BPYProperty
from sverchok.utils.sv_IO_monad_helpers import pack_monad

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONExporter:
    """Static class for responsible for exporting into JSON format"""
    @staticmethod
    def get_tree_structure(tree: SverchCustomTree) -> dict:
        """Generate structure of given tree which van be saved into json format"""
        return TreeExporter01().export_tree(tree)

    @staticmethod
    def get_nodes_structure(nodes: List[SverchCustomTreeNode]) -> dict:
        """Generate structure of given nodes which can be saved into json format"""
        return TreeExporter01().export_nodes(nodes)


class TreeExporter01:
    """
    It keeps structure of tree which can be saved into json format
    Structure including:
    export version
    nodes, node_name and node structure
    links which are determined by node names adn socket indexes
    frames
    monad(s) which are reading recursively what is efficiently
    """
    def __init__(self):
        self._structure = {
            "export_version": "0.10",
            "framed_nodes": dict(),
            "groups": dict(),
            "nodes": dict(),
            "update_lists": []
        }

    def export_tree(self, tree: SverchCustomTree) -> dict:
        """Generate structure from given tree"""
        for node in tree.nodes:
            self._add_node(node)
            self._add_node_in_frame(node)
        for link in self._ordered_links(tree):
            self._add_link(link)
        return self._structure

    def export_nodes(self, nodes: List[SverchCustomTreeNode]):
        """
        Generate structure from given node
        Expecting get nodes from one tree, for example importing only selected nodes in a tree
        """
        for node in nodes:
            self._add_node(node)
            self._add_node_in_frame(node)
        if nodes:
            tree = nodes[0].id_data
            input_node_names = {node.name for node in nodes}
            for link in self._ordered_links(tree):
                if link.from_node.name in input_node_names and link.to_node.name in input_node_names:
                    self._add_link(link)
        return self._structure

    def _add_node(self, node: SverchCustomTreeNode):
        """Add into structure name of given node and its structure"""
        self._structure['nodes'][node.name] = NodeExporter01().export_node(node, self._structure['groups'])

    def _add_link(self, link: bpy.types.NodeLink):
        """Add link into tree structure, it can have to formats:
        (from_node_name, from_socket_index, to_node_name, to_socket_index)
        and if at least at one side there is reroute node
        (from_node_name, from_socket_name, to_node_name, to_socket_name)
        """
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
        """It adds information to structure node name: frame name"""
        if node.parent:
            self._structure["framed_nodes"][node.name] = node.parent.name

    @staticmethod
    def _ordered_links(tree: SverchCustomTree) -> Generator[bpy.types.NodeLink]:
        """Returns all links in whole tree where links always are going in order from top input socket to bottom"""
        for node in tree.nodes:
            for input_socket in node.inputs:
                for link in input_socket.links:
                    yield link


class NodeExporter01:
    """
    It keeps structure of node data which can be converted into json format
    it keeps attributes like location, color, width
    all kinds of node properties including nesting collections and pointers
    the same properties for sockets
    only non default properties will get into the structure
    pointer properties will get only name of assigned data block
    also it calls `save_to_json(node_data: dict)` method of given node if it has got it
    but ut is not recommended to use it
    it saves special attributes for monad(s)
    it is possible to made it skip saving a property by marking it like that BoolProperty(option={'SKIP_SAVE'})
    this option will impact only on saving the property into json file
    """
    def __init__(self):
        self._structure = {
            "bl_idname": "",
            "height": None,
            "width": None,
            "label": '',
            "hide": False,
            "location": (0, 0),
            "params": dict(),
            "custom_socket_props": dict()
        }

    def export_node(self, node: SverchCustomTreeNode, groups: dict) -> dict:
        """It returns structure of given node"""
        self._add_mandatory_attributes(node)
        self._add_node_properties(node)
        self._add_socket_properties(node)

        if hasattr(node, 'monad') and node.monad:
            self._structure['bl_idname'] = 'SvMonadGenericNode'
            pack_monad(node, self._structure['params'], groups, TreeExporter01().export_tree)

        if node.bl_idname in {'SvGroupInputsNodeExp', 'SvGroupOutputsNodeExp'}:
            self._structure[node.node_kind] = node.stash()

        if hasattr(node, 'save_to_json'):
            node.save_to_json(self._structure)
        return self._structure

    def _add_mandatory_attributes(self, node: SverchCustomTreeNode):
        """It adds attributes which all nodes have"""
        self._structure['bl_idname'] = node.bl_idname
        self._structure['height'] = node.height
        self._structure['width'] = node.width
        self._structure['label'] = node.label
        self._structure['hide'] = node.hide
        self._structure['location'] = recursive_framed_location_finder(node, node.location[:])

        if node.use_custom_color:
            self._structure['color'] = node.color[:]
            self._structure['use_custom_color'] = True

    def _add_node_properties(self, node: SverchCustomTreeNode):
        """adds non default node properties"""
        for prop_name in node.keys():
            prop = BPYProperty(node, prop_name)
            if self._is_property_to_export(prop):
                if prop.type == 'COLLECTION':
                    # protection from storing default values
                    self._structure["params"][prop_name] = prop.filter_collection_values()
                else:
                    self._structure["params"][prop.name] = prop.value

    def _add_socket_properties(self, node: SverchCustomTreeNode):
        """
        add non default input socket properties
        output sockets does not have anything worth exporting
        """
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
                self._structure['custom_socket_props'][str(i)] = sock_props

    @staticmethod
    def _is_property_to_export(prop: BPYProperty) -> bool:
        """Mark properties which should be skipped to save into json"""
        if not prop.is_valid:
            return False  # deprecated property
        elif not prop.is_to_save:
            return False
        elif prop.default_value == prop.value:
            return False  # the value will be loaded from code
        else:
            return True
