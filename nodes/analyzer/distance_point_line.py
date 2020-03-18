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
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from mathutils import Vector as V
from mathutils.geometry import intersect_point_line
from numpy import array, all as np_all, newaxis
from numpy.linalg import norm as np_norm

def compute_distance(point, line, line_end, tolerance):
    '''call to the mathuutils function'''
    inter_p = intersect_point_line(point, line, line_end)
    dist = (inter_p[0] - point).length
    segment_percent = inter_p[1]
    print(tolerance, dist)
    is_in_line = dist < tolerance[0]
    closest_in_segment = 0 <= segment_percent <= 1
    is_in_segment = is_in_line and closest_in_segment
    return dist, is_in_segment, is_in_line, list(inter_p[0]), closest_in_segment


def compute_distances_mu(line, pts, result, gates, tolerance):
    '''calculate all distances with mathuutils'''
    line_origin = V(line[0])
    line_end = V(line[-1])
    local_result = [[], [], [], [], []]
    for point in pts:
        data = compute_distance(V(point), line_origin, line_end, tolerance)
        for i, res in enumerate(local_result):
            res.append(data[i])

    for i, res in enumerate(result):
        if gates[i]:
            res.append(local_result[i])


def compute_distances_np(line, pts, result, gates, tolerance):
    '''calculate all distances with NumPy'''
    # Adapted from https://math.stackexchange.com/questions/1905533/find-perpendicular-distance-from-point-to-line-in-3d

    np_pts = array(pts)
    segment = V(line[-1]) - V(line[0])
    segment_length = segment.length
    line_direction = segment / segment_length
    vect = np_pts - line[0]
    vect_proy = vect.dot(line_direction)
    closest_point = line[0] + vect_proy[:, newaxis] * line_direction
    dif_v = closest_point - np_pts
    dist = np_norm(dif_v, axis=1)

    is_in_segment = []
    is_in_line = []
    closest_in_segment = []
    if gates[4] or gates[1]:
        closest_in_segment = np_all([vect_proy >= 0, vect_proy <= segment_length], axis=0)
    if gates[1] or gates[2]:
        np_tolerance = array(tolerance)
        is_in_line = dist < tolerance
        if gates[1]:
            is_in_segment = np_all([closest_in_segment, is_in_line], axis=0)

    local_result = [dist, is_in_segment, is_in_line, closest_point, closest_in_segment]

    for i, res in enumerate(result):
        if gates[i]:
            res.append(local_result[i].tolist() if not gates[5] else local_result[i])


class SvDistancePointLineNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Perpendicular to segment
    Tooltip: Distance Point to line and closest point in the line
    '''
    bl_idname = 'SvDistancePointLineNode'
    bl_label = 'Distance Point Line'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DISTANCE_POINT_LINE'

    implentation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("MathUtils", "MathUtils", "MathUtils", 1)]

    compute_distances = {
        "NumPy": compute_distances_np,
        "MathUtils": compute_distances_mu}

    output_numpy : BoolProperty(
        name='Output NumPy', description='Output NumPy arrays',
        default=False, update=updateNode)

    implementation : EnumProperty(
        name='Implementation', items=implentation_modes,
        description='Choose calculation method',
        default="NumPy", update=updateNode)

    tolerance : FloatProperty(
        name="Tolerance", description='Intersection tolerance',
        default=1.0e-6, min=0.0, precision=6,
        update=updateNode)

    list_match_global : EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match_local : EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('SvVerticesSocket', "Vertices")
        sinw('SvVerticesSocket', "Verts Line")
        sinw('SvStringsSocket', "Tolerance").prop_name = 'tolerance'

        sonw('SvStringsSocket', "Distance")
        sonw('SvStringsSocket', "In Segment")
        sonw('SvStringsSocket', "In Line")
        sonw('SvVerticesSocket', "Closest Point")
        sonw('SvStringsSocket', "Closest in Segment")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=True)
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")


    def get_data(self):
        '''get all data from sockets and match lengths'''
        si = self.inputs
        return list_match_func[self.list_match_global]([s.sv_get(default=[[]], deepcopy=False) for s in si])

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        si = self.inputs
        if not (any(s.is_linked for s in so) and all(s.is_linked for s in si[:2])):
            return

        result = [[] for socket in so]
        gates = [socket.is_linked for socket in so]

        gates.append(self.output_numpy)

        group = self.get_data()
        main_func = self.compute_distances[self.implementation]
        match_func = list_match_func[self.list_match_local]

        for pts, line, tolerance in zip(*group):
            if len(tolerance) > 1:
                pts, tolerance = match_func([pts, tolerance])
            main_func(line, pts, result, gates, tolerance)

        for i, r in enumerate(result):
            if gates[i]:
                so[i].sv_set(r)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvDistancePointLineNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvDistancePointLineNode)
