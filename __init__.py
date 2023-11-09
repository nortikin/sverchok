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
#     Alex (aka Satabol)
#
#  ***** END GPL LICENSE BLOCK *****
#
# -*- coding: utf-8 -*-

bl_info = {
    "name": "Sverchok",
    "author": "sverchok-b3d@ya.ru various authors see https://github.com/nortikin/sverchok/graphs/contributors",
    "version": (1, 2, 0),
    "blender": (3, 5, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Parametric node-based geometry programming",
    "warning": "",
    "wiki_url": "https://nortikin.github.io/sverchok/docs/main.html",
    "tracker_url": "http://www.blenderartists.org/forum/showthread.php?272679"
}

VERSION = 'v1.3.0-alpha'  # looks like the only way to have custom format for the version

reload_event = "import_sverchok" in locals()  # reloading does not clear previous module names


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

    import sverchok.core as core

    imported_modules_ = core.init_architecture()

    if "nodes" not in globals():  # magic
        raise core.interupted_activation_detected()

    if not reload_event:
        node_modules_ = core.import_nodes()
    else:
        node_modules_ = core.handle_reload_event(imported_modules_)

    return imported_modules_, node_modules_, core


imported_modules, node_modules, core = import_sverchok()


@profiling_startup("reg_stats")
def register():
    from sverchok.utils import ascii_print
    core.sv_register_modules(imported_modules)
    core.enable_logging()
    core.sv_register_modules(core.imported_utils_modules())
    core.sv_register_modules(node_modules)
    ascii_print.show_welcome()


def unregister():
    core.sv_unregister_modules(imported_modules)
    core.sv_unregister_modules(core.imported_utils_modules())
    core.sv_unregister_modules(node_modules)
    core.disable_logging()

# EOF
