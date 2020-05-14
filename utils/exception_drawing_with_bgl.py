# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103
# pylint: disable=w0612
# pylint: disable=w0613

import time

import blf
import gpu
from gpu_extras.batch import batch_for_shader

import sverchok
from sverchok.ui import bgl_callback_nodeview as nvBGL2

def exception_nodetree_id(ng):
    """ only one node per ng will have an exception """
    return str(hash(ng)) + "_exception"


def get_preferences():
    """ obtain the dpi adjusted xy and scale factors """
    from sverchok.settings import get_params
    props = get_params({
        'render_scale': 1.0,
        'render_location_xy_multiplier': 1.0})
    return props.render_scale, props.render_location_xy_multiplier


def adjust_position_and_dimensions(node, loc):
    """ further adjustement is needed, not done yet in the code below Frames, nested 
        node param is used for this.
    """
    x, y = loc
    scale, multiplier = get_preferences()
    x, y = [x * multiplier, y * multiplier]
    # maybe we do something independant of scale.
    return x, y, scale


def xyoffset(node):
    """ what is the location, offset to draw to """
    a = node.absolute_location
    b = int(node.width) + 20
    return int(a[0] + b), int(a[1])


def clear_exception_drawing_with_bgl(nodes):
    """ remove the previously drawn exception if needed """
    ng = nodes.id_data
    ng_id = exception_nodetree_id(ng)
    nvBGL2.callback_disable(ng_id)


def start_exception_drawing_with_bgl(ng, node_name, error_text, err):
    """ start drawing the exception data beside the node """
    node = ng.nodes[node_name]
    config = lambda: None
    text = lambda: None
    text.final_error_message = str(err)
    
    if "\n" in error_text:
        text.body = error_text.splitlines()
    else:
        text.body = error_text

    x, y, scale = adjust_position_and_dimensions(node, xyoffset(node))
    config.loc = x, y
    config.scale = scale
    config.mode = "MOD 1" # "ORIGINAL"
    config.font_id = 0

    if config.mode == "MOD 1":

        final_error_dimensions = blf.dimensions(config.font_id, text.final_error_message)
        w, h = final_error_dimensions[0] * scale, final_error_dimensions[1] * scale * 2

        abs_x, abs_y = node.absolute_location
        ex, ey = abs_x + 0, abs_y + h
        """
        0        1          0 = (ex,     ey    )  
                            1 = (ex + w, ey    )
        2        3          2 = (ex,     ey - h)
                            3 = (ex + w, ey - h)
        """
        vertices = ((ex, ey), (ex + w, ey), (ex, ey - h), (ex + w, ey - h))
        indices = ((0, 1, 2), (2, 1, 3))

        config.text_error_only_location = abs_x, abs_y
        config.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        config.batch = batch_for_shader(config.shader, 'TRIS', {"pos": vertices}, indices=indices)


    ng_id = exception_nodetree_id(ng)
    draw_data = {
        'tree_name': ng.name[:],
        'mode': 'custom_function_context', 
        'custom_function': simple_exception_display,
        'args': (text, config)
    }
    nvBGL2.callback_enable(ng_id, draw_data)

def simple_exception_display(context, args):
    """
    a simple bgl/blf exception showing tool for nodeview
    """
    text, config = args
    font_id = config.font_id

    RED = 0.911393, 0.090249, 0.257536, 1.0
    x, y = config.loc
    x, y = int(x), int(y)
    r, g, b = (1.0, 1.0, 1.0)
    font_id = 0
    scale = config.scale * 1.5
    
    text_height = 15 * scale
    line_height = 14 * scale

    blf.size(font_id, int(text_height), 72)
    blf.color(font_id, r, g, b, 1.0)
    ypos = y

    if config.mode == "ORIGINAL":

        if isinstance(text.body, list):
            for line in text.body:
                blf.position(0, x, ypos, 0)
                blf.draw(font_id, line)
                ypos -= int(line_height * 1.3)
        
        elif isinstance(text.body, str):
            blf.position(0, x, ypos, 0)
            blf.draw(font_id, text.body)
            ypos -= int(line_height * 1.3)

        blf.color(font_id, *RED)
        blf.position(0, x, ypos, 0)
        blf.draw(font_id, text.final_error_message)
    
    elif config.mode == "MOD 1":

        config.shader.bind()
        config.shader.uniform_float("color", (0, 0.1, 0.1, 1.0))
        config.batch.draw(config.shader)
        ex, ey = config.text_error_only_location
        blf.color(font_id, *RED)
        blf.position(0, ex, ey, 0)
        blf.draw(font_id, text.final_error_message)        
