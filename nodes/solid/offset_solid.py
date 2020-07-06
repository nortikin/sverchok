
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvOffsetSolidNode', 'Offset Solid', 'FreeCAD')
else:
    import bpy
    from bpy.props import FloatProperty, BoolProperty, EnumProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr

    import Part


    class SvOffsetSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Offset Solid
        Tooltip: Generate solid by offseting the boundaries of another along its normals.
        """
        bl_idname = 'SvOffsetSolidNode'
        bl_label = 'Offset Solid'
        bl_icon = 'MESH_CUBE'
        sv_icon = 'SV_OFFSET_SOLID'
        solid_catergory = "Operators"

        offset: FloatProperty(
            name="Offset",
            default=0.1,
            precision=4,
            update=updateNode)
        tolerance: FloatProperty(
            name="Tolerance",
            default=0.01,
            precision=4,
            update=updateNode)

        join_type_items = [
            ('Arcs', 'Arcs', "", 0),
            ('Intersections', 'Intersections', "", 2)]
        join_type: EnumProperty(
            name="Join Type",
            items=join_type_items,
            default="Intersections",
            update=updateNode)
        intersection: BoolProperty(
            name="Intersection",
            description="Allow intersection",
            default=True,
            update=updateNode)
        refine_solid: BoolProperty(
            name="Refine Solid",
            description="Removes redundant edges (may slow the process)",
            default=True,
            update=updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, "tolerance")
            layout.prop(self, "join_type")
            layout.prop(self, "intersection")
            layout.prop(self, "refine_solid")

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
            self.outputs.new('SvSolidSocket', "Solid")


        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids_in = self.inputs[0].sv_get(deepcopy=False)
            offsets = self.inputs[1].sv_get(deepcopy=False)[0]

            solids = []
            for solid_base, offset in zip(*mlr([solids_in, offsets])):

                shape = solid_base.makeOffsetShape(offset, self.tolerance, inter=self.intersection, join=self['join_type'])
                if self.refine_solid:
                    shape = shape.removeSplitter()
                solid = Part.makeSolid(shape)

                solids.append(solid)


            self.outputs['Solid'].sv_set(solids)




def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvOffsetSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvOffsetSolidNode)
