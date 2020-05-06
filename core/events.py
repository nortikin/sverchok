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
from typing import TYPE_CHECKING, NamedTuple, Union, List, Callable, Set, Dict, Iterable, Generator, KeysView
from itertools import takewhile, count
from contextlib import contextmanager
import traceback
from operator import getitem
from time import time, strftime

from bpy.types import Node, NodeTree, NodeLink
import bpy

from sverchok.utils.context_managers import sv_preferences

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode


def property_update(prop_name: str, call_function=None):

    # https://docs.python.org/3/library/functools.html#functools.partial
    def handel_update_call(node, context):
        CurrentEvents.add_new_event(event_type=BlenderEventsTypes.node_property_update,
                                    node_tree=node.id_data,
                                    node=node,
                                    call_function=handel_update_call.call_function,
                                    call_function_arguments=(node, context))
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
    # using sverchok defined properties (link_id) leads to crash during the event
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
    add_link = auto()
    free_link = auto()
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
    BlenderEventsTypes.add_link_to_node: SverchokEventsTypes.add_link,
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
    tree_id: str = None
    node_id: str = None
    link_id: str = None

    def print(self):
        if self.node_id:
            if self.type == SverchokEventsTypes.free_node:
                reconstruction_tree = NodeTreesReconstruction.get_node_tree_reconstruction(self.tree_id)
                node = reconstruction_tree.nodes[self.node_id]
            else:
                node = HashedBlenderData.get_node(self.tree_id, self.node_id)
            self.type.print(node)
        else:
            self.type.print()


class BlenderEvent(NamedTuple):
    # objects can't be kept only their ID, because they can lead to wrong memory address
    type: BlenderEventsTypes
    tree_id: str = None
    node_id: str = None
    link_id: str = None

    @property
    def is_wave_end(self):
        return IS_WAVE_END.get(self.type, False)

    def convert_to_sverchok_event(self) -> SverchokEvent:
        sverchok_event_type = EVENT_CONVERSION[self.type]
        return SverchokEvent(
            type=sverchok_event_type,
            tree_id=self.tree_id,
            node_id=self.node_id,
            link_id=self.link_id
        )


