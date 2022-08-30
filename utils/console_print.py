# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import pprint
import bpy
import re
import numpy as np

last_print = {}

def console_print(message, node=None, kind='OUTPUT', allow_repeats=True, pretty=False, width=80, rounding=0, compact=True, print_origin=False):
    """
    this function finds an open console in Blender and writes to it, useful for debugging small stuff.
    but beware what you throw at it.

    "node"  can be a node, or any hasahable object. This is just to identify where the print comes from
    "message" can be text or data
    "kind" can be any of the accepted types known by scrollback_append operator.
    """
    if node is None:
        node = "generic"
    
    if not allow_repeats:
        
        previously_printed_text = last_print.get(hash(node))
        
        # or  (np.ndarray, np.generic)
        if previously_printed_text is None: pass
        elif all([isinstance(obj, np.ndarray) for obj in [previously_printed_text, message]]):
            if np.array_equal(previously_printed_text, message): return
        else:  
            if message == previously_printed_text: return

    if compact:
        # first ten + ... + last ten
        pass

    if pretty:
        message = pprint.pformat(message, width=width, depth=5, compact=compact)

        if rounding > 0:
            rounded_vals = re.compile(r"\d*\.\d+")

            def mround(match): return f"{float(match.group()):.{rounding}g}"

            out = []
            for line in message.split("\n"):
                passthru = ("bpy." in line)
                out.append(line if passthru else re.sub(rounded_vals, mround, line))
            message = "\n".join(out)


    last_print[hash(node)] = message


    AREA = 'CONSOLE'
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in window.screen.areas:
            if not area.type == AREA: continue

            for region in area.regions:
                if region.type == 'WINDOW': 
                    override = {'window': window, 'screen': screen, 'area': area, 'region': region}
                    
                    if print_origin:
                        bpy.ops.console.scrollback_append(override, text=f"{node}", type=kind)

                    if not "\n" in f"{message}":
                        bpy.ops.console.scrollback_append(override, text=f"{message}", type=kind)
                    else:
                        for line in f"{message}".split("\n"):
                            bpy.ops.console.scrollback_append(override, text=line, type=kind)
                    break        
