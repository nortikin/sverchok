# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle

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
    relatively to bounding box of base mesh
    """
    bl_idname = 'SvAlignMeshByMesh'
    bl_label = 'Align mesh by mesh'
    bl_icon = 'SNAP_ON'

    align_enum = [('L', ' ', '', 'BACK', 1),
                  ('M', ' ', '', 'ARROW_LEFTRIGHT', 2),
                  ('R', ' ', '', 'FORWARD', 3)]

    axis: bpy.props.EnumProperty(items=[(i, i, '') for i in ['x', 'y', 'z']], default={'x'}, options={'ENUM_FLAG'},
                                 update=updateNode)
    align_base_mesh: bpy.props.EnumProperty(items=align_enum, update=updateNode)
    align_moved_mesh: bpy.props.EnumProperty(items=align_enum, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Base').custom_draw = 'draw_base_sock'
        self.inputs.new('SvVerticesSocket', 'Move mesh').custom_draw = 'draw_move_sock'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvVerticesSocket', "Move vector")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'axis', expand=True)

    def draw_base_sock(self, socket, context, layout):
        layout.label(text=socket.name)
        layout.prop(self, 'align_base_mesh', expand=True)

    def draw_move_sock(self, socket, context, layout):
        layout.label(text=socket.name)
        layout.prop(self, 'align_moved_mesh', expand=True)

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        if not self.axis:
            self.outputs['Verts'].sv_set(self.inputs['Move mesh'].sv_get())
            self.outputs['Move vector'].sv_set([[(0, 0, 0)]])
            return

        move_out = []
        for base_obj, move_obj in zip(*match_long_repeat([sock.sv_get() for sock in self.inputs])):
            move_vector_obj = Vector((0, 0, 0))
            for axis in self.axis:
                position_base = align(base_obj, self.align_base_mesh, axis)
                position_move = align(move_obj, self.align_moved_mesh, axis)
                v_temp = Vector((0, 0, 0))
                setattr(v_temp, axis, position_base - position_move)
                move_vector_obj += v_temp
            move_out.append([move_vector_obj])

        if self.outputs['Verts'].is_linked:
            verts = [[(Vector(v) + mov)[:] for v, mov in zip(move_obj, cycle(move_vec))] for 
                      move_obj, move_vec in zip(*match_long_repeat([self.inputs['Move mesh'].sv_get(), move_out]))]
            self.outputs['Verts'].sv_set(verts)

        if self.outputs['Move vector'].is_linked:
            self.outputs['Move vector'].sv_set([[v[:] for v in lv] for lv in move_out])


classes = [SvAlignMeshByMesh]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes]
