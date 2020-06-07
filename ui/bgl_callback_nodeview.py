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

from inspect import isfunction

import bpy
import blf
import bgl
from bpy.types import SpaceNodeEditor

from sverchok.utils.sv_stethoscope_helper import draw_text_data, draw_graphical_data


callback_dict = {}
point_dict = {}


def tag_redraw_all_nodeviews():

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()
   

def callback_enable(*args):
    n_id = args[0]
    # global callback_dict
    if n_id in callback_dict:
        return

    handle_pixel = SpaceNodeEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')
    callback_dict[n_id] = handle_pixel
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





def restore_opengl_defaults():
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    # bgl.glColor4f(0.0, 0.0, 0.0, 1.0)     # doesn't exist anymore ..    


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
 
    if not ng_view.bl_idname in {"SverchCustomTreeType"}:
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

        bgl.glEnable(bgl.GL_DEPTH_TEST)
        drawing_func = data.get('custom_function')
        args = data.get('args', (None,))
        drawing_func(bpy.context, args, (x, y))
        restore_opengl_defaults()
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        
        
def unregister():
    callback_disable_all()
