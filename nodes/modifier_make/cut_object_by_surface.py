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
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvCutObjBySurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Cut object by surface
    Tooltip: Cut object's edges by surface
    """
    bl_idname = 'SvCutObjBySurfaceNode'
    bl_label = 'Cut by Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CUT'

    @throttled
    def update_sockets(self, context):
        self.inputs['FillSides'].hide_safe = not self.fill
        self.outputs['ObjVertices'].hide_safe = not self.make_pieces
        self.outputs['ObjEdges'].hide_safe = not self.make_pieces
        self.outputs['ObjFaces'].hide_safe = not self.make_pieces

    fill: BoolProperty(
        name='Make cut faces',
        description='Fill cuts',
        default=False,
        update = update_sockets)

    fill_sides : IntProperty(
        name = "Cut sides",
        description = "Maximum number of cut face sides",
        default = 12,
        update = updateNode)

    make_pieces : BoolProperty(
        name = "Make cut pieces",
        description = "Output cut pieces",
        default=False,
        update = update_sockets)

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

            bvh = mathutils.bvhtree.BVHTree.FromPolygons(surf_vertices, surf_faces)
            bm_obj = bmesh_from_pydata(obj_vertices, obj_edges, obj_faces)
            bm_cut = bmesh.new()
            edges_by_face = defaultdict(list)
            bm_obj.verts.index_update()
            bm_obj.edges.index_update()
            for bm_edge in bm_obj.edges:
                v1, v2 = bm_edge.verts
                edge = v1.co - v2.co
                distance = edge.length

                cast = bvh.ray_cast(v1.co, -edge, distance)
                #self.debug("Edge %s: %s -> %s, Cast 0: %s", bm_edge.index, v1.co, edge, cast)
                intersection = cast[0]
                if intersection is not None: 
                    bm_intersection = bm_cut.verts.new(intersection)
                    remember_connection(edges_by_face, bm_edge, bm_intersection)
                else:
                    cast = bvh.ray_cast(v2.co, edge, distance)
                    #self.debug("Edge %s: %s -> %s, Cast 1: %s", bm_edge.index, v2.co, -edge, cast)
                    intersection = cast[0]
                    if intersection is not None: 
                        bm_intersection = bm_cut.verts.new(intersection)
                        remember_connection(edges_by_face, bm_edge, bm_intersection)

            bm_cut.verts.index_update()

            bm_cut_edges = []
            for intersections in edges_by_face.values():
                if len(intersections) == 1:
                    self.debug("Only one of object face's edges intersects the surface")
                    continue
                if len(intersections) > 2:
                    raise Exception("Unsupported: more than two edges of the face intersect the surface")
                v1, v2 = intersections[0][0], intersections[1][0]
                bm_edge = bm_cut.edges.new((v1, v2))
                bm_cut_edges.append(bm_edge)

            if len(bm_cut.verts) > 0:
                if self.fill:
                    bmesh.ops.holes_fill(bm_cut, edges=bm_cut_edges, sides=fill_sides)

            new_verts_cut, new_edges_cut, new_faces_cut = pydata_from_bmesh(bm_cut)

            if self.make_pieces:
                new_verts_by_old_edge = dict()
                new_verts_by_old_face = dict()
                for old_obj_face in edges_by_face:
                    intersections = edges_by_face[old_obj_face]
                    if len(intersections) == 1:
                        continue
                    int1, int2 = intersections 
                    intersection1, intersection2 = int1[0].co, int2[0].co
                    old_edge1, old_edge2 = int1[1], int2[1]
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
                    if len(intersections) == 1:
                        continue

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
                            self.debug("Old edge %s - %s is to be split; use new vert %s", old_vert_1.index, old_vert_2.index, new_vert_1.index)
                            #new_face_verts[new_face_side].append(old_vert_1)
                            new_face_verts[new_face_side].append(new_vert_1)
                            #self.debug("new_face_verts[%s].append(%s)", new_face_side, new_vert_1.index)
                            new_face_side = not new_face_side
                            new_face_verts[new_face_side].append(new_vert_1)
                            #self.debug("new_face_verts[%s].append(%s)", new_face_side, new_vert_2.index)
                            new_face_verts[new_face_side].append(old_vert_2)
                            #self.debug("new_face_verts[%s].append(%s)", new_face_side, old_vert_2.index)
                        else:
                            self.debug("Old edge %s - %s is not to be split", old_vert_1.index, old_vert_2.index)
                            #new_face_verts[new_face_side].append(old_vert_1)
                            new_face_verts[new_face_side].append(old_vert_2)

                    if need_split:
                        faces_to_remove.append(old_obj_face)
                        self.debug("Splitting face: %s", [v.index for v in old_obj_face.verts])
                        for new_face_list in new_face_verts.values():
                            print(new_face_list)
                            bm_obj.faces.new(new_face_list)

                for old_face in faces_to_remove:
                    bm_obj.faces.remove(old_face)
                for old_v1, old_v2 in edges_to_remove:
                    old_edge = bm_obj.edges.get((old_v1, old_v2))
                    if old_edge:
                        bm_obj.edges.remove(old_edge)

                edges_to_split = []
                for new_vert_1, new_vert_2 in new_verts_by_old_face.values():
                    edge = bm_obj.edges.get((new_vert_1, new_vert_2))
                    edges_to_split.append(edge)

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

