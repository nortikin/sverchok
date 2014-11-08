# -*- coding: utf-8 -*-
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

import bpy

from sverchok.menu import make_node_cats
import sverchok

colors_cache = {}


def sv_colors_definition():
    addon_name = sverchok.__name__
    addon = bpy.context.user_preferences.addons.get(addon_name)
    if addon:
        prefs = addon.preferences
        sv_node_colors = {
            "Viz": prefs.sv_color_viz,
            "Text": prefs.sv_color_tex,
            "Scene": prefs.sv_color_sce,
            "Layout": prefs.sv_color_lay,
            "Generators": prefs.sv_color_gen,
            }
    else:
        sv_node_colors = {
            "Viz": (1, 0.3, 0),
            "Text": (0.5, 0.5, 1),
            "Scene": (0, 0.5, 0.2),
            "Layout": (0.674, 0.242, 0.363),
            "Generators": (0, 0.5, 0.5),
            }
    sv_node_cats = make_node_cats()
    sv_cats_node = {}
    for ca, no in sv_node_cats.items():
        for n in no:
            try:
                sv_cats_node[n[0]] = sv_node_colors[ca]
            except:
                sv_cats_node[n[0]] = False
    return sv_cats_node


def get_color(bl_id):
    global colors_cache
    if not colors_cache:
        colors_cache = sv_colors_definition()
    return colors_cache.get(bl_id)
