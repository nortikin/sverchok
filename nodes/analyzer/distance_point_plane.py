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
from mathutils.geometry import intersect_point_line, distance_point_to_plane, normal, intersect_point_tri
import numpy as np


def compute_point_tri_dist(p, plane_origin, plane_a, plane_b, norm, tolerance):

    dist = distance_point_to_plane(p, plane_origin, norm)
    closest = p - norm * dist
    side = dist > 0
    dist_abs = abs(dist)
    is_in_plane = dist_abs < tolerance
    closest_in_plane =  intersect_point_tri(closest, plane_origin , plane_a, plane_b)
    is_in_segment = is_in_plane and closest_in_plane
    return dist_abs, is_in_segment, is_in_plane, list(closest), bool(closest_in_plane), side


def compute_distances_mu(plane, pts, result, gates, tolerance):
    plane_origin = V(plane[0])
    plane_a, plane_b = V(plane[1]), V(plane[2])
    norm = normal([plane_origin, plane_a, plane_b])
    if norm.length == 0:
        print("Error: the three points of the plane are aligned. Not valid plane")
    local_result = [[] for res in result]
    for p in pts:
        data = compute_point_tri_dist(V(p), plane_origin, plane_a, plane_b, norm, tolerance)
        for i, r in enumerate(local_result):
            r.append(data[i])

    for i, res in enumerate(result):
        if gates[i]:
            res.append(local_result[i])

def barycentric_mask_np(pts, edges, np_pol_v, pol_normals, ed_id, tolerance):
    '''Helper function to mask which points are inside the triangles'''
       
    edge = edges[ed_id, :]
    triangle_vert = np_pol_v[ed_id, :]
    vert_pts = pts - triangle_vert[np.newaxis, :]
    cross = np.cross(edge[ np.newaxis, :], vert_pts)
    
    return np.sum(pol_normals * cross, axis=1) > -tolerance

def pts_in_tris_np(pts, edges, pol_v, pol_normals, tolerance):
    '''calculate if points are inside the triangles'''
    w = barycentric_mask_np(pts, edges, pol_v, pol_normals, 0, tolerance)
    u = barycentric_mask_np(pts, edges, pol_v, pol_normals, 1, tolerance)
    v = barycentric_mask_np(pts, edges, pol_v, pol_normals, 2, tolerance)
    return w * u * v 
    
def compute_distances_np(plane, pts, result, gates, tolerance):
    '''The theory of this function was taken from "Optimizing The Computation Of Barycentric Coordinates" in
       https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/barycentric-coordinates'''

    np_plane_v = np.array(plane)
    v1 = np_plane_v[1,:] - np_plane_v[0,:]
    v2 = np_plane_v[2,:] - np_plane_v[0,:]
    normals = np.cross(v1, v2)
    normals_d = np.linalg.norm(normals, axis=0)
    np_tolerance = np.array(tolerance)
    if normals_d == 0:
        print("Error: the three points of the plane are aligned. Not valid plane")
    normals_n = normals / normals_d 
    edges = np.zeros(np_plane_v.shape, dtype=np.float32)
    edges[ 0, :] = v1
    edges[ 1, :] = np_plane_v[ 2, :] - np_plane_v[ 1, :]
    edges[ 2, :] = np_plane_v[ 0, :] - np_plane_v[ 2, :]
    plane_co = np_plane_v[ 0, :]
    np_pts = np.array(pts)

    vector_base = np_pts - plane_co
    distance = np.sum(vector_base * normals_n, axis=1)

    closest = np_pts - normals_n[np.newaxis, :] * distance[:,np.newaxis]
    side = (distance >= 0 ) if gates[5] else []
    dist_abs = np.abs(distance)
    
    is_in_triangle = []
    is_in_plane = []
    closest_in_tri = []
    
    if gates[4] or gates[1]:
        closest_in_tri = pts_in_tris_np(closest, edges, np_plane_v, normals_n, np_tolerance)
    if gates[1] or gates[2]:
        is_in_plane = dist_abs < np_tolerance
        if gates[1]:
            is_in_triangle = np.all([closest_in_tri, is_in_plane], axis=0)
            

    local_result = [dist_abs, is_in_triangle, is_in_plane, closest, closest_in_tri, side]

    for i, r in enumerate(result):
        if gates[i]:
            r.append(local_result[i].tolist() if not gates[6] else local_result[i])


class SvDistancePointPlaneNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Perpendicular to triangle
    Tooltip: Distance Point to plane and closest point in the plane
    '''
    bl_idname = 'SvDistancePointPlaneNode'
    bl_label = 'Distance Point Plane'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DISTANCE'

    implentation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("MathUtils", "MathUtils", "MathUtils", 1)]

    compute_distances = {
        "NumPy": compute_distances_np,
        "MathUtils": compute_distances_mu}

    output_numpy = BoolProperty(
        name='Output NumPy', description='Output NumPy arrays',
        default=False, update=updateNode)

    implementation = EnumProperty(
        name='Implementation', items=implentation_modes,
        description='Choose calculation method',
        default="NumPy", update=updateNode)
    
    tolerance = FloatProperty(
        name="Tolerance", description='Intersection tolerance',
        default=1.0e-6, min=0.0, precision=6,
        update=updateNode)

    list_match_global = EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
        
    list_match_local = EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('VerticesSocket', "Verts")
        sinw('VerticesSocket', "Verts Plane")
        sinw('StringsSocket', "Tolerance").prop_name = 'tolerance'

        sonw('StringsSocket', 'Distance')
        sonw('StringsSocket', 'In Triangle')
        sonw('StringsSocket', 'In Plane')
        sonw('VerticesSocket', 'Closest Point')
        sonw('StringsSocket', 'Closest in Triangle')
        sonw('StringsSocket', 'Side')

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", expand=False)
        layout.prop(self, "list_match_local", expand=False)
        
    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

        
    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        return list_match_func[self.list_match_global]([sckt.sv_get(default=[[]]) for sckt in si])

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

        for pts, plane, tolerance in zip(*group):
            if len(tolerance)>1:
                pts, tolerance = match_func([pts, tolerance])
            main_func(plane, pts, result, gates, tolerance)

        for i, r in enumerate(result):
            if gates[i]:
                so[i].sv_set(result[i])


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvDistancePointPlaneNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvDistancePointPlaneNode)
