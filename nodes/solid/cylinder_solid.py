
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvCylinderSolidNode', 'Cylinder (Solid)', 'FreeCAD')
else:

    import bpy
    from bpy.props import FloatProperty, FloatVectorProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvCylinderSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Cylinder
        Tooltip: Create Solid cylinder
        """
        bl_idname = 'SvCylinderSolidNode'
        bl_label = 'Cylinder (Solid)'
        bl_icon = 'META_CAPSULE'
        solid_catergory = "Inputs"

        cylinder_radius: FloatProperty(
            name="Radius",
            default=1,
            precision=4,
            update=updateNode)
        cylinder_height: FloatProperty(
            name="Height",
            default=1,
            precision=4,
            update=updateNode)
        cylinder_angle: FloatProperty(
            name="Angle",
            default=360,
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
            self.inputs.new('SvStringsSocket', "Radius").prop_name = 'cylinder_radius'
            self.inputs.new('SvStringsSocket', "Height").prop_name = 'cylinder_height'
            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
            self.inputs.new('SvStringsSocket', "Angle").prop_name = 'cylinder_angle'
            self.outputs.new('SvSolidSocket', "Solid")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            params = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for rad, height, origin, direc, angle  in zip(*mlr(params)):
                cylinder = Part.makeCylinder(rad, height, Base.Vector(origin), Base.Vector(direc), angle)
                solids.append(cylinder)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvCylinderSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvCylinderSolidNode)