class EventsWave:
    # It is stack of Blender events (signals) for handling them together as one event
    id_counter = count()

    def __init__(self):
        self.events_wave: List[BlenderEvent] = []
        self._id = next(EventsWave.id_counter)
        self._id_reroutes_was_done = False

        self.links_was_added = False
        self.links_was_removed = False
        self.reroutes_was_added = False
        self.reroutes_was_removed = False
        self.relinking = False  # when number of links is unchanged but connections are different

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
        if self.events_wave and not self.is_end():
            # even during sub events of update tree event the objects can change their memory address
            raise RuntimeError("You should waite wave end before calling this property")
        return self._id

    def convert_to_sverchok_events(self) -> Set[SverchokEvent]:
        if not self.is_end():
            raise RuntimeError("You should waite wave end before calling this method")
        tree_was_changed = (self.events_wave[-1].type in [
            BlenderEventsTypes.tree_update,
            BlenderEventsTypes.monad_tree_update,
            BlenderEventsTypes.node_property_update])
        if tree_was_changed:
            self.analyze_changes()
            # todo reset id copied reroutes
            known_sv_events = self.convert_known_events()
            found_sv_events = self.search_linking_events()
            known_sv_events.update(found_sv_events)
            return known_sv_events
        else:
            known_sv_events = self.convert_known_events()
            return known_sv_events

    def is_end(self) -> bool:
        return self.events_wave and self.events_wave[-1].is_wave_end

    def analyze_changes(self):
        if (self.events_wave[0].type == BlenderEventsTypes.tree_update or
                self.events_wave[0].type == BlenderEventsTypes.monad_tree_update):
            # New: Nodes = 0; Links = 0-inf; Reroutes = 0-inf
            # Remove: Nodes=0, Links = 0-n, Reroutes = 0-n
            # Tools: F, Ctrl + RMB, Shift + RMB, manual unlink, python (un)link
            self.links_was_added = (len(self.current_tree.links) - len(self.previous_tree.links)) > 0
            # todo it has appeared that relinking also is possible via Blender API and such fast tests can`t detect it.
            self.links_was_removed = (len(self.current_tree.links) - len(self.previous_tree.links)) < 0
            self.reroutes_was_added = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) > 0
            self.reroutes_was_removed = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) < 0
        elif self.events_wave[0].type == BlenderEventsTypes.add_node:
            # New: Nodes = 1; Links = 0; Reroutes = 0
            # Tools: manual adding, via python adding
            pass
        elif self.events_wave[0].type == BlenderEventsTypes.copy_node:
            # New: Nodes = 1-n; Links = 0-n; Reroutes = 0-n
            # Tools: manual copy
            self.links_was_added = (len(self.current_tree.links) - len(self.previous_tree.links)) > 0

            copy_events = list(self.first_type_events())
            new_nodes_total = len(self.current_tree.nodes) - len(self.previous_tree.nodes)
            self.reroutes_was_added = (new_nodes_total - len(copy_events)) > 0
        elif self.events_wave[0].type == BlenderEventsTypes.free_node:
            # Remove: Nodes = 1-n; Links = 0-n; Reroutes = 0-n
            # Tools: manual delete selected, python delete one node (reroutes are node included)
            self.links_was_removed = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) < 0

            free_events = list(self.first_type_events())
            free_nodes_total = len(self.current_tree.nodes) - len(self.previous_tree.nodes)
            self.reroutes_was_removed = (free_nodes_total - len(free_events)) > 0
        elif self.events_wave[0].type == BlenderEventsTypes.add_link_to_node:
            # New: Nodes = 0; Links = 0-n; Reroutes = 0
            # Tools: manual link or relink, with relink bunch of links could be changed
            number_of_links_was_not_change = len(self.current_tree.links) == len(self.previous_tree.links)
            self.relinking = True if number_of_links_was_not_change else False
        elif self.events_wave[0].type == BlenderEventsTypes.node_property_update:
            # Remove: Nodes = 0; Links = 0-n; Reroutes = 0
            # Tools: via Blender API
            self.links_was_removed = (len(self.current_tree.links) - len(self.previous_tree.links)) < 0

    def convert_known_events(self) -> Set[SverchokEvent]:
        if self.events_wave[0].type not in [BlenderEventsTypes.tree_update, BlenderEventsTypes.monad_tree_update]:
            return {bl_event.convert_to_sverchok_event() for bl_event in self.first_type_events()}
        else:
            return set()

    def search_linking_events(self) -> List[SverchokEvent]:
        if self.links_was_added:
            if self.events_wave[0].type == BlenderEventsTypes.copy_node or self.reroutes_was_added:
                # the idea was get new links from copied nodes
                # but API does not let to get links linked to a node efficiently
                pass

            new_links = self.search_new_links()
            return [SverchokEvent(type=SverchokEventsTypes.add_link,
                                  tree_id=self.main_event.tree_id,
                                  link_id=link.link_id) for link in new_links]
        elif self.links_was_removed:
            if self.events_wave[0].type == BlenderEventsTypes.free_node or self.reroutes_was_removed:
                nodes_removed = {self.previous_tree.nodes[ev.node_id] for ev in self.first_type_events()}
                removed_links = self.search_free_links_from_nodes(nodes_removed)
                return [SverchokEvent(type=SverchokEventsTypes.free_link,
                                      tree_id=self.main_event.tree_id,
                                      link_id=link.id) for link in removed_links]
            else:
                removed_links = self.search_free_links()
                return [SverchokEvent(type=SverchokEventsTypes.free_link,
                                      tree_id=self.main_event.tree_id,
                                      link_id=link.id) for link in removed_links]
        elif self.relinking:
            relinked_nodes = set()
            for link_event in self.first_type_events():
                bl_node_from = self.current_tree.links[link_event.link_id].from_node
                bl_node_to = self.current_tree.links[link_event.link_id].to_node
                relinked_nodes.add(self.previous_tree.nodes[bl_node_from.node_id])
                relinked_nodes.add(self.previous_tree.nodes[bl_node_to.node_id])
            removed_links = self.search_free_links_from_nodes(relinked_nodes)
            return [SverchokEvent(type=SverchokEventsTypes.free_link,
                                  tree_id=self.main_event.tree_id,
                                  link_id=link.id) for link in removed_links]
        return []

    def search_new_links(self):
        # should be called if user pressed F, Shift+RMB, copied linked reroutes, added via Python API
        return self.current_tree.links - self.previous_tree.links

    def search_free_links(self):
        # should be called if user unconnected link(s), Ctrl+RMB, delete reroutes, deleted via Python API
        return self.previous_tree.links - self.current_tree.links

    def search_free_links_from_nodes(self, sverchok_nodes: Set[SvNode]) -> List[SvLink]:
        # should be called if user deleted node, or relinking (add and remove links simultaneously)
        sv_links_keys = set()
        [sv_links_keys.update(node.inputs.keys()) for node in sverchok_nodes]
        [sv_links_keys.update(node.outputs.keys()) for node in sverchok_nodes]
        deleted_links_keys = sv_links_keys - self.current_tree.links.keys()
        return [self.previous_tree.links[key] for key in deleted_links_keys]

    def search_new_reroutes(self):
        # should be called if user created/copied new reroute(s), Shift+RMB, added via Python API
        pass

    def search_free_reroutes(self):
        # should be called if user deleted selected, deleted via Python API
        pass

    def first_type_events(self) -> Generator[BlenderEvent, None, None]:
        yield from takewhile(lambda ev: ev.type == self.events_wave[0].type, self.events_wave)

    @property
    def previous_tree(self) -> 'SvTree':
        return NodeTreesReconstruction.get_node_tree_reconstruction(self.main_event.tree_id)

    @property
    def current_tree(self) -> 'HashedTreeData':
        return HashedBlenderData.get_tree(self.main_event.tree_id)


