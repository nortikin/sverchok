# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from itertools import zip_longest
import traceback

import bpy
from mathutils import Matrix, Vector
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import Matrix_generate, match_long_repeat, updateNode, get_data_nesting_level, ensure_nesting_level, describe_data_shape, zip_long_repeat, fullList
from sverchok.utils.sv_obj_helper import SvObjHelper

class SvNurbsCurveOutNode(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    """
    Triggers: Output NURBS Curve
    Tooltip: Create Blender's NURBS Curve object
    """

    bl_idname = 'SvNurbsCurveOutNode'
    bl_label = 'NURBS Curve Out'
    bl_icon = 'CURVE_NCURVE'

    data_kind: StringProperty(default='CURVE')

    def get_curve_name(self, index):
        return f'{self.basedata_name}.{index:04d}'

    def create_curve(self, index):
        object_name = self.get_curve_name(index)
        surface_data = bpy.data.curves.new(object_name, 'CURVE')
        surface_data.dimensions = '3D'
        surface_object = bpy.data.objects.get(object_name)
        if not surface_object:
            surface_object = self.create_object(object_name, index, surface_data)
        return surface_object

    def find_curve(self, index):
        object_name = self.get_curve_name(index)
        return bpy.data.objects.get(object_name)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            default = False,
            update = updateNode)

    use_endpoint : BoolProperty(
            name = "Endpoint",
            default = True,
            update = updateNode)

    degree : IntProperty(
            name = "Degree",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)
        layout.prop(self, 'is_cyclic', toggle=True)
        row = layout.row(align=True)
        row.prop(self, 'use_endpoint', toggle=True)
        row.enabled = not self.is_cyclic

    def draw_label(self):
        return f"NURBS Curve {self.basedata_name}"

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'ControlPoints')
        self.inputs.new('SvStringsSocket', 'Weights')
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.outputs.new('SvObjectSocket', "Objects")

    def process(self):
        if not self.activate:
            return

        vertices_s = self.inputs['ControlPoints'].sv_get()
        has_weights = self.inputs['Weights'].is_linked
        weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
        degree_s = self.inputs['Degree'].sv_get()

        vertices_s = ensure_nesting_level(vertices_s, 3)
            
        # we need to suppress depsgraph updates emminating from this part of the process/            
        with self.sv_throttle_tree_update():
            inputs = zip_long_repeat(vertices_s, weights_s, degree_s)
            object_index = 0
            for vertices, weights, degree in inputs:
                if not vertices or not weights:
                    continue
                object_index += 1
                if isinstance(degree, (tuple, list)):
                    degree = degree[0]

                fullList(weights, len(vertices))

                curve_object = self.create_curve(object_index)
                self.debug("Object: %s", curve_object)
                if not curve_object:
                    continue

                curve_object.data.splines.clear()
                spline = curve_object.data.splines.new(type='NURBS')
                spline.use_bezier_u = False
                spline.use_bezier_v = False
                spline.points.add(len(vertices)-1)

                for p, new_co, new_weight in zip(spline.points, vertices, weights):
                    p.co = Vector(list(new_co) + [new_weight])
                    p.select = True

                spline.use_cyclic_u = self.is_cyclic
                spline.use_endpoint_u = not self.is_cyclic and self.use_endpoint
                spline.order_u = degree + 1

            self.remove_non_updated_objects(object_index)
            self.set_corresponding_materials()
            objects = self.get_children()

            self.outputs['Objects'].sv_set(objects)

classes = [SvNurbsCurveOutNode]
register, unregister = bpy.utils.register_classes_factory(classes)

