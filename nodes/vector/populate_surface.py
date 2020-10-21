# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import random

import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty, FloatProperty
from mathutils.kdtree import KDTree

from sverchok.core.socket_data import SvNoDataError
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.populate import populate_surface
from sverchok.utils.field.scalar import SvScalarField

class SvPopulateSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Populate Surface
    Tooltip: Generate random points on the surface
    """
    bl_idname = 'SvPopulateSurfaceNode'
    bl_label = 'Populate Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FIELD_RANDOM_PROBE'

    threshold : FloatProperty(
            name = "Threshold",
            default = 0.5,
            update = updateNode)

    field_min : FloatProperty(
            name = "Field Minimum",
            default = 0.0,
            update = updateNode)

    field_max : FloatProperty(
            name = "Field Maximum",
            default = 1.0,
            update = updateNode)

    seed: IntProperty(default=0, name='Seed', update=updateNode)

    count : IntProperty(
            name = "Count",
            default = 50,
            min = 1,
            update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True

    proportional : BoolProperty(
            name = "Proportional",
            default = False,
            update = update_sockets)

    min_r : FloatProperty(
            name = "Min Distance",
            default = 0.5,
            min = 0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "proportional", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "UVPoints")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.proportional and not self.inputs['Field'].is_linked:
            raise SvNoDataError(socket=self.inputs['Field'], node=self)

        surface_s = self.inputs['Surface'].sv_get()
        fields_s = self.inputs['Field'].sv_get(default=[[None]])
        count_s = self.inputs['Count'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()

        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        has_field = self.inputs['Field'].is_linked
        if has_field:
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))

        verts_out = []
        uv_out = []

        parameters = zip_long_repeat(surface_s, fields_s, count_s, threshold_s, field_min_s, field_max_s, min_r_s, seed_s)
        for surfaces, fields, counts, thresholds, field_mins, field_maxs, min_rs, seeds in parameters:
            objects = zip_long_repeat(surfaces, fields, counts, thresholds, field_mins, field_maxs, min_rs, seeds)
            for surface, field, count, threshold, field_min, field_max, min_r, seed in objects:
                new_uv, new_verts = populate_surface(surface, field, count, threshold, self.proportional, field_min, field_max, min_r, seed)
                verts_out.append(new_verts)
                uv_out.append(new_uv)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['UVPoints'].sv_set(uv_out)

def register():
    bpy.utils.register_class(SvPopulateSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvPopulateSurfaceNode)