class CurrentEvents:
    events_wave = EventsWave()
    _to_listen_new_events = True  # todo should be something more safe

    @classmethod
    def add_new_event(cls, event_type: BlenderEventsTypes,
                      node_tree: Union[NodeTree, SverchCustomTree] = None,
                      node: Union[Node, SverchCustomTreeNode] = None,
                      link: NodeLink = None,
                      call_function: Callable = None,
                      call_function_arguments: tuple = tuple()):
        if not cls._to_listen_new_events:
            return

        if cls.is_in_debug_mode():
            event_type.print(node or node_tree or None)

        with cls.deaf_mode():
            if call_function:
                # For such events like: new node, copy node, free node, property update
                # This methods can't be call later because their arguments can become bad
                call_function(*call_function_arguments)
            if event_type == BlenderEventsTypes.copy_node:
                # id of copied nodes should be reset, it should be done before event wave end
                # take in account that ID of copied reroutes also should be rested but later and not too late
                node.n_id = ''

        tree_id = node_tree.tree_id if node_tree else None
        node_id = node.node_id if node and event_type != BlenderEventsTypes.add_link_to_node else None
        link_id = link.link_id if link else None
        bl_event = BlenderEvent(event_type, tree_id, node_id, link_id)

        cls.events_wave.add_event(bl_event)
        cls.handle_new_event()

    @classmethod
    def handle_new_event(cls):
        if not cls.events_wave.is_end():
            return

        HashedBlenderData.reset_data(cls.events_wave.main_event.tree_id)

        with cls.deaf_mode():
            if cls.events_wave.main_event.type in [BlenderEventsTypes.tree_update,
                                                   BlenderEventsTypes.node_property_update]:
                cls.handle_tree_update_event()
            elif cls.events_wave.main_event.type == BlenderEventsTypes.frame_change:
                cls.handle_frame_change_event()
            elif cls.events_wave.main_event.type == BlenderEventsTypes.undo:
                cls.handle_undo_event()
            else:
                raise TypeError(f"Such event type={cls.events_wave.main_event.type} can't be handle")

        cls.events_wave = EventsWave()

    @classmethod
    def handle_tree_update_event(cls):
        # property changes chan lead to node tree changes (remove links)
        sv_events = cls.events_wave.convert_to_sverchok_events()
        if cls.is_in_debug_mode():
            [sv_event.print() for sv_event in sv_events]
        cls.redraw_nodes(sv_events)  # it should be done before reconstruction update
        # previous step can change links and relocate them in memory
        if (SverchokEventsTypes.add_link in [ev.type for ev in sv_events] or
            SverchokEventsTypes.free_link in [ev.type for ev in sv_events]):
            HashedBlenderData.reset_data(cls.events_wave.main_event.tree_id, reset_nodes=False)

        tree_reconstruction = cls.events_wave.previous_tree
        tree_reconstruction.update_reconstruction(sv_events)

        sv_nodes = tree_reconstruction.get_sverchok_nodes_to_calculate()
        cls.update_nodes(sv_nodes)

    @classmethod
    def handle_frame_change_event(cls): ...

    @classmethod
    def handle_undo_event(cls): ...

    @classmethod
    def redraw_nodes(cls, sverchok_events: Iterable[SverchokEvent]):
        # this method is calling nodes method which can make Blender relocate nodes and links in memory
        # so after this method all memorized Blender links and nodes should be reset
        hashed_tree = HashedBlenderData.get_tree(cls.events_wave.main_event.tree_id)
        previous_tree = NodeTreesReconstruction.get_node_tree_reconstruction(cls.events_wave.main_event.tree_id)
        deleted_node_ids = {ev.node_id for ev in sverchok_events if ev.type == SverchokEventsTypes.free_node}
        bl_link_update_nodes = set()
        for sv_event in sverchok_events:
            if sv_event.type == SverchokEventsTypes.add_link:
                # new links should be read from Blender tree
                link = hashed_tree.links[sv_event.link_id]
                bl_link_update_nodes.add(link.from_node)
                bl_link_update_nodes.add(link.to_node)
            if sv_event.type == SverchokEventsTypes.free_link:
                # deleted link should be read from reconstruction
                sv_link = previous_tree.links[sv_event.link_id]
                if sv_link.from_node.id not in deleted_node_ids:
                    bl_link_update_nodes.add(hashed_tree.nodes[sv_link.from_node.id])
                if sv_link.to_node.id not in deleted_node_ids:
                    bl_link_update_nodes.add(hashed_tree.nodes[sv_link.to_node.id])
        [node.sv_update() for node in bl_link_update_nodes]

    @classmethod
    def update_nodes(cls, changed_sv_nodes: Iterable[SvNode]):
        hashed_tree = HashedBlenderData.get_tree(cls.events_wave.main_event.tree_id)
        walker = Walkers.get_walker(cls.events_wave.main_event.tree_id)
        if cls.events_wave.main_event.type in [BlenderEventsTypes.monad_tree_update,
                                               BlenderEventsTypes.tree_update,
                                               BlenderEventsTypes.node_property_update]:
            walker.prepare_walk_after_tree_topology_changes()
        for recalculation_node in walker.walk_on_worth_recalculating_nodes(changed_sv_nodes):
            bl_node = hashed_tree.nodes[recalculation_node.id]
            with cls.record_node_statistics(bl_node) as node:
                if hasattr(node, 'process'):
                    node.process()


    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG" and prefs.log_update_events

    @classmethod
    @contextmanager
    def deaf_mode(cls):
        cls._to_listen_new_events = False
        try:
            yield
        except Exception:
            # todo using logger
            traceback.print_exc()
        finally:
            cls._to_listen_new_events = True

    @staticmethod
    @contextmanager
    def record_node_statistics(node: Union[Node, SverchCustomTreeNode]):
        exception = None
        start_time = time()
        try:
            yield node
        except Exception as e:
            # todo using logger
            exception = e
            traceback.print_exc()
        finally:
            node.updates_total += 1
            node.last_update = strftime("%H:%M:%S")
            node.update_time = int((time() - start_time) * 1000)
            node.error = repr(exception) if exception else ''


