# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import os
import importlib
import inspect
from typing import Union

import bpy

from sverchok.utils.sv_oldnodes_parser import get_old_node_bl_idnames
from sverchok.utils.logging import error
from sverchok.utils.handle_blender_data import BlTrees


imported_mods = {}
old_bl_idnames = get_old_node_bl_idnames(path=os.path.dirname(__file__))


def is_old(node_info: Union[str, bpy.types.Node]):
    """
    Check if node or node.bl_idname is among
    the old nodes
    """
    if isinstance(node_info, str):
        # assumes bl_idname
        return node_info in old_bl_idnames
    elif isinstance(node_info, bpy.types.Node):
        return node_info.bl_idname in old_bl_idnames
    raise TypeError(f"String or Node is expected, {node_info} is given")


def mark_old(node):
    """Create a frame node around given one with deprecated label"""
    if node.parent and node.parent.label == "Deprecated node!":
        return
    ng = node.id_data
    frame = ng.nodes.new("NodeFrame")
    if node.parent:
        frame.parent = node.parent
    node.parent = frame
    frame.label = "Deprecated node!"
    frame.use_custom_color = True
    frame.color = (.8, 0, 0)
    frame.shrink = True


def mark_all():
    """Add frames with deprecated label to all deprecated nodes if necessary"""
    for node in (n for t in BlTrees().sv_trees for n in t.nodes):
        if node.bl_idname in old_bl_idnames:
            mark_old(node)


def register_old(bl_id):
    """Register old node class"""
    if bl_id in old_bl_idnames:
        mod = importlib.import_module(".{}".format(old_bl_idnames[bl_id]), __name__)
        res = inspect.getmembers(mod)
        for name, cls in res:
            if inspect.isclass(cls):
                if issubclass(cls, bpy.types.Node) and cls.bl_idname == bl_id:
                    if bl_id not in imported_mods:
                        mod.register()
                        imported_mods[bl_id] = mod
    else:
        raise LookupError(f"Cannot find {bl_id} among old nodes")


def register_all():
    """Register all old node classes"""
    for bl_id in old_bl_idnames:
        try:
            register_old(bl_id)
        except Exception as e:
            # when a code of an old node is copied to old folder
            # it can be copied with other classes (property groups)
            # which does not change it version to MK2, so we have the error
            error(e)


def register():

    import sverchok
    # This part is called upon scrip.reload (F8), because old nodes will be unregistered again
    # There is no way to say which old node classes should be registered without registering them all
    if sverchok.reload_event:
        register_all()


def unregister():
    for mod in imported_mods.values():
        try:
            mod.unregister()
        except Exception as e:
            error(e)
