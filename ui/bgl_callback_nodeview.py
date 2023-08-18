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

from __future__ import annotations  # this will fix backward compatibility with Python 3.8 and less

from inspect import isfunction

import bpy
import blf
from bpy.types import SpaceNodeEditor

from sverchok.utils.sv_stethoscope_helper import draw_text_data, draw_graphical_data
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.modules.drawing_abstractions import drawing 

callback_dict = {}
point_dict = {}


def tag_redraw_all_nodeviews():

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()
   

def callback_enable(*args, overlay='POST_VIEW'):
    n_id = args[0]
    # global callback_dict
    if n_id in callback_dict:
        return

    handle_pixel = SpaceNodeEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', overlay)
    callback_dict[n_id] = handle_pixel
    tag_redraw_all_nodeviews()


def draw_text(node, text: str, draw_id=None, color=(1, 1, 1, 1), scale=1., align="RIGHT", dynamic_location=True):
    """Draw any text nearby a node, use together with callback_disable
    align = {"RIGHT", "UP", "DOWN"} todo replace with typing.Literal"""
    draw_id = draw_id or node.node_id
    if draw_id in callback_dict:
        callback_disable(draw_id)

    color = color if len(color) == 4 else (*color, 1)
    text_location = None if dynamic_location else _get_text_location(node, align)
    handle_pixel = SpaceNodeEditor.draw_handler_add(
        _draw_text_handler,
        (node.id_data.tree_id, node.node_id, text, color, scale, align, text_location),
        'WINDOW',
        'POST_VIEW')
    callback_dict[draw_id] = handle_pixel
    tag_redraw_all_nodeviews()


def callback_disable(n_id):
    # global callback_dict
    handle_pixel = callback_dict.get(n_id, None)
    if not handle_pixel:
        return
    SpaceNodeEditor.draw_handler_remove(handle_pixel, 'WINDOW')
    del callback_dict[n_id]
    tag_redraw_all_nodeviews()


def callback_disable_all():
    # global callback_dict
    temp_list = list(callback_dict.keys())
    for n_id in temp_list:
        if n_id:
            callback_disable(n_id)

def callback_disable_filtered(pattern):
    temp_list = list(callback_dict.keys())
    for ident in temp_list:
        if ident.endswith(pattern):
            callback_disable(ident)


def restore_opengl_defaults():
    drawing.set_line_width(1)
    drawing.disable_blendmode()


def get_xy_from_data(data):
    location = data.get('loc')
    if isfunction(location):
        x, y = get_sane_xy(data)
    elif isinstance(location, (tuple, list)):
        x, y = location
    else:
        x, y = 20, 20
    return x, y


def get_sane_xy(data):
    return_value = (120, 120)
    location_function = data.get('loc')
    if location_function:
        ng = bpy.data.node_groups.get(data['tree_name'])
        if ng:
            node = ng.nodes.get(data['node_name'])
            if node:
                return_value = location_function(node)

    return return_value    


def draw_callback_px(n_id, data):

    space = bpy.context.space_data
    ng_view = space.edit_tree

    # ng_view can be None
    if not ng_view:
        return

    ng_name = space.edit_tree.name

    if not (data['tree_name'] == ng_name):
        return
 
    if not ng_view.bl_idname in {"SverchCustomTreeType", 'SvGroupTree'}:
        return

    if data.get('mode', 'text-based') == 'text-based':
        draw_text_data(data)
    elif data.get('mode') == "graphical":
        draw_graphical_data(data)
        restore_opengl_defaults()
    elif data.get('mode') == 'custom_function':
        drawing_func = data.get('custom_function')

        x, y = get_xy_from_data(data)
        args = data.get('args', (None,))
        
        drawing_func(x, y, args)
        restore_opengl_defaults()
    elif data.get('mode') == 'LEAN_AND_MEAN':
        drawing_func = data.get('custom_function')
        args = data.get('args', (None,))
        drawing_func(*args)
        restore_opengl_defaults()
    elif data.get('mode') == 'custom_function_context':
        
        '''
        0) this mode is useful for custom shader inside 2d drawing context, like nodeview
        1) you will supply this function with args, and args will contain (geom, config) 
        2) your passing function might look something like

            config = lambda: None
            config.shader_data = ...

            geom = lambda: None
            geom.stuff = ..

            draw_data = {
                'loc': function_returning_xy,
                'mode': 'custom_function_context',
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],
                'custom_function': advanced_grid_xy,
                'args': (geom, config)
            }

            nvBGL.callback_enable(self.n_id, draw_data)

        '''
        x, y = get_xy_from_data(data)

        drawing_func = data.get('custom_function')
        args = data.get('args', (None,))
        drawing_func(bpy.context, args, (x, y))
        restore_opengl_defaults()


def _draw_text_handler(tree_id, node_id, text: str, color=(1, 1, 1, 1), scale=1.0, align='RIGHT',
                       text_coordinates=None):
    """Draw the text in a node tree editor nearby the given node"""
    editor = bpy.context.space_data

    if editor.type != 'NODE_EDITOR':
        return

    if editor.tree_type not in {"SverchCustomTreeType", 'SvGroupTree'}:
        return

    if not editor.edit_tree or editor.edit_tree.tree_id != tree_id:
        return

    # this is less efficient because it requires search of the node each redraw call
    if not text_coordinates:
        if not any(n for n in editor.edit_tree.nodes if n.node_id == node_id):
            sv_logger.debug(f'Some node looks like was removed without removing bgl drawing, text: {text}')
            return

        # find node location
        node = next(n for n in editor.edit_tree.nodes if n.node_id == node_id)
        (x, y), z = _get_text_location(node, align), 0

    # put static coordinates if there are a lot of nodes with text to draw (does not react on the node movements)
    else:
        (x, y), z = text_coordinates, 0

    # https://github.com/nortikin/sverchok/issues/4247
    ui_scale = bpy.context.preferences.system.ui_scale
    x, y = x * ui_scale, y * ui_scale

    # todo add scale from the preferences
    text_height = int(15 * scale * ui_scale)
    line_height = int(18 * scale * ui_scale)
    font_id = 0
    dpi = 72

    drawing.blf_size(font_id, text_height, dpi)
    blf.color(font_id, *color)

    for line in text.split('\n'):
        blf.position(font_id, x, y, z)
        blf.draw(font_id, line)
        y -= line_height


def _get_text_location(node, align='RIGHT') -> tuple[int, int]:
    """Find location for a text nearby given node"""
    (x, y) = node.absolute_location
    gap = 10

    # some nodes override standard attributes
    try:
        dx, dy = node.dimensions
    except (TypeError, ValueError):
        dx, dy = 1, 1  # todo would be nice to have something more sensible here

    # find text location
    if align == "RIGHT":
        x, y = int(x + dx + gap), int(y)
    elif align == "UP":
        if node.hide:  # when the node is hidden its location moves slightly upper
            max_sock_num = max(len([s for s in node.inputs if not s.hide]),
                               len([s for s in node.outputs if not s.hide]))
            gap += (max_sock_num * 0.3) * max_sock_num
        x, y = int(x), int(y + gap)
    elif align == "DOWN":
        x, y = int(x), int(y - dy - gap)
    else:
        sv_logger.debug(f'Some node drawing text with unsupported align: {align}')
    return x, y


def unregister():
    callback_disable_all()
