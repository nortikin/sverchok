import os
import sys
from sverchok.utils.development import get_version_string

# pylint: disable=c0304
# pylint: disable=c0326
# pylint: disable=w1401

color_terminal = {'displays_colors': False}

def is_terminal_color_capable():
    can_paint = os.name in {'posix'}
    try:
        if hasattr(sys, 'getwindowsversion'):
            if sys.getwindowsversion().major == 10:
                can_paint = True
    except:
        ...

    color_terminal['displays_colors'] = can_paint

def logo():

    l1 = r" ______ _    _ _______  ______ _______ _     _  _____  _     _"
    l2 = r"/______  \  /  |______ |_____/ |       |_____| |     | |____/ "
    l3 = r"______/   \/   |______ |    \_ |_____  |     | |_____| |    \_"
    l4 = r"initialized."
    lines = [l1, l2, l3, l4]

    with_color = "\033[1;31m{0}\033[0m" if color_terminal['displays_colors'] else "{0}"
    for line in lines:
        print(with_color.format(line))

def show_welcome():
    is_terminal_color_capable()
    logo()
    print("\nsv: version:", get_version_string())
