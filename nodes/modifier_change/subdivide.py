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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList, Matrix_generate
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvSubdivideNode(bpy.types.Node, SverchCustomTreeNode):
    '''Subdivide'''
    
    bl_idname = 'SvSubdivideNode'
    bl_label = 'Subdivide'
    bl_icon = 'OUTLINER_OB_EMPTY'

    falloff_types = [
            ("0", "Smooth", "", 'SMOOTHCURVE', 0),
            ("1", "Sphere", "", 'SPHERECURVE', 1),
            ("2", "Root", "", 'ROOTCURVE', 2),
            ("3", "Sharp", "", 'SHARPCURVE', 3),
            ("4", "Linear", "", 'LINCURVE', 4),
            ("7", "Inverse Square", "", 'ROOTCURVE', 7)
        ]

    corner_types = [
            ("0", "Inner Vertices", "", 0),
            ("1", "Path", "", 1),
            ("2", "Fan", "", 2),
            ("3", "Straight Cut", "", 3)
        ]

    def update_mode(self, context):
        updateNode(self, context)

    falloff_type = EnumProperty(name = "Falloff",
            items = falloff_types,
            default = "4",
            update=update_mode)
    corner_type = EnumProperty(name = "Corner Cut Type",
            items = corner_types,
            default = "0",
            update=update_mode)

    cuts = IntProperty(name = "Number of Cuts",
            description = "Specifies the number of cuts per edge to make",
            min=1, default=1,
            update=updateNode)
    smooth = FloatProperty(name = "Smooth",
            description = "Displaces subdivisions to maintain approximate curvature",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    fractal = FloatProperty(name = "Fractal",
            description = "Displaces the vertices in random directions after the mesh is subdivided",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    along_normal = FloatProperty(name = "Along normal",
            description = "Causes the vertices to move along the their normals, instead of random directions",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    seed = IntProperty(name = "Seed",
            description = "Random seed",
            default = 0,
            update=updateNode)
    grid_fill = BoolProperty(name = "Grid fill",
            description = "fill in fully-selected faces with a grid",
            default = True,
            update=updateNode)
    single_edge = BoolProperty(name = "Single edge",
            description = "tessellate the case of one edge selected in a quad or triangle",
            default = False,
            update=updateNode)
    only_quads = BoolProperty(name = "Only Quads",
            description = "only subdivide quads (for loopcut)",
            default = False,
            update=updateNode)
    smooth_even = BoolProperty(name = "Even smooth",
            description = "maintain even offset when smoothing",
            default = False,
            update=updateNode)

    def draw_buttons(self, context, layout):
        pass

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "falloff_type")
        layout.prop(self, "corner_type")

        col = layout.column()
        col.prop(self, "grid_fill")
        col.prop(self, "single_edge")
        col.prop(self, "only_quads")
        col.prop(self, "smooth_even")

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('StringsSocket', 'Faces', 'Faces')
        self.inputs.new('StringsSocket', 'EdgeMask')

        self.inputs.new('StringsSocket', 'Cuts').prop_name = "cuts"
        self.inputs.new('StringsSocket', 'Smooth').prop_name = "smooth"
        self.inputs.new('StringsSocket', 'Fractal').prop_name = "fractal"
        self.inputs.new('StringsSocket', 'AlongNormal').prop_name = "along_normal"
        self.inputs.new('StringsSocket', 'Seed').prop_name = "seed"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Faces')

        self.update_mode(context)

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['EdgeMask'].sv_get(default=[[1]])

        cuts_s = self.inputs['Cuts'].sv_get()[0]
        smooth_s = self.inputs['Smooth'].sv_get()[0]
        fractal_s = self.inputs['Fractal'].sv_get()[0]
        along_normal_s = self.inputs['AlongNormal'].sv_get()[0]
        seed_s = self.inputs['Seed'].sv_get()[0]

        result_vertices = []
        result_edges = []
        result_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, cuts_s, smooth_s, fractal_s, along_normal_s, seed_s])
        for vertices, edges, faces, masks, cuts, smooth, fractal, along_normal, seed in zip(*meshes):
            fullList(masks,  len(edges))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)

            selected_edges = []
            for m, edge in zip(masks, edges):
                if not m:
                    continue
                found = False
                for bmesh_edge in bm.edges:
                    if set(v.index for v in bmesh_edge.verts) == set(edge):
                        found = True
                        break
                if found:
                    selected_edges.append(bmesh_edge)
                else:
                    print("Cant find edge: " + str(edge))

            geom = bmesh.ops.subdivide_edges(bm, edges = selected_edges,
                    smooth = smooth,
                    smooth_falloff = int(self.falloff_type),
                    fractal = fractal, along_normal = along_normal,
                    cuts = cuts, seed = seed,
                    use_grid_fill = self.grid_fill,
                    use_single_edge = self.single_edge,
                    use_only_quads = self.only_quads,
                    use_smooth_even = self.smooth_even)
            new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()

            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Faces'].sv_set(result_faces)


def register():
    bpy.utils.register_class(SvSubdivideNode)


def unregister():
    bpy.utils.unregister_class(SvSubdivideNode)

