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
import numpy as np
from bpy.props import EnumProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)
from sverchok.utils.geom import linear_approximation

class SvLinearApproxNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Linear Approximation
    Tooltip: Approximate vertices with straight line or plane.
    """
    bl_idname = 'SvLinearApproxNode'
    bl_label = 'Linear Approximation'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LINEAR_APPROXIMATION'

    modes = [
            ("Line", "Line", "Straight line", 1),
            ("Plane", "Plane", "Plane", 2)
        ]

    def update_mode(self, context):
        self.outputs['Direction'].hide_safe = (self.mode != 'Line')
        self.outputs['Normal'].hide_safe = (self.mode != 'Plane')
        updateNode(self, context)
    
    mode : EnumProperty(name = "Approximate by",
            items = modes,
            default = "Line",
            update = update_mode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")

        self.outputs.new('SvVerticesSocket', "Center")
        self.outputs.new('SvVerticesSocket', "Normal")
        self.outputs.new('SvVerticesSocket', "Direction")
        self.outputs.new('SvVerticesSocket', "Projections")
        self.outputs.new('SvVerticesSocket', "Diffs")
        self.outputs.new('SvStringsSocket', "Distances")

        self.update_mode(context)

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])

        out_centers = []
        out_normals = []
        out_directions = []
        out_projections = []
        out_diffs = []
        out_distances = []

        for vertices in vertices_s:
            approx = linear_approximation(vertices)

            out_centers.append(approx.center)

            if self.mode == 'Line':
                line = approx.most_similar_line()
                out_directions.append(tuple(line.direction.normalized()))

                projections = []
                diffs = []
                distances = []
                for vertex in vertices:
                    projection = line.projection_of_point(vertex)
                    projections.append(tuple(projection))
                    diff = projection - Vector(vertex)
                    diffs.append(tuple(diff))
                    distances.append(diff.length)

                out_projections.append(projections)
                out_diffs.append(diffs)
                out_distances.append(distances)

            elif self.mode == 'Plane':
                plane = approx.most_similar_plane()
                out_normals.append(tuple(plane.normal.normalized()))

                projections = []
                diffs = []
                distances = list(map(float, list(plane.distance_to_points(vertices))))
                projections_np = plane.projection_of_points(vertices)
                vertices_np = np.array(vertices)
                projections = list(map(tuple, list(projections_np)))
                diffs_np = projections_np - vertices_np
                diffs = list(map(tuple, list(diffs_np)))

                out_projections.append(projections)
                out_diffs.append(diffs)
                out_distances.append(distances)

        self.outputs['Center'].sv_set([out_centers])
        self.outputs['Normal'].sv_set([out_normals])
        self.outputs['Direction'].sv_set([out_directions])
        self.outputs['Projections'].sv_set(out_projections)
        self.outputs['Diffs'].sv_set(out_diffs)
        self.outputs['Distances'].sv_set(out_distances)

def register():
    bpy.utils.register_class(SvLinearApproxNode)


def unregister():
    bpy.utils.unregister_class(SvLinearApproxNode)

