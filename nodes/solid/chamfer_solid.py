
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvChamferSolidNode', 'Chamfer Solid', 'FreeCAD')
else:
    import bpy
    from sverchok.node_tree import SverchCustomTreeNode
    from bpy.props import FloatProperty, StringProperty
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr, fullList
    import FreeCAD as F
    import Part
    from FreeCAD import Base

    class SvChamferSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Straight Bevel
        Tooltip: Sraight cut in solid edge
        """
        bl_idname = 'SvChamferSolidNode'
        bl_label = 'Chamfer Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'
        solid_catergory = "Operators"

        distance_a: FloatProperty(
            name="Distance A",
            default=0.1,
            min=1e-6,
            precision=4,
            update=updateNode)
        distance_b: FloatProperty(
            name="Distance B",
            default=0.1,
            min=1e-6,
            precision=4,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvStringsSocket', "Distance A").prop_name="distance_a"
            self.inputs.new('SvStringsSocket', "Distance B").prop_name="distance_b"
            self.inputs.new('SvStringsSocket', "Mask")
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids_in = self.inputs[0].sv_get()
            distance_a_s = self.inputs[1].sv_get()[0]
            distance_b_s = self.inputs[2].sv_get()[0]
            mask_s = self.inputs[3].sv_get(default=[[1]])
            solids = []
            for solid, d_a, d_b, mask in zip(*mlr([solids_in, distance_a_s, distance_b_s, mask_s])):

                selected_edges = []
                fullList(mask, len(solid.Edges))

                for edge, m in zip(solid.Edges, mask):
                    if m:
                        selected_edges.append(edge)
                solid_o = solid.makeChamfer(d_a, d_b, selected_edges)
                solids.append(solid_o)


            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvChamferSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvChamferSolidNode)
