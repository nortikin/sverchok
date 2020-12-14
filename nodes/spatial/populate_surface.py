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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, throttle_and_update_node
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.populate import populate_surface
from sverchok.utils.field.scalar import SvScalarField

class SvPopulateSurfaceMk2Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Populate Surface
    Tooltip: Generate random points on the surface
    """
    bl_idname = 'SvPopulateSurfaceMk2Node'
    bl_label = 'Populate Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POPULATE_SURFACE'

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

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True
        self.inputs['RadiusField'].hide_safe = self.distance_mode != 'FIELD'
        self.inputs['MinDistance'].hide_safe = self.distance_mode != 'CONST'
        self.outputs['Radiuses'].hide_safe = self.distance_mode != 'FIELD'

    proportional : BoolProperty(
            name = "Proportional",
            default = False,
            update = update_sockets)

    min_r : FloatProperty(
            name = "Min Distance",
            default = 0.5,
            min = 0,
            update = updateNode)

    distance_modes = [
            ('CONST', "Min. Distance", "Specify minimum distance between points", 0),
            ('FIELD', "Radius Field", "Specify radius of empty sphere around each point by scalar field", 1)
        ]

    distance_mode : EnumProperty(
            name = "Distance",
            description = "How minimum distance between points is restricted",
            items = distance_modes,
            default = 'CONST',
            update = update_sockets)

    random_radius : BoolProperty(
            name = "Random radius",
            description = "Make sphere radiuses random, restricted by scalar field values",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'distance_mode')
        layout.prop(self, "proportional")
        if self.distance_mode == 'FIELD':
            layout.prop(self, 'random_radius')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvScalarFieldSocket', "Field").enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvScalarFieldSocket', "RadiusField")
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "UVPoints")
        self.outputs.new('SvStringsSocket', "Radiuses")
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
        if self.distance_mode == 'FIELD':
            radius_s = self.inputs['RadiusField'].sv_get()
        else:
            radius_s = [[None]]
        seed_s = self.inputs['Seed'].sv_get()

        input_level = get_data_nesting_level(surface_s, data_types=(SvSurface,))
        nested_surface = input_level > 1
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        has_field = self.inputs['Field'].is_linked
        if has_field:
            input_level = get_data_nesting_level(fields_s, data_types=(SvScalarField,))
            nested_field = input_level > 1
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        else:
            nested_field = False

        if self.distance_mode == 'FIELD':
            input_level = get_data_nesting_level(radius_s, data_types=(SvScalarField,))
            nested_radius = input_level > 1
            radius_s = ensure_nesting_level(radius_s, 2, data_types=(SvScalarField,))
        else:
            nested_radius = False

        nested_output = nested_surface or nested_field or nested_radius

        verts_out = []
        uv_out = []
        radius_out = []

        inputs = zip_long_repeat(surface_s, fields_s, radius_s, count_s, threshold_s, field_min_s, field_max_s, min_r_s, seed_s)
        for params in inputs:
            new_uv = []
            new_verts = []
            new_radius = []
            for surface, field, radius, count, threshold, field_min, field_max, min_r, seed in zip_long_repeat(*params):
                if self.distance_mode == 'FIELD':
                    min_r = 0
                uvs, verts, radiuses = populate_surface(surface, field, count, threshold,
                                        self.proportional, field_min, field_max,
                                        min_r = min_r, min_r_field = radius,
                                        random_radius = self.random_radius,
                                        seed = seed)
                new_verts.append(verts)
                new_uv.append(uvs)
                new_radius.append(radiuses)

            if nested_output:
                verts_out.append(new_verts)
                uv_out.append(new_uv)
                radius_out.append(new_radius)
            else:
                verts_out.extend(new_verts)
                uv_out.extend(new_uv)
                radius_out.extend(new_radius)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['UVPoints'].sv_set(uv_out)
        self.outputs['Radiuses'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvPopulateSurfaceMk2Node)

def unregister():
    bpy.utils.unregister_class(SvPopulateSurfaceMk2Node)

