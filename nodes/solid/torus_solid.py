
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvToursSolidNode', 'Torus (Solid)', 'FreeCAD')
else:

    import bpy
    from bpy.props import FloatProperty, FloatVectorProperty, StringProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvToursSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Torus Cylinder
        Tooltip: Create Solid Torus
        """
        bl_idname = 'SvToursSolidNode'
        bl_label = 'Torus (Solid)'
        bl_icon = 'MESH_TORUS'
        solid_catergory = "Inputs"

        cylinder_radius: FloatProperty(
            name="Radius",
            default=1,
            precision=4,
            update=updateNode)
        cylinder_radius_top: FloatProperty(
            name="Radius",
            default=0.25,
            precision=4,
            update=updateNode)
        torus_angle: FloatProperty(
            name="Angle",
            description="Min Theta angle (angle with Z axis)",
            default=360,
            min=-0,
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
            self.inputs.new('SvStringsSocket', "Radius").prop_name = 'cylinder_radius'
            self.inputs.new('SvStringsSocket', "Radius 2").prop_name = 'cylinder_radius_top'

            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
            self.inputs.new('SvStringsSocket', "Angle").prop_name = 'torus_angle'

            self.outputs.new('SvSolidSocket', "Solid")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            p = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for rad, rad_small, origin, direc, angle  in zip(*mlr(p)):
                solid = Part.makeTorus(rad, rad_small, Base.Vector(origin), Base.Vector(direc), 0, 360, angle)
                solids.append(solid)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvToursSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvToursSolidNode)
