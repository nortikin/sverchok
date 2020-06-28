
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import StringProperty, FloatProperty, FloatVectorProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvSolidEdgesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Edges
        Tooltip: Get Edges from Solid
        """
        bl_idname = 'SvSolidEdgesNode'
        bl_label = 'Solid Edges'
        bl_icon = 'META_CUBE'



        box_length: FloatProperty(
            name="Length",
            default=1,
            precision=4,
            update=updateNode)
        box_width: FloatProperty(
            name="Width",
            default=1,
            precision=4,
            update=updateNode)
        box_height: FloatProperty(
            name="Height",
            default=1,
            precision=4,
            update=updateNode)

        origin: FloatVectorProperty(
            name="Origin",
            default=(0, 0, 0),
            size=3,
            update=updateNode)
        direction: FloatVectorProperty(
            name="Direction",
            default=(0, 0, 1),
            size=3,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvCurveSocket', "Edges")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs[0].sv_get()

            edges = []
            for solid in solids:
                edges_curves=[]
                for e in solid.Edges:
                    try:
                        edge_curve= e.Curve
                        edges_curves.append(edge_curve)
                    except TypeError:
                        pass


                edges.append(edges_curves)

            self.outputs['Edges'].sv_set(edges)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidEdgesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidEdgesNode)
