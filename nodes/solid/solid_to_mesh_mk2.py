import math
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, has_element, match_long_repeat as mlr
from sverchok.utils.solid import mesh_from_solid_faces, mesh_from_solid_faces_MOD
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import non_redundant_faces_indices_np as clean
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import MeshPart


def is_triangles_only(faces):
    if has_element(faces): return all((len(f) == 3 for f in faces))


class SvSolidToMeshNodeMk2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Solid to Mesh
    Tooltip: Generate mesh from solid
    """
    bl_idname = 'SvSolidToMeshNodeMk2'
    bl_label = 'Solid to Mesh'
    bl_icon = 'MESH_CUBE'
    sv_icon = 'SV_SOLID_TO_MESH'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}
    modes = [
        ('Basic',    'Basic',    '', 0),
        ('Standard', 'Standard', '', 1),
        ('Mefisto',  'Mefisto',  '', 2),
        # ('NetGen', 'NetGen',   '', 3),
        ('Trivial',  'Trivial',  '', 10),
        ('Lenient',  'Lenient',  '', 14)
    ]
    shape_types = [
        ('Solid', 'Solid', '', 0),
        ('Face', 'Face', '', 1),
    ]

    def set_sockets(self,context):
        self.update_sockets()
        updateNode(self, context)
    def set_shape_sockets(self,context):
        self.shape_sockets()
        updateNode(self, context)

    def shape_sockets(self):
        self.inputs['Solid'].hide_safe = self.shape_type == 'Face'
        self.inputs['Face'].hide_safe = self.shape_type == 'Solid'

    def update_sockets(self):
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

        elif self.mode in {'Trivial', 'Lenient'}:    
            self.inputs['Precision'].hide_safe = True
            self.inputs['Surface Deviation'].hide_safe = True
            self.inputs['Angle Deviation'].hide_safe = True
            self.inputs['Max Edge Length'].hide_safe = True

    precision: FloatProperty(
        name="Precision",
        default=0.1,
        precision=4,
        update=updateNode)

    mode: EnumProperty(
        name="Mode",
        description="Algorithm used for conversion",
        items=modes, default="Basic",
        update=set_sockets)

    shape_type: EnumProperty(
        name="Type",
        description="Algorithm used for conversion",
        items=shape_types, default="Solid",
        update=set_shape_sockets)

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
        layout.prop(self, "shape_type", expand=True)
        layout.prop(self, "mode")
        if self.mode == 'Standard':
            layout.prop(self, "relative_surface_deviation")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvSurfaceSocket', "Face")
        self.inputs.new('SvStringsSocket', "Precision").prop_name = 'precision'
        self.inputs.new('SvStringsSocket', "Surface Deviation").prop_name = 'surface_deviation'
        self.inputs.new('SvStringsSocket', "Angle Deviation").prop_name = 'angle_deviation'
        self.inputs.new('SvStringsSocket', "Max Edge Length").prop_name = 'max_edge_length'
        self.shape_type = "Solid"
        self.inputs['Face'].hide_safe = True
        self.update_sockets()

        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Faces")


    def basic_mesher(self):
        solids = self.inputs[self["shape_type"]].sv_get()
        precisions = self.inputs["Precision"].sv_get()[0]
        verts = []
        faces = []
        for solid, precision in zip(*mlr([solids, precisions])):
            if self.shape_type == 'Solid':
                rawdata = solid.tessellate(precision)
            else:
                rawdata = solid.face.tessellate(precision)

            b_verts = [(v.x, v.y, v.z) for v in rawdata[0]]
            b_faces = [f for f in rawdata[1]]
            b_faces = clean(b_faces).tolist() if is_triangles_only(b_faces) else b_faces

            verts.append(b_verts)
            faces.append(b_faces)

        return verts, faces

    def standard_mesher(self):
        solids = self.inputs[self["shape_type"]].sv_get()
        surface_deviation = self.inputs["Surface Deviation"].sv_get()[0]
        angle_deviation = self.inputs["Angle Deviation"].sv_get()[0]
        verts = []
        faces = []
        for solid, s_dev, ang_dev in zip(*mlr([solids, surface_deviation, angle_deviation])):
            if self.shape_type == 'Solid':
                shape = solid
            else:
                shape = solid.face

            mesh = MeshPart.meshFromShape(
                Shape=shape,
                LinearDeflection=s_dev,
                AngularDeflection=math.radians(ang_dev),
                Relative=self.relative_surface_deviation)

            verts.append([v[:] for v in mesh.Topology[0]])

            b_faces = mesh.Topology[1]
            b_faces = clean(b_faces).tolist() if is_triangles_only(b_faces) else b_faces
            faces.append(b_faces)

        return verts, faces

    def mefisto_mesher(self):
        solids = self.inputs[self["shape_type"]].sv_get()
        max_edge_length = self.inputs['Max Edge Length'].sv_get()[0]

        verts = []
        faces = []
        for solid, max_edge in zip(*mlr([solids, max_edge_length])):
            if self.shape_type == 'Solid':
                shape = solid
            else:
                shape = solid.face
            mesh = MeshPart.meshFromShape(
                Shape=shape,
                MaxLength=max_edge
                )

            verts.append([v[:] for v in mesh.Topology[0]])
            faces.append(mesh.Topology[1])

        return verts, faces

    def trivial_mesher(self):
        """
        this mode will produce a variety of polygon types (tris, quads, ngons...)
        """
        solids = self.inputs[self["shape_type"]].sv_get()

        verts = []
        faces = []
        for solid in solids:
            if self.shape_type == 'Solid':
                shape = solid
            else:
                shape = solid.face

            new_verts, new_edges, new_faces = mesh_from_solid_faces(shape)
            new_verts, new_edges, new_faces = recalc_normals(new_verts, new_edges, new_faces)

            verts.append(new_verts)
            faces.append(new_faces)

        return verts, faces

    def lenient_mesher(self):
        """
        this mode will produce a variety of polygon types (tris, quads, ngons...)
        """
        solids = self.inputs[self["shape_type"]].sv_get()

        verts = []
        faces = []
        for idx, solid in enumerate(solids):
            if self.shape_type == 'Solid':
                shape = solid
            else:
                shape = solid.face
            new_verts, new_faces = mesh_from_solid_faces_MOD(shape, quality=1.0)

            verts.append(new_verts)
            faces.append(new_faces)

        return verts, faces

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.mode == 'Basic':
            verts, faces = self.basic_mesher()
        elif self.mode == 'Standard':
            verts, faces = self.standard_mesher()
        elif self.mode == 'Mefisto':
            verts, faces = self.mefisto_mesher()
        elif self.mode == 'Lenient':
            verts, faces = self.lenient_mesher()
        else: # Trivial
            verts, faces = self.trivial_mesher()

        self.outputs['Verts'].sv_set(verts)
        self.outputs['Faces'].sv_set(faces)


def register():
    bpy.utils.register_class(SvSolidToMeshNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvSolidToMeshNodeMk2)
