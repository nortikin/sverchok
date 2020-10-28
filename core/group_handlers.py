# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from functools import wraps

import bpy

from sverchok.core.events import GroupEvent
from sverchok.utils.tree_structure import Tree


class MainHandler:
    def __init__(self):
        self.handlers = group_node_update()

    def send(self, event: GroupEvent):
        self.handlers.send(event)


def coroutine(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        cr = f(*args, **kwargs)
        cr.send(None)
        return cr
    return wrap


@coroutine
def group_node_update(next_handler=None):
    while True:
        event: GroupEvent
        event = yield  # this variable can't have annotations here - syntax error
        if event.type == GroupEvent.GROUP_NODE_UPDATE:

            try:
                bl_tree = bpy.data.node_groups[event.updated_tree]
                tree = Tree(bl_tree)
                # nodes_to_update = {n for n in tree.bfs_walk(
                #     [n for n in tree.input_nodes if n.get_bl_node(bl_tree, by_name=False).bl_idname == 'NodeGroupInput'])}
                for node in tree.sorted_walk(
                        [n for n in tree.output_nodes
                         if n.get_bl_node(bl_tree, by_name=False).bl_idname == 'NodeGroupOutput']):
                    bl_node = node.get_bl_node(bl_tree, by_name=False)
                    if hasattr(bl_node, 'process'):
                        bl_node.process()
            except Exception as e:
                print(e)

        else:
            if next_handler:
                next_handler.send(event)
