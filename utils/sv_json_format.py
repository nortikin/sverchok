# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations


class JSONFormat01:
    """It's only know about Sverchok JSON structure nad can fill it"""
    def __init__(self, json_data=None):
        self._json_data = {
            "export_version": "0.10",
            "framed_nodes": dict(),
            "groups": dict(),
            "nodes": dict(),
            "update_lists": []
        } if json_data is None else json_data

    def add_node_in_frame(self, node_name, frame_name): ...

    def add_monad_tree(self, monad_name, magic_string): ...

    def add_node(self, node_name) -> NodeFormat:
        node_data = dict()
        self._json_data['nodes'][node_name] = node_data
        return NodeFormat(node_data)

    def add_link(self, from_node_name, from_socket_index, to_node_name, to_node_index): ...

    def extract_json(self, node_group): ...


class NodeFormat:
    def __init__(self, empty_node_data: dict):
        self._json_data = empty_node_data
        self._json_data.update({
            "bl_idname": "",
            "location": [],
            "params": dict(),
            "custom_socket_props": dict()
        })

    def add_mandatory_attributes(self, bl_idname: str, location: list): ...

    def add_node_custom_attribute(self, attr_name, attr_value): ...

    def add_socket_attribute(self, socket_index: int, attr_name: str, attr_value): ...

    def create_node(self, node_group, node_name): ...
