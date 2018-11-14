# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils import Matrix, Vector


class MatrixDraw28(object):

    """
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos" : coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", line4f)
    batch.draw(shader)
    """

    def __init__(self):
        self.zero = Vector((0.0, 0.0, 0.0))
        self.x_p = Vector((0.5, 0.0, 0.0))
        self.x_n = Vector((-0.5, 0.0, 0.0))
        self.y_p = Vector((0.0, 0.5, 0.0))
        self.y_n = Vector((0.0, -0.5, 0.0))
        self.z_p = Vector((0.0, 0.0, 0.5))
        self.z_n = Vector((0.0, 0.0, -0.5))
        self.bb = [Vector() for i in range(24)]

    def draw_matrix(self, mat, bbcol=(1.0, 1.0, 1.0), skip=False, grid=True):
        bb = self.bb

        if not isinstance(mat, Matrix):
            mat = Matrix(mat)
            
        zero_tx = mat @ self.zero

        axis = [
            [(1.0, 0.2, 0.2), self.x_p],
            [(0.6, 0.0, 0.0), self.x_n],
            [(0.2, 1.0, 0.2), self.y_p],
            [(0.0, 0.6, 0.0), self.y_n],
            [(0.2, 0.2, 1.0), self.z_p],
            [(0.0, 0.0, 0.6), self.z_n]]

        glLineWidth(2.0)
        for idx, (col, axial) in enumerate(axis):
            if idx % 2 and skip:
                continue
            glColor3f(*col)
            glBegin(GL_LINES)
            glVertex3f(*(zero_tx))
            glVertex3f(*(mat @ axial))
            glEnd()

        # bounding box vertices
        i = 0
        glColor3f(*bbcol)
        series1 = (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)
        series2 = (-0.5, 0.5)
        z = 0

        if not grid:
            return

        # bounding box drawing
        glLineWidth(1.0)

        def yield_xy():
            for x in series1:
                for y in series2:
                    yield x, y
            for y in series1:
                for x in series2:
                    yield x, y

        for x, y in yield_xy():
            bb[i][:] = x, y, z
            bb[i] = mat @ bb[i]
            i += 1


        glLineStipple(1, 0xAAAA)
        glEnable(GL_LINE_STIPPLE)

        for i in range(0, 24, 2):
            glBegin(GL_LINE_STRIP)
            glVertex3f(*bb[i])
            glVertex3f(*bb[i+1])
            glEnd()
        glDisable(GL_LINE_STIPPLE)
