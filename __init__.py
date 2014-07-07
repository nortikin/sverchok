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
    "author": "Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, Agustin Jimenez, Dealga McArdle",
    "version": (0, 4, 0),
    "blender": (2, 7, 0),
    "location": "Nodes > CustomNodesTree > Add user nodes",
    "description": "Do parametric node-based geometry programming",
    "warning": "requires nodes window",
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
import nodes

import data_structure
import node_tree
import menu
from .utils import sv_tools
from .core import handlers

nodes_list = []
for category, names in nodes.nodes_dict.items():
    nodes_cat = importlib.import_module('.{}'.format(category), 'nodes')
    for name in names:
        node = importlib.import_module('.{}'.format(name),
                                       'nodes.{}'.format(category))
        nodes_list.append(node)

if "bpy" in locals():
    import importlib
    import nodeitems_utils
    importlib.reload(data_structure)
    importlib.reload(node_tree)
    importlib.reload(nodes)
    importlib.reload(menu)
    importlib.reload(sv_tools)
    importlib.reload(handlers)
    # (index_)viewer_draw -> name not defined error, because I never used it??
    #importlib.reload(viewer_draw)
    #importlib.reload(index_viewer_draw)
    for n in nodes_list:
        importlib.reload(n)
    
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu.make_categories())

import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty

class SverchokPreferences(AddonPreferences):

    bl_idname = __name__

    def update_debug_mode(self, context):
        #print(dir(context))
        data_structure.DEBUG_MODE = self.show_debug

    def update_heat_map(self, context):
        data_structure.heat_map_state(self.heat_map)

    def set_frame_change(self, context):
        handlers.set_frame_change(self.frame_change_mode)
        
    show_debug = BoolProperty(name="Print update timings",
                              description="Print update timings in console",
                              default=False, subtype='NONE',
                              update=update_debug_mode)

    heat_map = BoolProperty(name="Heat map",
                            description="Color nodes according to time",
                            default=False, subtype='NONE',
                            update=update_heat_map)

    heat_map_hot = FloatVectorProperty(name="Heat map hot", description='',
                                       size=3, min=0.0, max=1.0,
                                       default=(.8, 0, 0), subtype='COLOR')

    heat_map_cold = FloatVectorProperty(name="Heat map cold", description='',
                                        size=3, min=0.0, max=1.0,
                                        default=(1, 1, 1), subtype='COLOR')
    
    frame_change_modes = \
            [("PRE", "Pre", "Update Sverchok before frame change", 0),
             ("POST", "Post", "Update Sverchok after frame change", 1),
             ("NONE", "None", "Sverchok doesn't update on frame change", 2)]
 
    frame_change_mode = EnumProperty(items=frame_change_modes, 
                            name="Frame change",
                            description="Select frame change handler", 
                            default="POST",
                            update=set_frame_change)
    
 
    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.label(text="General")
        col.label(text="Frame change handler:")
        row =  col.row()
        row.prop(self, "frame_change_mode", expand=True)
        col.separator()
        col.label(text="Debug")
        col.prop(self, "show_debug")
        col.prop(self, "heat_map")
        row = col.row()
        row.active = self.heat_map
        row.prop(self, "heat_map_hot")
        row.prop(self, "heat_map_cold")

        col.separator()
        row=layout.row()
        row.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        if sv_tools.sv_new_version:
            row.operator('node.sverchok_update_addon', text='Upgrade Sverchok addon')
        else:
            row.operator('node.sverchok_check_for_upgrades', text='Check for new version')


def register():
    import nodeitems_utils
    from .utils import sv_tools, text_editor_plugins, text_editor_submenu

    node_tree.register()
    for n in nodes_list:
        n.register()
    sv_tools.register()
    text_editor_plugins.register()
    text_editor_submenu.register()
    handlers.register()

    bpy.utils.register_class(SverchokPreferences)

    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.register_node_categories("SVERCHOK", menu.make_categories())


def unregister():
    import nodeitems_utils
    from .utils import sv_tools, text_editor_plugins, text_editor_submenu

    node_tree.unregister()
    for n in nodes_list:
        n.unregister()
    sv_tools.unregister()
    text_editor_plugins.unregister()
    text_editor_submenu.unregister()
    handlers.unregister()

    bpy.utils.unregister_class(SverchokPreferences)

    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
