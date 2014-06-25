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

# <pep8 compliant>
import math
import pprint
import re

import bpy
import blf
import bgl
from mathutils import Vector
from bpy.types import SpaceNodeEditor

from data_structure import Vector_generate, Matrix_generate

callback_dict = {}
point_dict = {}


def adjust_list(in_list, x, y):
    return [[old_x + x, old_y + y] for (old_x, old_y) in in_list]


def generate_points(width, height):
    amp = 5  # radius fillet

    width += 2
    height += 4
    width = ((width/2) - amp) + 2
    height -= (2*amp)

    pos_list, final_list = [], []

    n_points = 12
    seg_angle = 2 * math.pi / n_points
    for i in range(n_points + 1):
        angle = i * seg_angle
        x = math.cos(angle) * amp
        y = math.sin(angle) * amp
        pos_list.append([x, -y])

    w_list, h_list = [1, -1, -1, 1], [-1, -1, 1, 1]
    slice_list = [[i, i+4] for i in range(0, n_points, 3)]

    for idx, (start, end) in enumerate(slice_list):
        point_array = pos_list[start:end]
        w = width * w_list[idx]
        h = height * h_list[idx]
        final_list += adjust_list(point_array, w, h)

    return final_list


def get_points(index):
    '''
    index:   string representation of the index number
    returns: rounded rect point_list used for background.
    the neat thing about this is if a width has been calculated once, it
    is stored in a dict and used if another polygon is saught with that width.
    '''
    width, height = blf.dimensions(0, index)
    if not (width in point_dict):
        point_dict[width] = generate_points(width, height)

    return point_dict[width]


## end of util functions

def tag_redraw_all_nodeviews():
    context = bpy.context

    # Py cant access notifers
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()


def callback_enable(*args):
    n_id = args[0]

    global callback_dict
    if n_id in callback_dict:
        return

    handle_pixel = SpaceNodeEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')
    callback_dict[n_id] = handle_pixel
    tag_redraw_all_nodeviews()


def callback_disable(n_id):
    global callback_dict
    handle_pixel = callback_dict.get(n_id, None)
    if not handle_pixel:
        return
    SpaceNodeEditor.draw_handler_remove(handle_pixel, 'WINDOW')
    del callback_dict[n_id]
    tag_redraw_all_nodeviews()


def callback_disable_all():
    global callback_dict
    temp_list = list(callback_dict.keys())
    for n_id in temp_list:
        if n_id:
            callback_disable(n_id)


def draw_callback_px(n_id, data):

    context = bpy.context
    region = context.region
    rv2d = region.view2d

    content = data.get('content', 'no data')
    x, y = data.get('location', (120, 120))

    font_id = 0
    text_height = 13
    blf.size(font_id, text_height, 72)  # should check prefs.dpi

    # x = 30  # region.width
    # y = region.height - 40
    ypos = y
    str_width = 60

    def draw_text(content, rgb, ypos):
        ''' draw text '''
        txt_width, txt_height = blf.dimensions(0, content)
        bgl.glColor3f(*rgb)
        blf.position(0, x, ypos, 0)
        blf.draw(0, content)

    def print_section(content_array, ypos):

        # http://stackoverflow.com/a/7584567/1243487
        rounded_vals = re.compile(r"\d*\.\d+")
        def mround(match):
           return "{:.5f}".format(float(match.group()))

        for line in content_array:
            line_rounded = re.sub(rounded_vals, mround, line)
            draw_text(line_rounded, (0.02, 0.02, 0.02), ypos)
            ypos -= (text_height * 1.3)

    content_str = pprint.pformat(content, width=str_width)
    content_array = content_str.split('\n')

    if len(content_array) > 20:
        ''' first 10, ellipses, last 10 '''
        ellipses = ['... ... ...']
        head = content_array[0:10]
        tail = content_array[-10:]
        display_text = head + ellipses + tail

    elif len(content_array) == 1:
        ''' split on subunit - case of no newline to split on. '''
        content_array = content_array[0].replace("), (", "),\n (")
        display_text = content_array.split("\n")

    else:
        display_text = content_array

    print_section(display_text, ypos)
    