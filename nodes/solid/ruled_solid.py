# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode, rotate_list
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface, SvFreeCadNurbsSurface
from sverchok.utils.dummy_nodes import add_dummy

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvRuledSolidNode', 'Solid from two Faces', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

def calc_rho(edges1, edges2):
    s = 0
    for e1, e2 in zip(edges1, edges2):
        s1 = e1.Curve.StartPoint
        s2 = e2.Curve.StartPoint
        e1 = e1.Curve.EndPoint
        e2 = e2.Curve.EndPoint
        s += s1.distanceToPoint(s2) + e1.distanceToPoint(e2)
    return s

def reorder(edges1, edges2):
    min_sum_rho = None
    best = None
    for i in range(len(edges1)):
        rotated2 = rotate_list(edges2, i)
        sum_rho = calc_rho(edges1, rotated2)
        if min_sum_rho is None or sum_rho < min_sum_rho:
            best = rotated2
            min_sum_rho = sum_rho
    return edges1, best

def reverse_edges(edges, reverse=True, flip=True):
    result = []
    input = reversed(edges) if reverse else edges
    for edge in input:
        if flip:
            edge.reverse()
        result.append(edge)
    return result

class SvRuledSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ruled Solid Surface
    Tooltip: Make a Solid from two Faces ("floor" and "ceil") by adding ruled surfaces between them ("walls")
    """
    bl_idname = 'SvRuledSolidNode'
    bl_label = 'Solid from two Faces'
    bl_icon = 'EDGESEL'
    sv_icon = 'SV_RULED_SOLID'
    solid_catergory = "Operators"

    reverse1 : BoolProperty(
            name = "Reverse",
            description = "Reverse the order of edges in the first face",
            default = False,
            update = updateNode)

    reverse2 : BoolProperty(
            name = "Reverse",
            description = "Reverse the order of edges in the second face",
            default = False,
            update = updateNode)

    flip1 : BoolProperty(
            name = "Flip",
            description = "Reverse the direction of edges in the first face",
            default = False,
            update = updateNode)

    flip2 : BoolProperty(
            name = "Flip",
            description = "Reverse the direction of edges in the second face",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "SolidFace1")
        self.inputs.new('SvSurfaceSocket', "SolidFace2")
        self.outputs.new('SvSolidSocket', "Solid")

    def draw_buttons(self, context, layout):
        layout.label(text='First Face:')
        row = layout.row(align=True)
        row.prop(self, 'reverse1', toggle=True)
        row.prop(self, 'flip1', toggle=True)

        layout.label(text='Second Face:')
        row = layout.row(align=True)
        row.prop(self, 'reverse2', toggle=True)
        row.prop(self, 'flip2', toggle=True)

    def make_solid(self, face1, face2):
        edges1 = face1.face.OuterWire.Edges
        edges2 = face2.face.OuterWire.Edges
        if len(edges1) != len(edges2):
            raise Exception("Faces have different number of edges")

        fc_sides = []
        sv_sides = []

        edges1 = reverse_edges(edges1, reverse=self.reverse1, flip=self.flip1)
        edges2 = reverse_edges(edges2, reverse=self.reverse2, flip=self.flip2)
        edges1, edges2 = reorder(edges1, edges2)

        for edge1, edge2 in zip(edges1, edges2):
            side = Part.makeRuledSurface(edge1, edge2)
            sv_side = SvFreeCadNurbsSurface(side.Surface, face=side)
            fc_sides.append(side)
            sv_sides.append(sv_side)

        shell = Part.makeShell([face1.face, face2.face] + fc_sides)
        solid = Part.makeSolid(shell)
        return solid

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        face1_surfaces_s = self.inputs['SolidFace1'].sv_get()
        face1_surfaces_s = ensure_nesting_level(face1_surfaces_s, 2, data_types=(SvSurface,))
        face2_surfaces_s = self.inputs['SolidFace2'].sv_get()
        face2_surfaces_s = ensure_nesting_level(face2_surfaces_s, 2, data_types=(SvSurface,))

        solids_out = []
        for face1_surfaces, face2_surfaces in zip_long_repeat(face1_surfaces_s, face2_surfaces_s):
            for face1_surface, face2_surface in zip_long_repeat(face1_surfaces, face2_surfaces):
                if not is_solid_face_surface(face1_surface):
                    face1_surface = surface_to_freecad(face1_surface, make_face=True) # SvFreeCadNurbsSurface
                if not is_solid_face_surface(face2_surface):
                    face2_surface = surface_to_freecad(face2_surface, make_face=True) # SvFreeCadNurbsSurface

                solid = self.make_solid(face1_surface, face2_surface)
                solids_out.append(solid)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvRuledSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvRuledSolidNode)

