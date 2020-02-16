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
from sverchok.utils.geom import spherical_approximation

class SvSphereApproxNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sphere Fit
    Tooltip: Fit a sphere through vertices
    """
    bl_idname = 'SvSphereApproxNode'
    bl_label = 'Sphere Fit'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LINEAR_APPROXIMATION'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")
        self.outputs.new('SvVerticesSocket', "Projections")
        self.outputs.new('SvVerticesSocket', "Diffs")
        self.outputs.new('SvStringsSocket', "Distances")

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()

        centers_out = []
        radiuses_out = []
        projections_out = []
        diffs_out = []
        distances_out = []

        for vertices in vertices_s:
            approx = spherical_approximation(vertices)
            if self.outputs['Projections'].is_linked or self.outputs['Diffs'].is_linked or self.outputs['Distances'].is_linked:
                projections = approx.get_projections(vertices)
                diffs = projections - np.array(vertices)
                distances = np.linalg.norm(diffs, axis=1)
                projections_out.append(projections.tolist())
                diffs_out.append(diffs.tolist())
                distances_out.append(distances.tolist())
            centers_out.append(approx.center.tolist())
            radiuses_out.append(approx.radius)

        self.outputs['Center'].sv_set([centers_out])
        self.outputs['Radius'].sv_set([radiuses_out])
        self.outputs['Projections'].sv_set(projections_out)
        self.outputs['Diffs'].sv_set(diffs_out)
        self.outputs['Distances'].sv_set(distances_out)

def register():
    bpy.utils.register_class(SvSphereApproxNode)


def unregister():
    bpy.utils.unregister_class(SvSphereApproxNode)

