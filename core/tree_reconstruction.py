# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from typing import Dict, Iterable, TYPE_CHECKING, Union, List, Generator, Set, NamedTuple
from operator import getitem
from itertools import count

import bpy

import sverchok.core.events_types as evt
import sverchok.core.hashed_tree_data as hash_data
from sverchok.utils.context_managers import sv_preferences

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from sverchok.core.events import SverchokEvent
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode

    NodeTree = Union[bpy.types.NodeTree, SverchCustomTreeNode]


"""
This data structure is coping data structure of existing Sverchok node trees
It helps to analyze changes which happens in a node tree
Also it is used for walking on tree for searching nodes which should be recalculated
It is always consistent to Blender trees
So it can be used for searching connections between nodes
The only problem is it has not any information about sockets for simplicity
They can be added in future

Warning: don't use `from` statement for import the module
"""


class NodeTreesReconstruction:
    node_trees: Dict[str, SvTree] = dict()

    @classmethod
    def get_node_tree_reconstruction(cls, tree_id: str) -> SvTree:
        if tree_id not in cls.node_trees:
            cls.node_trees[tree_id] = SvTree(tree_id)
        return cls.node_trees[tree_id]


class SvTree:
    def __init__(self, tree_id: str):
        self.id: str = tree_id
        self.nodes: SvNodesCollection = SvNodesCollection(self)
        self.links: SvLinksCollection = SvLinksCollection(self)

        self.walk: WalkSvTree = WalkSvTree(self)

    def update_reconstruction(self, sv_events: Iterable[SverchokEvent]):
        if self.need_total_reconstruction():
            self.total_reconstruction()
        else:

            for sv_event in sv_events:
                if sv_event.node_id:
                    # nodes should be first
                    if sv_event.type in [evt.SverchokEventsTypes.add_node, evt.SverchokEventsTypes.copy_node]:
                        self.nodes.add(sv_event.node_id)
                    elif sv_event.type == evt.SverchokEventsTypes.free_node:
                        self.nodes.free(sv_event.node_id)
                    elif sv_event.type == evt.SverchokEventsTypes.node_property_update:
                        self.nodes.set_is_outdated(sv_event.node_id)
                    else:
                        raise TypeError(f"Can't handle event={sv_event.type}")

            for sv_event in sv_events:
                if sv_event.link_id:
                    if sv_event.type == evt.SverchokEventsTypes.add_link:
                        self.links.add(sv_event.link_id)
                    elif sv_event.type == evt.SverchokEventsTypes.free_link:
                        self.links.free(sv_event.link_id)
                    else:
                        raise TypeError(f"Can't handle event={sv_event.type}")

        if self.is_in_debug_mode():
            self.check_reconstruction_correctness()

    def total_reconstruction(self):
        bl_tree = get_blender_tree(self.id)
        [self.nodes.add(node.node_id) for node in bl_tree.nodes]
        [self.links.add(link.link_id) for link in bl_tree.links]

    def need_total_reconstruction(self) -> bool:
        # usually node tree should not be empty
        return len(self.nodes) == 0

    def check_reconstruction_correctness(self):
        bl_tree = get_blender_tree(self.id)
        bl_links = {link.link_id for link in bl_tree.links}
        bl_nodes = {node.node_id for node in bl_tree.nodes}
        if bl_links == self.links and bl_nodes == self.nodes:
            print("Reconstruction is correct")
        else:
            print("!!! Reconstruction does not correct !!!")

    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG" and prefs.log_update_events

    def __repr__(self):
        return f"<SvTree(nodes={len(self.nodes)}, links={len(self.links)})>"


class SvLinksCollection:
    def __init__(self, tree: SvTree):
        self._tree: SvTree = tree
        self._links: Dict[str, SvLink] = dict()

    def add(self, link_id: str):
        bl_link = hash_data.HashedBlenderData.get_link(self._tree.id, link_id)
        from_node = self._tree.nodes[bl_link.from_node.node_id]
        to_node = self._tree.nodes[bl_link.to_node.node_id]
        sv_link = SvLink(link_id, from_node, to_node)
        from_node.outputs[link_id] = sv_link
        if not from_node.outputs:
            # if node already was connected it has actual calculations
            from_node.is_outdated = True
        to_node.inputs[link_id] = sv_link
        to_node.is_outdated = True
        self._links[link_id] = sv_link

    def free(self, link_id: str):
        sv_link = self._links[link_id]
        sv_link.from_node.free_link(sv_link)
        sv_link.to_node.free_link(sv_link)
        sv_link.to_node.is_outdated = True
        del self._links[link_id]

    def __eq__(self, other):
        return self._links.keys() == other

    def __repr__(self):
        return repr(self._links.values())

    def __len__(self):
        return len(self._links)

    def __sub__(self, other) -> List['SvLink']:
        if hasattr(other, '_links'):
            other._memorize_links()
            deleted_links_keys = self._links.keys() - other._links.keys()
            return [getitem(self._links, key) for key in deleted_links_keys]
        else:
            return NotImplemented

    def __getitem__(self, item: str) -> SvLink:
        return self._links[item]


