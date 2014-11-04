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
#  Contributor(s):
#     Nedovizin Alexander
#     Gorodetskiy Nikita
#     Linus Yng
#     Agustin Gimenez
#     Dealga McArdle
#
#  ***** END GPL LICENSE BLOCK *****
#
# -*- coding: utf-8 -*-

bl_info = {
    "name": "Sverchok",
    "author": (
        "(sverchok-b3d@yandex.ru) "
        "Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, "
        "Agustin Jimenez, Dealga McArdle"
    ),
    "version": (0, 5,1),
    "blender": (2, 7, 2),
    "location": "Nodes > CustomNodesTree > Add user nodes",
    "description": "Do parametric node-based geometry programming",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok",
    "tracker_url": (
        "http://www.blenderartists.org/forum/showthread.php?272679"
        "-Addon-WIP-Sverchok-parametric-tool-for-architects"),
    "category": "Node"}

import sys
import importlib


# monkey patch the sverchok name, I am sure there is a better way to do this.

if __name__ != "sverchok":
    sys.modules["sverchok"] = sys.modules[__name__]
    
# to store imported modules
imported_modules = []

# ugly hack, should make respective dict in __init__ like nodes
# or parse it
root_modules = ["node_tree", "data_structure","core", 
                "utils", "utils", "sv_nodes_menu", "nodes", "old_nodes"]
core_modules = ["handlers", "update_system", "upgrade_nodes"]
utils_modules = [
    # non UI tools
    "cad_module", "sv_bmesh_utils", "sv_curve_utils", "voronoi", 
    "sv_script", "sv_itertools", "script_importhelper",
    # callbacks for bgl
    "viewer_draw", "index_viewer_draw", "nodeview_bgl_viewer_draw", "viewer_draw_mk2",
    # UI
    #     - text editor ui
    "text_editor_submenu", "text_editor_plugins",
    #     - node_view ui tool + panels + custom menu
    "sv_panels_tools", "sv_IO_panel", "sv_panels", "nodeview_space_menu", "group_tools"
]

# modules and pkg path, nodes are done separately.
mods_bases = [(root_modules, "sverchok"), 
              (core_modules, "sverchok.core"), 
              (utils_modules, "sverchok.utils")]

#  settings have to be treated separately incase the folder name
#  is something else than sverchok...
settings = importlib.import_module(".settings", __name__)
imported_modules.append(settings)

def import_modules(modules, base, im_list):
    for m in modules:
        im = importlib.import_module('.{}'.format(m), base)
        im_list.append(im)

# parse the nodes/__init__.py dictionary and load all nodes

def make_node_list():
    node_list = []
    base_name = "sverchok.nodes"
    for category, names in nodes.nodes_dict.items():
        importlib.import_module('.{}'.format(category), base_name)
        import_modules(names, '{}.{}'.format(base_name, category), node_list)
    return node_list

for mods, base in mods_bases:
    import_modules(mods, base, imported_modules)

node_list = make_node_list()

reload_event = bool("bpy" in locals())

if reload_event:   
    import nodeitems_utils
    #  reload the base modules
    #  then reload nodes after the node module as been reloaded
    for im in imported_modules:
        importlib.reload(im)
    node_list = make_node_list()
    for node in node_list:
        importlib.reload(node)

    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")

    from sverchok.sv_nodes_menu import make_categories
    nodeitems_utils.register_node_categories("SVERCHOK", make_categories()[0])

import bpy
import nodeitems_utils

def register():
    from sverchok.sv_nodes_menu import make_categories

    menu, node_count = make_categories()
    for m in imported_modules + node_list:
        if hasattr(m, "register"):
            m.register()
    # this is used to access preferences, should/could be hidden
    # in an interface
    data_structure.SVERCHOK_NAME = __name__
    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.register_node_categories("SVERCHOK", menu)
        
    print("** Sverchok loaded with {i} nodes **".format(i=node_count))
    
    if reload_event:
        data_structure.RELOAD_EVENT = True
        print("Sverchok is reloaded, press update")


def unregister():
    for m in reversed(imported_modules + node_list):
        if hasattr(m, "unregister"):
            m.unregister()

    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
