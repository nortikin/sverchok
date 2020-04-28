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

from sverchok.utils.sv_update_utils import sv_get_local_path

sv_path = os.path.dirname(sv_get_local_path()[0])


def get_template_path():
    return os.path.join(sv_path, "node_scripts", "SNLite_templates")

def get_templates():
    path = get_template_path()
    return [(t, t, "") for t in next(os.walk(path))[1]]

snlite_template_path =  get_template_path()

# def make_menu(name, path):
#     def draw(self, context):
#         layout = self.layout
#         self.path_menu(searchpaths=[path], operator="text.open", props_default={"internal": True})

#     folder_name = 'TEXT_MT_SvSNliteTemplates_' + name
#     attributes = dict(bl_idname=folder_name, bl_label=name, draw=draw)
#     return type(name, (bpy.types.Menu,), attributes)

# submenus = []
# menu_names = []

# m = get_templates()
# for name, p, _ in m:
#     final_path = os.path.join(snlite_template_path, name)

# for subdir in get_subdirs(current_dir):
#     submenu_name = os.path.basename(subdir)
#     menu_names.append(submenu_name)
#     dynamic_class = make_menu(submenu_name, subdir)
#     submenus.append(dynamic_class)


# def get_submenu_names():
#     for k in sorted(menu_names):
#         yield k, 'TEXT_MT_xtemplates_' + k


class SvTextSubMenu(bpy.types.Menu):
    bl_idname = "TEXT_MT_templates_submenu"
    bl_label = "Sv NodeScripts"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        args = dict(operator='text.open', props_default={'internal': True})
        m = get_templates()
        for name, p, _ in m:
            final_path = os.path.join(snlite_template_path, name)
            self.path_menu(searchpaths=[final_path], **args)



def menu_draw(self, context):
    self.layout.menu("TEXT_MT_templates_submenu")

classes = [SvTextSubMenu]


def register():
    sverchok.utils.register_multiple_classes(classes)
    bpy.types.TEXT_MT_templates.append(menu_draw)


def unregister():
    bpy.types.TEXT_MT_templates.remove(menu_draw)
    sverchok.utils.unregister_multiple_classes(classes)
