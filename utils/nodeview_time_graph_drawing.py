# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


# import bgl
import blf
import bpy
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader

import sverchok
from sverchok.ui import bgl_callback_nodeview as nvBGL2
from sverchok.utils.modules.shader_utils import ShaderLib2D


# https://github.com/nortikin/sverchok/commit/c0ef777acef561a5e9cd308ec05c1382b9006de8


display_dict = {} # 'sverchok': None}

def get_drawing_state(ng):
    if not ng.tree_id_memory:
        # because this function is called inside sv_panels, it happens early on in the life
        # of a new tree, it does not yet have a tree_id. We are not allowed to write to ng.tree_id
        # from inside a draw function of sv_panels. (a sane bpy limitation!)
        return
    return display_dict.get(ng.tree_id)

def set_drawing_state(ng, state=False):
    display_dict[ng.tree_id] = state

def set_other_trees_to_false(ng):
    for key in list(display_dict.keys()):
        if ng.tree_id == key: continue
        display_dict[key] = False

timer_config = lambda: None
timer_config.get_drawing_state = get_drawing_state
timer_config.set_drawing_state = set_drawing_state
timer_config.set_other_trees_to_false = set_other_trees_to_false

def tick_display(i, whole_milliseconds):
    if whole_milliseconds < 10:
        return True

    filter = 2
    for j in range(10, whole_milliseconds + 10, 5):
        if j <= whole_milliseconds < j+5:
            return i % filter == 0
        filter += 1

def string_from_duration(duration):
    return f"{(1000*duration):.3f} ms"

def get_preferences():
    from sverchok.settings import get_dpi_factor
    return get_dpi_factor()

def get_time_graph(): # tree_name):
    # m = sverchok.core.update_system.graph_dicts.get(tree_name)
    # return {idx: event for idx, event in enumerate(m)} if m else {}
    m = sverchok.core.update_system.graphs
    if len(m) == 1:
        return {idx: event for idx, event in enumerate(m[0])}
    else:
        cumulative_dict = {}
        counter = 0
        for graph in m:
            for event in graph:
                cumulative_dict[counter] = event
                counter += 1
        return cumulative_dict

def draw_text(font_id, location, text, color):

    x, y = location
    r, g, b = color
    blf.position(font_id, x, y, 0)
    level = 5 # 3, 5 or 0

    blf.color(font_id, r, g, b, 1.0)
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, level, 0, 0, 0, 1)
    blf.shadow_offset(font_id, 1, -1)
    blf.draw(font_id, text)
    blf.disable(font_id, blf.SHADOW)

def draw_node_time_infos(*data):

    location_theta = data[1]
    tree_name = data[2]
    data_tree = get_time_graph() # tree_name)
    node_tree = bpy.data.node_groups.get(tree_name)

    if not node_tree.sv_show_time_nodes:
        return

    r, g, b = (0.9, 0.9, 0.9)
    index_color = (0.98, 0.6, 0.6)
    font_id = 0
    text_height = 20

    def get_xy_for_bgl_drawing(node):
        _x, _y = node.absolute_location
        _x, _y = _x, _y + (text_height - 9)
        return _x * location_theta, _y * location_theta

    blf.size(font_id, int(text_height), 72)
    blf.color(font_id, r, g, b, 1.0)
    for idx, node_data in data_tree.items():
        node = node_tree.nodes.get(node_data['name'])
        if not node: continue
        if not tree_name == node_data['tree_name']: continue

        x, y = get_xy_for_bgl_drawing(node)
        x, y = int(x), int(y)

        if node.hide and isinstance(node.dimensions, Vector):
            # just in case we are still overriding node.dimensions anywhere.
            # this is not exact, but it's better than the alternative
            y += (node.dimensions[1] / 2) - 10

        show_str = string_from_duration(node_data['duration'])
        draw_text(font_id, (x, y), show_str, (r, g, b))

        process_index = str(idx)
        index_width, _ = blf.dimensions(font_id, process_index)
        padding = 9
        draw_text(font_id, (x - padding - index_width, y), process_index, index_color)

