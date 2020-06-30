
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr
    from sverchok.utils.curve import SvSolidEdgeCurve, SvCircle
    from sverchok.utils.modules.matrix_utils import vectors_to_matrix
    import Part
    from FreeCAD import Base

    class SvSolidEdgesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Edges
        Tooltip: Get Edges from Solid
        """
        bl_idname = 'SvSolidEdgesNode'
        bl_label = 'Solid Edges'
        bl_icon = 'EDGESEL'


        flat_output: BoolProperty(
            name="Flat Output",
            default=False,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvCurveSocket', "Edges")


        def draw_buttons(self, context, layout):
            layout.prop(self, 'flat_output')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs[0].sv_get()

            edges = []
            edges_add = edges.extend if self.flat_output else edges.append
            for solid in solids:
                edges_curves = []
                for e in solid.Edges:
                    try:
                        curve = SvSolidEdgeCurve(e)
                        edges_curves.append(curve)
                    except TypeError:
                        pass


                edges_add(edges_curves)

            self.outputs['Edges'].sv_set(edges)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidEdgesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidEdgesNode)
