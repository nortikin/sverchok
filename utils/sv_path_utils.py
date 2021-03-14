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


def get_addons_path():
    script_paths = os.path.normpath(os.path.dirname(__file__))
    addons_path = os.path.split(os.path.dirname(script_paths))[0]
    return addons_path


def get_sverchok_path():
    script_paths = os.path.normpath(os.path.dirname(__file__))  # /path/to/sverchock/utils
    sverchok_path = os.path.dirname(script_paths)  # /path/to/sverchock
    return sverchok_path


def get_icons_path():
    icons_path = os.path.join(get_sverchok_path(), "ui", "icons")
    return icons_path


def get_fonts_path():
    fonts_path = os.path.join(get_sverchok_path(), "ui", "fonts")
    return fonts_path
