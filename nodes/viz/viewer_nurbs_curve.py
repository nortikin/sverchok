# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Matrix, Vector
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, match_long_repeat, updateNode, get_data_nesting_level, ensure_nesting_level, describe_data_shape, zip_long_repeat, repeat_last_for_length, numpy_full_list
from sverchok.utils.sv_obj_helper import SvObjHelper
from sverchok.utils.curve.core import SvCurve 
from sverchok.utils.curve.nurbs import SvNurbsCurve

def _deconstruct(curve):
    curve = SvNurbsCurve.to_nurbs(curve)
    if curve is None:
        raise Exception("Curve is not NURBS")

    if not curve.is_periodic():
        raise Exception("Non-periodic NURBS curves are not supported by Blender")

    cpts = curve.get_control_points().tolist()
    weights = curve.get_weights().tolist()
    degree = curve.get_degree()

    return cpts, weights, degree

class SvNurbsCurveOutMk2Node(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    """
    Triggers: Output NURBS Curve
    Tooltip: Create Blender's NURBS Curve object
    """

    bl_idname = 'SvNurbsCurveOutMk2Node'
    bl_label = 'NURBS Curve Out'
    bl_icon = 'CURVE_NCURVE'

    data_kind: StringProperty(default='CURVE')

    def get_curve_name(self, index):
        return f'{self.basedata_name}.{index:04d}'

    def create_curve(self, index, matrix=None, bevel=None, taper=None):
        object_name = self.get_curve_name(index)
        curve_data = bpy.data.curves.new(object_name, 'CURVE')
        curve_data.dimensions = '3D'
        curve_object = bpy.data.objects.get(object_name)
        if not curve_object:
            curve_object = self.create_object(object_name, index, curve_data)

        if matrix is not None:
            curve_object.matrix_local = matrix

        if bevel is not None:
            curve_object.data.bevel_mode = 'OBJECT'
            curve_object.data.bevel_object = bevel
        else:
            curve_object.data.bevel_mode = 'ROUND'

        if taper is not None:
            curve_object.data.taper_object = taper
        else:
            curve_object.data.taper_object = None

        curve_object.data.taper_radius_mode = self.taper_radius_mode

        curve_object.data.bevel_depth = self.bevel_depth
        curve_object.data.bevel_resolution = self.bevel_resolution
        #curve_object.data.resolution_u = self.preview_resolution_u
        curve_object.data.use_fill_caps = self.caps
        curve_object.show_wire = self.show_wire

        if self.material_pointer:
            curve_object.data.materials.clear()
            curve_object.data.materials.append(self.material_pointer)

        return curve_object

    def find_curve(self, index):
        object_name = self.get_curve_name(index)
        return bpy.data.objects.get(object_name)

    def create_spline(self, curve_object, control_points, weights, degree, radiuses=None, tilts=None, is_clamped=True):
        curve_object.data.splines.clear()
        spline = curve_object.data.splines.new(type='NURBS')
        spline.use_bezier_u = False
        spline.use_bezier_v = False
        spline.points.add(len(control_points)-1)

        for p, new_co, new_weight in zip(spline.points, control_points, weights):
            p.co = Vector(list(new_co) + [new_weight])
            p.select = True
        
        spline.use_cyclic_u = self.is_cyclic
        spline.use_endpoint_u = is_clamped
        spline.order_u = degree + 1
        spline.resolution_u = self.resolution

        if radiuses is not None:
            spline.points.foreach_set('radius', numpy_full_list(radiuses, len(spline.points)))
        if tilts is not None:
            spline.points.foreach_set('tilt', numpy_full_list(tilts, len(spline.points)))

        spline.use_smooth = self.use_smooth

        return spline

    def update_sockets(self, context):
        input_curve = self.input_mode == 'CURVE'
        self.inputs['ControlPoints'].hide_safe = input_curve
        self.inputs['Weights'].hide_safe = input_curve
        self.inputs['Degree'].hide_safe = input_curve
        self.inputs['Curve'].hide_safe = not input_curve
        updateNode(self, context)

    input_modes = [
            ('CONTROL_POINTS', "Control points", "Curve's control points and weights", 0),
            ('CURVE', "NURBS curve", "Sverchok's NURBS or NURBS-like Curve object", 1)
        ]

    input_mode : EnumProperty(
            name = "Input mode",
            items = input_modes,
            default = 'CURVE',
            update = update_sockets)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            description = "Whether to make cyclic curve",
            default = False,
            update = updateNode)

    use_endpoint : BoolProperty(
            name = "Endpoint",
            description = "Whether should the curve touch it's end points",
            default = True,
            update = updateNode)

    degree : IntProperty(
            name = "Degree",
            description = "Degree of the curve",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    resolution : IntProperty(
            name = "Resolution",
            min = 1, max = 64,
            default = 10,
            description = "The resolution property defines the number of points that are"
                          " computed between every pair of control points.",
            update = updateNode)

    bevel_radius : FloatProperty(
            name = "Radius",
            description = "Bevel radius",
            min = 0.0,
            default = 0.0,
            update = updateNode)

    tilt : FloatProperty(
            name = "Tilt",
            default = 0.0,
            update = updateNode)

    caps: BoolProperty(
            update = updateNode,
            description="Seals the ends of a beveled curve")

    bevel_depth: FloatProperty(
            name = "Bevel depth",
            description = "Changes the size of the bevel",
            min = 0.0,
            default = 0.0,
            update = updateNode)

    taper_radius_modes = [
            ('OVERRIDE', "Override", "Override the radius of the spline point with the taper radius", 0),
            ('MULTIPLY', "Multiply", "Multiply the radius of the spline point by the taper radius", 1),
            ('ADD', "Add", "Add the radius of the bevel point to the taper radius", 2)
        ]

    taper_radius_mode : EnumProperty(
            name = "Taper radius mode",
            description = "Determine how the effective radius of the spline point is computed when a taper object is specified",
            items = taper_radius_modes,
            default = 'OVERRIDE',
            update = updateNode)

    bevel_resolution: IntProperty(
            name = "Bevel Resolution",
            description = "Alters the smoothness of the bevel",
            min = 0,
            default = 3,
            update = updateNode)

    use_smooth: BoolProperty(
            name = "Smooth shading",
            update = updateNode,
            default = True)

    show_wire: BoolProperty(
            name = "Show Wire",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)
        layout.label(text="Input mode:")
        layout.prop(self, 'input_mode', text='')
        layout.prop(self, 'is_cyclic')

        if self.input_mode == 'CONTROL_POINTS':
            row = layout.row(align=True)
            row.prop(self, 'use_endpoint')
            row.enabled = not self.is_cyclic

        layout.prop(self, 'bevel_depth')

    def draw_buttons_ext(self, context, layout):
        col = layout.column()
        col.prop(self, 'resolution')
        col.prop(self, 'show_wire')
        col.prop(self, 'use_smooth')
        col.prop(self, 'taper_radius_mode')
        col.prop(self, 'bevel_resolution')

    def draw_label(self):
        return f"NURBS Curve {self.basedata_name}"

    def draw_bevel_object_props(self, socket, context, layout):
        row = layout.row(align=True)
        if not socket.is_linked:
            row.prop_search(socket, 'object_ref_pointer', bpy.data, 'objects',
                            text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        else:
            row.label(text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        row = row.row(align=True)
        row.ui_units_x = 0.6
        row.prop(self, 'caps', text='C', toggle=True)

    def draw_taper_object_props(self, socket, context, layout):
        row = layout.row(align=True)
        if not socket.is_linked:
            row.prop_search(socket, 'object_ref_pointer', bpy.data, 'objects',
                            text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        else:
            row.label(text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'ControlPoints')
        self.inputs.new('SvStringsSocket', 'Weights')
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvCurveSocket', 'Curve')
        self.inputs.new('SvMatrixSocket', 'Matrix')
        self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'bevel_radius'
        self.inputs.new('SvStringsSocket', 'Tilt').prop_name = 'tilt'

        obj_socket = self.inputs.new('SvObjectSocket', 'BevelObject')
        obj_socket.custom_draw = 'draw_bevel_object_props'
        obj_socket.object_kinds = "CURVE"

        obj_socket = self.inputs.new('SvObjectSocket', 'TaperObject')
        obj_socket.custom_draw = 'draw_taper_object_props'
        obj_socket.object_kinds = "CURVE"

        self.outputs.new('SvObjectSocket', "Objects")

        self.update_sockets(context)

    def process(self):
        if not self.activate:
            return

        if self.input_mode == 'CONTROL_POINTS':
            vertices_s = self.inputs['ControlPoints'].sv_get()
            has_weights = self.inputs['Weights'].is_linked
            weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
            degree_s = self.inputs['Degree'].sv_get()
            curve_s = [None]

            vertices_s = ensure_nesting_level(vertices_s, 3)
        else:
            vertices_s = [[[]]]
            has_weights = False
            weights_s = [[]]
            degree_s = [[]]
            curve_s = self.inputs['Curve'].sv_get()

            curve_s = ensure_nesting_level(curve_s, 1, data_types=(SvCurve,))

        matrix_s = self.inputs['Matrix'].sv_get(deepcopy=False, default=[None])
        radius_s = self.inputs['Radius'].sv_get(deepcopy=False)
        tilt_s = self.inputs['Tilt'].sv_get(deepcopy=False)
        bevel_s = self.inputs['BevelObject'].sv_get(deepcopy=False, default=[None])
        taper_s = self.inputs['TaperObject'].sv_get(deepcopy=False, default=[None])
            
        inputs = zip_long_repeat(vertices_s, weights_s, degree_s, curve_s, matrix_s, radius_s, tilt_s, bevel_s, taper_s)
        object_index = 0
        for vertices, weights, degree, curve, matrix, radiuses, tilts, bevel, taper in inputs:
            if self.input_mode == 'CURVE':
                vertices, weights, degree = _deconstruct(curve)

            if not vertices or not weights:
                continue
            object_index += 1
            if isinstance(degree, (tuple, list)):
                degree = degree[0]

            weights = repeat_last_for_length(weights, len(vertices))

            curve_object = self.create_curve(object_index, matrix, bevel, taper)
            self.debug("Object: %s", curve_object)
            if not curve_object:
                continue

            if self.input_mode == 'CONTROL_POINTS':
                is_clamped = not self.is_cyclic and self.use_endpoint
            else:
                is_clamped = curve.is_clamped()

            self.create_spline(curve_object, vertices, weights, degree, radiuses, tilts, is_clamped)

        self.remove_non_updated_objects(object_index)
        self.set_corresponding_materials()
        objects = self.get_children()

        self.outputs['Objects'].sv_set(objects)


classes = [SvNurbsCurveOutMk2Node]
register, unregister = bpy.utils.register_classes_factory(classes)

