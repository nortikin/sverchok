import os
import sys

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

def str_color(text, color):
    """
    input:
    - text  : should be a string
    - color : must be any of https://github.com/nortikin/sverchok/pull/4511#issuecomment-1151478312
    output:
    - a str : the text is returned with additional color-markup if the terminal can display colors.
 
    available colors:
        30 = black, 31 = red, 32 = green, 33 = yellow, 34 = blue, 35 = purple, 36 = ilghtblue, 37 = white-ish
        90 = grey,  91 = red+,92 = green+,93 = yellow+,94 = blue+,95 = purple+,96 = lightblue+,97 = white
    
       """
    if color_terminal['displays_colors']:
        return f"\033[1;{color}m{text}\033[0m"
    return text


def logo():

    l1 = r" ______ _    _ _______  ______ _______ _     _  _____  _     _"
    l2 = r"/______  \  /  |______ |_____/ |       |_____| |     | |____/ "
    l3 = r"______/   \/   |______ |    \_ |_____  |     | |_____| |    \_"
    l4 = r"initialized."
    lines = [l1, l2, l3, l4]

    for line in lines: print(str_color(line, 31))

def show_welcome():
    is_terminal_color_capable()
    logo()
    # print("\nsv: version:", get_version_string())
