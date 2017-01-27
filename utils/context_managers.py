import bpy
from sverchok.data_structure import SVERCHOK_NAME as addon_name

import bpy
from sverchok.data_structure import SVERCHOK_NAME as addon_name
from contextlib import contextmanager


@contextmanager
def hard_freeze(self):
    '''
    Use this when you don't want modifications to node properties 
    to trigger the node's `process()` function. 

    usage  (when self is a reference to a node)

        from sverchok.utils.context_managers import hard_freeze

        ...
        ...

        with hard_freeze(self) as node:
            node.some_prop = 'some_value_change'
            node.some_other_prop = 'some_other_value_change'

    '''
    self.id_data.freeze(hard=True)
    yield self
    self.id_data.unfreeze(hard=True)

@contextmanager
def sv_preferences():
    '''
    use this whenever you need set or get content of the user_preferences class
    usage
        from sverchok.utils.context_managers import sv_preferences
        ...
        with sv_preferences() as prefs:
            print(prefs.<some attr>)
    '''
    addon = bpy.context.user_preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        yield addon.preferences
