# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom import grid

def process_string_to_charmap(node, str):
    for line in str.split():
        line_limited = line[:node.terminal_width]
        # ord(char) , a = 65

# this data need only be generated once, or at runtime at request.
grid_data = {}
grid_data[(30, 30, 120, 80)] = grid(dim_x=30, dim_y=30, nx=120, ny=80, anchor=0, matrix=None, mode='pydata')

class SvConsoleNode(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvConsoleNode
    Tooltip: 
    
    This node prints the input to the nodeview using a fixedwidth character map.

    This generates 2d grid, into which we texture each polygon with it's associated character UV

    AA -  -  -AB -  -  -AC -  -  -AD -  -  - n
     |         |         |         |
     |         |         |         |
     |         |         |         |
    BA -  -  -BB -  -  -BC -  - 
     |         |
     |         |
     |         |
    CA -  -  -CB -  -  -
     |
     |
    etc

    There's a mapping between int(char) to uv coordinates, charmap will support ascii only.

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
