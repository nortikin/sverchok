# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

import bpy
import sverchok.core.events as ev
import sverchok.core.update_system as us
import sverchok.core.group_update_system as gus
import sverchok.core.concurrent_update_system as cus
import sverchok


update_systems = [us.control_center, gus.control_center]
concurrent_us = [cus.control_center]
is_parallel = None


def handle_event(event):
    """Main control center
    1. preprocess the event
    2. Pass the event to update system(s)"""
    # print(f"{event=}")

    # something changed in scene
    if type(event) is ev.SceneEvent:
        # this event was caused by update system itself and should be ignored
        if 'SKIP_UPDATE' in event.tree:
            del event.tree['SKIP_UPDATE']
            return

    was_handled = dict()
    for handler in concurrent_us if get_is_parallel() else update_systems:
        res = handler(event)
        was_handled[handler] = res

    if (results := sum(was_handled.values())) > 1:
        duplicates = [f.__module__ for f, r in was_handled if r == 1]
        raise RuntimeError(f"{event=} was executed more than one time, {duplicates=}")
    elif results == 0:
        raise RuntimeError(f"{event} was not handled")


def get_is_parallel():
    global is_parallel
    if is_parallel is None:
        sv_settings = bpy.context.preferences.addons[sverchok.__name__].preferences
        is_parallel = sv_settings.is_parallel
    return is_parallel