def draw_overlay(*data):

    # bpy.context.area.height  & area.width  = total
    region = bpy.context.region

    # visible width ( T panel is not included, only N panel)
    region_width = region.width

    shader = data[1]
    tree_name = data[2]
    data_tree = get_time_graph() # tree_name)
    node_tree = bpy.data.node_groups.get(tree_name)

    r, g, b = (0.9, 0.9, 0.95)
    font_id = 0
    text_height = 10
    line_height = 10 + 3

    blf.size(font_id, int(text_height), 72)
    blf.color(font_id, r, g, b, 1.0)

    if not node_tree.sv_show_time_graph:
        # in this case only draw the total time and return early
        cumsum = 0.0
        for idx, node_data in data_tree.items():
            node = node_tree.nodes.get(node_data['name'])
            if not node: continue
            if not tree_name == node_data['tree_name']: continue
            cumsum += node_data['duration']

        y = 26
        cum_duration = string_from_duration(cumsum)
        draw_text(font_id, (20, y), f"total: {cum_duration}", (r, g, b))
        return

    white = (1.0, 1.0, 1.0, 1.0)
    left_offset = 140
    right_padding = 50
    time_domain_px = region_width - left_offset - right_padding

    x, y = 20, 50
    cumsum = 0.0
    used_idx = 0
    display_info = {}

    for idx in sorted(data_tree, key=lambda value: data_tree.get(value).get("start")):
        node_data = data_tree.get(idx)
        node = node_tree.nodes.get(node_data['name'])

        if not node: continue
        if not tree_name == node_data['tree_name']: continue

        cumsum += node_data['duration']
        txt_width, txt_height = blf.dimensions(font_id, node_data['name'])
        display_info[used_idx] = (x, y, node_data, txt_width)
        y += line_height
        used_idx += 1

    if cumsum == 0.0:
        return

    y = 26
    cum_duration = string_from_duration(cumsum)
    draw_text(font_id, (20, y), f"total: {cum_duration}", (r, g, b))

    px_per_ms = time_domain_px / cumsum

    canvas = ShaderLib2D()
    bar_start_offset = 0
    orange = (0.8, 0.3, 0.2, 1.0)
    darker = (0.4, 0.4, 0.4, 1.0)
    offwhite = (0.1, 0.5, 0.6, 1.0)
    starts = {}
    for key, value in display_info.items():
        (x, y, node_data, txt_width) = value
        bar_width = px_per_ms * node_data['duration']
        canvas.add_rect(left_offset + bar_start_offset, y+10, bar_width, 13, offwhite)
        starts[key] = left_offset + bar_start_offset
        bar_start_offset += bar_width

    # draw time axis
    canvas.add_rect(left_offset, 40, time_domain_px, 1, white)

    # draw time ticks
    milliseconds = cumsum * 1000
    whole_milliseconds = int(milliseconds)
    graph_height = line_height * len(display_info)
    for i in range(whole_milliseconds + 1):
        tick_location = px_per_ms * i/1000
        final_tick_x = left_offset + tick_location

        # this is where we skip ticks if they get too dense.
        if tick_display(i, whole_milliseconds):
            canvas.add_rect(final_tick_x, 42, 1, 5, white)
            canvas.add_rect(final_tick_x, 42, 1, -graph_height, darker)

            time_width, _ = blf.dimensions(font_id, str(i))
            time_str_offset = final_tick_x - (time_width/2)
            draw_text(font_id, (time_str_offset, 26), str(i), (r, g, b))

    geom = canvas.compile()

    batch = batch_for_shader(shader, 'TRIS',
        {"pos": geom.vectors,
        "color": geom.vertex_colors},
        indices=geom.indices
    )
    batch.draw(shader)

    for key, value in display_info.items():
        (x, y, node_data, text_width) = value
        x_right_aligned = left_offset - 10 - text_width
        draw_text(font_id, (x_right_aligned, y), node_data['name'], (r, g, b))
        xpos = starts[key]
        duration_as_str = string_from_duration(node_data['duration'])
        draw_text(font_id, (xpos + 3, y), duration_as_str, (r, g, b))

def start_node_times(ng):
    named_tree = ng.name
    data_time_infos = (None, get_preferences(), named_tree)

    config_node_info = {
        'tree_name': named_tree,
        'mode': 'LEAN_AND_MEAN',
        'custom_function': draw_node_time_infos,
        'args': data_time_infos
    }
    nvBGL2.callback_enable(f"{ng.tree_id}_node_time_info", config_node_info)

def start_time_graph(ng):
    if not ng:
        return
    ng.update_gl_scale_info(origin=f"configure_time_graph, tree: {ng.name}")

    named_tree = ng.name
    shader_name = f'{"2D_" if bpy.app.version < (3, 4) else ""}SMOOTH_COLOR'
    shader = gpu.shader.from_builtin(shader_name)
    data_overlay = (None, shader, named_tree)

    config_graph_overlay = {
        'tree_name': named_tree,
        'mode': 'LEAN_AND_MEAN',
        'custom_function': draw_overlay,
        'args': data_overlay
    }
    nvBGL2.callback_enable(f"{ng.tree_id}_time_graph_overlay", config_graph_overlay, overlay="POST_PIXEL")
