import time
from contextlib import contextmanager

import bpy
import sverchok
from sverchok.utils.logging import info
from sverchok.utils.ascii_print import str_color


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

@contextmanager
def timed(func):
    start_time = time.time()
    
    #result = func(*args, **kwargs)
    yield func
    
    duration = (time.time() - start_time) * 1000

    func_name = str_color(func.__name__, 31)
    duration = str_color(f"{duration:.5g} ms", 32)
        
    msg = f"\n{func_name}: {duration}" # + display_args + display_kwargs
    info(msg)