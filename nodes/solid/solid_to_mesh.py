

from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import math
    import bpy
    from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr

    import Part
    import MeshPart
    from FreeCAD import Base

    class SvSolidToMeshNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid to Mesh
        Tooltip: Generate mesh from solid
        """
        bl_idname = 'SvSolidToMeshNode'
        bl_label = 'Solid to Mesh'
        bl_icon = 'MESH_CUBE'
        sv_icon = 'SV_SOLID_TO_MESH'

        modes = [
            ('Basic', 'Basic', '', 0),
            ('Standard', 'Standard', '', 1),
            ('Mefisto', 'Mefisto', '', 2),
            # ('NetGen', 'NetGen', '', 3),
        ]
        def update_sockets(self, context):
            if self.mode == 'Basic':
                self.inputs['Precision'].hide_safe = False
                self.inputs['Surface Deviation'].hide_safe = True
                self.inputs['Angle Deviation'].hide_safe = True
                self.inputs['Max Edge Length'].hide_safe = True

            elif self.mode == 'Standard':
                self.inputs['Precision'].hide_safe = True
                self.inputs['Surface Deviation'].hide_safe = False
                self.inputs['Angle Deviation'].hide_safe = False
                self.inputs['Max Edge Length'].hide_safe = True

            elif self.mode == 'Mefisto':
                self.inputs['Precision'].hide_safe = True
                self.inputs['Surface Deviation'].hide_safe = True
                self.inputs['Angle Deviation'].hide_safe = True
                self.inputs['Max Edge Length'].hide_safe = False


            updateNode(self, context)

        precision: FloatProperty(
            name="Precision",
            default=0.1,
            precision=4,
            update=updateNode)
        mode: EnumProperty(
            name="Mode",
            description="Algorithm used for conversion",
            items=modes, default="Basic",
            update=update_sockets)
        surface_deviation: FloatProperty(
            name="Surface Deviation",
            default=10,
            min=1e-2,
            precision=4,
            update=updateNode)
        angle_deviation: FloatProperty(
            name="Angle Deviation",
            default=30,
            min=5,
            precision=3,
            update=updateNode)
        relative_surface_deviation: BoolProperty(
            name='Relative Surface Deviation',
            default=False,
            update=updateNode)
        max_edge_length: FloatProperty(
            name="max_edge_length",
            default=1,
            soft_min=0.1,
            precision=4,
            update=updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, "mode")
            if self.mode == 'Standard':
                layout.prop(self, "relative_surface_deviation")

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvStringsSocket', "Precision").prop_name = 'precision'
            self.inputs.new('SvStringsSocket', "Surface Deviation").prop_name = 'surface_deviation'
            self.inputs.new('SvStringsSocket', "Angle Deviation").prop_name = 'angle_deviation'
            self.inputs.new('SvStringsSocket', "Max Edge Length").prop_name = 'max_edge_length'


            self.outputs.new('SvVerticesSocket', "Verts")
            self.outputs.new('SvStringsSocket', "Faces")


        def basic_mesher(self):
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

            return verts, faces

        def standard_mesher(self):
            solids = self.inputs[0].sv_get()
            surface_deviation = self.inputs[2].sv_get()[0]
            angle_deviation = self.inputs[3].sv_get()[0]
            verts = []
            faces = []
            for solid, s_dev, ang_dev in zip(*mlr([solids, surface_deviation, angle_deviation])):
                mesh =  MeshPart.meshFromShape(
                    Shape=solid,
                    LinearDeflection=s_dev,
                    AngularDeflection=math.radians(ang_dev),
                    Relative=self.relative_surface_deviation)

                verts.append([v[:] for v in mesh.Topology[0]])
                faces.append(mesh.Topology[1])

            return verts, faces

        def mefisto_mesher(self):
            solids = self.inputs[0].sv_get()
            max_edge_length = self.inputs['Max Edge Length'].sv_get()[0]

            verts = []
            faces = []
            for solid, max_edge in zip(*mlr([solids, max_edge_length])):
                mesh = MeshPart.meshFromShape(
                    Shape=solid,
                    MaxLength=max_edge
                    )

                verts.append([v[:] for v in mesh.Topology[0]])
                faces.append(mesh.Topology[1])

            return verts, faces


        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return


            if self.mode == 'Basic':
                verts, faces = self.basic_mesher()
            elif self.mode == 'Standard':
                verts, faces = self.standard_mesher()
            else:
                verts, faces = self.mefisto_mesher()

            self.outputs['Verts'].sv_set(verts)
            self.outputs['Faces'].sv_set(faces)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidToMeshNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidToMeshNode)
