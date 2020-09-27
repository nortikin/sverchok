
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvImportSolidNode', 'Import Solid', 'FreeCAD')
else:
    import bpy
    from sverchok.node_tree import SverchCustomTreeNode
    import Part

    class SvImportSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Import Solid
        Tooltip: Import Solid from BREP file
        """
        bl_idname = 'SvImportSolidNode'
        bl_label = 'Import Solid'
        bl_icon = 'IMPORT'
        solid_catergory = "Inputs"
        
        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            files = self.inputs[0].sv_get()[0]

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
