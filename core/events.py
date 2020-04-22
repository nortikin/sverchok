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


class BlenderEvents(Enum):
    node_tree_update = 1
    node_update = 2

    def print(self, updated_element):
        print(f"EVENT: {self.name: <25} IN: {updated_element.bl_idname: <25} INSTANCE: {updated_element.name: <25}")


class CurrentEvents:
    events_stack = []  # todo should be freed somehow

    @classmethod
    def node_tree_update(cls, node_tree):
        cls.events_stack.append(BlenderEvents.node_tree_update)
        BlenderEvents.node_tree_update.print(node_tree)

    @classmethod
    def node_update(cls, node):
        cls.events_stack.append(BlenderEvents.node_update)
        BlenderEvents.node_update.print(node)