# -------------------------------------------------------------------------
# ---------This part should be moved to separate module later--------------


class NodeTreesReconstruction:
    node_trees: Dict[str, 'SvTree'] = dict()

    @classmethod
    def get_node_tree_reconstruction(cls, tree_id: str) -> 'SvTree':
        if tree_id not in cls.node_trees:
            cls.node_trees[tree_id] = SvTree(tree_id)
        return cls.node_trees[tree_id]


class SvTree:
    def __init__(self, tree_id: str):
        self.id: str = tree_id
        self.nodes: SvNodesCollection = SvNodesCollection(self)
        self.links: SvLinksCollection = SvLinksCollection(self)

    def update_reconstruction(self, sv_events: Iterable[SverchokEvent]):
        if self.need_total_reconstruction():
            self.total_reconstruction()
        else:

            for sv_event in sv_events:
                if sv_event.node_id:
                    # nodes should be first
                    if sv_event.type in [SverchokEventsTypes.add_node, SverchokEventsTypes.copy_node]:
                        self.nodes.add(sv_event.node_id)
                    elif sv_event.type == SverchokEventsTypes.free_node:
                        self.nodes.free(sv_event.node_id)
                    elif sv_event.type == SverchokEventsTypes.node_property_update:
                        self.nodes.set_is_outdated(sv_event.node_id)
                    else:
                        raise TypeError(f"Can't handle event={sv_event.type}")

            for sv_event in sv_events:
                if sv_event.link_id:
                    if sv_event.type == SverchokEventsTypes.add_link:
                        self.links.add(sv_event.link_id)
                    elif sv_event.type == SverchokEventsTypes.free_link:
                        self.links.free(sv_event.link_id)
                    else:
                        raise TypeError(f"Can't handle event={sv_event.type}")

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
        bl_link = HashedBlenderData.get_link(self._tree.id, link_id)
        from_node = self._tree.nodes[bl_link.from_node.node_id]
        to_node = self._tree.nodes[bl_link.to_node.node_id]
        sv_link = SvLink(link_id, from_node, to_node)
        from_node.outputs[link_id] = sv_link
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
        if isinstance(other, HashedLinks):
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
        bl_node = HashedBlenderData.get_node(self._tree.id, node_id)
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
        if isinstance(other, HashedNodes):
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


