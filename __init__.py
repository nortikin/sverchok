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
#     Victor Doval (aka vicdoval)
#
#  ***** END GPL LICENSE BLOCK *****
#
# -*- coding: utf-8 -*-

bl_info = {
    "name": "Sverchok",
    "author": "sverchok-b3d@ya.ru various authors see https://github.com/nortikin/sverchok/graphs/contributors",
    "version": (1, 2, 0),
    "blender": (2, 93, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Parametric node-based geometry programming",
    "warning": "",
    "wiki_url": "https://nortikin.github.io/sverchok/docs/main.html",
    "tracker_url": "http://www.blenderartists.org/forum/showthread.php?272679"
}

VERSION = 'v1.2.0-alpha'  # looks like the only way to have custom format for the version

reload_event = "bpy" in locals()
import bpy  # to detect reload event

# pylint: disable=E0602
# pylint: disable=C0413
# pylint: disable=C0412


def profiling_startup(file_name):
    """Start blender with `blender -- --sv-profile` to create two
    files with profiling of Sverchok startup. "imp_stats" file keeps stats of
    importing modules and "reg_stats" keeps stats of add-on registration."""
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrap():
            import cProfile
            import pstats
            profile = cProfile.Profile()
            profile.enable()
            res = func()
            profile.disable()
            stats = pstats.Stats(profile)
            stats.dump_stats(file_name)
            return res

        import sys
        return wrap if "--sv-profile" in sys.argv else func
    return decorator


@profiling_startup("imp_stats")
def import_sverchok():
    import sys

    # make sverchok the root module name, (if sverchok dir not named exactly "sverchok")
    if __name__ != "sverchok":
        sys.modules["sverchok"] = sys.modules[__name__]

    from sverchok.core import init_architecture, make_node_list
    from sverchok.core import interupted_activation_detected, handle_reload_event
    from sverchok.utils import utils_modules
    from sverchok.ui import ui_modules

    imported_modules_ = init_architecture(__name__, utils_modules, ui_modules)

    if "nodes" not in globals():  # magic
        raise interupted_activation_detected()

    if reload_event:
        node_list_ = handle_reload_event(nodes, imported_modules_)
    else:
        node_list_ = make_node_list(nodes)

    return imported_modules_, node_list_


imported_modules, node_list = import_sverchok()


@profiling_startup("reg_stats")
def register():
    from sverchok.core import sv_register_modules
    import sverchok
    sv_register_modules(imported_modules + node_list)
    sverchok.core.init_bookkeeping(__name__)

    if reload_event:
        from sverchok import data_structure
        data_structure.RELOAD_EVENT = True


def unregister():
    import sverchok
    from sverchok.core import sv_unregister_modules

    sverchok.utils.clear_node_classes()
    sv_unregister_modules(imported_modules)
    sv_unregister_modules(node_list)

# EOF
