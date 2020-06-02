# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from collections import defaultdict
import blf


def get_sane_xy(data):
    return_value = (120, 120)
    location_function = data.get('location')
    if location_function:
        ng = bpy.data.node_groups.get(data['tree_name'])
        if ng:
            node = ng.get(data['node_name'])
            if node:
                return_value = location_function(node)

    return return_value



def draw_text_data(data):
    lines = data.get('content', 'no data')

    x, y = get_sane_xy(data)
    
    x, y = int(x), int(y)
    r, g, b = data.get('color', (0.1, 0.1, 0.1))
    font_id = data.get('font_id', 0)
    scale = data.get('scale', 1.0)
    
    text_height = 15 * scale
    line_height = 14 * scale

    blf.size(font_id, int(text_height), 72)
    blf.color(font_id, r, g, b, 1.0)
    ypos = y

    for line in lines:
        blf.position(0, x, ypos, 0)
        blf.draw(font_id, line)
        ypos -= int(line_height * 1.3)


def draw_graphical_data(data):
    lines = data.get('content')
    x, y = get_sane_xy(data)
    color = data.get('color', (0.1, 0.1, 0.1))
    font_id = data.get('font_id', 0)
    scale = data.get('scale', 1.0)
    text_height = 15 * scale

    if not lines:
        return

    blf.size(font_id, int(text_height), 72)
    
    def draw_text(color, xpos, ypos, line):
        r, g, b = color
        blf.color(font_id, r, g, b, 1.0) # bgl.glColor3f(*color)
        blf.position(0, xpos, ypos, 0)
        blf.draw(font_id, line)
        return blf.dimensions(font_id, line)

    lineheight = 20 * scale
    num_containers = len(lines)
    for idx, line in enumerate(lines):
        y_pos = y - (idx*lineheight)
        gfx_x = x

        num_items = str(len(line))
        kind_of_item = type(line).__name__

        tx, _ = draw_text(color, gfx_x, y_pos, f"{kind_of_item} of {num_items} items")
        gfx_x += (tx + 5)
        
        content_dict = defaultdict(int)
        for item in line:
            content_dict[type(item).__name__] += 1

        tx, _ = draw_text(color, gfx_x, y_pos, str(dict(content_dict)))
        gfx_x += (tx + 5)

        if idx == 19 and num_containers > 20:
            y_pos = y - ((idx+1)*lineheight)
            text_body = f"Showing the first 20 of {num_containers} items"
            draw_text(color, x, y_pos, text_body)
            break
