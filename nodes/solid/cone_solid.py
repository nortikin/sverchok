
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:

    import bpy
    from bpy.props import FloatProperty, FloatVectorProperty, StringProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvConeSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Cylinder
        Tooltip: Create Solid cylinder
        """
        bl_idname = 'SvConeSolidNode'
        bl_label = 'Cone (Solid)'
        bl_icon = 'MESH_CONE'


        cylinder_radius: FloatProperty(
            name="Radius",
            default=1,
            precision=4,
            update=updateNode)
        cylinder_radius_top: FloatProperty(
            name="Radius",
            default=0,
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
            self.inputs.new('SvStringsSocket', "Radius Top").prop_name = 'cylinder_radius_top'
            self.inputs.new('SvStringsSocket', "Height").prop_name = 'cylinder_height'
            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
            self.inputs.new('SvStringsSocket', "Angle").prop_name = 'cylinder_angle'
            self.outputs.new('SvSolidSocket', "Solid")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            p = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for rad, rad_top, height, origin, direc, angle  in zip(*mlr(p)):
                if rad_top == rad:
                    solid = Part.makeCylinder(rad, height, Base.Vector(origin), Base.Vector(direc), angle)
                else:
                    solid = Part.makeCone(rad, rad_top, height, Base.Vector(origin), Base.Vector(direc), angle)
                solids.append(solid)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvConeSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvConeSolidNode)
