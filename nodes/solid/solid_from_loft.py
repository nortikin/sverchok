
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvTransformSolidNode', 'Transform Solid', 'FreeCAD')
else:
    import bpy
    from bpy.props import FloatProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvSolidFromLoftNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Apply Matrix to Solid
        Tooltip: Transform Solid with Matrix
        """
        bl_idname = 'SvSolidFromLoftNode'
        bl_label = 'Solid from Loft'
        bl_icon = 'MESH_CUBE'
        sv_icon = 'SV_TRANSFORM_SOLID'
        solid_catergory = "Operators"

        precision: FloatProperty(
            name="Precision",
            default=0.1,
            precision=4,
            update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Face A")
            self.inputs.new('SvSurfaceSocket', "Face B")
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            faces_a = self.inputs[0].sv_get()
            faces_b = self.inputs[1].sv_get()
            solids = []
            for face_a, face_b in zip(*mlr([faces_a, faces_b])):

                solid_o = Part.makeLoft([face_a.face.OuterWire, face_b.face.OuterWire], False,True,False)
                solids.append(solid_o)

            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFromLoftNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFromLoftNode)
