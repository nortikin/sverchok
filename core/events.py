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


from enum import Enum, auto
from typing import NamedTuple, Union, List, Callable, Set, Dict
from itertools import takewhile

from bpy.types import Node, NodeTree, NodeLink
import bpy

from sverchok.utils.context_managers import sv_preferences
from sverchok.core.update_system import process_from_nodes


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
    add_link_to_node = auto()  # it can detects only manually created links
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


LINKS_COULD_BE_CHANGED = {
    BlenderEventsTypes.tree_update: True,
    BlenderEventsTypes.monad_tree_update: True,
    BlenderEventsTypes.node_update: False,
    BlenderEventsTypes.add_node: False,
    BlenderEventsTypes.copy_node: True,  # here can be used more fast test for only copied nodes
    BlenderEventsTypes.free_node: False,  # because we exactly know which links should be deleted with node
    BlenderEventsTypes.add_link_to_node: False,  # because added links are known
    BlenderEventsTypes.node_property_update: False,
    BlenderEventsTypes.undo: False,  # something like reload event will be appropriate to call
    BlenderEventsTypes.frame_change: False
}


class SverchokEvent(NamedTuple):
    type: SverchokEventsTypes
    tree: NodeTree = None
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
    tree: NodeTree = None
    node: Node = None
    link: NodeLink = None
    update_function: Callable = None  # for properties updates
    function_arguments: tuple = tuple()

    @property
    def is_wave_end(self):
        return IS_WAVE_END.get(self.type, False)

    @property
    def could_links_be_changed(self):
        return LINKS_COULD_BE_CHANGED[self.type]

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


class CurrentEvents:
    events_wave: List[BlenderEvent] = []
    _to_listen_new_events = True  # todo should be something more safe

    @classmethod
    def add_new_event(cls, bl_event: BlenderEvent):
        if not cls._to_listen_new_events:
            return
        if bl_event.type == BlenderEventsTypes.node_update:
            # such updates are not informative
            return

        if cls.is_in_debug_mode():
            bl_event.print()

        cls.events_wave.append(bl_event)
        cls.handle_new_event()

    @classmethod
    def handle_new_event(cls):
        if not cls.is_wave_end():
            return

        cls._to_listen_new_events = False

        link_change_events = cls.detect_new_links_events()
        node_change_events = cls.convert_wave_to_sverchok_events()
        # update reconstruction here
        cls.redraw_nodes(node_change_events + link_change_events)
        cls.update_nodes(node_change_events + link_change_events)

        cls._to_listen_new_events = True
        cls.events_wave.clear()

    @classmethod
    def is_wave_end(cls):
        return cls.events_wave[-1].is_wave_end

    @classmethod
    def detect_new_links_events(cls):
        if cls.events_wave[0].could_links_be_changed:
            # todo some simple changes test first
            return []
        else:
            return []

    @classmethod
    def convert_wave_to_sverchok_events(cls):
        if cls.events_wave[0].type == BlenderEventsTypes.undo:
            return []  # todo reload every thing probably
        elif cls.events_wave[0].type == BlenderEventsTypes.frame_change:
            return []  # todo should be implemented some changes test
        elif cls.events_wave[0].type in [BlenderEventsTypes.tree_update, BlenderEventsTypes.monad_tree_update]:
            return []  # todo new links should be tested
        else:  # node changes event
            all_events_of_first_type = takewhile(lambda ev: ev.type == cls.events_wave[0].type, cls.events_wave)
            return [ev.convert_to_sverchok_event() for ev in all_events_of_first_type]

    @classmethod
    def redraw_nodes(cls, sverchok_events: List[SverchokEvent]):
        for sv_event in sverchok_events:
            if cls.is_in_debug_mode():
                sv_event.print()
            sv_event.redraw_node()

    @staticmethod
    def update_nodes(sverchok_events: List[SverchokEvent]):
        process_from_nodes([ev.node for ev in sverchok_events if ev.type != SverchokEventsTypes.free_node])

    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG" and prefs.log_update_events


# -------------------------------------------------------------------------
# ---------This part should be moved to separate module later--------------


class NodeTreesReconstruction:
    node_trees = dict()

    @classmethod
    def update_reconstruction(cls, sv_event: SverchokEvent): ...

    @classmethod
    def get_node_tree_reconstruction(cls, node_tree) -> 'SvTree': ...


class SvTree:
    def __init__(self, tree_id: str):
        self.id: str = tree_id
        self.nodes: NodesCollection = NodesCollection(self)
        self.links: LinksCollection = LinksCollection(self)

    def update_reconstruction(self, sv_event: SverchokEvent):
        if self.need_total_reconstruction():
            self.total_reconstruction()
        else:
            pass
        if self.is_in_debug_mode():
            self.check_reconstruction_correctness()

    def total_reconstruction(self):
        bl_tree = self.get_blender_tree()
        [self.nodes.add(node) for node in bl_tree.nodes]
        [self.links.add(link) for link in bl_tree.links]

    def need_total_reconstruction(self) -> bool:
        # usually node tree should not be empty
        return bool(len(self.nodes))

    def check_reconstruction_correctness(self):
        bl_tree = self.get_blender_tree()
        bl_links = {link.from_socket.socket_id + link.to_socket.socket_id for link in bl_tree.links}
        bl_nodes = {node.node_id for node in bl_tree.nodes}
        if bl_links == self.links and bl_nodes == self.nodes:
            print("Reconstruction is correct")
        else:
            print("!!! Reconstruction does not correct !!!")

    def get_blender_tree(self) -> NodeTree:
        for ng in bpy.data.node_groups:
            if ng.bl_idname == 'SverchCustomTreeType':
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

    def add(self, node: Node):
        sv_node = SvNode(node.node_id, node.name)
        self._nodes[node.node_id] = sv_node

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


class SvNode:
    def __init__(self, node_id: str, name: str):
        self.id: str = node_id
        self.name: str = name  # todo take in account renaming
        self.inputs: Dict[str, SvLink] = dict()
        self.outputs: Dict[str, SvLink] = dict()

    def __repr__(self):
        return f'<SvNode="{self.name}">'


class SvLink(NamedTuple):
    id: str  # from_socket.id + to_socket.id
    from_node: SvNode
    to_node: SvNode

    def __repr__(self):
        return f'<SvLink(from="{self.from_node.name}", to="{self.to_node.name}")>'


# todo find appropriate place
import time


def node_id(self):
    if not self.n_id:
        self.n_id = str(hash(self) ^ hash(time.monotonic()))
    return self.n_id


def socket_id(self):
    """Id of socket used by data_cache"""
    return str(hash(self.node.node_id + self.identifier))


bpy.types.NodeReroute.n_id = bpy.props.StringProperty(default="")
bpy.types.NodeReroute.node_id = property(node_id)
bpy.types.NodeSocketColor.socket_id = property(socket_id)
