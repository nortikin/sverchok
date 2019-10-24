# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import mathutils
from mathutils import Vector

from bpy.props import IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.geom import interpolate_quadratic_bezier

class SvQuadraticSplineNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bezier Quadratic Curve Spline
    Tooltip: Generate quadratic Bezier curve by two end points and one control point.
    """
    bl_idname = 'SvQuadraticSplineNode'
    bl_label = '2pt Quadratic Spline'
    bl_icon = 'OUTLINER_OB_EMPTY'

    num_verts: IntProperty(
            name = "Divisions",
            description = "Number of vertices",
            default = 10, min = 3,
            update=updateNode)

    knot1: FloatVectorProperty(
            size = 3,
            name = "Knot 1",
            description = "The beginning of the curve",
            default = (-1, 0, 0),
            update=updateNode)

    knot2: FloatVectorProperty(
            size = 3,
            name = "Knot 2",
            description = "The end of the curve",
            default = (+1, 0, 0),
            update=updateNode)

    handle: FloatVectorProperty(
            size = 3,
            name = "Handle",
            description = "The control point for the curve",
            default = (0, +1, 0),
            update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "NumVerts").prop_name = 'num_verts'

        self.inputs.new('SvVerticesSocket', "Knot1").prop_name = 'knot1'
        self.inputs.new('SvVerticesSocket', "Knot2").prop_name = 'knot2'
        self.inputs.new('SvVerticesSocket', "Handle").prop_name = 'handle'

        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvVerticesSocket', "ControlVerts")
        self.outputs.new('SvStringsSocket', "ControlEdges")

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        num_verts_s = self.inputs['NumVerts'].sv_get()
        knot1_s = self.inputs['Knot1'].sv_get()
        knot2_s = self.inputs['Knot2'].sv_get()
        handle_s = self.inputs['Handle'].sv_get()

        out_verts = []
        out_edges = []
        out_control_verts = []
        out_control_edges = []

        parameters = match_long_repeat([num_verts_s, knot1_s, knot2_s, handle_s])
        for num_verts, knot1, knot2, handle in zip(*parameters):
            objects = match_long_repeat([num_verts, knot1, knot2, handle])
            for num_verts, knot1, knot2, handle in zip(*objects):
                verts = interpolate_quadratic_bezier(knot1, handle, knot2, num_verts)
                verts = [tuple(vert) for vert in verts]
                edges = [(n, n+1) for n in range(len(verts)-1)]

                out_verts.append(verts)
                out_edges.append(edges)

                control_verts = [knot1, handle, knot2]
                control_edges = [(0, 1), (1, 2)]
                out_control_verts.append(control_verts)
                out_control_edges.append(control_edges)

        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['ControlVerts'].sv_set(out_control_verts)
        self.outputs['ControlEdges'].sv_set(out_control_edges)


def register():
    bpy.utils.register_class(SvQuadraticSplineNode)


def unregister():
    bpy.utils.unregister_class(SvQuadraticSplineNode)

