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

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONImporter01:
    def __init__(self, structure: dict):
        self._structure = structure

    @classmethod
    def init_from_path(cls, path: str) -> JSONImporter01:
        if path.endswith('.zip'):
            structure = get_file_obj_from_zip(path)
        elif path.endswith('.json'):
            with open(path) as fp:
                structure = json.load(fp)
                return cls(structure)
        else:
            warning(f'File should have .zip or .json extension, got ".{path.rsplit(".")[-1]}" instead')

    def import_into_tree(self, tree: SverchCustomTree):
        with TreeGenerator.start_from_tree(tree) as tree_builder:
            for node_importer in self._nodes():
                node = tree_builder.add_node(node_importer.node_type, node_importer.node_name)
            tree_builder.report_import_result()

    def _nodes(self) -> Generator[NodeImporter01]:
        if "nodes" in self._structure:
            nodes = self._structure["nodes"]
            if isinstance(nodes, dict):
                for node_name, node_structure in nodes.items():
                    yield NodeImporter01(node_name, node_structure)
            else:
                info('Nodes have unsupported format')
        else:
            debug('Nodes in root tree was not found')

    def _links(self) -> Generator[tuple]: ...

    def _parent_nodes(self) -> Generator[tuple]: ...

    def _monads(self) -> Generator[str]: ...


class NodeImporter01:
    def __init__(self, node_name: str, structure: dict):
        self.node_name = node_name
        self._structure = structure

    @property
    def node_type(self):
        return self._structure['bl_idname']

    def node_attributes(self) -> Generator[tuple]: ...

    def node_properties(self) -> Generator[tuple]: ...

    def input_socket_properties(self) -> Generator[tuple]: ...


class TreeGenerator:
    def __init__(self, tree_name: str):
        self._tree_name = tree_name
        self._fails_log = defaultdict(int)

    @classmethod
    @contextmanager
    def start_from_new(cls, tree_name) -> TreeGenerator: ...

    @classmethod
    @contextmanager
    def start_from_tree(cls, tree: SverchCustomTree) -> ContextManager[TreeGenerator]:
        tree.freeze(hard=True)
        builder = cls(tree.name)
        try:
            yield builder
        finally:
            # avoiding using tree object directly for crash preventing
            builder._tree.unfreeze(hard=True)

    def add_node(self, bl_type: str, node_name: str) -> NodeGenerator:
        try:
            node = self._tree.nodes.new(bl_type)
        except Exception as e:
            debug(f'Exporting node "{node_name}" is failed, {e}')
            self._fails_log['import node fails'] += 1
        else:
            node.name = node_name
            return node

    def add_link(self, from_node_name, from_socket_identifier, to_node_name, to_socket_identifier): ...

    def apply_frame(self, frame_name: str, nodes): ...

    def report_import_result(self):
        if self._fails_log:
            warning(f'During import next fails has happened:')
            [print(f'{msg} - {number}') for msg, number in self._fails_log.items()]
        else:
            info(f'Import into tree "{self._tree_name}" done with no fails')

    @property
    def _tree(self) -> SverchCustomTree:
        return bpy.data.node_groups[self._tree_name]


class NodeGenerator:
    def __init__(self, tree_name, node_name): ...

    def set_node_attribute(self, attr_name, value): ...

    def set_node_property(self, prop: BPYProperty): ...

    def set_socket_property(self, socket_identifier: str, prop: BPYProperty): ...


class BPYProperty:
    def __init__(self, data, prop_name: str): ...

    def set_property(self, data): ...
