# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector
from sverchok.utils.logging import info, error

if bpy.app.background:
    print("Will not initialize shaders in the background mode")

    class MatrixDraw28(object):
        def draw_matrix(self, *args, **kwargs):
            info("draw_matrix: do nothing in background mode")

else:

    uniform_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    smooth_shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')


    class MatrixDraw28(object):

        def __init__(self):
            self.zero = Vector((0.0, 0.0, 0.0))
            self.x_p = Vector((0.5, 0.0, 0.0))
            self.x_n = Vector((-0.5, 0.0, 0.0))
            self.y_p = Vector((0.0, 0.5, 0.0))
            self.y_n = Vector((0.0, -0.5, 0.0))
            self.z_p = Vector((0.0, 0.0, 0.5))
            self.z_n = Vector((0.0, 0.0, -0.5))
            self.bb = [Vector() for i in range(24)]
            self.mat = Matrix()

        def draw_matrix(self, mat, bbcol=(1.0, 1.0, 1.0, 1.0), skip=False, grid=True, scale=1): # , show_plate=False):
            """.."""
            if not isinstance(mat, Matrix):
                mat = Matrix(mat)
            self.mat = mat

            self.draw_axis(skip, scale)
            if grid:
                self.draw_grid(bbcol, scale)

        def draw_axis(self, skip, scale):
            """.."""
            zero_tx = self.mat @ self.zero

            axis = [
                [(1.0, 0.2, 0.2, 1.0), self.x_p],
                [(0.6, 0.0, 0.0, 1.0), self.x_n],
                [(0.2, 1.0, 0.2, 1.0), self.y_p],
                [(0.0, 0.6, 0.0, 1.0), self.y_n],
                [(0.2, 0.2, 1.0, 1.0), self.z_p],
                [(0.0, 0.0, 0.6, 1.0), self.z_n]]

            coords, colors = [], []
            for idx, (col, axial) in enumerate(axis):
                if idx % 2 and skip:
                    continue
                colors.extend([col, col])
                coords.extend([zero_tx, self.mat @ (axial*scale)])

            batch = batch_for_shader(smooth_shader, "LINES", dict(pos=coords, color=colors))
            batch.draw(smooth_shader)

        def draw_grid(self, bbcol, scale):
            """.."""
            bb = self.bb

            i = 0
            series1 = (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)
            series2 = (-0.5, 0.5)
            series1_scaled = [n*scale for n in series1]
            series2_scaled = [n*scale for n in series2]
            z = 0

            def yield_xy():
                for x in series1_scaled:
                    for y in series2_scaled:
                        yield x, y
                for y in series1_scaled:
                    for x in series2_scaled:
                        yield x, y

            for x, y in yield_xy():
                bb[i][:] = x, y, z
                bb[i] = self.mat @ bb[i]
                i += 1

            points = []
            concat = points.extend
            _ = [concat([bb[i], bb[i+1]]) for i in range(0, 24, 2)]

            batch = batch_for_shader(uniform_shader, "LINES", {"pos" : points})
            uniform_shader.bind()
            uniform_shader.uniform_float("color", bbcol)
            batch.draw(uniform_shader)
