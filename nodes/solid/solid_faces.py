
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.utils.surface.nurbs import SvNurbsSurface
#from sverchok.utils.curve.core import SvConcatCurve
from sverchok.utils.curve.freecad import SvFreeCadNurbsCurve, SvFreeCadCurve

if FreeCAD is None:
    add_dummy('SvSolidFacesNode', 'Solid Faces', 'FreeCAD')
else:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, flatten_data, map_unzip_recursirve
    from sverchok.utils.curve.core import SvCurve
    from sverchok.utils.surface.core import SvSurface
    from sverchok.utils.curve.freecad import SvSolidEdgeCurve
    from sverchok.utils.surface.freecad import SvSolidFaceSurface

    import Part

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

        nurbs_output : BoolProperty(
            name = "NURBS Output",
            description = "Output curves and surfaces in NURBS representation",
            default = False,
            update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvSurfaceSocket', "Solid Faces")
            self.outputs.new('SvCurveSocket', "Outer Wire")
            self.outputs.new('SvCurveSocket', "TrimCurves")


        def draw_buttons(self, context, layout):
            layout.prop(self, 'flat_output')

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'nurbs_output', toggle=True)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs['Solid'].sv_get()

            def get_faces(solid):
                face_surface = []
                outer_wires = []
                trims = []
                for f in solid.Faces:
                    surface = SvSolidFaceSurface(f)
                    if self.nurbs_output:
                        out_surface = SvNurbsSurface.get(surface)
                        if out_surface is None:
                            out_surface = surface
                    else:
                        out_surface = surface
                    face_surface.append(out_surface)
                    outer_wire = []
                    face_trims = []
                    for e in f.OuterWire.Edges:
                        try:
                            if self.nurbs_output:
                                outer_wire.append(SvSolidEdgeCurve(e).to_nurbs())
                            else:
                                outer_wire.append(SvSolidEdgeCurve(e))
                        except TypeError:
                            pass
                        trim,m,M = f.curveOnSurface(e)
                        if self.nurbs_output:
                            trim = trim.toBSpline(m,M)
                            trim = SvFreeCadNurbsCurve(trim, ndim=2)
                        else:
                            #trim = trim.trim(m, M)
                            trim = SvFreeCadCurve(trim, (m,M), ndim=2)
                        face_trims.append(trim)

                    outer_wires.append(outer_wire)
                    trims.append(face_trims)

                return face_surface, outer_wires, trims

            faces_out, wires_out, trims_out = map_unzip_recursirve(get_faces, solids, data_types=(Part.Shape,))
            if self.flat_output:
                faces_out = flatten_data(faces_out, data_types=(SvSurface,))
                wires_out = flatten_data(wires_out, target_level=2, data_types=(SvCurve,))
                trims_out = flatten_data(trims_out, target_level=2, data_types=(SvCurve,))

            self.outputs['Solid Faces'].sv_set(faces_out)
            self.outputs['Outer Wire'].sv_set(wires_out)
            if 'TrimCurves' in self.outputs:
                self.outputs['TrimCurves'].sv_set(trims_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFacesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFacesNode)
