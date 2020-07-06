
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvMirrorSolidNode', 'Mirror Solid', 'FreeCAD')
else:
    import bpy
    from bpy.props import FloatProperty, StringProperty
    from mathutils import Vector
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    from FreeCAD import Base

    class SvMirrorSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Mirror Solid
        Tooltip: Mirror Solid with Matrix as Plane
        """
        bl_idname = 'SvMirrorSolidNode'
        bl_label = 'Mirror Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_MIRROR_SOLID'
        solid_catergory = "Operators"

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
                loc = Vector((0,0,0)) @ matrix
                norm = Vector((0,0,1)) @ matrix
                solid_o = solid.mirror(Base.Vector(loc[:]),Base.Vector(norm[:]))
                solids.append(solid_o)

            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvMirrorSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvMirrorSolidNode)
