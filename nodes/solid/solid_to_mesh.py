

from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import FloatProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr

    import Part
    from FreeCAD import Base

    class SvSolidToMeshNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid to Mesh
        Tooltip: Generate mesh from solid
        """
        bl_idname = 'SvSolidToMeshNode'
        bl_label = 'Solid to Mesh'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        precision: FloatProperty(
            name="Precision",
            default=0.1,
            precision=4,
            update=updateNode)
        # def draw_buttons(self, context, layout):
        #     layout.prop(self, "join", toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvStringsSocket', "Precision").prop_name = 'precision'

            self.outputs.new('SvVerticesSocket', "Verts")
            self.outputs.new('SvStringsSocket', "Faces")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs[0].sv_get()
            precisions = self.inputs[1].sv_get()[0]
            verts = []
            faces = []
            for solid, precision in zip(*mlr([solids, precisions])):
                rawdata = solid.tessellate(precision)
                b_verts = []
                b_faces = []
                for v in rawdata[0]:
                    b_verts.append((v.x, v.y, v.z))
                for f in rawdata[1]:
                    b_faces.append(f)
                verts.append(b_verts)
                faces.append(b_faces)


            self.outputs['Verts'].sv_set(verts)
            self.outputs['Faces'].sv_set(faces)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidToMeshNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidToMeshNode)
