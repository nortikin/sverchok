# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

import json
from typing import TYPE_CHECKING, Union, Generator

import bpy
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.handle_blender_data import BPYProperty, BPYPointers
from sverchok.utils.sv_IO_monad_helpers import pack_monad

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONImporter:
    """It's only know about Sverchok JSON structure nad can fill it"""
    @staticmethod
    def get_structure(tree: SverchCustomTree, save_defaults: bool = False) -> dict:
        return TreeImporter01().import_tree(tree)

    @classmethod
    def create_from_nodes(cls, nodes: list, save_defaults: bool = False) -> JSONImporter: ...


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

    def import_monad(self, monad, owner_node_type) -> dict:
        self._structure['bl_idname'] = monad.bl_idname
        self._structure['cls_bl_idname'] = owner_node_type
        self.import_tree(monad)
        return json.dumps(self._structure)

    def _add_node(self, node: SverchCustomTreeNode):
        self._structure['nodes'][node.name] = NodeImporter01().import_node(node, self._structure['groups'])

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


class NodeImporter01:
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

    def import_node(self, node: SverchCustomTreeNode, groups: dict) -> dict:
        self._add_mandatory_attributes(node)
        self._add_node_properties(node)
        self._add_socket_properties(node)

        if hasattr(node, 'monad') and node.monad:
            self._structure['bl_idname'] = 'SvMonadGenericNode'
            pack_monad(node, self._structure['params'], groups, TreeImporter01().import_tree)

        if node.bl_idname in {'SvGroupInputsNodeExp', 'SvGroupOutputsNodeExp'}:
            self._structure[node.node_kind] = node.stash()

        if hasattr(node, 'save_to_json'):
            node.save_to_json(self._structure)
        return self._structure

    def _add_mandatory_attributes(self, node: SverchCustomTreeNode):
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
        for prop_name in node.keys():
            prop = BPYProperty(node, prop_name)
            if self._is_property_to_export(prop):
                if prop.type == 'COLLECTION':
                    # protection from storing default values
                    self._structure["params"][prop_name] = prop.filter_collection_values()
                else:
                    self._structure["params"][prop.name] = prop.value

    def _add_socket_properties(self, node: SverchCustomTreeNode):
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
                self._structure['custom_socket_props'][str(i)] = sock_props

    @staticmethod
    def _is_property_to_export(prop: BPYProperty) -> bool:
        if not prop.is_valid:
            return False  # deprecated property
        elif not prop.is_to_save:
            return False
        elif prop.default_value == prop.value:
            return False  # the value will be loaded from code
        else:
            return True
