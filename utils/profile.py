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

import cProfile
import pstats
from io import StringIO

import bpy

from sverchok.utils.logging import info
from sverchok.utils.context_managers import sv_preferences

# Global cProfile.Profile singleton
_global_profile = None
# Nesting level for @profile decorator
_profile_nesting = 0
# Whether the profiling is enabled by "Start profiling" toggle
is_currently_enabled = False

def get_global_profile():
    """
    Get cProfile.Profile singleton object
    """
    global _global_profile
    if _global_profile is None:
        _global_profile = cProfile.Profile()
    return _global_profile

def is_profiling_enabled(section):
    """
    Check if profiling is enabled in general,
    and if it is enabled for specified section.
    """
    global is_currently_enabled
    if not is_currently_enabled:
        return False
    with sv_preferences() as prefs:
        return prefs.profile_mode == section

def profile(function = None, section = "MANUAL"):
    """
    Decorator for profiling the specific methods.
    It can be used in two ways:

    @profile
    def method(...):
        ...

    or

    @profile(section="SECTION"):
    def method(...):
        ...

    The second form is equivalent to the first with section = "MANUAL".
    Profiling section is a named set of methods which should be profiled.
    Supported values of section are listed in SverchokPreferences.profiling_sections.
    The @profile(section) decorator does profile the method only if
    profiling for specified section is enabled in settings (profile_mode option),
    and profiling is currently active.
    """
    def profiling_decorator(func):
        def wrapper(*args, **kwargs):
            if is_profiling_enabled(section):
                global _profile_nesting

                profile = get_global_profile()
                _profile_nesting += 1
                if _profile_nesting == 1:
                    profile.enable()
                result = func(*args, **kwargs)
                _profile_nesting -= 1
                if _profile_nesting == 0:
                    profile.disable()
                return result
            else:
                return func(*args, **kwargs)
            
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    if callable(function):
        return profiling_decorator(function)
    else:
        return profiling_decorator

def dump_stats():
    """
    Dump profiling statistics to the log.
    """
    profile = get_global_profile()
    stream = StringIO()
    stats = pstats.Stats(profile, stream=stream).sort_stats('tottime')
    stats.print_stats()
    info("Profiling results:\n" + stream.getvalue())
    info("---------------------------")

class SvProfilingToggle(bpy.types.Operator):
    """Toggle profiling on/off"""
    bl_idname = "node.sverchok_profile_toggle"
    bl_label = "Toggle profiling"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        global is_currently_enabled

        is_currently_enabled = not is_currently_enabled
        info("Profiling is set to %s", is_currently_enabled)

        return {'FINISHED'}

class SvProfileDump(bpy.types.Operator):
    """Dump profiling statistics to log"""
    bl_idname = "node.sverchok_profile_dump"
    bl_label = "Dump profiling statistics"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        dump_stats()
        return {'FINISHED'}

classes = [SvProfilingToggle, SvProfileDump]

def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)

def unregister():
    for class_name in reversed(classes):
        bpy.utils.unregister_class(class_name)

