# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.field.vector_primitives import SvTaperVectorField

class SvTaperFieldNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Taper Field
    Tooltip: Generate taper field
    """
    bl_idname = 'SvTaperFieldNode'
    bl_label = 'Taper Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_ATTRACT'

    def update_sockets(self, context):
        self.inputs['MinZ'].hide_safe = not self.use_min_z
        self.inputs['MaxZ'].hide_safe = not self.use_max_z
        updateNode(self, context)

    use_min_z : BoolProperty(
            name = "Use Min Z",
            default = False,
            update = update_sockets)

    use_max_z : BoolProperty(
            name = "Use Max Z",
            default = False,
            update = update_sockets)

    min_z : FloatProperty(
            name = "Min Z",
            default = 0.0,
            update = updateNode)

    max_z : FloatProperty(
            name = "Max Z",
            default = 1.0,
            update = updateNode)

    flat_output : BoolProperty(
            name = "Flat Output",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Restrict Along Axis:')
        r = layout.row(align=True)
        r.prop(self, 'use_min_z', toggle=True)
        r.prop(self, 'use_max_z', toggle=True)
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        d = self.inputs.new('SvVerticesSocket', "Point")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)

        d = self.inputs.new('SvVerticesSocket', "Vertex")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)

        self.inputs.new('SvStringsSocket', 'MinZ').prop_name = 'min_z'
        self.inputs.new('SvStringsSocket', 'MaxZ').prop_name = 'max_z'

        self.outputs.new('SvVectorFieldSocket', "Field")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point_s = self.inputs['Point'].sv_get()
        vertex_s = self.inputs['Vertex'].sv_get()
        if self.use_min_z:
            min_z_s = self.inputs['MinZ'].sv_get()
        else:
            min_z_s = [[None]]
        if self.use_max_z:
            max_z_s = self.inputs['MaxZ'].sv_get()
        else:
            max_z_s = [[None]]

        fields_out = []
        for params in zip_long_repeat(point_s, vertex_s, min_z_s, max_z_s):
            new_fields = []
            for point, vertex, min_z, max_z in zip_long_repeat(*params):
                field = SvTaperVectorField.from_base_point_and_vertex(point, vertex,
                                                min_z = min_z, max_z = max_z)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvTaperFieldNode)

def unregister():
    bpy.utils.unregister_class(SvTaperFieldNode)