# -------------------------------------------------------------------------
# ---------This part should be moved to separate module later--------------


class HashedNodes:
    def __init__(self, tree: 'HashedTreeData'):
        self._tree: HashedTreeData = tree
        self._nodes: Dict[str, Node] = dict()

    def __getitem__(self, item: str) -> Union[Node, SverchCustomTreeNode]:
        self._memorize_nodes()
        return self._nodes[item]

    def __len__(self):
        return len(get_blender_tree(self._tree.tree_id).nodes)

    def __sub__(self, other) -> List[Union[Node, SverchCustomTreeNode]]:
        if isinstance(other, SvNodesCollection):
            self._memorize_nodes()
            new_nodes_keys = self._nodes.keys() - other._nodes.keys()
            return [getitem(self._nodes, key) for key in new_nodes_keys]
        else:
            return NotImplemented

    def _memorize_nodes(self):
        if not self._nodes:
            tree = get_blender_tree(self._tree.tree_id)
            self._nodes.update({node.node_id: node for node in tree.nodes})


class HashedLinks:
    def __init__(self, tree: 'HashedTreeData'):
        self._tree: HashedTreeData = tree
        self._links: Dict[str, NodeLink] = dict()

    def keys(self) -> KeysView:
        return self._links.keys()

    def __getitem__(self, item: str) -> NodeLink:
        self._memorize_links()
        return self._links[item]

    def __len__(self):
        return len(get_blender_tree(self._tree.tree_id).links)

    def __sub__(self, other) -> List[NodeLink]:
        self._memorize_links()
        if isinstance(other, SvLinksCollection):
            new_links_keys = self._links.keys() - other._links.keys()
            return [getitem(self._links, key) for key in new_links_keys]
        elif isinstance(other, set):
            new_links_keys = self._links.keys() - other
            return [getitem(self._links, key) for key in new_links_keys]
        else:
            return NotImplemented

    def _memorize_links(self):
        if not self._links:
            tree = get_blender_tree(self._tree.tree_id)
            self._links.update({link.link_id: link for link in tree.links})


class HashedTreeData:
    def __init__(self, tree_id: str):
        self.tree_id = tree_id

        self.nodes: HashedNodes = HashedNodes(self)
        self.links: HashedLinks = HashedLinks(self)

    def reset_node(self):
        self.nodes = HashedNodes(self)

    def reset_links(self):
        self.links = HashedLinks(self)


