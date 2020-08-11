
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidFacesNode', 'Solid Faces', 'FreeCAD')
else:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.surface import SvSurface
    from sverchok.utils.curve import SvSolidEdgeCurve
    from sverchok.utils.surface import SvSolidFaceSurface


    class SvSolidFacesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Faces
        Tooltip: Get Faces from Solid
        """
        bl_idname = 'SvSolidFacesNode'
        bl_label = 'Solid Faces (Surfaces)'
        bl_icon = 'FACESEL'
        solid_catergory = "Outputs"


        flat_output: BoolProperty(
            name="Flat Output",
            default=False,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvSurfaceSocket', "Solid Faces")
            self.outputs.new('SvCurveSocket', "Outer Wire")


        def draw_buttons(self, context, layout):
            layout.prop(self, 'flat_output')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs[0].sv_get()

            faces = []
            faces_add = faces.extend if self.flat_output else faces.append
            wires =[]
            wires_add = wires.extend if self.flat_output else wires.append
            for solid in solids:
                face_surface = []
                outer_wires = []
                for f in solid.Faces:
                    surface = SvSolidFaceSurface(f)
                    face_surface.append(surface)
                    outer_wire = []
                    for e in f.OuterWire.Edges:
                        try:
                            outer_wire.append(SvSolidEdgeCurve(e))
                        except TypeError:
                            pass
                    outer_wires.append(outer_wire)



                faces_add(face_surface)
                wires_add(outer_wires)


            self.outputs['Solid Faces'].sv_set(faces)
            self.outputs['Outer Wire'].sv_set(wires)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFacesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFacesNode)
