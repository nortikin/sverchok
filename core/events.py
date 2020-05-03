# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Purpose of this module is centralization of update events.

For now it can be used in debug mode for understanding which event method are triggered by Blender
during evaluation of Python code.

Details: https://github.com/nortikin/sverchok/issues/3077
"""


from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple, Union, List, Callable, Set, Dict, Iterable
from itertools import takewhile, count
from contextlib import contextmanager

from bpy.types import Node, NodeTree, NodeLink
import bpy

from sverchok.utils.context_managers import sv_preferences
from sverchok.core.update_system import process_from_nodes

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode


def property_update(prop_name: str, call_function=None):

    # https://docs.python.org/3/library/functools.html#functools.partial
    def handel_update_call(node, context):
        bl_event = BlenderEvent(
            type=BlenderEventsTypes.node_property_update,
            tree=node.id_data,
            node=node,
            update_function=handel_update_call.call_function,
            function_arguments=(node, context)
        )
        CurrentEvents.add_new_event(bl_event)
    handel_update_call.prop_name = prop_name
    handel_update_call.call_function = call_function
    return handel_update_call


class BlenderEventsTypes(Enum):
    tree_update = auto()  # this updates is calling last with exception of creating new node
    monad_tree_update = auto()
    node_update = auto()  # it can be called last during creation new node event
    add_node = auto()   # it is called first in update wave
    copy_node = auto()  # it is called first in update wave
    free_node = auto()  # it is called first in update wave
    # all properties of free node are set to default and can't be change, so it loos its ID
    # never the less it keeps its actual name even if the node was renamed
    add_link_to_node = auto()  # it can detects only manually created links
    # link leeds to wrong memory address out of the signal method
    node_property_update = auto()  # can be in correct in current implementation
    undo = auto()  # changes in tree does not call any other update events
    frame_change = auto()

    def print(self, updated_element=None):
        event_name = f"EVENT: {self.name: <30}"
        if updated_element is not None:
            element_data = f"IN: {updated_element.bl_idname: <25} INSTANCE: {updated_element.name: <25}"
        else:
            element_data = ""
        print(event_name + element_data)


class SverchokEventsTypes(Enum):
    add_node = auto()
    copy_node = auto()
    free_node = auto()
    node_property_update = auto()
    node_link_update = auto()
    undo = auto()
    undefined = auto()  # probably should be deleted
    frame_change = auto()

    def print(self, updated_element=None):
        event_name = f"SVERCHOK EVENT: {self.name: <21}"
        element_data = f"NODE: {updated_element.name}" if updated_element else ""
        print(event_name + element_data)


EVENT_CONVERSION = {
    BlenderEventsTypes.tree_update: SverchokEventsTypes.undefined,
    BlenderEventsTypes.monad_tree_update: SverchokEventsTypes.undefined,
    BlenderEventsTypes.node_update: SverchokEventsTypes.undefined,
    BlenderEventsTypes.add_node: SverchokEventsTypes.add_node,
    BlenderEventsTypes.copy_node: SverchokEventsTypes.copy_node,
    BlenderEventsTypes.free_node: SverchokEventsTypes.free_node,
    BlenderEventsTypes.add_link_to_node: SverchokEventsTypes.node_link_update,
    BlenderEventsTypes.node_property_update: SverchokEventsTypes.node_property_update,
    BlenderEventsTypes.undo: SverchokEventsTypes.undo,
    BlenderEventsTypes.frame_change: SverchokEventsTypes.frame_change
}


IS_WAVE_END = {
    BlenderEventsTypes.tree_update: True,
    BlenderEventsTypes.node_property_update: True,
    BlenderEventsTypes.monad_tree_update: True,
    BlenderEventsTypes.undo: True,
    BlenderEventsTypes.frame_change: True
}


class SverchokEvent(NamedTuple):
    type: SverchokEventsTypes
    tree: SverchCustomTree = None
    node: Node = None
    link: NodeLink = None
    update_function: Callable = None  # for properties updates
    function_arguments: tuple = tuple()

    def redraw_node(self):
        if self.update_function:
            self.update_function(*self.function_arguments)

    def print(self):
        self.type.print(self.node)


class BlenderEvent(NamedTuple):
    type: BlenderEventsTypes
    tree: SverchCustomTree = None
    node: Node = None
    link: NodeLink = None
    update_function: Callable = None  # for properties updates
    function_arguments: tuple = tuple()

    @property
    def is_wave_end(self):
        return IS_WAVE_END.get(self.type, False)

    def convert_to_sverchok_event(self) -> SverchokEvent:
        sverchok_event_type = EVENT_CONVERSION[self.type]
        return SverchokEvent(
            type=sverchok_event_type,
            tree=self.tree,
            node=self.node,
            link=self.link,
            update_function=self.update_function,
            function_arguments=self.function_arguments
        )

    def print(self):
        self.type.print(self.node or self.tree)


class EventsWave:
    # It is stack of Blender events (signals) for handling them together as one event
    id_counter = count()

    def __init__(self):
        self.events_wave: List[BlenderEvent] = []
        self._id = next(EventsWave.id_counter)

        self.links_was_added = False
        self.links_was_removed = False
        self.reroutes_was_added = False
        self.reroutes_was_removed = False

    def add_event(self, bl_event: BlenderEvent):
        if bl_event.type == BlenderEventsTypes.node_update:
            # such updates are not informative
            return
        self.events_wave.append(bl_event)

    @property
    def main_event(self) -> BlenderEvent:
        if not self.is_end():
            raise RuntimeError("You should waite wave end before calling this property")
        return self.events_wave[-1]

    @property
    def id(self):
        if not self.is_end():
            # even during sub events of update tree event the objects can change their memory address
            raise RuntimeError("You should waite wave end before calling this property")
        return self._id

    def convert_to_sverchok_events(self) -> List[SverchokEvent]:
        if not self.is_end():
            raise RuntimeError("You should waite wave end before calling this method")
        tree_was_changed = (self.events_wave[-1].type == BlenderEventsTypes.tree_update or
                            self.events_wave[-1].type == BlenderEventsTypes.monad_tree_update)
        known_sv_events = self.convert_known_events()
        if tree_was_changed:
            self.analyze_changes()
            # found_sv_events = self.search_extra_events()
            return known_sv_events  # + found_sv_events
        else:
            return known_sv_events

    def is_end(self) -> bool:
        return self.events_wave and self.events_wave[-1].is_wave_end

    def analyze_changes(self):
        if (self.events_wave[0].type == BlenderEventsTypes.tree_update or
              self.events_wave[0].type == BlenderEventsTypes.monad_tree_update):
            # New: Nodes = 0; Links = 0-inf; Reroutes = 0-inf
            # Remove: Nodes=0, Links = 0-n, Reroutes = 0-n
            # Tools: F, Ctrl + RMB, Shift + RMB, manual unlink, python (un)link
            links_was_added = (len(self.current_tree.links) - len(self.previous_tree.links)) > 0
            links_was_removed = (len(self.current_tree.links) - len(self.previous_tree.links)) < 0
            reroutes_was_added = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) > 0
            reroutes_was_removed = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) < 0
            # todo continue
        elif self.events_wave[0].type == BlenderEventsTypes.add_node:
            # New: Nodes = 1; Links = 0; Reroutes = 0
            # Tools: manual adding, via python adding
            pass
        elif self.events_wave[0].type == BlenderEventsTypes.copy_node:
            # New: Nodes = 1-n; Links = 0-n; Reroutes = 0-n
            # Tools: manual copy
            links_was_added: bool
            reroutes_was_added: bool
        elif self.events_wave[0].type == BlenderEventsTypes.free_node:
            # Remove: Nodes = 1-n; Links = 0-n; Reroutes = 0-n
            # Tools: manual delete selected, python delete one node (reroutes are node included)
            links_was_removed: bool
            reroutes_was_removed: bool
        elif self.events_wave[0].type == BlenderEventsTypes.add_link_to_node:
            # New: Nodes = 0; Links = 0-n; Reroutes = 0
            # Tools: manual link or relink, with relink bunch of links could be changed
            pass
        else:
            pass

    def convert_known_events(self) -> List[SverchokEvent]:
        all_events_of_first_type = takewhile(lambda ev: ev.type == self.events_wave[0].type, self.events_wave)
        sv_events = dict()
        for bl_event in all_events_of_first_type:
            sv_event = bl_event.convert_to_sverchok_event()
            sv_events[sv_event] = sv_event
        return list(sv_events.values())

    def search_extra_events(self) -> List[SverchokEvent]: ...

    def search_new_links(self):
        # should be called if user pressed F, Shift+RMB, copied linked reroutes, added via Python API
        pass

    def search_new_links_from_new_nodes(self, copied_blender_nodes):
        # should be called if user copied linked nodes
        pass

    def search_free_links(self):
        # should be called if user unconnected link(s), Ctrl+RMB, delete reroutes, deleted via Python API
        pass

    def search_free_links_from_deleted_nodes(self, deleted_sverchok_nodes):
        # should be called if user deleted node
        pass

    def search_new_reroutes(self):
        # should be called if user created/copied new reroute(s), Shift+RMB, added via Python API
        pass

    def search_free_reroutes(self):
        # should be called if user deleted selected, deleted via Python API
        pass

    @property
    def previous_tree(self) -> 'SvTree':
        return NodeTreesReconstruction.get_node_tree_reconstruction(self.main_event.tree)

    @property
    def current_tree(self) -> SverchCustomTree:
        return self.events_wave[0].tree


class CurrentEvents:
    events_wave = EventsWave()
    _to_listen_new_events = True  # todo should be something more safe

    @classmethod
    def add_new_event(cls, bl_event: BlenderEvent):
        if not cls._to_listen_new_events:
            return

        if cls.is_in_debug_mode():
            if bl_event.type != BlenderEventsTypes.node_update:
                bl_event.print()

        cls.events_wave.add_event(bl_event)
        cls.handle_new_event()

    @classmethod
    def handle_new_event(cls):
        if not cls.events_wave.is_end():
            return

        with cls.deaf_mode():
            if cls.events_wave.main_event.type == BlenderEventsTypes.tree_update:
                cls.handle_tree_update_event()
            elif cls.events_wave.main_event.type == BlenderEventsTypes.node_property_update:
                cls.handle_property_change_event()
            elif cls.events_wave.main_event.type == BlenderEventsTypes.frame_change:
                cls.handle_frame_change_event()
            elif cls.events_wave.main_event.type == BlenderEventsTypes.undo:
                cls.handle_undo_event()
            else:
                raise TypeError(f"Such event type={cls.events_wave.main_event.type} can't be handle")

    @classmethod
    def handle_tree_update_event(cls):
        sv_events = cls.events_wave.convert_to_sverchok_events()
        cls.reset_nodes_id(sv_events)  # or copied nodes will have the same ides
        cls.redraw_nodes(sv_events)

        tree_reconstruction = cls.events_wave.previous_tree
        tree_reconstruction.update_reconstruction(sv_events)

        sv_nodes = tree_reconstruction.get_sverchok_nodes_to_calculate()
        hashed_tree_data = HashedBlenderData.get_tree_data(cls.events_wave.current_tree, cls.events_wave.id)
        bl_nodes = [hashed_tree_data.get_node_by_id(node.id) for node in sv_nodes]
        cls.update_nodes(bl_nodes)

    @classmethod
    def handle_property_change_event(cls): ...

    @classmethod
    def handle_frame_change_event(cls): ...

    @classmethod
    def handle_undo_event(cls): ...

    @classmethod
    def reset_nodes_id(cls, sv_events: Iterable[SverchokEvent]):
        [setattr(event.node, 'n_id', '') for event in sv_events if event.type == SverchokEventsTypes.copy_node]

    @classmethod
    def redraw_nodes(cls, sverchok_events: Iterable[SverchokEvent]):
        for sv_event in sverchok_events:
            if cls.is_in_debug_mode():
                sv_event.print()
            sv_event.redraw_node()

    @staticmethod
    def update_nodes(bl_nodes: List[Node]):
        process_from_nodes(bl_nodes)

    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG" and prefs.log_update_events

    @classmethod
    @contextmanager
    def deaf_mode(cls, recreate_wave=True):
        cls._to_listen_new_events = False
        try:
            yield
        except Exception as e:
            raise e
        finally:
            cls._to_listen_new_events = True
            if recreate_wave:
                cls.events_wave = EventsWave()


# -------------------------------------------------------------------------
# ---------This part should be moved to separate module later--------------


class NodeTreesReconstruction:
    node_trees: Dict[str, 'SvTree'] = dict()

    @classmethod
    def get_node_tree_reconstruction(cls, node_tree: SverchCustomTree) -> 'SvTree':
        if node_tree.tree_id not in cls.node_trees:
            cls.node_trees[node_tree.tree_id] = SvTree(node_tree.tree_id)
        return cls.node_trees[node_tree.tree_id]


class SvTree:
    def __init__(self, tree_id: str):
        self.id: str = tree_id
        self.nodes: NodesCollection = NodesCollection(self)
        self.links: LinksCollection = LinksCollection(self)

    def update_reconstruction(self, sv_events: Iterable[SverchokEvent]):
        if self.need_total_reconstruction():
            self.total_reconstruction()
        else:

            for sv_event in sv_events:
                if sv_event.node and not sv_event.link:
                    # nodes should be first
                    if sv_event.type in [SverchokEventsTypes.add_node, SverchokEventsTypes.copy_node]:
                        self.nodes.add(sv_event.node)
                    elif sv_event.type == SverchokEventsTypes.free_node:
                        self.nodes.free(sv_event.node)
                    elif sv_event.type == SverchokEventsTypes.node_property_update:
                        self.nodes.set_is_outdated(sv_event.node)
                    else:
                        raise TypeError(f"Can't handle event={sv_event.type}")
                elif sv_event.link:
                    if sv_event.type == SverchokEventsTypes.node_link_update:
                        self.links.add(sv_event.link)
                    else:
                        pass
                        # todo how to handle remove link
                else:
                    pass
                    # raise TypeError(f"Can't handle event={sv_event.type}")

        if self.is_in_debug_mode():
            self.check_reconstruction_correctness()

    def get_sverchok_nodes_to_calculate(self) -> List['SvNode']:
        # todo here "to update" property should be checked
        out = []
        for sv_node in self.nodes:
            if sv_node.is_outdated:
                sv_node.is_outdated = False
                out.append(sv_node)
        return out

    def total_reconstruction(self):
        bl_tree = self.get_blender_tree()
        [self.nodes.add(node) for node in bl_tree.nodes]
        [self.links.add(link) for link in bl_tree.links]

    def need_total_reconstruction(self) -> bool:
        # usually node tree should not be empty
        return len(self.nodes) == 0

    def check_reconstruction_correctness(self):
        bl_tree = self.get_blender_tree()
        bl_links = {link.from_socket.socket_id + link.to_socket.socket_id for link in bl_tree.links}
        bl_nodes = {node.node_id for node in bl_tree.nodes}
        if bl_links == self.links and bl_nodes == self.nodes:
            print("Reconstruction is correct")
        else:
            print("!!! Reconstruction does not correct !!!")

    def get_blender_tree(self) -> SverchCustomTree:
        for ng in bpy.data.node_groups:
            if ng.bl_idname == 'SverchCustomTreeType':
                ng: SverchCustomTree
                if ng.tree_id == self.id:
                    return ng
        raise LookupError(f"Looks like some node tree has disappeared, or its ID has changed")

    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG" and prefs.log_update_events

    def __repr__(self):
        return f"<SvTree(nodes={len(self.nodes)}, links={len(self.links)})>"


class LinksCollection:
    def __init__(self, tree: SvTree):
        self._tree: SvTree = tree
        self._links: Dict[str, SvLink] = dict()

    def add(self, link: NodeLink):
        link_id = link.from_socket.socket_id + link.to_socket.socket_id
        from_node = self._tree.nodes[link.from_node.node_id]
        to_node = self._tree.nodes[link.to_node.node_id]
        sv_link = SvLink(link_id, from_node, to_node)
        from_node.outputs[link_id] = sv_link
        to_node.inputs[link_id] = sv_link
        self._links[link_id] = sv_link

    def free(self, link: NodeLink):
        sv_link = self._links[link.link_id]
        sv_link.from_node.free_link(sv_link)
        sv_link.to_node.free_link(sv_link)
        del self._links[link.link_id]

    def __eq__(self, other):
        return self._links.keys() == other

    def __repr__(self):
        return repr(self._links.values())

    def __len__(self):
        return len(self._links)


class NodesCollection:
    def __init__(self, tree: SvTree):
        self._tree: SvTree = tree
        self._nodes: Dict[str, SvNode] = dict()

    def add(self, node: Union[SverchCustomTreeNode, Node]):
        sv_node = SvNode(node.node_id, node.name)
        self._nodes[node.node_id] = sv_node

    def free(self, node: Union[SverchCustomTreeNode, Node]):
        # links should be deleted separately
        # event if node is deleted from node collection its steal exist in its links
        sv_node = self._nodes[node.node_id]
        sv_node.inputs.clear()
        sv_node.outputs.clear()
        del self._nodes[node.node_id]

    def set_is_outdated(self, node: Union[SverchCustomTreeNode, Node]):
        sv_node = self._nodes[node.node_id]
        sv_node.is_outdated = True

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

    def __repr__(self):
        return f'<SvNode="{self.name}">'


class SvLink(NamedTuple):
    id: str  # from_socket.id + to_socket.id
    from_node: SvNode
    to_node: SvNode

    def __repr__(self):
        return f'<SvLink(from="{self.from_node.name}", to="{self.to_node.name}")>'


# -------------------------------------------------------------------------
# ---------This part should be moved to separate module later--------------


class HashedTreeData:
    def __init__(self, tree_id: str, update_wave_id: int):
        self.tree_id = tree_id
        self.update_wave_id = update_wave_id
        self.hashed_nodes_by_id: Dict[str, Node] = dict()

    def get_node_by_id(self, node_id: str) -> Node:
        if not self.hashed_nodes_by_id:
            self.hashed_nodes_by_id.update({node.node_id: node for node in self.get_tree().nodes})
        return self.hashed_nodes_by_id[node_id]

    def get_tree(self) -> Union[SverchCustomTree, NodeTree]:
        for ng in bpy.data.node_groups:
            if ng.bl_idname == 'SverchCustomTreeType':
                ng: SverchCustomTree
                if ng.tree_id == self.tree_id:
                    return ng
        raise LookupError(f"Looks like some node tree has disappeared, or its ID has changed")


class HashedBlenderData:
    tree_data: Dict[str, HashedTreeData] = dict()

    @classmethod
    def get_tree_data(cls, node_tree: SverchCustomTree, update_wave_id: int) -> 'HashedTreeData':
        if node_tree not in cls.tree_data:
            cls.tree_data[node_tree.tree_id] = HashedTreeData(node_tree.tree_id, update_wave_id)
        elif cls.tree_data[node_tree.tree_id].update_wave_id != update_wave_id:
            cls.tree_data[node_tree.tree_id] = HashedTreeData(node_tree.tree_id, update_wave_id)
        return cls.tree_data[node_tree.tree_id]
