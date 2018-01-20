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
#  Contact:      sverchok-b3d@ya.ru    ###
#  Information:  http://nikitron.cc.ua/sverchok_en.html   ###
#
#  The Original Code is: all of this file.
#
#  Contributor(s):
#     Nedovizin Alexander (aka Cfyzzz)
#     Gorodetskiy Nikita (aka Nikitron)
#     Linus Yng (aka Ly29)
#     Agustin Jimenez (aka AgustinJB)
#     Dealga McArdle (aka zeffii)
#     Konstantin Vorobiew (aka Kosvor)
#     Ilya Portnov (aka portnov)
#     Eleanor Howick (aka elfnor)
#     Walter Perdan (aka kalwalt)
#     Marius Giurgi (aka DolphinDream)
#
#  ***** END GPL LICENSE BLOCK *****
#
# -*- coding: utf-8 -*-

bl_info = {
    "name": "Sverchok",
    "author": (
        "sverchok-b3d@ya.ru, "
        "Cfyzzz, Nikitron, Ly29, "
        "AgustinJB, Zeffii, Kosvor, "
        "Portnov, Elfnor, kalwalt, DolphinDream"
    ),
    "version": (0, 5, 9, 6),
    "blender": (2, 7, 8),
    "location": "Nodes > CustomNodesTree > Add user nodes",
    "description": "Parametric node-based geometry programming",
    "warning": "",
    "wiki_url": "http://nikitron.cc.ua/sverch/html/main.html",
    "tracker_url": (
        "http://www.blenderartists.org/forum/showthread.php?272679"
        "-Addon-WIP-Sverchok-parametric-tool-for-architects"),
    "category": "Node"}


import sys
import importlib


# make sverchok the base module name, (if sverchok dir not named exactly "sverchok") 
if __name__ != "sverchok":
    sys.modules["sverchok"] = sys.modules[__name__]

from sverchok.core import root_modules, core_modules
from sverchok.utils import utils_modules
from sverchok.ui import ui_modules

# modules and pkg path, nodes are done separately.
mods_bases = [(root_modules, "sverchok"),
              (core_modules, "sverchok.core"),
              (utils_modules, "sverchok.utils"),
              (ui_modules, "sverchok.ui")]

# "settings" treated separately incase the sverchok dir not named "sverchok"
settings = importlib.import_module(".settings", __name__)
imported_modules = []
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

    # reload base modules
    for im in imported_modules:
        importlib.reload(im)

    # reload nodes
    node_list = make_node_list()
    for node in node_list:
        importlib.reload(node)
    old_nodes.reload_old()


import bpy
from sverchok.utils import ascii_print, auto_gather_node_classes, node_classes
from sverchok.core import node_defaults

def register():
    for m in imported_modules + node_list:
        if m.__name__ != "sverchok.menu":
            if hasattr(m, "register"):
                # print("Registering module: {}".format(m.__name__))
                m.register()

    data_structure.SVERCHOK_NAME = __name__
    ascii_print.show_welcome()
    node_defaults.register_defaults()
    auto_gather_node_classes()

    # register menu module after all nodes are registered
    menu.register()

    if reload_event:
        data_structure.RELOAD_EVENT = True
        menu.reload_menu()


def unregister():
    node_classes.clear()
    for m in reversed(imported_modules + node_list):
        if hasattr(m, "unregister"):
            # print("Unregistering module: {}".format(m.__name__))
            m.unregister()
