
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import FloatProperty, StringProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvImportSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Import Solid
        Tooltip: Import Solid from BREP file
        """
        bl_idname = 'SvImportSolidNode'
        bl_label = 'Import Solid'
        bl_icon = 'IMPORT'

        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            files = self.inputs[0].sv_get()

            solids = []
            for f in files:
                shape = Part.Shape()
                shape.importBrep(f)
                solid = Part.makeSolid(shape)
                solids.append(solid)

            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvImportSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvImportSolidNode)
