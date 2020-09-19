# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Union, Generator

import bpy

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]
    SverchCustomTreeNode = Union[SverchCustomTreeNode, bpy.types.Node]


class JSONImporter01:
    def __init__(self, structure: dict): ...

    @classmethod
    def init_from_path(cls, path) -> JSONImporter01: ...

    def import_into_tree(self, tree: SverchCustomTree): ...

    def _nodes(self) -> Generator[NodeImporter01]: ...

    def _links(self) -> Generator[tuple]: ...

    def _parent_nodes(self) -> Generator[tuple]: ...

    def _monads(self) -> Generator[str]: ...


class NodeImporter01:
    def __init__(self, structure: dict): ...

    def node_attributes(self) -> Generator[tuple]: ...

    def node_properties(self) -> Generator[tuple]: ...

    def input_socket_properties(self) -> Generator[tuple]: ...


class TreeGenerator:
    def __init__(self, tree_name): ...

    @classmethod
    @contextmanager
    def start_from_new(cls, tree_name) -> TreeGenerator: ...

    @classmethod
    @contextmanager
    def start_from_tree(cls, tree: SverchCustomTree) -> TreeGenerator: ...

    def add_node(self, bl_type: str, node_name: str) -> NodeGenerator: ...

    def add_link(self, from_node_name, from_socket_identifier, to_node_name, to_socket_identifier): ...

    def apply_frame(self, frame_name: str, nodes): ...


class NodeGenerator:
    def __init__(self, tree_name, node_name): ...

    def set_node_attribute(self, attr_name, value): ...

    def set_node_property(self, prop: BPYProperty): ...

    def set_socket_property(self, socket_identifier: str, prop: BPYProperty): ...


class BPYProperty:
    def __init__(self, data, prop_name: str): ...

    def set_property(self, data): ...
