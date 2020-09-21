# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

import json
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Union, Generator, ContextManager

import bpy
from sverchok.utils.sv_IO_panel_tools import get_file_obj_from_zip
from sverchok.utils.logging import debug, info, warning
from sverchok.utils import dummy_nodes
from sverchok.utils.handle_blender_data import BPYProperty

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONImporter01:
    def __init__(self, structure: dict):
        self._structure = structure
        self._fails_log = FailsLog()

    @classmethod
    def init_from_path(cls, path: str) -> JSONImporter01:
        if path.endswith('.zip'):
            structure = get_file_obj_from_zip(path)
            return cls(structure)
        elif path.endswith('.json'):
            with open(path) as fp:
                structure = json.load(fp)
                return cls(structure)
        else:
            warning(f'File should have .zip or .json extension, got ".{path.rsplit(".")[-1]}" instead')

    def import_into_tree(self, tree: SverchCustomTree):

        root_tree_builder = TreeImporter01(tree, self._structure, self._fails_log)
        root_tree_builder.import_tree()
        self._fails_log.report_log_result()

    def _monads(self) -> Generator[str]:
        ...


class TreeImporter01:
    def __init__(self, tree: SverchCustomTree, structure: dict, log: FailsLog):
        self._tree = tree
        self._structure = structure
        self._fails_log = log
        self._new_node_names = dict()  # map(old_node_name, new_node_name)

    def import_tree(self):
        with TreeGenerator.start_from_tree(self._tree, self._fails_log) as tree_builder:
            for node_name, node_type, node_structure in self._nodes():
                node = tree_builder.add_node(node_type, node_name)
                if node is None:
                    continue
                self._new_node_names[node_name] = node.name
                NodeImporter01(node, node_structure, self._fails_log).import_node()

            for from_node_name, from_socket_index, to_node_name, to_socket_index in self._links():
                with self._fails_log.add_fail("Search node to link"):
                    from_node_name = self._new_node_names[from_node_name]
                    to_node_name = self._new_node_names[to_node_name]
                tree_builder.add_link(from_node_name, from_socket_index, to_node_name, to_socket_index)

    def _nodes(self) -> Generator[tuple]:
        if "nodes" not in self._structure:
            return
        nodes = self._structure["nodes"]
        with self._fails_log.add_fail("Reading nodes"):
            for node_name, node_structure in nodes.items():
                with self._fails_log.add_fail("Reading node"):
                    yield node_name, node_structure['bl_idname'], node_structure

    def _links(self) -> Generator[tuple]:
        if 'update_lists' not in self._structure:
            return
        links = self._structure['update_lists']
        with self._fails_log.add_fail("Reading links"):
            for from_node_name, form_socket_index, to_node_name, to_socket_index in links:
                yield from_node_name, form_socket_index, to_node_name, to_socket_index

    def _parent_nodes(self) -> Generator[tuple]: ...


class NodeImporter01:
    def __init__(self, node: SverchCustomTreeNode, structure: dict, log: FailsLog):
        self._node = node
        self._structure = structure
        self._fails_log = log

    def import_node(self):
        for attr_name, attr_value in self._node_attributes():
            with self._fails_log.add_fail(
                    "Setting node attribute",
                    f'Tree: {self._node.id_data.name}, Node: {self._node.name}, attr: {attr_name}'):
                setattr(self._node, attr_name, attr_value)

        for prop_name, prop_value in self._node_properties():
            with self._fails_log.add_fail(
                    "Setting node property",
                    f'Tree: {self._node.id_data.name}, Node: {self._node.name}, prop: {prop_name}'):
                BPYProperty(self._node, prop_name).value = prop_value

        for sock_index, prop_name, prop_value in self._input_socket_properties():
            with self._fails_log.add_fail(
                    "Setting socket property",
                    f'Tree: {self._node.id_data.name}, Node: {self._node.name}, prop: {prop_name}'):
                socket = self._node.inputs[sock_index]
                BPYProperty(socket, prop_name).value = prop_value

    def _node_attributes(self) -> Generator[tuple]:
        with self._fails_log.add_fail("Reading node location", f'Node: {self._node.name}'):
            yield "location", self._structure["location"]

        required_attributes = ["height", "width", "label", "hide", "color", "use_custom_color"]
        for attr in required_attributes:
            if attr in self._structure:
                yield attr, self._structure[attr]

    def _node_properties(self) -> Generator[tuple]:
        with self._fails_log.add_fail("Reading node properties", f'Node: {self._node.name}'):
            for prop_name, prop_value in self._structure.get('params', dict()).items():
                yield prop_name, prop_value

    def _input_socket_properties(self) -> Generator[tuple]:
        with self._fails_log.add_fail("Reading sockets properties", f'Node: {self._node.name}'):
            for str_index, sock_props in self._structure.get('custom_socket_props', dict()).items():
                with self._fails_log.add_fail("Reading socket properties", 
                                              f'Node: {self._node.name}, Socket: {str_index}'):
                    sock_index = int(str_index)
                    for prop_name, prop_value in sock_props.items():
                        yield sock_index, prop_name, prop_value


class TreeGenerator:
    def __init__(self, tree_name: str, log: FailsLog):
        self._tree_name: str = tree_name
        self._fails_log: FailsLog = log

    @classmethod
    @contextmanager
    def start_from_new(cls, tree_name) -> TreeGenerator: ...

    @classmethod
    @contextmanager
    def start_from_tree(cls, tree: SverchCustomTree, log: FailsLog) -> ContextManager[TreeGenerator]:
        tree.freeze(hard=True)
        builder = cls(tree.name, log)
        try:
            yield builder
        finally:
            # avoiding using tree object directly for crash preventing, probably too cautious
            builder._tree.unfreeze(hard=True)

    def add_node(self, bl_type: str, node_name: str) -> Union[SverchCustomTreeNode, None]:
        with self._fails_log.add_fail("Creating node", f'Tree: {self._tree_name}, Node: {node_name}'):
            if dummy_nodes.is_dependent(bl_type):
                # some node types are not registered if dependencies are not installed
                # in this case such nodes are registered as dummies
                dummy_nodes.register_dummy(bl_type)
            node = self._tree.nodes.new(bl_type)
            node.name = node_name
            return node

    def add_link(self, from_node_name, from_socket_index, to_node_name, to_socket_index):
        with self._fails_log.add_fail(
                "Creating link", f'Tree: {self._tree_name}, from: {from_node_name, from_socket_index}, '
                                 f'to: {to_node_name, to_socket_index}'):
            from_socket = self._tree.nodes[from_node_name].outputs[from_socket_index]
            to_socket = self._tree.nodes[to_node_name].inputs[to_socket_index]
            self._tree.links.new(from_socket, to_socket)

    def apply_frame(self, frame_name: str, nodes): ...

    @property
    def _tree(self) -> SverchCustomTree:
        return bpy.data.node_groups[self._tree_name]


class FailsLog:
    def __init__(self):
        self._log = defaultdict(int)

    @contextmanager
    def add_fail(self, fail_name, source=None):
        try:
            yield
        except Exception as e:
            self._log[fail_name] += 1
            debug(f'FAIL: "{fail_name}", {"SOURCE: " if source else ""}{source or ""}, {e}')

    @property
    def has_fails(self) -> bool:
        return bool(self._log)

    def report_log_result(self):
        if self.has_fails:
            warning(f'During import next fails has happened:')
            [print(f'FAIL: {msg} - {number}') for msg, number in self._log.items()]
        else:
            info(f'Import done with no fails')
