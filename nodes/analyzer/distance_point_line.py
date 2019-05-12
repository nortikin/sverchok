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
from bpy.props import BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from mathutils import Vector as V
from mathutils.geometry import intersect_point_line
import numpy as np


def computeDistance(p, line, line_end):

    inter_p = intersect_point_line(p, line, line_end)
    dist = (inter_p[0] - p).length
    t = inter_p[1]
    is_in_line = dist < 1e-6
    closest_in_segment =  t > 0 and t < 1
    is_in_segment = is_in_line and closest_in_segment
    return dist, is_in_segment, is_in_line, inter_p[0], closest_in_segment


def compute_distances_mu(line, pts, result, gates):
    line_origin = V(line[0])
    line_end = V(line[-1])
    local_result = [[], [], [], [],[]]
    for p in pts:
        # dist, is_in_segment, is_in_line, closest = computeDistance(V(p), line_origin, line_end)
        data = computeDistance(V(p), line_origin, line_end)
        for i, r in enumerate(local_result):
            r.append(data[i])
        # local_result[0].append(dist)
        # local_result[1].append(is_in_segment)
        # local_result[2].append(is_in_line)
        # local_result[3].append(closest)

    for i, r in enumerate(result):
        if gates[i]:
            r.append(local_result[i])


def compute_distances_np(line, pts, result, gates):
    '''Adapted from https://math.stackexchange.com/questions/1905533/find-perpendicular-distance-from-point-to-line-in-3d'''

    np_pts = np.array(pts)
    segment = V(line[-1]) - V(line[0])
    segment_length = segment.length
    direction = segment / segment_length
    v = np_pts - line[0]
    t = v.dot(direction)
    P = line[0] + t[:, np.newaxis] * direction
    dif_v = P - np_pts
    dist = np.linalg.norm(dif_v, axis=1)
    is_in_segment = []
    is_in_line = []
    closest_in_segment = []
    if gates[4] or gates[1]:
        closest_in_segment = np.all([t >= 0, t <= segment_length], axis=0)
    if gates[1] or gates[2]:
        is_in_line = dist < 1e-6
        if gates[1]:
            is_in_segment = np.all([closest_in_segment, is_in_line], axis=0)

    local_result = [dist, is_in_segment, is_in_line, P, closest_in_segment]

    for i, r in enumerate(result):
        if gates[i]:
            r.append(local_result[i].tolist() if not gates[5] else local_result[i])


class DistancePointLineNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Perpendicular to segment
    Tooltip: Distance Point to line and closest point in the line
    '''
    bl_idname = 'DistancePointLineNode'
    bl_label = 'Distance Point Line'
    bl_icon = 'MOD_SIMPLEDEFORM'

    implentation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("MathUtils", "MathUtils", "MathUtils", 1)]

    compute_distances = {
         "NumPy": compute_distances_np,
         "MathUtils": compute_distances_mu}

    output_numpy = BoolProperty(
        name='Output NumPy', description='output NumPy arrays',
        default=False, update=updateNode)

    implementation = EnumProperty(
        name='Segment', items=implentation_modes,
        description='Get segments length or the sum of them',
        default="NumPy", update=updateNode)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', "Verts")
        sinw('VerticesSocket', "Verts Line")

        sonw('StringsSocket', "Distance")
        sonw('StringsSocket', "In Segment")
        sonw('StringsSocket', "In Line")
        sonw('VerticesSocket', "Closest Point")
        sonw('StringsSocket', "Closest in Segment")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "implementation", expand=True)
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)

    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        vertices_s = si['Verts'].sv_get(default=[[]])
        verts_line = si['Verts Line'].sv_get(default=[[]])

        return match_long_repeat([vertices_s, verts_line])

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        si = self.inputs
        if not (any(s.is_linked for s in so) and all(s.is_linked for s in si)):
            return

        result = [[], [], [], [], []]
        gates = []
        gates.append(so['Distance'].is_linked)
        gates.append(so['In Segment'].is_linked)
        gates.append(so['In Line'].is_linked)
        gates.append(so['Closest Point'].is_linked)
        gates.append(so['Closest in Segment'].is_linked)
        gates.append(self.output_numpy)

        group = self.get_data()

        for pts, line in zip(*group):
            self.compute_distances[self.implementation](line, pts, result, gates)

        for i, r in enumerate(result):
            if gates[i]:
                so[i].sv_set(result[i])


def register():
    '''register class in Blender'''
    bpy.utils.register_class(DistancePointLineNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(DistancePointLineNode)
