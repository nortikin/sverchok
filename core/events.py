# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Union, List, Callable, Set, Iterable, Generator
from itertools import takewhile, count
from contextlib import contextmanager
import traceback
from time import time, strftime

from bpy.types import Node, NodeTree, NodeLink
import bpy

from sverchok.utils.context_managers import sv_preferences
from sverchok.core.tree_reconstruction import NodeTreesReconstruction, SvTree, SvNode, SvLink
from sverchok.core.hashed_tree_data import HashedBlenderData
import sverchok.core.events_types as evt

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode

    Node = Union[bpy.types.Node, SverchCustomTreeNode]
    NodeTree = Union[bpy.types.NodeTree, SverchCustomTreeNode]


"""
Purpose of this module is centralization of update events.

It used for getting signals of Blender, analyze them, keeping tree reconstruction, updating and colorizing nodes.

Details: https://github.com/nortikin/sverchok/issues/3077
         https://github.com/nortikin/sverchok/issues/3058
"""


def property_update(prop_name: str, call_function=None):

    # https://docs.python.org/3/library/functools.html#functools.partial
    def handel_update_call(node, context):
        CurrentEvents.add_new_event(event_type=evt.BlenderEventsTypes.node_property_update,
                                    node_tree=node.id_data,
                                    node=node,
                                    call_function=handel_update_call.call_function,
                                    call_function_arguments=(node, context))
    handel_update_call.prop_name = prop_name
    handel_update_call.call_function = call_function
    return handel_update_call


class SverchokEvent(NamedTuple):
    type: evt.SverchokEventsTypes
    tree_id: str = None
    node_id: str = None
    link_id: str = None

    def print(self):
        if self.node_id:
            if self.type == evt.SverchokEventsTypes.free_node:
                reconstruction_tree = NodeTreesReconstruction.get_node_tree_reconstruction(self.tree_id)
                node = reconstruction_tree.nodes[self.node_id]
            else:
                node = HashedBlenderData.get_node(self.tree_id, self.node_id)
            self.type.print(node)
        else:
            self.type.print()


