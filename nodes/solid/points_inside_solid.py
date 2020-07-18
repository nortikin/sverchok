
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvIsInsideSolidNode', 'Point Inside Solid', 'FreeCAD')
else:
    import bpy
    from sverchok.node_tree import SverchCustomTreeNode
    from bpy.props import FloatProperty, StringProperty, BoolProperty
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr, fullList
    from FreeCAD import Base

    class SvIsInsideSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Straight Bevel
        Tooltip: Sraight cut in solid edge
        """
        bl_idname = 'SvIsInsideSolidNode'
        bl_label = 'Points Inside Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_POINTS_INSIDE_SOLID'
        solid_catergory = "Operators"

        tolerance: FloatProperty(
            name="Tolerance",
            default=1e-5,
            min=1e-6,
            precision=4,
            update=updateNode)
        in_surface: BoolProperty(
            name="Accept in surface",
            description="Accept point if it is over solid surface",
            default=True,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Mask")
            self.outputs.new('SvVerticesSocket', "Inside Vertices")
            self.outputs.new('SvVerticesSocket', "Outside Vertices")

        def draw_buttons(self, context, layout):
            layout.prop(self, "tolerance")
            layout.prop(self, "in_surface")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids_in = self.inputs[0].sv_get()
            points = self.inputs[1].sv_get()

            inside_mask = []
            inside_verts_out = []
            outside_verts_out = []
            for solid, points, in zip(*mlr([solids_in, points])):
                verts_inside = []
                verts_outside = []
                is_inside = []
                for v in points:
                    v_is_inside = solid.isInside(Base.Vector(v), self.tolerance, self.in_surface)
                    is_inside.append(v_is_inside)
                    if v_is_inside:
                        verts_inside.append(v)
                    else:
                        verts_outside.append(v)
                inside_mask.append(is_inside)
                inside_verts_out.append(verts_inside)
                outside_verts_out.append(verts_outside)


            self.outputs['Mask'].sv_set(inside_mask)
            self.outputs['Inside Vertices'].sv_set(inside_verts_out)
            self.outputs['Outside Vertices'].sv_set(outside_verts_out)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvIsInsideSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvIsInsideSolidNode)
