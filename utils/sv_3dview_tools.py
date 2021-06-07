# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import sys

import bpy
from mathutils import Matrix, Vector

from sverchok.core.socket_conversions import is_matrix
from sverchok.utils.modules import geom_utils
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator


def get_matrix(socket):
    matrix_in_data = socket.sv_get()
    try:
        matrix = matrix_in_data[0]
        if isinstance(matrix, Matrix):
            return matrix
        else:
            return matrix[0]

    except Exception as err:
        print(repr(err))


def get_center(self, context, node):

    location = (0, 0, 0)
    matrix = None
    print('node:', node.name)

    try:
        inputs = node.inputs

        if node.bl_idname in {'SvViewerDrawMk4'}:
            matrix_socket = inputs['Matrix']
            vertex_socket = inputs['Vertices']

            # from this point the function is generic.
            vertex_links = vertex_socket.is_linked
            matrix_links = matrix_socket.is_linked

            if matrix_links:
                matrix = get_matrix(matrix_socket)

            if vertex_links:
                vertex_in_data = vertex_socket.sv_get()
                verts = vertex_in_data[0]
                location = geom_utils.mean([verts[idx] for idx in range(0, len(verts), 3)])

            if matrix:
                if not vertex_links:
                    location = Matrix(matrix).to_translation()[:]
                else:
                    location = (Matrix(matrix) @ Vector(location))[:]

        else:
            self.report({'INFO'}, 'viewer has no get_center function, or node not found')

    except Exception as err:
        self.report({'INFO'}, 'no active node found')

        sys.stderr.write('ERROR: %s\n' % str(err))
        print(sys.exc_info()[-1].tb_frame.f_code)
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

    return location



class Sv3DviewAlign(bpy.types.Operator, SvGenericNodeLocator):
    """ Zoom to viewer output """
    bl_idname = "node.view3d_align_from"
    bl_label = "Align 3dview to Viewer"

    fn_name: bpy.props.StringProperty(default='')

    def sv_execute(self, context, node):

        vector_3d = get_center(self, context, node)
        if not vector_3d:
            print(vector_3d)
            return {'CANCELLED'}

        print(vector_3d)
        context.scene.cursor.location = vector_3d[:]

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                ctx = bpy.context.copy()
                ctx['area'] = area
                ctx['region'] = area.regions[-1]
                bpy.ops.view3d.view_center_cursor(ctx)


classes = [Sv3DviewAlign,]
register, unregister = bpy.utils.register_classes_factory(classes)
