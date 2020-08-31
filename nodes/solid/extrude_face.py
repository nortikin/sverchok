

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.curve.freecad import SvFreeCadCurve, SvFreeCadNurbsCurve, curves_to_wire
from sverchok.utils.surface.freecad import SvSolidFaceSurface, curves_to_face, surface_to_freecad
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSolidFaceExtrudeNode', 'Extrude Face (Solid)', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

class SvSolidFaceExtrudeNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Solid Face
    Tooltip: Make a Solid by extruding one face
    """
    bl_idname = 'SvSolidFaceExtrudeNode'
    bl_label = 'Extrude Face (Solid)'
    bl_icon = 'EDGESEL'
    #solid_catergory = "Outputs"

    @throttled
    def update_sockets(self, context):
        self.inputs['Surface'].hide_safe = self.face_mode != 'SURFACE'
        self.inputs['Curves'].hide_safe = self.face_mode != 'CURVES'

    face_modes = [
            ('SURFACE', "Surface", "Extrude surface", 0),
            ('CURVES', "Curves", "Make a face from list of curves and extrude it", 1)
        ]

    face_mode : EnumProperty(
            name = "Face",
            description = "How the face is defined",
            items = face_modes,
            default = 'SURFACE',
            update = update_sockets)

#     make_caps : BoolProperty(
#             name = "Make Caps",
#             default = True,
#             update = updateNode)

    refine_solid: BoolProperty(
            name="Refine Solid",
            description="Removes redundant edges (may slow the process)",
            default=False,
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'face_mode')
        #layout.prop(self, 'make_caps', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvCurveSocket', 'Curves')
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.prop = (0.0, 0.0, 1.0)
        self.outputs.new('SvSolidSocket', "Solid")
        self.update_sockets(context)

    def make_face(self, surface, curves):
        if self.face_mode == 'SURFACE':
            fc_surface = surface_to_freecad(surface)
            face = Part.Face(fc_surface.surface)
            return face
        else: # CURVES
            face, _, _ = curves_to_face(curves)
            return face

    def make_wire(self, surface, curves):
        if self.face_mode == 'SURFACE':
            fc_surface = surface_to_freecad(surface).surface
            fc_face = Part.Face(fc_surface)
            return fc_face.OuterWire
        else: # CURVES
            wire = curves_to_wire(curves)
            return wire

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.face_mode == 'SURFACE':
            surface_s = self.inputs['Surface'].sv_get()
            surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
            curve_s = [[None]]
        else:
            surface_s = [[None]]
            curve_s = self.inputs['Curves'].sv_get()
            curve_s = ensure_nesting_level(curve_s, 3, data_types=(SvCurve,))
        offset_s = self.inputs['Vector'].sv_get()
        offset_s = ensure_nesting_level(offset_s, 3)

        solids_out = []
        for surface_i, curves_i, offsets in zip_long_repeat(surface_s, curve_s, offset_s):
            #new_solids = []
            for surface, curves, offset in zip_long_repeat(surface_i, curves_i, offsets):
                fc_offset = Base.Vector(*offset)
                #if self.make_caps:
                face = self.make_face(surface, curves)
                shape = face.extrude(fc_offset)
                #else:
#                     wire = self.make_wire(surface, curves)
#                     shape = wire.extrude(fc_offset)
                solids_out.append(shape)
            #solids_out.append(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidFaceExtrudeNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidFaceExtrudeNode)

