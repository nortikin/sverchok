# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from gpu_extras.batch import batch_for_shader
from sverchok.utils.modules.drawing_abstractions import drawing

def draw_edges(shader, points, edges, line_width, color, is_smooth=False):
    if is_smooth:
        draw_edges_colored(shader, points, edges, line_width, [color for _ in range(len(points))])
    else:
        drawing.set_line_width(line_width)
        batch = batch_for_shader(shader, 'LINES', {"pos": points}, indices=edges)
        shader.bind()
        shader.uniform_float('color', color)
        batch.draw(shader)
        drawing.reset_line_width()

def draw_arrows(shader, tips, pts1, pts2, line_width, color):
    n = len(tips)
    points = np.concatenate((tips, pts1, pts2))
    edges = [(i, i+n) for i in range(n-1)]
    edges.extend([(i, i+2*n) for i in range(n-1)])
    drawing.set_line_width(line_width)
    batch = batch_for_shader(shader, 'LINES', {"pos": points.tolist()}, indices=edges)
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    drawing.reset_line_width()

def draw_edges_colored(shader, points, edges, line_width, colors):
    drawing.set_line_width(line_width)
    batch = batch_for_shader(shader, 'LINES', {"pos": points, "color": colors}, indices=edges)
    shader.bind()
    batch.draw(shader)
    drawing.reset_line_width()

def draw_points(shader, points, size, color):
    drawing.set_point_size(size)
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    drawing.reset_point_size()

def draw_points_colored(shader, points, size, colors):
    drawing.set_point_size(size)
    batch = batch_for_shader(shader, 'POINTS', {"pos": points, "color": colors})
    shader.bind()
    batch.draw(shader)
    drawing.reset_point_size()

def draw_polygons(shader, points, tris, vertex_colors):
    batch = batch_for_shader(shader, 'TRIS', {"pos": points, 'color': vertex_colors}, indices=tris)
    shader.bind()
    batch.draw(shader)

