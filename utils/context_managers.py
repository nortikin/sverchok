from contextlib import contextmanager
import time

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

@contextmanager
def timed(func):
    """
    usage:
    
    from sverchok.utils.context_managers import timed

    ...

        with timed(your_func) as func:
            result = func(....)    
        ...

        >>> func_name: 29.987335205078125

    """

    from sverchok.utils.ascii_print import str_color

    start_time = time.time()
    
    yield func

    duration = (time.time() - start_time) * 1000
    
    func_name = str_color(func.__name__, 31)
    duration = str_color(f"{duration:.5g} ms", 32)
    func_name = func.__name__
    msg = f"{func_name}: {duration}"
    print(msg)

@contextmanager
def timepart(section_name=">"):
    """
    usage:
    
    from sverchok.utils.context_managers import timepart

    ...

        with timepart("section 1"):
            f = []
            for i in range(100_000):
                f.append(i*random())

        >>> section 1: 29.987335205078125

    """
    from sverchok.utils.ascii_print import str_color

    start_time = time.time()
    
    yield None

    duration = (time.time() - start_time) * 1000

    section_name = str_color(section_name, 31)
    duration = str_color(f"{duration:.5g} ms", 32)
    msg = f"{section_name}: {duration}"
    print(msg)
