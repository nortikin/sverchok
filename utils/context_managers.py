from contextlib import contextmanager

import bpy
import sverchok


@contextmanager
def sv_preferences():
    '''
    use this whenever you need set or get content of the preferences class
    usage
        from sverchok.utils.context_managers import sv_preferences
        ...
        with sv_preferences() as prefs:
            print(prefs.<some attr>)
    '''
    # by using svercok.__name__ we increase likelihood that the addon preferences will correspond
    addon = bpy.context.preferences.addons.get(sverchok.__name__)
    if addon and hasattr(addon, "preferences"):
        yield addon.preferences

@contextmanager
def addon_preferences(addon_name):
    '''
    use this whenever you need set or get content of the preferences class
    usage
        from sverchok.utils.context_managers import addon_preferences
        ...
        with addon_preferences(addon_name) as prefs:
            print(prefs.<some attr>)

        addon_name sverchok passing sverchok.__name__
    '''
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        yield addon.preferences
