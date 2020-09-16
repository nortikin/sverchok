
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.utils.surface.nurbs import SvNurbsSurface
#from sverchok.utils.curve.core import SvConcatCurve
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve

if FreeCAD is None:
    add_dummy('SvSolidFacesNode', 'Solid Faces', 'FreeCAD')
else:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.surface.core import SvSurface
    from sverchok.utils.curve.freecad import SvSolidEdgeCurve
    from sverchok.utils.surface.freecad import SvSolidFaceSurface

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
            self.outputs.new('SvCurveSocket', "TrimCurves")


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
            face_trims_out = []
            for solid in solids:
                face_surface = []
                outer_wires = []
                for f in solid.Faces:
                    surface = SvSolidFaceSurface(f)
                    nurbs = SvNurbsSurface.get(surface)
                    if nurbs is None:
                        nurbs = surface
                    face_surface.append(nurbs)
                    outer_wire = []
                    face_trims = []
                    for e in f.OuterWire.Edges:
                        try:
                            outer_wire.append(SvSolidEdgeCurve(e).to_nurbs())
                        except TypeError:
                            pass
                        trim,m,M = f.curveOnSurface(e)
                        trim = trim.toBSpline(m,M)
                        trim = SvFreeCadNurbsCurve(trim, ndim=2)
                        face_trims.append(trim)
                    #face_trims = SvConcatCurve(face_trims)
                    
                    outer_wires.append(outer_wire)
                    face_trims_out.append(face_trims)

                faces_add(face_surface)
                wires_add(outer_wires)


            self.outputs['Solid Faces'].sv_set(faces)
            self.outputs['Outer Wire'].sv_set(wires)
            if 'TrimCurves' in self.outputs:
                self.outputs['TrimCurves'].sv_set(face_trims_out)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFacesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFacesNode)
