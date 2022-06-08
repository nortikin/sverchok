# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import pprint
import bpy
last_print = {}

def console_print(node, message, kind='OUTPUT', allow_repeats=False, pprint=False, width=80):
    """
    this function finds an open console in Blender and writes to it, useful for debugging small stuff.
    but beware what you throw at it.

    "node"  can be a node, or any hasahable object. This is just to identify where the print comes from
    "message" can be text or data
    "kind" can be any of the accepted types known by scrollback_append operator.
    """
    
    if not allow_repeats:
        if (previously_printed_text := last_print.get(hash(node))):
            # i do not need to see repeat text
            if message == previously_printed_text: return

    if pprint:
        message = pprint.pformat(message, width=width, depth=5)


    last_print[hash(node)] = message

    AREA = 'CONSOLE'
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in window.screen.areas:
            if not area.type == AREA: continue

            for region in area.regions:
                if region.type == 'WINDOW': 
                    override = {'window': window, 'screen': screen, 'area': area, 'region': region}
                    if not "\n" in f"{message}":
                        bpy.ops.console.scrollback_append(override, text=f"{message}", type=kind)
                    else:
                        for line in f"{message}".split("\n"):
                            bpy.ops.console.scrollback_append(override, text=line, type=kind)
                    break        
