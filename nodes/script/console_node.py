# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from mathutils import Vector, Matrix

# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom import grid


def process_string_to_charmap(node, str):
    for line in str.split():
        line_limited = line[:node.terminal_width]
        # ord(char) , a = 65

def triangles_from_quads(F):
    r"""
                (ABCD)                   (ABC, ACD)

    go from:    A - - - B           to    A - B            A 
                |       |                  \  |            | \
                |       |                   \ |            |  \
                D - - - C                     C            D - C
    """
    TF = []
    TF_add = TX.extend
    _ = [TF_add((poly[0], poly[1], poly[2]), (poly[0], poly[2], poly[3])) for poly in F]
    return TF


def tri_grid(dim_x, dim_y, nx, ny):
    """
    This generates 2d grid, into which we texture each polygon with it's associated character UV

    AA -  -  -AB -  -  -AC -  -  -AD -  -  - n
     | -       | -       | -       |
     |    -    |    -    |    -    |
     |       - |       - |       - |
    BA -  -  -BB -  -  -BC -  - 
     | -       | -
     |    -    |    -
     |       - |       -
    CA -  -  -CB -  -  -
     | -
     |    -
     |       -
    etc

    There's a mapping between int(char) to uv coordinates, charmap will support ascii only.
    """

    neg_y = Matrix(((1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    V, E, F = grid(dim_x, dim_y, nx, ny, anchor=7, matrix=neg_y, mode='pydata')
    TF = triangles_from_quads(F)
    return V, TF


V, F = tri_grid(dim_x, dim_y, nx, ny)


# this data need only be generated once, or at runtime at request.
grid_data = {}
grid_data[(30, 30, 120, 80)] = grid(30, 30, 120, 80)

class SvConsoleNode(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvConsoleNode
    Tooltip: 

    This node prints the input to the nodeview using a fixedwidth character map.
    """

    bl_idname = 'SvConsoleNode'
    bl_label = 'Console Node'
    bl_icon = 'GREASEPENCIL'

    def sv_init(self, context):
        ...

    def draw_buttons(self, context, layout):
        ...

    def process(self):
        ...


classes = [SvConsoleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
