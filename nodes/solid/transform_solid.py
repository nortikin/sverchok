import bpy
from bpy.props import FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat as mlr
from sverchok.utils.solid import transform_solid


class SvTransformSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Apply Matrix to Solid
    Tooltip: Transform Solid with Matrix
    """
    bl_idname = 'SvTransformSolidNode'
    bl_label = 'Transform Solid'
    bl_icon = 'MESH_CUBE'
    sv_icon = 'SV_TRANSFORM_SOLID'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    precision: FloatProperty(
        name="Precision",
        default=0.1,
        precision=4,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvSolidSocket', "Solid")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs[0].sv_get()
        matrixes = self.inputs[1].sv_get()
        solids = []
        for solid, matrix in zip(*mlr([solids_in, matrixes])):
            solid_o = transform_solid(matrix, solid)
            solids.append(solid_o)

        self.outputs['Solid'].sv_set(solids)


def register():
    bpy.utils.register_class(SvTransformSolidNode)


def unregister():
    bpy.utils.unregister_class(SvTransformSolidNode)
