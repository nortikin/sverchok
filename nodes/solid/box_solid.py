
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import StringProperty, FloatProperty, FloatVectorProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvBoxSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Box
        Tooltip: Generate Solid Box
        """
        bl_idname = 'SvBoxSolidNode'
        bl_label = 'Box (Solid)'
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
            self.inputs.new('SvStringsSocket', "Length").prop_name = 'box_length'
            self.inputs.new('SvStringsSocket', "Width").prop_name = 'box_width'
            self.inputs.new('SvStringsSocket', "Height").prop_name = 'box_height'
            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
            self.outputs.new('SvSolidSocket', "Solid")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            p = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for l, w, h, o ,d  in zip(*mlr(p)):
                box = Part.makeBox(l, w, h, Base.Vector(o), Base.Vector(d))
                solids.append(box)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvBoxSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvBoxSolidNode)
