
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvBoxSolidNode', 'Box (Solid)', 'FreeCAD')
else:
    import bpy
    from bpy.props import FloatProperty, FloatVectorProperty, EnumProperty
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
        solid_catergory = "Inputs"
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

        origin_options = [
                ('CORNER', "Corner", "`Origin` input defines the location of box's corner with smallest X, Y, Z coordinate values", 0),
                ('CENTER', "Center", "`Origin` input defines the location of box's center", 1),
                ('BOTTOM', "Bottom", "`Origin` input defines the location of center of box's bottom face", 2)
            ]

        origin_type : EnumProperty(
            name = "Origin type",
            description = "Which point of the box is defined by `Origin` input",
            items = origin_options,
            default = 'CORNER',
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Length").prop_name = 'box_length'
            self.inputs.new('SvStringsSocket', "Width").prop_name = 'box_width'
            self.inputs.new('SvStringsSocket', "Height").prop_name = 'box_height'
            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
            self.outputs.new('SvSolidSocket', "Solid")

        def draw_buttons(self, context, layout):
            layout.prop(self, 'origin_type')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            p = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for l, w, h, o ,d  in zip(*mlr(p)):
                origin = Base.Vector(o)
                if self.origin_type == 'CENTER':
                    dc = Base.Vector(l/2.0, w/2.0, h/2.0)
                    origin = origin - dc
                elif self.origin_type == 'BOTTOM':
                    dc = Base.Vector(l/2.0, w/2.0, 0)
                    origin = origin - dc
                box = Part.makeBox(l, w, h, origin, Base.Vector(d))
                solids.append(box)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvBoxSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvBoxSolidNode)
