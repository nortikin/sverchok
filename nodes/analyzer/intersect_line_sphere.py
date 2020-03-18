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


from numpy import (
    array,
    all as np_all,
    newaxis,
    sum as np_sum,
    arccos,
    sin,
    any as np_any,
    concatenate,
    invert,
)
from numpy.linalg import norm as np_norm
import bpy
from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes


def compute_intersect_edges_sphere_np(
        verts_in, edges_in, sphere_loc, radius, result, gates):
    '''
        Calculate all intersections of a sphere with one edges mesh with NumPy and in case of none intersection returns closest point of line and over the sphere.
        Adapted from Marco13 answer in https://math.stackexchange.com/questions/1905533/
        segments are calculated from verts_in and edges_in (regular lists
        sphere_loc and radius as regular lists or tuples
        result as a [[], [], [], [], [], [], []] to append the data
        and gates as a boolean list to return:
            [mask: valid intersection,
            inter_a: the intersection nearer to the end point of the segment,
            inter_b: the intersection nearer to the start point of the segment,
            inter_a_in_segment: if A intersection is over the segment,
            inter_b_in_segment: if B intersection is over the segment,
            first_inter_in_segment: returns the first valid value between Int. A, Int. B and Closest point,
            inter_with_segment: returns true if there is any intersection in the segment
            all_inter: returns a flat list of all the intersections
            out_numpy: return NumPy arrays or regular lists]
    '''

    np_verts = array(verts_in)
    if not edges_in:
        edges_in = [[0, -1]]
    np_edges = array(edges_in)
    np_centers = array(sphere_loc)
    np_rad = array(radius)

    segment_orig = np_verts[np_edges[:, 0]]
    segment = np_verts[np_edges[:, 1]] - segment_orig
    segment_mag = np_norm(segment, axis=1)
    segment_dir = segment / segment_mag[:, newaxis]

    join_vect = np_centers[:, newaxis] -  segment_orig
    join_vect_proy = np_sum(join_vect * segment_dir, axis=2)

    closest_point = segment_orig + join_vect_proy[:, :, newaxis] * segment_dir
    dif_v = closest_point - np_centers[:, newaxis, :]
    dist = np_norm(dif_v, axis=2)

    mask = dist > np_rad[:, newaxis]
    ang = arccos(dist / np_rad[:, newaxis])
    offset = np_rad[:, newaxis] *sin(ang)


    inter_a, inter_b = [], []
    inter_a_in_segment, inter_b_in_segment = [], []
    first_inter_in_segment, inter_with_segment = [], []
    all_inter = []
    any_inter = any(gates[5:8])

    if gates[1] or any_inter:
        inter_a = closest_point + segment_dir * offset[:, :, newaxis]
        inter_a[mask] = closest_point[mask]
    if gates[2] or any_inter:
        inter_b = closest_point - segment_dir * offset[:, :, newaxis]
        inter_b[mask] = closest_point[mask]

    if gates[3] or any_inter:
        inter_a_in_segment = np_all(
            [join_vect_proy + offset >= 0, join_vect_proy + offset <= segment_mag],
            axis=0,
        )
    if gates[4] or any_inter:
        inter_b_in_segment = np_all(
            [join_vect_proy - offset >= 0, join_vect_proy - offset <= segment_mag],
            axis=0,
        )

    if gates[5]:
        first_inter_in_segment = closest_point
        first_inter_in_segment[inter_b_in_segment] = inter_b[inter_b_in_segment]
        first_inter_in_segment[inter_a_in_segment] = inter_a[inter_a_in_segment]

    if gates[6]:
        inter_with_segment = np_any([inter_a_in_segment, inter_b_in_segment], axis=0)

    if gates[7]:
        all_inter = concatenate(
            (inter_a[inter_a_in_segment, :], inter_b[inter_b_in_segment, :]), axis=0
            )[newaxis, :, :]

    local_result = [
        invert(mask),
        inter_a,
        inter_b,
        inter_a_in_segment,
        inter_b_in_segment,
        first_inter_in_segment,
        inter_with_segment,
        all_inter,
    ]
    for i, res in enumerate(result):
        if gates[i]:
            if not gates[8]:

                for subres in local_result[i].tolist():
                    res.append(subres)

            else:
                res.append(local_result[i])

class SvIntersectLineSphereNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Sphere Line Intersect
    Tooltip: Find find point in line at desired distance
    '''
    bl_idname = 'SvIntersectLineSphereNode'
    bl_label = 'Compass 3D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_COMPASS_3D'

    radius : FloatProperty(
        name="Radius", description='Sphere Radius',
        default=1, min=0.0,
        update=updateNode)

    sphere_center : FloatVectorProperty(
        name='Center', description='Origin of sphere',
        size=3, default=(0, 0, 0),
        update=updateNode)

    output_numpy : BoolProperty(
        name='Output NumPy', description='Output NumPy arrays',
        default=False, update=updateNode)

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
        sinw('SvVerticesSocket', "Verts")
        sinw('SvStringsSocket', "Edges")
        sinw('SvVerticesSocket', "Center").prop_name = 'sphere_center'
        sinw('SvStringsSocket', "Radius").prop_name = 'radius'

        sonw('SvStringsSocket', "Intersect Line")
        sonw('SvVerticesSocket', "Intersection A")
        sonw('SvVerticesSocket', "Intersection B")
        sonw('SvStringsSocket', "Int. A in segment")
        sonw('SvStringsSocket', "Int. B in segment")
        sonw('SvVerticesSocket', "First in segment")
        sonw('SvStringsSocket', "Int. with segment")
        sonw('SvVerticesSocket', "All Segment int.")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "output_numpy", toggle=False)
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop(self, "output_numpy", toggle=True)
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")


    def get_data(self):
        '''get all data from sockets and match lengths'''
        inputs = self.inputs
        return list_match_func[self.list_match_global]([s.sv_get(default=[[]], deepcopy=False) for s in inputs])

    def process(self):
        '''main node function called every update'''
        outputs = self.outputs
        inputs = self.inputs
        if not (any(s.is_linked for s in outputs) and inputs[0].is_linked):
            return

        result = [[] for socket in outputs]
        gates = [socket.is_linked for socket in outputs]

        gates.append(self.output_numpy)
        group = self.get_data()

        for verts, edges, all_centers, all_radius in zip(*group):
            all_centers, all_radius = list_match_func[self.list_match_local]([all_centers, all_radius])
            compute_intersect_edges_sphere_np(verts, edges, all_centers, all_radius, result, gates)

        for i, res in enumerate(result):
            if gates[i]:
                outputs[i].sv_set(res)


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvIntersectLineSphereNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvIntersectLineSphereNode)
