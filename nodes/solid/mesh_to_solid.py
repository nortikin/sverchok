import bpy
from bpy.props import FloatProperty, BoolProperty

from mathutils import Vector
from mathutils.geometry import tessellate_polygon as tessellate
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat as mlr
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part
    import Mesh


def svmesh_to_solid(verts, faces, precision):
    """
    input: verts / faces / precision
    output a Solid (FreeCad type)

    this utility function is included in the node, to keep this code in the same place
    """

    tri_faces = ensure_triangles(verts, faces, True)
    faces_t = [[verts[c] for c in f] for f in tri_faces]
    mesh = Mesh.Mesh(faces_t)
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, precision)
    shape = shape.removeSplitter()  # may slow it down, or be totally necessary
    return Part.makeSolid(shape)


def ensure_triangles(coords, indices, handle_concave_quads):
    """
    this fully tesselates the incoming topology into tris,
    not optimized for meshes that don't contain ngons
    """
    new_indices = []
    concat = new_indices.append
    concat2 = new_indices.extend
    for idxset in indices:
        num_verts = len(idxset)
        if num_verts == 3:
            concat(tuple(idxset))
        elif num_verts == 4 and not handle_concave_quads:
            # a b c d  ->  [a, b, c], [a, c, d]
            concat2([(idxset[0], idxset[1], idxset[2]), (idxset[0], idxset[2], idxset[3])])
        else:
            subcoords = [Vector(coords[idx]) for idx in idxset]
            for pol in tessellate([subcoords]):
                concat([idxset[i] for i in pol])
    return new_indices


class SvMeshToSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Mesh to Solid
    Tooltip: Generate solid from closed mesh
    """
    bl_idname = 'SvMeshToSolidNode'
    bl_label = 'Mesh to Solid'
    bl_icon = 'MESH_CUBE'
    sv_icon = 'SV_MESH_TO_SOLID'
    sv_category = "Solid Inputs"
    sv_dependencies = {'FreeCAD'}

    precision: FloatProperty(
        name="Precision",
        default=0.1,
        precision=4,
        update=updateNode)
    refine_solid: BoolProperty(
        name="Refine Solid",
        description="Removes redundant edges (may slow the process)",
        default=True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "precision")
        layout.prop(self, "refine_solid")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Verts")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvSolidSocket', "Solid")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs[0].sv_get(deepcopy=False)
        faces_s = self.inputs[1].sv_get(deepcopy=False)
        solids = []
        faces = []
        for verts, faces in zip(*mlr([verts_s, faces_s])):
            tri_faces = ensure_triangles(verts, faces, True)
            faces_t = []
            for f in tri_faces:
                faces_t.append([verts[c] for c in f])

            mesh = Mesh.Mesh(faces_t)
            shape = Part.Shape()
            shape.makeShapeFromMesh(mesh.Topology, self.precision)
            if self.refine_solid:
                shape = shape.removeSplitter()
            solid = Part.makeSolid(shape)

            solids.append(solid)

        self.outputs['Solid'].sv_set(solids)


def register():
    bpy.utils.register_class(SvMeshToSolidNode)


def unregister():
    bpy.utils.unregister_class(SvMeshToSolidNode)
