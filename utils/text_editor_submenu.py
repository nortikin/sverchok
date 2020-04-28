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

import bpy
from bpy.props import StringProperty

from sverchok.utils import register_multiple_classes, unregister_multiple_classes
from sverchok.utils.sv_update_utils import sv_get_local_path

sv_path = os.path.dirname(sv_get_local_path()[0])
menu_prefix = "TEXT_MT_SvSNLiteTemplates"

def get_template_path():
    return os.path.join(sv_path, "node_scripts", "SNLite_templates")

def get_templates():
    path = get_template_path()
    return [(t, t, "") for t in next(os.walk(path))[1]]


def make_menu(name, path):
    """
    this generates a menu class at runtime, preferably when sverchok is starting up.
    """
    def draw(self, context):
        layout = self.layout
        self.path_menu(searchpaths=[path], operator="text.open", props_default={"internal": True})
    
    folder_name = f'{menu_prefix}_{name}'
    attributes = dict(bl_idname=folder_name, bl_label=name, draw=draw)
    return type(name, (bpy.types.Menu,), attributes)


snlite_template_path =  get_template_path()
submenus = []

for name, _, _ in get_templates():
    final_path = os.path.join(snlite_template_path, name)
    submenus.append(make_menu(name, final_path))

def get_submenu_names():
    for k in submenus:
        yield k.bl_label, k.bl_idname


class SvTextSubMenu(bpy.types.Menu):
    bl_idname = f'{menu_prefix}_menu'
    bl_label = "Sv NodeScripts"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        for menu_bl_label, menu_bl_idname in get_submenu_names():
            self.layout.menu(menu_bl_idname, text=menu_bl_label)


def menu_draw(self, context):
    self.layout.menu(f'{menu_prefix}_menu')

classes = submenus + [SvTextSubMenu]


def register():
    register_multiple_classes(classes)
    bpy.types.TEXT_MT_templates.append(menu_draw)


def unregister():
    bpy.types.TEXT_MT_templates.remove(menu_draw)
    unregister_multiple_classes(classes)
