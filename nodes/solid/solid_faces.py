
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.core import SvConcatCurve

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

        def to_nurbs(self, implementation = SvNurbsSurface.NATIVE):
            surface = self.surface.toBSpline()
            nurbs = SvNurbsSurface.build(implementation,
                        surface.UDegree, surface.VDegree,
                        surface.UKnotSequence, surface.VKnotSequence,
                        surface.getPoles(), surface.getWeights())
            return nurbs


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
                    face_surface.append(surface)
                    outer_wire = []
                    face_trims = []
                    for e in f.OuterWire.Edges:
                        try:
                            outer_wire.append(SvSolidEdgeCurve(e).to_nurbs())
                        except TypeError:
                            pass
                        trim,m,M = f.curveOnSurface(e)
                        trim = trim.toBSpline(m,M)
                        controls = [(v.x,v.y,0.0) for v in trim.getPoles()]
                        trim = SvNurbsCurve.build(SvNurbsCurve.NATIVE,
                                    trim.Degree, trim.KnotSequence,
                                    controls,
                                    trim.getWeights())
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
