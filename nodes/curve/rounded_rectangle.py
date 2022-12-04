
import numpy as np
from math import pi

from mathutils import Vector, Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length, get_data_nesting_level
from sverchok.utils.curve import SvCircle, SvLine
from sverchok.utils.curve.algorithms import concatenate_curves

class SvRoundedRectangleNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Rounded Rectangle
    Tooltip: Generate rounded rectangle curve
    """
    bl_idname = 'SvRoundedRectangleNode'
    bl_label = 'Rounded Rectangle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ROUNDED_RECTANGLE'

    sizex: FloatProperty(
        name='Size X', description='Size of the rectangle along the X axis (rectangle width)',
        default=10.0, min=0.01, update=updateNode)

    sizey: FloatProperty(
        name='Size Y', description='Size of the rectangle along the Y axis (rectangle height)',
        default=10.0, min=0.01, update=updateNode)

    radius : FloatProperty(
        name = "Radius",
        description = "Rounded corner radius",
        default = 1.0, min = 0,
        update = updateNode)

    scale_to_unit : BoolProperty(
        name = "Even domains",
        description = "If checked, give each segment a domain of length 1. Otherwise, each arc will have a domain of length pi/2, and each straight line segment will have a domain of length equal to the segment’s length",
        default = False,
        update = updateNode)

    make_nurbs : BoolProperty(
        name = "NURBS output",
        description = "If checked, the node will output a NURBS curve. Built-in NURBS maths implementation will be used. If not checked, the node will output generic concatenated curve from several straight segments and circular arcs. In most cases, there will be no difference; you may wish to output NURBS if you want to use NURBS-specific API methods with generated curve, or if you want to output the result in file format that understands NURBS only",
        default = False,
        update = updateNode)

    center: BoolProperty(
        name='Center', description='If checked, then the generated curve will be centered around world’s origin. If not checked, the left-down corner of the rectangle will be at the origin',
        default=False, update=updateNode)

    radius_per_corner : BoolProperty(
        name = "Radius per corner",
        description = "Expect Radius input of nesting level 3: one value for each corner of each rectangle",
        default = False,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "center", toggle=True)
        layout.prop(self, "scale_to_unit", toggle=True)
        #layout.prop(self, "radius_per_corner", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'make_nurbs', toggle=True)

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

        if self.make_nurbs:
            curves = [curve.to_nurbs() for curve in curves]
        curve = concatenate_curves(curves, scale_to_unit = self.scale_to_unit)
        return (c1, c2, c3, c4), curve

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        size_x_s = self.inputs['Size X'].sv_get()
        size_y_s = self.inputs['Size Y'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()

        size_x_s = ensure_nesting_level(size_x_s, 2)
        size_y_s = ensure_nesting_level(size_y_s, 2)
        radius_nesting = get_data_nesting_level(radius_s)
        if radius_nesting < 2 or radius_nesting > 3:
            raise TypeError(f"Radius input can only handle nesting level 2 or 3, got {radius_nesting}")
        radius_per_corner = (radius_nesting == 3)
        #if radius_nesting == 2:
            #radius_s = [[radiuses] for radiuses in radius_s]
            #radius_s = [[[r] for r in radiuses] for radiuses in radius_s]

        curves_out = []
        centers_out = []

        for size_x_i, size_y_i, radius_i in zip_long_repeat(size_x_s, size_y_s, radius_s):
            new_curves = []
            new_centers = []
            for size_x, size_y, radiuses in zip_long_repeat(size_x_i, size_y_i, radius_i):
                if not radius_per_corner:
                    radiuses = [radiuses]
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

