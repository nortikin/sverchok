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

import numpy as np
from collections import defaultdict

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.voronoi3d import voronoi_on_solid
from sverchok.utils.geom import scale_relative
from sverchok.utils.solid import svmesh_to_solid, SvSolidTopology
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy, FreeCAD

if scipy is None or FreeCAD is None:
    add_dummy('SvVoronoiOnSolidNode', "Voronoi on Solid", 'scipy and FreeCAD')

if FreeCAD is not None:
    import Part

def mesh_from_faces(fragments):
    verts = [(v.X, v.Y, v.Z) for v in fragments.Vertexes]

    all_fc_verts = {SvSolidTopology.Item(v) : i for i, v in enumerate(fragments.Vertexes)}
    def find_vertex(v):
        #for i, fc_vert in enumerate(fragments.Vertexes):
        #    if v.isSame(fc_vert):
        #        return i
        #return None
        return all_fc_verts[SvSolidTopology.Item(v)]

    edges = []
    for fc_edge in fragments.Edges:
        edge = [find_vertex(v) for v in fc_edge.Vertexes]
        if len(edge) == 2:
            edges.append(edge)

    faces = []
    for fc_face in fragments.Faces:
        incident_verts = defaultdict(set)
        for fc_edge in fc_face.Edges:
            edge = [find_vertex(v) for v in fc_edge.Vertexes]
            if len(edge) == 2:
                i, j = edge
                incident_verts[i].add(j)
                incident_verts[j].add(i)

        face = [find_vertex(v) for v in fc_face.Vertexes]

        vert_idx = face[0]
        correct_face = [vert_idx]

        for i in range(len(face)):
            incident = list(incident_verts[vert_idx])
            other_verts = [i for i in incident if i not in correct_face]
            if not other_verts:
                break
            other_vert_idx = other_verts[0]
            correct_face.append(other_vert_idx)
            vert_idx = other_vert_idx

        if len(correct_face) > 2:
            faces.append(correct_face)

    return verts, edges, faces

class SvVoronoiOnSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi Solid
    Tooltip: Generate Voronoi diagram on the Solid object
    """
    bl_idname = 'SvVoronoiOnSolidNode'
    bl_label = 'Voronoi on Solid'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    modes = [
            ('FACES', "Surface - Inner", "Generate inner regions of Voronoi diagram on the surface of the solid", 0),
            ('WIRE', "Surface - Outer", "Cut inner regions of Voronoi diagram from solid surface", 1),
            ('REGIONS', "Volume", "Split volume of the solid body into regions of Voronoi diagram", 2),
            ('NEGVOLUME', "Negative Volume", "Cut regions of Voronoi diagram from the volume of the solid object", 3),
            ('MESH', "Mesh Faces", "Generate mesh", 4)
        ]

    @throttle_and_update_node
    def update_sockets(self, context):
        self.outputs['Vertices'].hide_safe = self.mode != 'MESH'
        self.outputs['Edges'].hide_safe = self.mode != 'MESH'
        self.outputs['Faces'].hide_safe = self.mode != 'MESH'
        self.outputs['Solids'].hide_safe = self.mode not in {'FACES', 'WIRE', 'REGIONS', 'NEGVOLUME'}

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        update = update_sockets)
    
    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh to solid transformation",
            default = 6,
            min = 1,
            update = updateNode)

    inset : FloatProperty(
        name = "Inset",
        min = 0.0, max = 1.0,
        default = 0.0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', 'Solid')
        self.inputs.new('SvVerticesSocket', "Sites")
        self.inputs.new('SvStringsSocket', "Inset").prop_name = 'inset'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvSolidSocket', "Solids")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        solid_in = self.inputs['Solid'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        inset_in = self.inputs['Inset'].sv_get()

        solid_in = ensure_nesting_level(solid_in, 2, data_types=(Part.Shape,))
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        inset_in = ensure_nesting_level(inset_in, 2)

        nested_output = input_level > 3

        precision = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        fragment_faces_out = []
        for params in zip_long_repeat(solid_in, sites_in, inset_in):
            new_verts = []
            new_edges = []
            new_faces = []
            new_fragment_faces = []
            for solid, sites, inset in zip_long_repeat(*params):
                verts, edges, faces = voronoi_on_solid(solid, sites,
                            do_clip=True, clipping=None)

                if inset != 0.0:
                    scale = 1.0 - inset
                    verts = [scale_relative(vs, site, scale) for vs, site in zip(verts, sites)]

                fragments = [svmesh_to_solid(vs, fs, precision) for vs, fs in zip(verts, faces)]

                if solid.Shells:
                    shell = solid.Shells[0]
                else:
                    shell = Part.Shell(solid.Faces)

                if self.mode == 'FACES':
                    fragments = [shell.common(fragment) for fragment in fragments]
                elif self.mode == 'WIRE':
                    fragments = [shell.cut(fragments)]
                elif self.mode == 'REGIONS':
                    fragments = [solid.common(fragment) for fragment in fragments]
                elif self.mode == 'NEGVOLUME':
                    fragments = [solid.cut(fragments)]
                else: # MESH
                    fragments = shell.common(fragments)

                if self.mode in {'FACES', 'WIRE', 'REGIONS', 'NEGVOLUME'}:
                    new_fragment_faces.append(fragments)
                else: # MESH
                    verts, edges, faces = mesh_from_faces(fragments)

                new_verts.append(verts)
                new_edges.append(edges)
                new_faces.append(faces)

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
                fragment_faces_out.append(new_fragment_faces)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                fragment_faces_out.extend(new_fragment_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['Solids'].sv_set(fragment_faces_out)

def register():
    if scipy is not None and FreeCAD is not None:
        bpy.utils.register_class(SvVoronoiOnSolidNode)

def unregister():
    if scipy is not None and FreeCAD is not None:
        bpy.utils.unregister_class(SvVoronoiOnSolidNode)

