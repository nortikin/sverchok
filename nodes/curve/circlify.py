
from math import pi
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCircle
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import circlify

if circlify is None:
    add_dummy('SvExCirclifyNode', "Circlify", 'circlify')
else:

    class SvExCirclifyNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Circlify
        Tooltip: Generate circles packed into a larger circle
        """
        bl_idname = 'SvExCirclifyNode'
        bl_label = 'Circlify'
        bl_icon = 'MESH_CIRCLE'
        sv_icon = 'SV_CIRCLIFY'

        major_radius : FloatProperty(
            name = "Major Radius",
            default = 1.0,
            update = updateNode)

        planes = [
            ('XY', "XY", "XOY plane", 0),
            ('YZ', "YZ", "YOZ plane", 1),
            ('XZ', "XZ", "XOZ plane", 2)
        ]

        plane : EnumProperty(
            name = "Plane",
            items = planes,
            default = 'XY',
            update = updateNode)

        show_enclosure : BoolProperty(
            name = "Show enclosure",
            default = True,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'plane', expand=True)
            layout.prop(self, 'show_enclosure', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', 'Radiuses')
            d = self.inputs.new('SvVerticesSocket', "Center")
            d.use_prop = True
            d.default_property = (0.0, 0.0, 0.0)

            self.inputs.new('SvStringsSocket', "MajorRadius").prop_name = 'major_radius'
            self.outputs.new('SvCurveSocket', "Circles")
            self.outputs.new('SvVerticesSocket', "Centers")
            self.outputs.new('SvStringsSocket', "Radiuses")

        def to_2d(self, v):
            x,y,z = v
            if self.plane == 'XY':
                return x,y
            elif self.plane == 'YZ':
                return y,z
            else:
                return x,z

        def circle_to_curve(self, general_center, circle):
            x0 = circle.x
            y0 = circle.y
            if self.plane == 'XY':
                center = Vector((x0, y0, general_center[2]))
                matrix = Matrix.Translation(center)
            elif self.plane == 'YZ':
                center = Vector((general_center[0], x0, y0))
                matrix = Matrix.Rotation(pi/2, 4, 'Y')
                matrix.translation = center
            else:
                center = Vector((x0, general_center[1], y0))
                matrix = Matrix.Rotation(pi/2, 4, 'X')
                matrix.translation = center
            curve = SvCircle(matrix, circle.r)
            return curve

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            radiuses_s = self.inputs['Radiuses'].sv_get()
            radiuses_s = ensure_nesting_level(radiuses_s, 3)
            center_s = self.inputs['Center'].sv_get()
            center_s = ensure_nesting_level(center_s, 3)
            major_radius_s = self.inputs['MajorRadius'].sv_get()
            major_radius_s = ensure_nesting_level(major_radius_s, 2)

            curves_out = []
            centers_out = []
            radius_out = []
            for radiuses, centers, major_radiuses in zip_long_repeat(radiuses_s, center_s, major_radius_s):
                for radiuses, center, major_radius in zip_long_repeat(radiuses, centers, major_radiuses):
                    center_2d = self.to_2d(center)
                    enclosure = circlify.Circle(x=center_2d[0], y=center_2d[1], r=major_radius)
                    circles = circlify.circlify(radiuses, target_enclosure=enclosure, show_enclosure=self.show_enclosure)
                    curves = [self.circle_to_curve(center, circle) for circle in circles]
                    curves_out.extend(curves)
                    centers_out.append([tuple(curve.center) for curve in curves])
                    radius_out.append([curve.radius for curve in curves])

            self.outputs['Circles'].sv_set(curves_out)
            self.outputs['Centers'].sv_set(centers_out)
            self.outputs['Radiuses'].sv_set(radius_out)

def register():
    if circlify is not None:
        bpy.utils.register_class(SvExCirclifyNode)

def unregister():
    if circlify is not None:
        bpy.utils.unregister_class(SvExCirclifyNode)

