# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from typing import TYPE_CHECKING, Union

import bpy
from sverchok.utils.sv_json_struct import FileStruct, NodePresetFileStruct

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTree
    SverchCustomTree = Union[SverchCustomTree, bpy.types.NodeTree]


class JSONExporter:
    """Static class for responsible for exporting into JSON format"""
    @staticmethod
    def get_tree_structure(tree: SverchCustomTree, use_selection=False) -> dict:
        """Generate structure of given tree which van be saved into json format"""
        return FileStruct().export_tree(tree, use_selection)

    @staticmethod
    def get_node_structure(node) -> dict:
        """For exporting node properties"""
        return NodePresetFileStruct().export(node)