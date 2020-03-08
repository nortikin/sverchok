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
from sverchok.ui import bgl_callback_nodeview as nvBGL2
from sverchok.settings import get_params


def exception_nodetree_id(ng):
    """ only one node per ng will have an exception """
    return str(hash(ng) ^ hash(time.monotonic())) + "_exception"


def get_preferences():
    """ obtain the dpi adjusted xy and scale factors """
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
    return x, y


def xyoffset(node):
    """ what is the location, offset to draw to """
    a = node.location[:]
    b = int(node.width) + 20
    return int(a[0] + b), int(a[1])


def clear_exception_drawing_with_bgl(ng):
    """ remove the previously drawn exception if needed """
    ng_id = exception_nodetree_id(ng)
    nvBGL2.callback_disable(ng_id)


def start_exception_drawing_with_bgl(ng, node_name, err):
    """ start drawing the exception data beside the node """
    node = ng.nodes[node_name]
    text = lambda: None
    text.body = err
    config = lambda: None
    config.loc = adjust_position_and_dimensions(node, xyoffset(node))

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
    ...