class SvNodesCollection:
    def __init__(self, tree: SvTree):
        self._tree: SvTree = tree
        self._nodes: Dict[str, SvNode] = dict()

    def add(self, node_id: str):
        bl_node = hash_data.HashedBlenderData.get_node(self._tree.id, node_id)
        sv_node = SvNode(node_id, bl_node.name)
        self._nodes[node_id] = sv_node

    def free(self, node_id: str):
        # links should be deleted separately
        # event if node is deleted from node collection its steal exist in its links
        sv_node = self._nodes[node_id]
        sv_node.inputs.clear()
        sv_node.outputs.clear()
        del self._nodes[node_id]

    def set_is_outdated(self, node_id: str):
        sv_node = self._nodes[node_id]
        sv_node.is_outdated = True

    @staticmethod
    def walk_forward(from_nodes: Iterable[SvNode]) -> Generator[SvNode, None, None]:
        #  1----3
        #  \  /
        # 4-2
        # walk is unordered, it means that from one you can get to 3 and then to 2
        # you will never get to 4 moving forward from 1 and to 1 moving from 4
        visited_nodes = set()
        next_nodes = set(from_nodes)
        while next_nodes:
            current_node = next_nodes.pop()
            yield current_node
            visited_nodes.add(current_node)
            next_nodes.update(current_node.next() - visited_nodes)

    @staticmethod
    def walk_backward(from_nodes: Iterable[SvNode]) -> Generator[SvNode, None, None]:
        #  1----3
        #  \  /
        #   2--4
        # walk is unordered, it means that from 3 you can get to 1 and then to 2
        # you will never get to 4 moving forward from 3 and to 3 moving from 4
        visited_nodes = set()
        next_nodes = set(from_nodes)
        while next_nodes:
            current_node = next_nodes.pop()
            yield current_node
            visited_nodes.add(current_node)
            next_nodes.update(current_node.last() - visited_nodes)

    def __eq__(self, other):
        return self._nodes.keys() == other

    def __getitem__(self, item):
        return self._nodes[item]

    def __setitem__(self, key, value):
        self._nodes[key] = value

    def __repr__(self):
        return repr(self._nodes.values())

    def __len__(self):
        return len(self._nodes)

    def __iter__(self):
        return iter(self._nodes.values())

    def __sub__(self, other) -> List['SvNode']:
        if hasattr(other, '_nodes'):
            other._memorize_nodes()
            deleted_nodes = self._nodes.keys() - other._nodes.keys()
            return [getitem(self._nodes, key) for key in deleted_nodes]
        else:
            return NotImplemented


class SvNode:
    def __init__(self, node_id: str, name: str):
        self.id: str = node_id
        self.name: str = name  # todo take in account renaming
        self.is_outdated = True

        self.inputs: Dict[str, SvLink] = dict()
        self.outputs: Dict[str, SvLink] = dict()

    def free_link(self, sv_link: SvLink):
        if sv_link.id in self.inputs:
            del self.inputs[sv_link.id]
        if sv_link.id in self.outputs:
            del self.outputs[sv_link.id]

    def next(self) -> Set[SvNode]:
        return {output_link.to_node for output_link in self.outputs.values()}

    def last(self) -> Set[SvNode]:
        return {input_link.from_node for input_link in self.inputs.values()}

    def __repr__(self):
        return f'<SvNode="{self.name}">'

    def __eq__(self, other):
        if isinstance(other, SvNode):
            return self.id == other.id
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.id)


class SvLink(NamedTuple):
    id: str  # from_socket.id + to_socket.id
    from_node: SvNode
    to_node: SvNode

    def __repr__(self):
        return f'<SvLink(from="{self.from_node.name}", to="{self.to_node.name}")>'

    def __eq__(self, other):
        if isinstance(other, SvLink):
            return self.id == other.id
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.id)


