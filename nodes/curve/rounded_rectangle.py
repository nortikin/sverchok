
import numpy as np
from math import pi

from mathutils import Vector, Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.curve import SvCircle, SvConcatCurve, SvLine

class SvRoundedRectangleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Rounded Rectangle
    Tooltip: Generate rounded rectangle curve
    """
    bl_idname = 'SvRoundedRectangleNode'
    bl_label = 'Rounded Rectangle'
    bl_icon = 'SPHERECURVE'

    sizex: FloatProperty(
        name='Size X', description='Rectangle size along X',
        default=10.0, min=0.01, update=updateNode)

    sizey: FloatProperty(
        name='Size Y', description='Rectangle size along Y',
        default=10.0, min=0.01, update=updateNode)

    radius : FloatProperty(
        name = "Radius",
        description = "Rounded corner radius",
        default = 1.0, min = 0,
        update = updateNode)

    scale_to_unit : BoolProperty(
        name = "Even domains",
        description = "Give each segment and each arc equal T parameter domain of [0; 1]",
        default = False,
        update = updateNode)

    center: BoolProperty(
        name='Center', description='Center the rectangle around origin',
        default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "center", toggle=True)
        layout.prop(self, "scale_to_unit", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Size X").prop_name = 'sizex'
        self.inputs.new('SvStringsSocket', "Size Y").prop_name = 'sizey'
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "Centers")

    def make_curve(self, size_x, size_y, radiuses):
        r1, r2, r3, r4 = radiuses[:4]
        p1 = Vector((r1, 0, 0))
        p2 = Vector((size_x - r2, 0, 0))
        p3 = Vector((size_x, r2, 0))
        p4 = Vector((size_x, size_y - r3, 0))
        p5 = Vector((size_x - r3, size_y, 0))
        p6 = Vector((r4, size_y, 0))
        p7 = Vector((0, size_y - r4, 0))
        p8 = Vector((0, r1, 0))

        c1 = Vector((r1, r1, 0))
        c2 = Vector((size_x - r2, r2, 0))
        c3 = Vector((size_x - r3, size_y - r3, 0))
        c4 = Vector((r4, size_y - r4, 0))

        if self.center:
            center = Vector((size_x/2.0, size_y/2.0, 0))
            p1 -= center
            p2 -= center
            p3 -= center
            p4 -= center
            p5 -= center
            p6 -= center
            p7 -= center
            p8 -= center

            c1 -= center
            c2 -= center
            c3 -= center
            c4 -= center

        def make_arc(center, radius, angle):
            matrix = Matrix.Translation(center) @ Matrix.Rotation(angle, 4, 'Z')
            circle = SvCircle(matrix, radius)
            circle.u_bounds = (0, pi/2)
            return circle

        curves = []
        if r1 > 0:
            curves.append(make_arc(c1, r1, pi))
        if (p2 - p1).length > 0:
            curves.append(SvLine.from_two_points(p1, p2))
        if r2 > 0:
            curves.append(make_arc(c2, r2, 3*pi/2))
        if (p4 - p3).length > 0:
            curves.append(SvLine.from_two_points(p3, p4))
        if r3 > 0:
            curves.append(make_arc(c3, r3, 0))
        if (p6 - p5).length > 0:
            curves.append(SvLine.from_two_points(p5, p6))
        if r4 > 0:
            curves.append(make_arc(c4, r4, pi/2))
        if (p8 - p7).length > 0:
            curves.append(SvLine.from_two_points(p7, p8))

        curve = SvConcatCurve(curves, scale_to_unit = self.scale_to_unit)
        return (c1, c2, c3, c4), curve

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        size_x_s = self.inputs['Size X'].sv_get()
        size_y_s = self.inputs['Size Y'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()

        size_x_s = ensure_nesting_level(size_x_s, 2)
        size_y_s = ensure_nesting_level(size_y_s, 2)
        radius_s = ensure_nesting_level(radius_s, 3)

        curves_out = []
        centers_out = []

        for size_x_i, size_y_i, radius_i in zip_long_repeat(size_x_s, size_y_s, radius_s):
            new_curves = []
            new_centers = []
            for size_x, size_y, radiuses in zip_long_repeat(size_x_i, size_y_i, radius_i):
                radiuses = repeat_last_for_length(radiuses, 4)
                centers, curve = self.make_curve(size_x, size_y, radiuses)
                new_curves.append(curve)
                new_centers.append([tuple(c) for c in centers])
            curves_out.append(new_curves)
            centers_out.extend(new_centers)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Centers'].sv_set(centers_out)

def register():
    bpy.utils.register_class(SvRoundedRectangleNode)

def unregister():
    bpy.utils.unregister_class(SvRoundedRectangleNode)

