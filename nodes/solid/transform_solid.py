
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import FloatProperty, StringProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvTransformSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Apply Matrix to Solid
        Tooltip: Transform Solid with Matrix
        """
        bl_idname = 'SvTransformSolidNode'
        bl_label = 'Transform Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        precision: FloatProperty(
            name="Precision",
            default=0.1,
            precision=4,
            update=updateNode)
        # def draw_buttons(self, context, layout):
        #     layout.prop(self, "join", toggle=True)

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
                myMat = Base.Matrix(*[i for v in matrix for i in v])
                solid_o = solid.transformGeometry(myMat)
                solids.append(solid_o)

            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvTransformSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvTransformSolidNode)