OUTPUT_NODE_BL_IDNAMES = {  # todo make mixin instead
    # main viewers
    'SvVDExperimental', 'SvStethoscopeNodeMK2', 'SvBmeshViewerNodeV28',
    # viewers
    'Sv3DviewPropsNode', 'SvMatrixViewer28', 'SvIDXViewer28', 'SvCurveViewerNodeV28', 'SvPolylineViewerNodeV28',
    'SvTypeViewerNodeV28', 'SvSkinViewerNodeV28', 'SvMetaballOutNode', 'SvNurbsCurveOutNode', 'SvNurbsSurfaceOutNode',
    'SvGreasePencilStrokes', 'SvEmptyOutNode', 'SvTextureViewerNode', 'SvTextureViewerNodeLite', 'SvWaveformViewer',
    'SvConsoleNode', 'SvLampOutNode', 'SvInstancerNode', 'SvInstancerNodeMK2', 'SvDupliInstancesMK4',
    # text viewers
    'ViewerNodeTextMK3', 'SvTextOutNodeMK2', 'SvDataShapeNode', 'SvDebugPrintNode',
    # other
    'SvSetPropNode', 'SvObjRemoteNodeMK2', 'SvSetDataObjectNodeMK2', 'SvVertexGroupNodeMK2', 'SvVertexColorNodeMK3',
    'SvAssignMaterialListNode', 'SvMaterialIndexNode', 'SvSetCustomUVMap', 'SvMeshUVColorNode', 'SvLatticePropsNode',
    'SvSculptMaskNode', 'SvSetCustomMeshNormals', 'SvParticlesMK2Node', 'SvSetPropNodeMK2', 'SvDictionaryOut'
}


class WalkSvTree:
    # https://github.com/nortikin/sverchok/issues/3058
    def __init__(self, sv_tree: SvTree):
        self.tree: SvTree = sv_tree

        #  1----2-----3-----4
        #            / \
        #  8---9----5   6---7
        #     /
        #   10
        # 4 nod id output node because it is  in OUTPUT_NODE_BL_IDNAMES set
        # in this case the 6,7 nodes will never be calculated
        # 2,10 are changed nodes by their parameters
        # the goal is visit 10-9-5-2-3-4 nodes in this order

        self.output_nodes: Set[SvNode] = set()  # 4 node
        self.outdated_nodes: Set[SvNode] = set()  # 10,2 nodes
        # the intersection of two sets below gives set of nodes which should be recalculated
        self.nodes_connected_to_output: Set[SvNode] = set()  # all nodes without 6, 7 (in the example)
        self.effected_by_changes_nodes: Set[SvNode] = set()  # all nodes without 1, 8 (in the example)
        self.worth_recalculating_nodes: Set[SvNode] = set()  # all nodes without 6, 7, 1, 8

    def walk_on_worth_recalculating_nodes(self) -> Generator[SvNode, None, None]:
        self.recalculate_effected_by_changes_nodes()

        safe_counter = count()
        maximum_possible_nodes_in_tree = 1000
        visited_nodes = set()
        waiting_nodes = set()
        next_nodes = self.outdated_nodes & self.worth_recalculating_nodes
        while (next_nodes or waiting_nodes) and next(safe_counter) < maximum_possible_nodes_in_tree:
            if next_nodes:
                current_node = next_nodes.pop()
                if not self.node_can_be_recalculated(current_node, visited_nodes):
                    waiting_nodes.add(current_node)
                    continue
                else:
                    yield current_node
                    visited_nodes.add(current_node)
                    worth_recalculating_next = current_node.next() & self.worth_recalculating_nodes
                    next_nodes.update(worth_recalculating_next - waiting_nodes)
            else:
                next_nodes.update(waiting_nodes)
                waiting_nodes.clear()
        if next(safe_counter) >= maximum_possible_nodes_in_tree:
            raise RecursionError("Looks like update tree is broken, cant recalculate nodes")

    def prepare_walk_after_tree_topology_changes(self):
        self.search_output_nodes()
        self.recalculate_connected_to_output_nodes()

    def search_output_nodes(self):
        self.output_nodes.clear()
        for sv_node in self.tree.nodes:
            bl_node = hash_data.HashedBlenderData.get_node(self.tree.id, sv_node.id)
            if bl_node.bl_idname in OUTPUT_NODE_BL_IDNAMES:
                self.output_nodes.add(sv_node)

    def recalculate_connected_to_output_nodes(self):
        self.nodes_connected_to_output.clear()
        [self.nodes_connected_to_output.add(node) for node in self.tree.nodes.walk_backward(self.output_nodes)]

    def recalculate_effected_by_changes_nodes(self):
        self.outdated_nodes = set([node for node in self.tree.nodes if node.is_outdated])
        self.effected_by_changes_nodes.clear()
        [self.effected_by_changes_nodes.add(node) for node in self.tree.nodes.walk_forward(self.outdated_nodes)]
        self.worth_recalculating_nodes = self.nodes_connected_to_output & self.effected_by_changes_nodes

    def node_can_be_recalculated(self, node: SvNode, visited_nodes: Set[SvNode]) -> bool:
        # it test whether all nodes before was already calculated
        worth_recalculating_nodes = node.last() & self.worth_recalculating_nodes
        not_calculated_nodes_yet_before = worth_recalculating_nodes - visited_nodes
        return False if not_calculated_nodes_yet_before else True


def get_blender_tree(tree_id: str) -> NodeTree:
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            ng: SverchCustomTree
            if ng.tree_id == tree_id:
                return ng
    raise LookupError(f"Looks like some node tree has disappeared, or its ID has changed")
