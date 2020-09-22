
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvFilletSolidNode', 'Fillet Solid', 'FreeCAD')
else:
    import bpy
    from bpy.props import FloatProperty, StringProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr, fullList
    import Part
    from FreeCAD import Base

    class SvFilletSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Bevel Solid
        Tooltip: Transform Solid with Matrix
        """
        bl_idname = 'SvFilletSolidNode'
        bl_label = 'Fillet Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_FILLET_SOLID'
        solid_catergory = "Operators"

        replacement_nodes = [('SvChamferSolidNode', None, None)]

        radius_start: FloatProperty(
            name="Radius Start",
            default=0.1,
            precision=4,
            update=updateNode)
        radius_end: FloatProperty(
            name="Radius End",
            default=0.1,
            precision=4,
            update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvStringsSocket', "Radius Start").prop_name = "radius_start"
            self.inputs.new('SvStringsSocket', "Radius End").prop_name = "radius_end"
            self.inputs.new('SvStringsSocket', "Mask")
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids_in = self.inputs[0].sv_get()
            radius_start_s = self.inputs[1].sv_get()[0]
            radius_end_s = self.inputs[2].sv_get()[0]
            mask_s = self.inputs[3].sv_get(default=[[1]])
            solids = []
            for solid, r_s, r_e, mask in zip(*mlr([solids_in, radius_start_s, radius_end_s, mask_s])):

                selected_edges = []
                fullList(mask, len(solid.Edges))

                for edge, m in zip(solid.Edges, mask):
                    if m:
                        selected_edges.append(edge)
                solid_o = solid.makeFillet(r_s, r_e, selected_edges)
                solids.append(solid_o)


            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvFilletSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvFilletSolidNode)
