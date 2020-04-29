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
from typing import NamedTuple, Union, List, Callable, Set
from itertools import takewhile

from bpy.types import Node, NodeTree

from sverchok.utils.context_managers import sv_preferences
from sverchok.core.update_system import process_from_nodes


def property_update(prop_name: str, call_function=None):

    # https://docs.python.org/3/library/functools.html#functools.partial
    def handel_update_call(node, context):
        CurrentEvents.add_new_event(BlenderEventsTypes.node_property_update,
                                    updated_element=node,
                                    redraw_function=handel_update_call.call_function,
                                    redraw_function_argument=(node, context))
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

    def get_draw_method_name(self):
        try:
            return DRAW_METHODS[self]
        except KeyError:
            raise KeyError(f"Event={self.name} does not have related draw method")


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


LINKS_CAN_BE_CHANGED = {
    BlenderEventsTypes.tree_update: True,
    BlenderEventsTypes.monad_tree_update: True,
    BlenderEventsTypes.node_update: False,
    BlenderEventsTypes.add_node: False,
    BlenderEventsTypes.copy_node: True,
    BlenderEventsTypes.free_node: True,
    BlenderEventsTypes.add_link_to_node: False,  # because added links are known
    BlenderEventsTypes.node_property_update: False,
    BlenderEventsTypes.undo: False,  # something like reload event will be appropriate to call
    BlenderEventsTypes.frame_change: False
}


DRAW_METHODS = {
    SverchokEventsTypes.add_node: 'sv_init',
    SverchokEventsTypes.copy_node: 'sv_copy',
    SverchokEventsTypes.free_node: 'sv_free',
    SverchokEventsTypes.node_link_update: 'sv_update'
}


class SverchokEvent(NamedTuple):
    type: SverchokEventsTypes
    node: Node
    redraw_function: Callable = None  # for properties updates
    redraw_function_arguments: tuple = None

    def redraw_node(self):
        # todo some refactoring needed
        if self.type == SverchokEventsTypes.node_property_update:
            if self.redraw_function:
                self.redraw_function(*self.redraw_function_arguments)
            else:
                return
        elif self.type in [SverchokEventsTypes.add_node, SverchokEventsTypes.copy_node]:
            getattr(self.node, self.type.get_draw_method_name())(None)  # todo not None
        else:
            getattr(self.node, self.type.get_draw_method_name())()

    def print(self):
        self.type.print(self.node)


class BlenderEvent(NamedTuple):
    type: BlenderEventsTypes
    updated_element: Union[Node, NodeTree, None]
    redraw_function: Callable = None  # for properties updates
    redraw_function_arguments: tuple = None

    @property
    def is_wave_end(self):
        return IS_WAVE_END.get(self.type, False)

    @property
    def could_links_be_changed(self):
        return LINKS_CAN_BE_CHANGED[self.type]

    def convert_to_sverchok_event(self) -> SverchokEvent:
        try:
            sverchok_event_type = EVENT_CONVERSION[self.type]
            return SverchokEvent(sverchok_event_type, self.updated_element, self.redraw_function, self.redraw_function_arguments)
        except KeyError:
            raise KeyError(f"For Blender event type={self.type} Sverchek event is undefined")


class CurrentEvents:
    events_wave: List[BlenderEvent] = []
    _to_listen_new_events = True  # todo should be something more safe

    @classmethod
    def add_new_event(cls, event_type: BlenderEventsTypes, updated_element=None, redraw_function=None, redraw_function_argument=None):
        if not cls._to_listen_new_events:
            return
        if event_type == BlenderEventsTypes.node_update:
            # such updates are not informative
            return

        if cls.is_in_debug_mode():
            event_type.print(updated_element)
        cls.events_wave.append(BlenderEvent(event_type, updated_element, redraw_function, redraw_function_argument))
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
        self.nodes: Set[SvNode] = set()
        self.links: Set[SvLink] = set()

    def update_reconstruction(self, sv_event: SverchokEvent): ...

    def total_reconstruction(self): ...

    def need_total_reconstruction(self) -> bool: ...

    def check_reconstruction_correctness(self): ...

    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG" and prefs.log_update_events


class SvNode(NamedTuple):
    id: str

    @classmethod
    def init_from_node(cls, node) -> 'SvNode': ...

    def __hash__(self):
        return hash(id)

    def __eq__(self, other):
        return self.id == other


class SvLink(NamedTuple):
    id: str  # from_link.id + to_link.id
    from_node: SvNode
    to_node: SvNode

    @classmethod
    def init_from_link(cls, link) -> 'SvLink': ...

    def __hash__(self):
        return hash(id)

    def __eq__(self, other):
        return self.id == other