class BlenderEvent(NamedTuple):
    # objects can't be kept only their ID, because they can lead to wrong memory address
    type: evt.BlenderEventsTypes
    tree_id: str = None
    node_id: str = None
    link_id: str = None

    @property
    def is_wave_end(self):
        return evt.IS_WAVE_END.get(self.type, False)

    def convert_to_sverchok_event(self) -> SverchokEvent:
        sverchok_event_type = evt.EVENT_CONVERSION[self.type]
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
        if bl_event.type == evt.BlenderEventsTypes.node_update:
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
            evt.BlenderEventsTypes.tree_update,
            evt.BlenderEventsTypes.monad_tree_update,
            evt.BlenderEventsTypes.node_property_update])
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
        if (self.events_wave[0].type == evt.BlenderEventsTypes.tree_update or
                self.events_wave[0].type == evt.BlenderEventsTypes.monad_tree_update):
            # New: Nodes = 0; Links = 0-inf; Reroutes = 0-inf
            # Remove: Nodes=0, Links = 0-n, Reroutes = 0-n
            # Tools: F, Ctrl + RMB, Shift + RMB, manual unlink, python (un/re)link, past a node between links
            self.links_was_added = (len(self.current_tree.links) - len(self.previous_tree.links)) > 0
            # todo it has appeared that relinking also is possible via Blender API and such fast tests can`t detect it.
            self.links_was_removed = (len(self.current_tree.links) - len(self.previous_tree.links)) < 0
            self.reroutes_was_added = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) > 0
            self.reroutes_was_removed = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) < 0
        elif self.events_wave[0].type == evt.BlenderEventsTypes.add_node:
            # New: Nodes = 1; Links = 0; Reroutes = 0
            # Tools: manual adding, via python adding
            pass
        elif self.events_wave[0].type == evt.BlenderEventsTypes.copy_node:
            # New: Nodes = 1-n; Links = 0-n; Reroutes = 0-n
            # Tools: manual copy
            self.links_was_added = (len(self.current_tree.links) - len(self.previous_tree.links)) > 0

            copy_events = list(self.first_type_events())
            new_nodes_total = len(self.current_tree.nodes) - len(self.previous_tree.nodes)
            self.reroutes_was_added = (new_nodes_total - len(copy_events)) > 0
        elif self.events_wave[0].type == evt.BlenderEventsTypes.free_node:
            # Remove: Nodes = 1-n; Links = 0-n; Reroutes = 0-n
            # Tools: manual delete selected, python delete one node (reroutes are node included)
            self.links_was_removed = (len(self.current_tree.nodes) - len(self.previous_tree.nodes)) < 0

            free_events = list(self.first_type_events())
            free_nodes_total = len(self.current_tree.nodes) - len(self.previous_tree.nodes)
            self.reroutes_was_removed = (free_nodes_total - len(free_events)) > 0
        elif self.events_wave[0].type == evt.BlenderEventsTypes.add_link_to_node:
            # New: Nodes = 0; Links = 0-n; Reroutes = 0
            # Tools: manual link or relink, with relink bunch of links could be changed
            number_of_links_was_not_change = len(self.current_tree.links) == len(self.previous_tree.links)
            self.relinking = True if number_of_links_was_not_change else False
        elif self.events_wave[0].type == evt.BlenderEventsTypes.node_property_update:
            # Remove: Nodes = 0; Links = 0-n; Reroutes = 0
            # Tools: via Blender API
            self.links_was_removed = (len(self.current_tree.links) - len(self.previous_tree.links)) < 0

    def convert_known_events(self) -> Set[SverchokEvent]:
        if self.events_wave[0].type not in [evt.BlenderEventsTypes.tree_update,
                                            evt.BlenderEventsTypes.monad_tree_update]:
            return {bl_event.convert_to_sverchok_event() for bl_event in self.first_type_events()}
        else:
            return set()

    def search_linking_events(self) -> List[SverchokEvent]:
        if self.links_was_added:
            if self.events_wave[0].type == evt.BlenderEventsTypes.copy_node or self.reroutes_was_added:
                # the idea was get new links from copied nodes
                # but API does not let to get links linked to a node efficiently
                # but if copy node it means that only new links could be created
                new_links = self.search_new_links()
                return [SverchokEvent(type=evt.SverchokEventsTypes.add_link,
                                      tree_id=self.main_event.tree_id,
                                      link_id=link.link_id) for link in new_links]
            else:
                # also links could be deleted if a node was past between links
                new_links = self.search_new_links()
                free_links = self.search_free_links()
                add_links_events = [SverchokEvent(type=evt.SverchokEventsTypes.add_link,
                                                  tree_id=self.main_event.tree_id,
                                                  link_id=link.link_id) for link in new_links]
                remove_links_events = [SverchokEvent(type=evt.SverchokEventsTypes.free_link,
                                                     tree_id=self.main_event.tree_id,
                                                     link_id=link.id) for link in free_links]
                return add_links_events + remove_links_events
        elif self.links_was_removed:
            if self.events_wave[0].type == evt.BlenderEventsTypes.free_node or self.reroutes_was_removed:
                nodes_removed = {self.previous_tree.nodes[ev.node_id] for ev in self.first_type_events()}
                removed_links = self.search_free_links_from_nodes(nodes_removed)
                return [SverchokEvent(type=evt.SverchokEventsTypes.free_link,
                                      tree_id=self.main_event.tree_id,
                                      link_id=link.id) for link in removed_links]
            else:
                removed_links = self.search_free_links()
                return [SverchokEvent(type=evt.SverchokEventsTypes.free_link,
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
            return [SverchokEvent(type=evt.SverchokEventsTypes.free_link,
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
    def add_new_event(cls, event_type: evt.BlenderEventsTypes,
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
            if event_type == evt.BlenderEventsTypes.copy_node:
                # id of copied nodes should be reset, it should be done before event wave end
                # take in account that ID of copied reroutes also should be rested but later and not too late
                node.n_id = ''

        tree_id = node_tree.tree_id if node_tree else None
        node_id = node.node_id if node and event_type != evt.BlenderEventsTypes.add_link_to_node else None
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
            if cls.events_wave.main_event.type in [evt.BlenderEventsTypes.tree_update,
                                                   evt.BlenderEventsTypes.node_property_update]:
                cls.handle_tree_update_event()
            elif cls.events_wave.main_event.type == evt.BlenderEventsTypes.frame_change:
                cls.handle_frame_change_event()
            elif cls.events_wave.main_event.type == evt.BlenderEventsTypes.undo:
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
        if (evt.SverchokEventsTypes.add_link in [ev.type for ev in sv_events] or
            evt.SverchokEventsTypes.free_link in [ev.type for ev in sv_events]):
            HashedBlenderData.reset_data(cls.events_wave.main_event.tree_id, reset_nodes=False)

        tree_reconstruction = cls.events_wave.previous_tree
        tree_reconstruction.update_reconstruction(sv_events)

        updated_nodes = cls.update_nodes()
        cls.recolorize_nodes(set(updated_nodes))

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
        deleted_node_ids = {ev.node_id for ev in sverchok_events if ev.type == evt.SverchokEventsTypes.free_node}
        bl_link_update_nodes = set()
        for sv_event in sverchok_events:
            if sv_event.type == evt.SverchokEventsTypes.add_link:
                # new links should be read from Blender tree
                link = hashed_tree.links[sv_event.link_id]
                bl_link_update_nodes.add(link.from_node)
                bl_link_update_nodes.add(link.to_node)
            if sv_event.type == evt.SverchokEventsTypes.free_link:
                # deleted link should be read from reconstruction
                sv_link = previous_tree.links[sv_event.link_id]
                if sv_link.from_node.id not in deleted_node_ids:
                    bl_link_update_nodes.add(hashed_tree.nodes[sv_link.from_node.id])
                if sv_link.to_node.id not in deleted_node_ids:
                    bl_link_update_nodes.add(hashed_tree.nodes[sv_link.to_node.id])
        [node.sv_update() for node in bl_link_update_nodes]

    @classmethod
    def update_nodes(cls) -> List[Node]:
        hashed_tree = HashedBlenderData.get_tree(cls.events_wave.main_event.tree_id)
        reconstruction_tree = NodeTreesReconstruction.get_node_tree_reconstruction(cls.events_wave.main_event.tree_id)
        if cls.events_wave.main_event.type in [evt.BlenderEventsTypes.monad_tree_update,
                                               evt.BlenderEventsTypes.tree_update,
                                               evt.BlenderEventsTypes.node_property_update]:
            reconstruction_tree.walk.prepare_walk_after_tree_topology_changes()
        recalculated_nodes = []
        for recalculation_node in reconstruction_tree.walk.walk_on_worth_recalculating_nodes():
            bl_node = hashed_tree.nodes[recalculation_node.id]
            with cls.record_node_statistics(bl_node) as node:
                if hasattr(node, 'process'):
                    node.process()
                recalculation_node.is_outdated = False
            recalculated_nodes.append(bl_node)
        return recalculated_nodes

    @classmethod
    def recolorize_nodes(cls, last_updated_nodes: Set[Union[Node, SverchCustomTreeNode]]):
        tree = get_blender_tree(cls.events_wave.main_event.tree_id)
        tree.choose_colorizing_method_with_nodes(last_updated_nodes)

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


def get_blender_tree(tree_id: str) -> NodeTree:
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            ng: SverchCustomTree
            if ng.tree_id == tree_id:
                return ng
    raise LookupError(f"Looks like some node tree has disappeared, or its ID has changed")
