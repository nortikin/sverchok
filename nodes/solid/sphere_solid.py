
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import FloatProperty, FloatVectorProperty, StringProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr

    import Part
    from FreeCAD import Base

    class SvSphereSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Sphere
        Tooltip: Create Solid Sphere
        """
        bl_idname = 'SvSphereSolidNode'
        bl_label = 'Sphere (Solid)'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        sphere_radius: FloatProperty(
            name="Radius",
            default=1,
            precision=4,
            update=updateNode)

        sphere_angle1: FloatProperty(
            name="Angle 1",
            description="Min Theta angle (angle with Z axis)",
            default=-90,
            min=-90,
            max=90,
            precision=4,
            update=updateNode)
        sphere_angle2: FloatProperty(
            name="Angle 2",
            description="Max Theta angle (angle with Z axis)",
            default=90,
            min=-90,
            max=90,
            precision=4,
            update=updateNode)
        sphere_angle3: FloatProperty(
            name="Angle 3",
            description="Max Pi angle (angle with X axis)",
            default=360,
            min=0,
            max=360,
            precision=4,
            update=updateNode)

        origin: FloatVectorProperty(
            name="Origin",
            default=(0, 0, 0),
            size=3,
            update=updateNode)
        direction: FloatVectorProperty(
            name="Origin",
            default=(0, 0, 1),
            size=3,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Radius").prop_name = 'sphere_radius'
            self.inputs.new('SvStringsSocket', "Angle 1").prop_name = 'sphere_angle1'
            self.inputs.new('SvStringsSocket', "Angle 2").prop_name = 'sphere_angle2'
            self.inputs.new('SvStringsSocket', "Angle 3").prop_name = 'sphere_angle3'
            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'

            self.outputs.new('SvSolidSocket', "Solid")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            p = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for rad, ang1, ang2, ang3, origin, direc in zip(*mlr(p)):
                sphere = Part.makeSphere(rad, Base.Vector(origin), Base.Vector(direc), ang1, ang2, ang3)
                solids.append(sphere)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSphereSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSphereSolidNode)
