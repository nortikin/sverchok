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

from collections import defaultdict

import bpy
import bmesh
import mathutils
from bpy.props import BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode


class SvCutObjBySurfaceNode(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Cut object edges by surface
    Tooltip: Cut object's edges by surface
    """
    bl_idname = 'SvCutObjBySurfaceNode'
    bl_label = 'Cut Object by Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CUT'

    def update_sockets(self, context):
        self.inputs['FillSides'].hide_safe = not self.fill
        self.outputs['ObjVertices'].hide_safe = not self.make_pieces
        self.outputs['ObjEdges'].hide_safe = not self.make_pieces
        self.outputs['ObjFaces'].hide_safe = not self.make_pieces
        updateNode(self, context)

    fill: BoolProperty(
        name='Make cut faces',
        description='Fill cuts',
        default=False,
        update = update_sockets)

    fill_sides: IntProperty(
        name = "Cut sides",
        description = "Maximum number of cut face sides",
        default = 12,
        update = updateNode)

    make_pieces: BoolProperty(
        name = "Make cut pieces",
        description = "Output cut pieces",
        default=False,
        update = update_sockets)
        
    triangles: BoolProperty(
        name="All triangles",
        description="If your input mesh consists of triangles only, then this mode can improve performance a lot", default=False,
        update=updateNode)
        
    block: BoolProperty(
        name="Block",
        description="Whether to raise exception or not when more than two intersections are found on one object face", default=False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'ObjVertices')
        self.inputs.new('SvStringsSocket', 'ObjEdges')
        self.inputs.new('SvStringsSocket', 'ObjFaces')
        self.inputs.new('SvVerticesSocket', 'SurfVertices')
        self.inputs.new('SvStringsSocket', 'SurfEdges')
        self.inputs.new('SvStringsSocket', 'SurfFaces')
        self.inputs.new('SvStringsSocket', 'FillSides').prop_name = 'fill_sides'

        self.outputs.new('SvVerticesSocket', 'CutVertices')
        self.outputs.new('SvStringsSocket', 'CutEdges')
        self.outputs.new('SvStringsSocket', 'CutFaces')
        self.outputs.new('SvVerticesSocket', 'ObjVertices')
        self.outputs.new('SvStringsSocket', 'ObjEdges')
        self.outputs.new('SvStringsSocket', 'ObjFaces')

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "fill", toggle=True)
        col.prop(self, "make_pieces", toggle=True)
        
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "triangles")
        layout.prop(self, "block")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        obj_vertices_s = self.inputs['ObjVertices'].sv_get()
        obj_edges_s = self.inputs['ObjEdges'].sv_get(default=[[]])
        obj_faces_s = self.inputs['ObjFaces'].sv_get()
        surf_vertices_s = self.inputs['SurfVertices'].sv_get()
        surf_edges_s = self.inputs['SurfEdges'].sv_get(default=[[]])
        surf_faces_s = self.inputs['SurfFaces'].sv_get()
        fill_sides_s = self.inputs['FillSides'].sv_get()

        def remember_connection(edges_by_face, bm_edge, bm_intersection):
            for face in bm_edge.link_faces:
                edges_by_face[face].append((bm_intersection, bm_edge.index))

        cut_verts_out = []
        cut_edges_out = []
        cut_faces_out = []
        obj_verts_out = []
        obj_edges_out = []
        obj_faces_out = []
        inputs = zip_long_repeat(obj_vertices_s, obj_edges_s, obj_faces_s, surf_vertices_s, surf_edges_s, surf_faces_s, fill_sides_s)
        for obj_vertices, obj_edges, obj_faces, surf_vertices, surf_edges, surf_faces, fill_sides in inputs:
            if self.fill:
                if isinstance(fill_sides, (list, tuple)):
                    fill_sides = fill_sides[0]

            # We are using bvh's raycast to calculate intersections of object's edges
            # with the surface.
            bvh = mathutils.bvhtree.BVHTree.FromPolygons(surf_vertices, surf_faces, all_triangles = self.triangles)
            bm_obj = bmesh_from_pydata(obj_vertices, obj_edges, obj_faces)
            bm_cut = bmesh.new()
            edges_by_face = defaultdict(list)
            bm_obj.verts.index_update()
            bm_obj.edges.index_update()
            for bm_edge in bm_obj.edges:
                v1, v2 = bm_edge.verts
                edge = v2.co - v1.co
                # Distance restriction is used to find only intersections which are within the edge,
                # not anywhere on the ray.
                length = edge.length
                if length :
                    normalized_edge = edge/length
                    distance_limit = length
                    cast = bvh.ray_cast(v1.co, edge, distance_limit)
                    # self.debug("Edge %s: %s -> %s, Cast 0: %s", bm_edge.index, v1.co, edge, cast)
                    intersection = cast[0]
                    distance = cast[3]
                    # We keep raycasting further down the edge until we reach the other extremity
                    while intersection is not None:
                        bm_intersection = bm_cut.verts.new(intersection)
                        remember_connection(edges_by_face, bm_edge, bm_intersection)
                        # To avoid endlessly detecting the same intersection point,
                        # we set the new start point slightly further down the edge
                        # from the previous intersection point.
                        # We calculate this new start from the origin of the edge instead of the previous intersection point
                        # in order to avoid progressive divergence due to float precision limitation
                        # If multiple points end up being detected for a single intersection,
                        # it may be due to float imprecision,
                        # so a solution is to check if the point detected is really on the edge,
                        # i. e. the angle between (v1, point) and normalized_edge is small enough,
                        # and to ignore it if not.
                        distance_limit -= distance
                        start = v1.co + normalized_edge*(length - distance_limit + 1e-6)
                        distance_limit -= 1e-6
                        cast = bvh.ray_cast(start, edge, distance_limit)
                        intersection = cast[0]
                        distance = cast[3]

            bm_cut.verts.index_update()

            # Make "cut surface" object.
            # Of each object's face we are cutting, make an edge.
            bm_cut_edges = []
            for intersections in edges_by_face.values():
                if len(intersections) != 2:
                    # self.debug("More or less than two intersection between object face's edges and surface")
                    
                    # Idea on how to deal with any number of intersections :
                    # Intersect (project with raycast) each edge of the object with the surface mesh (already done)
                    # Intersect each edge of the surface with the object mesh
                    # For each intersection point, memorize to which faces it belongs,
                    # i. e. the faces linked by the edge, and the face intersected by the edge
                    # Save that information in a structure allowing easy access by faces
                    # For each pair of (face from the object, face from the surface),
                    # consider all the intersection points that belongs to both of them
                    # There should be an even number of them, forming a line.
                    # Link them two by two with an edge, starting from one extremity (1 with 2, 3 with 4, etc...)
                    # Now, all the new edges should form rings, which can then be used to cut the surface and object meshes,
                    # as we know which of their original edges/faces are concerned by which new edges
                    # Finally, for each object part, the cut surface within the corresponding ring
                    # is merged by distance with the part
                    
                    # This works in the general cases, but there are still a few corner cases to deal with :
                    # If the surface and the object do not fully intersect each other,
                    # i. e. there are new edges not included in any rings
                    # If the surface or the object has wire geometry, or has more than two faces linked to an edge,
                    # or has vertices linked to multiple mesh regions (see Blender select non manifold function)
                    if self.block:
                        raise Exception("Unsupported: more than two edges of the face intersect the surface")
                    else:
                        continue
                v1, v2 = intersections[0][0], intersections[1][0]
                try:
                    bm_edge = bm_cut.edges.new((v1, v2))
                    bm_cut_edges.append(bm_edge)
                except ValueError:
                    continue

            if len(bm_cut.verts) > 0:
                if self.fill:
                    bmesh.ops.holes_fill(bm_cut, edges=bm_cut_edges, sides=fill_sides)

            new_verts_cut, new_edges_cut, new_faces_cut = pydata_from_bmesh(bm_cut)

            if self.make_pieces:
                new_verts_by_old_edge = dict()
                new_verts_by_old_face = dict()
                for old_obj_face in edges_by_face:
                    intersections = edges_by_face[old_obj_face]
                    if len(intersections) != 2:
                        continue
                    int1, int2 = intersections 
                    intersection1, intersection2 = int1[0].co, int2[0].co
                    old_edge1, old_edge2 = int1[1], int2[1]
                    # Create a vertex in the "object" mesh at each intersection of
                    # it's edge with the surface.
                    # Remember which of new vertices corresponds to which edge.
                    if old_edge1 not in new_verts_by_old_edge:
                        new_vert_1 = bm_obj.verts.new(intersection1)
                        new_verts_by_old_edge[old_edge1] = new_vert_1
                    else:
                        new_vert_1 = new_verts_by_old_edge[old_edge1]
                    if old_edge2 not in new_verts_by_old_edge:
                        new_vert_2 = bm_obj.verts.new(intersection2)
                        new_verts_by_old_edge[old_edge2] = new_vert_2
                    else:
                        new_vert_2 = new_verts_by_old_edge[old_edge2]
                    new_verts_by_old_face[old_obj_face] = (new_vert_1, new_vert_2)
                    bm_obj.verts.index_update()

                faces_to_remove = []
                edges_to_remove = []
                for old_obj_face in edges_by_face:
                    intersections = edges_by_face[old_obj_face]
                    if len(intersections) != 2:
                        continue

                    # Walk through the edges of each face we are cutting, in order.
                    # Of each such face, we are making two. So in this loop we have
                    # two states: new_face_state == True means we are on the one side of
                    # the cut, False means we are on the another. Note that we do not know
                    # which is which (for example, which one is "inside" the surface); but
                    # it does not matter for us.
                    # So new_face_verts[True] will contain vertices of one piece,
                    # new_face_verts[False] - of another one.
                    new_face_verts = defaultdict(list)
                    new_face_side = True
                    old_vert_pairs = list(zip(old_obj_face.verts, old_obj_face.verts[1:])) + [(old_obj_face.verts[-1], old_obj_face.verts[0])]
                    need_split = False
                    for old_vert_1, old_vert_2 in old_vert_pairs:
                        old_edge = bm_obj.edges.get((old_vert_1, old_vert_2))
                        if old_edge.index in new_verts_by_old_edge:
                            edges_to_remove.append((old_edge.verts[0], old_edge.verts[1]))
                            need_split = True
                            new_vert_1 = new_verts_by_old_edge[old_edge.index]
                            # self.debug("Old edge %s - %s is to be split; use new vert %s", old_vert_1.index, old_vert_2.index, new_vert_1.index)
                            new_face_verts[new_face_side].append(new_vert_1)
                            # if this edge is to be split, then we are stepping from one piece of
                            # the face to another
                            new_face_side = not new_face_side
                            new_face_verts[new_face_side].append(new_vert_1)
                            new_face_verts[new_face_side].append(old_vert_2)
                        else:
                            # self.debug("Old edge %s - %s is not to be split", old_vert_1.index, old_vert_2.index)
                            new_face_verts[new_face_side].append(old_vert_2)

                    if need_split:
                        faces_to_remove.append(old_obj_face)
                        # self.debug("Splitting face: %s", [v.index for v in old_obj_face.verts])
                        for new_face_list in new_face_verts.values():
                            try:
                                bm_obj.faces.new(new_face_list)
                            except TypeError:
                                continue

                # remove old faces and edges (ones we cut in two)
                for old_face in faces_to_remove:
                    bm_obj.faces.remove(old_face)
                for old_v1, old_v2 in edges_to_remove:
                    # we can't just remember BMEdge instances themselves,
                    # since they will be invalidated when we remove faces.
                    old_edge = bm_obj.edges.get((old_v1, old_v2))
                    if old_edge:
                        bm_obj.edges.remove(old_edge)

                edges_to_split = []
                for new_vert_1, new_vert_2 in new_verts_by_old_face.values():
                    try:
                        edge = bm_obj.edges.get((new_vert_1, new_vert_2))
                        edges_to_split.append(edge)
                    except ValueError:
                        continue
                    
                # Split "object" by remembered cut edges. There will be "holes"
                # at places we cut.
                split_result = bmesh.ops.split_edges(bm_obj, edges=edges_to_split)
                if self.fill:
                    bmesh.ops.holes_fill(bm_obj, edges = split_result['edges'], sides=fill_sides)

                new_verts_obj, new_edges_obj, new_faces_obj = pydata_from_bmesh(bm_obj)
            else:
                new_verts_obj, new_edges_obj, new_faces_obj = [], [], []

            bm_cut.free()
            bm_obj.free()

            cut_verts_out.append(new_verts_cut)
            cut_edges_out.append(new_edges_cut)
            cut_faces_out.append(new_faces_cut)
            obj_verts_out.append(new_verts_obj)
            obj_edges_out.append(new_edges_obj)
            obj_faces_out.append(new_faces_obj)

        self.outputs['CutVertices'].sv_set(cut_verts_out)
        self.outputs['CutEdges'].sv_set(cut_edges_out)
        self.outputs['CutFaces'].sv_set(cut_faces_out)
        self.outputs['ObjVertices'].sv_set(obj_verts_out)
        self.outputs['ObjEdges'].sv_set(obj_edges_out)
        self.outputs['ObjFaces'].sv_set(obj_faces_out)

def register():
    bpy.utils.register_class(SvCutObjBySurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvCutObjBySurfaceNode)

