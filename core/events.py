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


from enum import Enum

from sverchok.utils.context_managers import sv_preferences


class BlenderEvents(Enum):
    node_tree_update = 1
    node_update = 2

    def print(self, updated_element):
        print(f"EVENT: {self.name: <25} IN: {updated_element.bl_idname: <25} INSTANCE: {updated_element.name: <25}")


class CurrentEvents:
    events_stack = []  # todo should be freed somehow

    @classmethod
    def new_event(cls, event: BlenderEvents, updated_element):
        cls.events_stack.append(event)
        if cls.is_in_debug_mode():
            event.print(updated_element)

    @staticmethod
    def is_in_debug_mode():
        with sv_preferences() as prefs:
            return prefs.log_level == "DEBUG"
