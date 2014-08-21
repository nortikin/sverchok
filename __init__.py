#  ***** BEGIN GPL LICENSE BLOCK *****
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
#  along with this program; if not, see <http://www.gnu.org/licenses/>
#  and write to the Free Software Foundation, Inc., 51 Franklin Street,
#  Fifth Floor, Boston, MA  02110-1301, USA..
#
#  The Original Code is Copyright (C) 2013-2014 by Gorodetskiy Nikita  ###
#  All rights reserved.
#
#  Contact:      sverchok-b3d@yandex.ru    ###
#  Information:  http://nikitron.cc.ua/sverchok.html   ###
#
#  The Original Code is: all of this file.
#
#  Contributor(s): Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, Agustin Gimenez.
#
#  ***** END GPL LICENSE BLOCK *****
#
# -*- coding: utf-8 -*-

bl_info = {
    "name": "Sverchok",
    "author": "(sverchok-b3d@yandex.ru) Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, Agustin Jimenez, Dealga McArdle",
    "version": (0, 4, 2),
    "blender": (2, 7, 0),
    "location": "Nodes > CustomNodesTree > Add user nodes",
    "description": "Do parametric node-based geometry programming",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok",
    "tracker_url": "http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects",
    "category": "Node"}


import os
import sys

current_path = os.path.dirname(__file__)
if not current_path in sys.path:
    sys.path.append(current_path)
    print("Have a nice day with Sverchok")


# use importlib instead of imp, which is deprecated since python 3.4
# importing first allows to stores a list of nodes before eventually reloading
# potential problem : are new nodes imported???
import importlib

imported_modules = []
node_list = []
# ugly hack, should make respective dict in __init__ like nodes
# or parse it
root_modules = ["node_tree",
                "data_structure", "menu"]
core_modules = ["handlers", "update_system", "upgrade_nodes"]
utils_modules = ["cad_module", "sv_bmesh_utils", "text_editor_submenu",
                 "index_viewer_draw", "sv_curve_utils", "viewer_draw",
                 "sv_tools", "voronoi", "nodeview_bgl_viewer_draw",
                 "text_editor_plugins"]

# parse the nodes/__init__.py dictionary and load all nodes
def make_node_list():
    node_list = []
    for category, names in nodes.nodes_dict.items():
        nodes_cat = importlib.import_module('.{}'.format(category), 'nodes')
        for name in names:
            node = importlib.import_module('.{}'.format(name),
                                           'nodes.{}'.format(category))
            node_list.append(node)
    return node_list

for m in root_modules:
    im = importlib.import_module('{}'.format(m), __name__)
    imported_modules.append(im)

menu = imported_modules[-1]

# settings needs __package__ set, so we use relative import
settings = importlib.import_module('.settings', __name__)
imported_modules.append(settings)

core = importlib.import_module('core')
imported_modules.append(core)


for m in core_modules:
    im = importlib.import_module('.{}'.format(m), "core")
    imported_modules.append(im)

utils = importlib.import_module('utils')
imported_modules.append(utils)

for m in utils_modules:
    im = importlib.import_module('.{}'.format(m),
                                 'utils')
    imported_modules.append(im)

nodes = importlib.import_module('nodes')
imported_modules.append(nodes)
node_list = make_node_list()
reload_event = False

if "bpy" in locals():
    import nodeitems_utils
    nodes = importlib.reload(nodes)
    node_list = make_node_list()
    for im in imported_modules+node_list:
        importlib.reload(im)

    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu.make_categories())
    # core.upgrade_nodes.upgrade_all()  # doesn't work, anyway.
    reload_event = True

import bpy


def register():
    import nodeitems_utils
    for m in imported_modules + node_list:
        if hasattr(m, "register"):
            m.register()
        else:
            pass
            #print("failed to register {}".format(m.__name__))
    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.register_node_categories("SVERCHOK", menu.make_categories())
    if reload_event:
        # tag reload event which will cause a full sverchok startup on
        # first update event
        for m in imported_modules:
            if m.__name__ == "data_structure":
                m.RELOAD_EVENT = True
        print("Sverchok is reloaded, press update")


def unregister():
    import nodeitems_utils
    for m in reversed(imported_modules + node_list):
        if hasattr(m, "unregister"):
            m.unregister()

    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
