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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (throttle_and_update_node, updateNode, ensure_nesting_level,
                                     zip_long_repeat, fullList)
from sverchok.utils.sv_obj_helper import SvObjHelper

# from python 3.5 docs https://docs.python.org/3.5/library/itertools.html recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return list(map(list, zip_longest(*args, fillvalue=fillvalue)))

def is_scene_event():
    stack = traceback.extract_stack()
    if not stack:
        return False
    file, line, method, text = stack[0]
    # During any scene event, the root of Python stack will
    # point at SvNodeTreeCommon.update().
    if "node_tree.py" in file and method == "update":
        return True
    return False

class SvNurbsSurfaceOutNode(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    """
    Triggers: Output NURBS Surface
    Tooltip: Create Blender's NURBS Surface object
    """

    bl_idname = 'SvNurbsSurfaceOutNode'
    bl_label = 'NURBS Surface Out'
    bl_icon = 'SURFACE_NSURFACE'

    data_kind: StringProperty(default='SURFACE')

    def get_surface_name(self, index):
        return f'{self.basedata_name}.{index:04d}'

    def create_surface(self, index):
        object_name = self.get_surface_name(index)
        surface_data = bpy.data.curves.new(object_name, 'SURFACE')
        surface_data.dimensions = '3D'
        surface_object = bpy.data.objects.get(object_name)
        if not surface_object:
            # FIXME: HACK:
            # during scene load event, Blender is currently returning None
            # when checking for bpy.data.objects.get('Alpha'); however,
            # the object may actually exist, and if we create a new object
            # with the same name, we will get Blender crash when trying to
            # switch the object to EDIT mode. So, let's check call stack
            # and do not do anything when processing scene events.
            if is_scene_event():
                self.info("Will not create object during scene event")
                return None
            surface_object = self.create_object(object_name, index, surface_data)
        return surface_object

    def find_surface(self, index):
        object_name = self.get_surface_name(index)
        return bpy.data.objects.get(object_name)

    input_modes = [
            ('1D', "Single list", "List of all control points (concatenated)", 1),
            ('2D', "Separated lists", "List of lists of control points", 2)
        ]

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['USize'].hide_safe = self.input_mode == '2D'

    input_mode : EnumProperty(
            name = "Input mode",
            description = "What to expect in ControlPoints and Weights inputs: either single list (and subdivide it into rows in the node), or pre-subdivided list of lists",
            default = '1D',
            items = input_modes,
            update = update_sockets)

    u_size : IntProperty(
            name = "U Size",
            description = "Number of control points in one row",
            default = 5,
            min = 3,
            update = updateNode)

    is_cyclic_u : BoolProperty(
            name = "Cyclic U",
            description = "Whether to make surface cyclic in the U direction",
            default = False,
            update = updateNode)

    is_cyclic_v : BoolProperty(
            name = "Cyclic V",
            description = "Whether to make surface cyclic in the V direction",
            default = False,
            update = updateNode)

    use_endpoint_u : BoolProperty(
            name = "Endpoint U",
            description = "Whether the surface should touch it's end points in the U direction",
            default = True,
            update = updateNode)

    use_endpoint_v : BoolProperty(
            name = "Endpoint V",
            description = "Whether the surface should touch it's end points in the V direction",
            default = True,
            update = updateNode)

    degree_u : IntProperty(
            name = "Degree U",
            description = "Degree of the surface in the U direction",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    degree_v : IntProperty(
            name = "Degree V",
            description = "Degree of the surface in the V direction",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    resolution_u : IntProperty(
            name = "Resolution U",
            description = "Surface subdivisions per segment",
            min = 1, max = 1024,
            default = 10,
            update = updateNode)

    resolution_v : IntProperty(
            name = "Resolution V",
            description = "Surface subdivisions per segment",
            min = 1, max = 1024,
            default = 10,
            update = updateNode)

    smooth : BoolProperty(
            name = "Smooth",
            description = "Smooth the normals of the surface",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)

        layout.prop(self, "input_mode")

        row = layout.row(align=True)
        row.prop(self, 'is_cyclic_u', toggle=True)
        row.prop(self, 'is_cyclic_v', toggle=True)

        row = layout.row(align=True)
        s1 = row.split()
        s1.prop(self, 'use_endpoint_u', toggle=True)
        s1.enabled = not self.is_cyclic_u
        s2 = row.split()
        row.prop(self, 'use_endpoint_v', toggle=True)
        s2.enabled = not self.is_cyclic_v

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'smooth')
        layout.prop(self, 'resolution_u')
        layout.prop(self, 'resolution_v')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'ControlPoints')
        self.inputs.new('SvStringsSocket', 'Weights')
        self.inputs.new('SvStringsSocket', "DegreeU").prop_name = 'degree_u'
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.inputs.new('SvStringsSocket', "USize").prop_name = 'u_size'
        self.outputs.new('SvObjectSocket', "Objects")

    def draw_label(self):
        return f"NURBS Surface {self.basedata_name}"

    def process(self):
        if not self.activate:
            return

        vertices_s = self.inputs['ControlPoints'].sv_get()
        has_weights = self.inputs['Weights'].is_linked
        weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
        u_size_s = self.inputs['USize'].sv_get()
        degree_u_s = self.inputs['DegreeU'].sv_get()
        degree_v_s = self.inputs['DegreeV'].sv_get()

        if self.input_mode == '1D':
            vertices_s = ensure_nesting_level(vertices_s, 3)
        else:
            vertices_s = ensure_nesting_level(vertices_s, 4)
            
        # we need to suppress depsgraph updates emminating from this part of the process/            
        with self.sv_throttle_tree_update():
            inputs = zip_long_repeat(vertices_s, weights_s, u_size_s, degree_u_s, degree_v_s)
            object_index = 0
            for vertices, weights, u_size, degree_u, degree_v in inputs:
                if not vertices or not weights:
                    continue
                object_index += 1

                if isinstance(u_size, (list, tuple)):
                    u_size = u_size[0]
                if isinstance(degree_u, (tuple, list)):
                    degree_u = degree_u[0]
                if isinstance(degree_v, (tuple, list)):
                    degree_v = degree_v[0]
                if self.input_mode == '1D':
                    fullList(weights, len(vertices))
                else:
                    if isinstance(weights[0], (int, float)):
                        weights = [weights]
                    fullList(weights, len(vertices))
                    for verts_u, weights_u in zip(vertices, weights):
                        fullList(weights_u, len(verts_u))

                surface_object = self.create_surface(object_index)
                self.debug("Object: %s", surface_object)
                if not surface_object:
                    continue

                if self.input_mode == '1D':
                    n_v = u_size
                    n_u = len(vertices) // n_v

                    vertices = grouper(vertices, n_u)
                    weights = grouper(weights, n_u)
                else:
                    n_v = len(vertices)
                    n_u = len(vertices[0])

                surface_object.data.splines.clear()
                for vertices_row, weights_row in zip(vertices, weights):
                    spline = surface_object.data.splines.new(type='NURBS')
                    spline.use_bezier_u = False
                    spline.use_bezier_v = False
                    spline.points.add(n_u - 1)

                    for p, new_co, new_weight in zip(spline.points, vertices_row, weights_row):
                        p.co = Vector(list(new_co) + [new_weight])
                        p.select = True

                    spline.use_cyclic_v = self.is_cyclic_u
                    spline.use_cyclic_u = self.is_cyclic_v
                    spline.use_endpoint_u = not self.is_cyclic_v and self.use_endpoint_v
                    spline.use_endpoint_v = not self.is_cyclic_u and self.use_endpoint_u

                surface_object = self.find_surface(object_index)
                bpy.context.view_layer.objects.active = surface_object
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.curve.make_segment()
                bpy.ops.object.mode_set(mode = 'OBJECT')
                spline = surface_object.data.splines[0]
                spline.order_u = degree_u + 1
                spline.order_v = degree_v + 1
                spline.resolution_u = self.resolution_v
                spline.resolution_v = self.resolution_u
                spline.use_smooth = self.smooth

            self.remove_non_updated_objects(object_index)
            self.set_corresponding_materials()
            objects = self.get_children()

            self.outputs['Objects'].sv_set(objects)

classes = [SvNurbsSurfaceOutNode]
register, unregister = bpy.utils.register_classes_factory(classes)

