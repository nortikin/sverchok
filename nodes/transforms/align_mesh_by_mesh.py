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


import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.data_structure import match_long_repeat


def align(vectors, position, axis):
    if position == 'L':
        return min([x if axis == 'x' else y if axis == 'y' else z for x, y, z in vectors])
    elif position == 'R':
        return max([x if axis == 'x' else y if axis == 'y' else z for x, y, z in vectors])
    elif position == 'M':
        x_min = min([x if axis == 'x' else y if axis == 'y' else z for x, y, z in vectors])
        x_max = max([x if axis == 'x' else y if axis == 'y' else z for x, y, z in vectors])
        return (x_min + x_max) / 2


class SvAlignMeshByMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Align mesh
    tip

    tip
    """
    bl_idname = 'SvAlignMeshByMesh'
    bl_label = 'Align mesh by mesh'
    bl_icon = 'SNAP_ON'

    align_enum = [('L', ' ', '', 'BACK', 1),
                  ('M', ' ', '', 'ARROW_LEFTRIGHT', 2),
                  ('R', ' ', '', 'FORWARD', 3)]

    axis = bpy.props.EnumProperty(items=[(i, i, '') for i in ['x', 'y', 'z']], options={'ENUM_FLAG'}, update=updateNode)
    align_base_mesh = bpy.props.EnumProperty(items=align_enum, update=updateNode)
    align_moved_mesh = bpy.props.EnumProperty(items=align_enum, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Base mesh')
        self.inputs.new('VerticesSocket', 'Move mesh')
        self.outputs.new('VerticesSocket', 'Move vector')

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'axis', expand=True)
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label('Base')
        row.prop(self, 'align_base_mesh', expand=True)
        row = col.row(align=True)
        row.label('Move')
        row.prop(self, 'align_moved_mesh', expand=True)

    def process(self):
        if not all([sock.is_linked for sock in self.inputs] + [self.outputs['Move vector'].is_linked]):
            return
        if not self.axis:
            self.outputs['Move vector'].sv_set([[(0, 0, 0)]])
            return

        out = []
        for base_obj, move_obj in zip(*match_long_repeat([sock.sv_get() for sock in self.inputs])):
            move_vector_obj = Vector((0, 0, 0))
            for axis in self.axis:
                position_base = align(base_obj, self.align_base_mesh, axis)
                position_move = align(move_obj, self.align_moved_mesh, axis)
                v_temp = Vector((0, 0, 0))
                setattr(v_temp, axis, position_base - position_move)
                move_vector_obj += v_temp
            out.append([move_vector_obj[:]])
        self.outputs['Move vector'].sv_set(out)


classes = [SvAlignMeshByMesh]


def register():
    [bpy.utils.register_class(cl) for cl in classes]

def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes]