class HashedBlenderData:
    # keeping data fresh is CurrentEvents class responsibility
    tree_data: Dict[str, HashedTreeData] = dict()

    @classmethod
    def get_node(cls, tree_id: str, node_id: str) -> Union[Node, SverchCustomTreeNode]:
        hashed_tree = cls.get_tree(tree_id)
        return hashed_tree.nodes[node_id]

    @classmethod
    def get_link(cls, tree_id: str, link_id: str) -> NodeLink:
        hashed_tree = cls.get_tree(tree_id)
        return hashed_tree.links[link_id]

    @classmethod
    def get_tree(cls, tree_id: str) -> HashedTreeData:
        if tree_id not in cls.tree_data:
            cls.tree_data[tree_id] = HashedTreeData(tree_id)
        return cls.tree_data[tree_id]

    @classmethod
    def reset_data(cls, tree_id: str = None, reset_nodes=True, reset_links=True):
        if tree_id is None:
            cls.tree_data.clear()
        if tree_id in cls.tree_data:
            if reset_nodes:
                cls.tree_data[tree_id].reset_node()
            if reset_links:
                cls.tree_data[tree_id].reset_links()


def get_blender_tree(tree_id: str) -> Union[SverchCustomTree, NodeTree]:
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            ng: SverchCustomTree
            if ng.tree_id == tree_id:
                return ng
    raise LookupError(f"Looks like some node tree has disappeared, or its ID has changed")


# -------------------------------------------------------------------------
# ---------This part should be moved to separate module later--------------


# todo should be implemented in another class
class Walkers:
    walkers: Dict[str, WalkSvTree] = dict()

    @classmethod
    def get_walker(cls, tree_id: str) -> WalkSvTree:
        if tree_id not in cls.walkers:
            sv_tree = NodeTreesReconstruction.get_node_tree_reconstruction(tree_id)
            cls.walkers[tree_id] = WalkSvTree(sv_tree)
        return cls.walkers[tree_id]


OUTPUT_NODE_BL_IDNAMES = {
    'SvVDExperimental', 'SvStethoscopeNodeMK2', 'SvBmeshViewerNodeV28'
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
        # the intersection of two sets below gives set of nodes which should be recalculated
        self.nodes_connected_to_output: Set[SvNode] = set()  # all nodes without 6, 7 (in the example)
        self.effected_by_changes_nodes: Set[SvNode] = set()  # all nodes without 1, 8 (in the example)
        self.worth_recalculating_nodes: Set[SvNode] = set()  # all nodes without 6, 7, 1, 8

    def walk_on_worth_recalculating_nodes(self, changed_nodes: Iterable[SvNode]) -> Generator[SvNode, None, None]:
        self.recalculate_effected_by_changes_nodes(changed_nodes)
        safe_counter = count()
        maximum_possible_nodes_in_tree = 1000
        visited_nodes = set()
        waiting_nodes = set()
        next_nodes = set(changed_nodes) & self.worth_recalculating_nodes
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
            bl_node = HashedBlenderData.get_node(self.tree.id, sv_node.id)
            if bl_node.bl_idname in OUTPUT_NODE_BL_IDNAMES:
                self.output_nodes.add(sv_node)

    def recalculate_connected_to_output_nodes(self):
        self.nodes_connected_to_output.clear()
        [self.nodes_connected_to_output.add(node) for node in self.tree.nodes.walk_backward(self.output_nodes)]

    def recalculate_effected_by_changes_nodes(self, changed_nodes: Iterable[SvNode]):
        self.effected_by_changes_nodes.clear()
        [self.effected_by_changes_nodes.add(node) for node in self.tree.nodes.walk_forward(changed_nodes)]
        self.worth_recalculating_nodes = self.nodes_connected_to_output & self.effected_by_changes_nodes

    def node_can_be_recalculated(self, node: SvNode, visited_nodes: Set[SvNode]) -> bool:
        # it test whether all nodes before was already calculated
        worth_recalculating_nodes = node.last() & self.worth_recalculating_nodes
        not_calculated_nodes_yet_before = worth_recalculating_nodes - visited_nodes
        return False if not_calculated_nodes_yet_before else True
