
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidVerticesNode', 'Solid Vertices', 'FreeCAD')
else:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr
    from sverchok.utils.curve import SvSolidEdgeCurve
    from sverchok.utils.modules.matrix_utils import vectors_to_matrix
    import Part
    from FreeCAD import Base

    class SvSolidVerticesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Vertices
        Tooltip: Get Vertices from Solid
        """
        bl_idname = 'SvSolidVerticesNode'
        bl_label = 'Solid Vertices'
        bl_icon = 'VERTEXSEL'
        solid_catergory = "Outputs"


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvVerticesSocket', "Vertices")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs[0].sv_get()

            verts_out = []
            verts_add = verts_out.append
            for solid in solids:
                verts = []
                for v in solid.Vertexes:
                    verts.append(v.Point[:])


                verts_add(verts)

            self.outputs['Vertices'].sv_set(verts_out)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidVerticesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidVerticesNode)
