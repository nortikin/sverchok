
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvTransformSolidNode', 'Transform Solid', 'FreeCAD')
else:
    import bpy
    from mathutils import Vector
    from bpy.props import BoolProperty

    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    from FreeCAD import Base
    import Part
    from sverchok.utils.curve import SvSolidEdgeCurve
    from sverchok.utils.surface import SvSolidFaceSurface

    class SvSliceSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Apply Matrix to Solid
        Tooltip: Transform Solid with Matrix
        """
        bl_idname = 'SvSliceSolidNode'
        bl_label = 'Slice Solid'
        bl_icon = 'MESH_CUBE'
        sv_icon = 'SV_SLICE_SOLID'
        solid_catergory = "Operators"

        flat_output: BoolProperty(
            name="Flat Output",
            default=False,
            update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvMatrixSocket', "Matrix")

            self.outputs.new('SvCurveSocket', "Edges")
            self.outputs.new('SvSurfaceSocket', "Faces")

        def draw_buttons(self, context, layout):
            layout.prop(self, 'flat_output')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids_in = self.inputs[0].sv_get(deepcopy=False)
            matrixes = self.inputs[1].sv_get(deepcopy=False)
            slices = []
            slices_face = []
            faces_add = slices_face.extend if self.flat_output else slices_face.append
            slices_add = slices.extend if self.flat_output else slices.append
            
            for solid, matrix in zip(*mlr([solids_in, matrixes])):

                location = matrix.decompose()[0]
                norm = (matrix @ Vector((0, 0, 1))) - location
                dist = norm.dot(location)

                wires = solid.slice(Base.Vector(norm), dist)
                edges_curves = []
                faces = []
                for wire in wires:
                    for edge in wire.Edges:
                        curve = SvSolidEdgeCurve(edge)
                        edges_curves.append(curve)
                    face = Part.Face(wire)
                    faces.append(SvSolidFaceSurface(face))
                if faces:
                    faces_add(faces)
                if edges_curves:
                    slices_add(edges_curves)

            self.outputs['Edges'].sv_set(slices)
            self.outputs['Faces'].sv_set(slices_face)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSliceSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSliceSolidNode)
