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
from os.path import dirname, basename, join
from pathlib import Path
import textwrap

import bpy

def message_on_layout(layout, text, width=140, **kwargs):
    box = layout.box()
    lines = textwrap.wrap(text, width=width, **kwargs)
    for line in lines:
        box.label(text=line)
    return box

def enum_split(layout, node, prop_name, label, factor):
    enum_row = layout.split(factor=factor, align=False)
    enum_row.label(text=label)
    enum_row.prop(node, prop_name, text="")

MENU_TYPE_DEFAULT = '__DEFAULT__'
MENU_TYPE_SVERCHOK = '__SVERCHOK__'
MENU_TYPE_USER = '__USER__'

datafiles = join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))

def get_sverchok_menu_presets_directory():
    return Path(__file__).parents[1] / 'menus'

def get_user_menu_presets_directory():
    return join(datafiles, 'menus')

def get_menu_preset_path(preset_path):
    preset_type, preset_name = preset_path.split(os.sep)
    if preset_type == MENU_TYPE_DEFAULT:
        directory = Path(__file__).parents[1]
    elif preset_type == MENU_TYPE_SVERCHOK:
        directory = get_sverchok_menu_presets_directory()
    else: # MENU_TYPE_USER
        directory = get_user_menu_presets_directory()
    preset_path = join(directory, preset_name)
    return preset_path

