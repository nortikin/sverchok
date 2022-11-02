import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part


class SvImportSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Import Solid
    Tooltip: Import Solid from BREP file
    """
    bl_idname = 'SvImportSolidNode'
    bl_label = 'Import Solid'
    bl_icon = 'IMPORT'
    sv_category = "Solid Inputs"
    sv_dependencies = {'FreeCAD'}

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
    bpy.utils.register_class(SvImportSolidNode)


def unregister():
    bpy.utils.unregister_class(SvImportSolidNode)
