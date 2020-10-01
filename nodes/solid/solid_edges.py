
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidEdgesNode', 'Solid Edges', 'FreeCAD')
else:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.curve.freecad import SvSolidEdgeCurve

    class SvSolidEdgesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Edges
        Tooltip: Get Edges from Solid
        """
        bl_idname = 'SvSolidEdgesNode'
        bl_label = 'Solid Edges (Curves)'
        bl_icon = 'EDGESEL'
        solid_catergory = "Outputs"


        flat_output: BoolProperty(
            name="Flat Output",
            default=False,
            update=updateNode)

        nurbs_output : BoolProperty(
            name = "NURBS Output",
            description = "Output curves in NURBS representation",
            default = False,
            update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvCurveSocket', "Edges")

        def draw_buttons(self, context, layout):
            layout.prop(self, 'flat_output')

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'nurbs_output', toggle=True)

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
                        if self.nurbs_output:
                            curve = curve.to_nurbs()
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

