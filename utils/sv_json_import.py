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
from sverchok.core.update_system import build_update_list, process_tree
from sverchok import old_nodes
from sverchok.utils.sv_IO_panel_tools import get_file_obj_from_zip
from sverchok.utils.logging import debug, info, warning
from sverchok.utils import dummy_nodes
from sverchok.utils.handle_blender_data import BPYProperty, BPYNode
from sverchok.utils.sv_IO_monad_helpers import unpack_monad

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONImporter:
    def __init__(self, structure: dict):
        self._structure = structure
        self._fails_log = FailsLog()

    @classmethod
    def init_from_path(cls, path: str) -> JSONImporter:
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

        # Update tree
        build_update_list(tree)
        process_tree(tree)

    def import_node_settings(self, node: SverchCustomTreeNode):
        """
        It takes first node from file and apply its settings to given node
        It is strange but it is how it was originally implemented
        """
        node = BPYNode(node)
        for prop in node.properties:
            if prop.is_to_save:
                prop.unset()

        tree_importer = TreeImporter01(node.data.id_data, self._structure, self._fails_log)
        for node_name, node_type, node_structure in tree_importer.nodes():
            node_importer = NodeImporter01(node.data, node_structure, self._fails_log, tree_importer.file_version)
            node_importer.import_node(apply_attributes=False)
            break


class TreeImporter01:
    def __init__(self, tree: SverchCustomTree, structure: dict, log: FailsLog):
        self._tree = tree
        self._structure = structure
        self._fails_log = log
        self._new_node_names = dict()  # map(old_node_name, new_node_name)

    def import_tree(self):
        # create recursion, this is how monad import intend to work
        # in original module monads does not take in account that they can get another name
        # it logic remains and in this module
        with self._fails_log.add_fail("Reading monads", f'Tree: {self._tree.name}'):
            for name, str_struct in self._structure.get('groups', dict()).items():
                monad = bpy.data.node_groups.new(name, 'SverchGroupTreeType')
                TreeImporter01(monad, json.loads(str_struct), self._fails_log).import_tree()

        with TreeGenerator.start_from_tree(self._tree, self._fails_log) as tree_builder:
            for node_name, node_type, node_structure in self.nodes():
                if node_type == 'SvMonadGenericNode':
                    node = None
                    with self._fails_log.add_fail("Creating monad node", f'Tree: {self._tree.name}'):
                        node = unpack_monad(self._tree.nodes, node_structure)
                else:
                    node = tree_builder.add_node(node_type, node_name)
                if node:
                    self._new_node_names[node_name] = node.name
                    NodeImporter01(node, node_structure, self._fails_log, self.file_version).import_node()

            for from_node_name, from_socket_index, to_node_name, to_socket_index in self._links():
                with self._fails_log.add_fail("Search node to link"):
                    from_node_name = self._get_new_node_name(from_node_name)
                    to_node_name = self._get_new_node_name(to_node_name)
                tree_builder.add_link(from_node_name, from_socket_index, to_node_name, to_socket_index)

            for node_name, parent_name in self._parent_nodes():
                with self._fails_log.add_fail(
                        "Assign node parent",
                        f'Tree: {self._tree.name}, Node: {node_name}, Parent node: {parent_name}'):
                    node_name = self._get_new_node_name(node_name)
                    parent_name = self._get_new_node_name(parent_name)
                    self._tree.nodes[node_name].parent = self._tree.nodes[parent_name]

    @property
    def file_version(self):
        return float(self._structure['export_version'])

    def nodes(self) -> Generator[tuple]:
        with self._fails_log.add_fail("Reading nodes", f'Tree: {self._tree.name}'):
            for node_name, node_structure in self._structure.get("nodes", dict()).items():
                with self._fails_log.add_fail("Reading node"):
                    yield node_name, node_structure['bl_idname'], node_structure

    def _get_new_node_name(self, old_name):
        return self._new_node_names[old_name]

    def _links(self) -> Generator[tuple]:
        with self._fails_log.add_fail("Reading links", f'Tree: {self._tree.name}'):
            for from_node_name, form_socket_index, to_node_name, to_socket_index in \
                    self._structure.get('update_lists', []):
                yield from_node_name, form_socket_index, to_node_name, to_socket_index

    def _parent_nodes(self) -> Generator[tuple]:
        with self._fails_log.add_fail("Reading parent nodes", f'Tree: {self._tree.name}'):
            for node, parent in self._structure.get("framed_nodes", dict()).items():
                yield node, parent


class NodeImporter01:
    def __init__(self, node: SverchCustomTreeNode, structure: dict, log: FailsLog, import_version: float):
        self._node = node
        self._structure = structure
        self._fails_log = log
        self._import_version = import_version

    def import_node(self, apply_attributes: bool = True):
        if apply_attributes:
            for attr_name, attr_value in self._node_attributes():
                with self._fails_log.add_fail(
                        "Setting node attribute",
                        f'Tree: {self._node.id_data.name}, Node: {self._node.name}, attr: {attr_name}'):
                    setattr(self._node, attr_name, attr_value)

        for prop_name, prop_value in self._node_properties():
            if prop_name in {"all_props", "cls_dict", "monad"}:
                return  # this properties for monads which are applied in another place
            with self._fails_log.add_fail(
                    "Setting node property",
                    f'Tree: {self._node.id_data.name}, Node: {self._node.name}, prop: {prop_name}'):
                prop = BPYProperty(self._node, prop_name)
                if prop.is_valid:  # some files can have outdated properties which should be filtered
                    prop.value = prop_value

        # this block is before applying socket properties because some nodes can generate them in load method
        if hasattr(self._node, 'load_from_json'):
            with self._fails_log.add_fail(
                    "Setting advance node properties",
                    f'Tree: {self._node.id_data.name}, Node: {self._node.name}'):
                self._node.load_from_json(self._structure, self._import_version)

        for sock_index, prop_name, prop_value in self._input_socket_properties():
            with self._fails_log.add_fail(
                    "Setting socket property",
                    f'Tree: {self._node.id_data.name}, Node: {self._node.name}, prop: {prop_name}'):
                socket = self._node.inputs[sock_index]
                prop = BPYProperty(socket, prop_name)
                if prop.is_valid:
                    prop.value = prop_value

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
            if old_nodes.is_old(bl_type):  # old node classes are registered only by request
                old_nodes.register_old(bl_type)
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
