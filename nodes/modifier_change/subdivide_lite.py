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
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
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

  #  def update_mode(self, context):
  #      self.outputs['NewVertices'].hide_safe = not self.show_new
  #      self.outputs['NewEdges'].hide_safe = not self.show_new
  #      self.outputs['NewFaces'].hide_safe = not self.show_new
  #      self.outputs['OldVertices'].hide_safe = not self.show_old
  #      self.outputs['OldEdges'].hide_safe = not self.show_old
  #      self.outputs['OldFaces'].hide_safe = not self.show_old
  #      updateNode(self, context)

    falloff_type= EnumProperty(name = "Falloff",
            items= falloff_types,
            default= "4",
            update=updateNode)
    corner_type= EnumProperty(name= "Corner Cut Type",
            items= corner_types,
            default= "0",
            update=updateNode)
    cuts= IntProperty(name= "Number of Cuts",
            description= "Specifies the number of cuts per edge to make",
            min=1, default=1,
            update=updateNode)
    smooth= FloatProperty(name= "Smooth",
            description= "Displaces subdivisions to maintain approximate curvature",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    fractal= FloatProperty(name= "Fractal",
            description= "Displaces the vertices in random directions after the mesh is subdivided",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    along_normal= FloatProperty(name= "Along normal",
            description= "Causes the vertices to move along the their normals, instead of random directions",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    seed= IntProperty(name= "Seed",
            description= "Random seed",
            default= 0,
            update=updateNode)
    grid_fill= BoolProperty(name= "Grid fill",
            description= "fill in fully-selected faces with a grid",
            default= True,
            update=updateNode)
    single_edge= BoolProperty(name= "Single edge",
            description= "tessellate the case of one edge selected in a quad or triangle",
            default= False,
            update=updateNode)
    only_quads= BoolProperty(name= "Only Quads",
            description= "only subdivide quads (for loopcut)",
            default= False,
            update=updateNode)
    smooth_even = BoolProperty(name= "Even smooth",
            description= "maintain even offset when smoothing",
            default= False,
            update=updateNode)
   # show_new = BoolProperty(name= "Show New",
   #         description= "Show outputs with new geometry",
   #         default= False,
   #         update=update_mode)
   # show_old = BoolProperty(name= "Show Old",
   #         description= "Show outputs with old geometry",
   #         default= False,
   #         update=update_mode)
    show_options = BoolProperty(name = "Show Options",
            description= "Show options on the node",
            default= False,
            update=updateNode)

    def draw_common(self, context, layout):
        col = layout.column(align=True)
      #  row = col.row(align=True)
      #  row.prop(self, "show_old", toggle=True)
      #  row.prop(self, "show_new", toggle=True)
        col.prop(self, "show_options", toggle=True)

    def draw_options(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "falloff_type")
        col.prop(self, "corner_type")
        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(self, "grid_fill", toggle=True)
        col.prop(self, "single_edge", toggle=True)
        col = row.column(align=True)
        col.prop(self, "only_quads", toggle=True)
        col.prop(self, "smooth_even", toggle=True)

    def draw_buttons(self, context, layout):
        layout.prop(self, "cuts", text="cuts")
        layout.prop(self, "smooth", text="smooth")
        layout.prop(self, "fractal", text="fractal")
        layout.prop(self, "along_normal", text="along_normal")
        layout.prop(self, "seed", text="seed")
        self.draw_common(context, layout)
        if self.show_options:
            self.draw_options(context, layout)

    def draw_buttons_ext(self, context, layout):
        self.draw_common(context, layout)
        self.draw_options(context, layout)

    def sv_init(self, context):
        sin, son = self.inputs.new, self.outputs.new
        sin('VerticesSocket', "Vertices", "Vertices")
        sin('StringsSocket', 'Edges', 'Edges')
        sin('StringsSocket', 'Faces', 'Faces')
        sin('StringsSocket', 'EdgeIndex')
        son('VerticesSocket', 'Vertices')
        son('StringsSocket', 'Edges')
        son('StringsSocket', 'Faces')
     #   son('VerticesSocket', 'NewVertices')
     #   son('StringsSocket', 'NewEdges')
     #   son('StringsSocket', 'NewFaces')
     #   son('VerticesSocket', 'OldVertices')
     #   son('StringsSocket', 'OldEdges')
     #   son('StringsSocket', 'OldFaces')
     #   self.update_mode(context)

  #  def get_result_pydata(self, geom):
  #      new_verts = [v for v in geom if isinstance(v, bmesh.types.BMVert)]
  #      new_edges = [e for e in geom if isinstance(e, bmesh.types.BMEdge)]
  #      new_faces = [f for f in geom if isinstance(f, bmesh.types.BMFace)]
  #      new_verts = [tuple(v.co) for v in new_verts]
  #      new_edges = [[v.index for v in edge.verts] for edge in new_edges]
  #      new_faces = [[v.index for v in face.verts] for face in new_faces]
  #      return new_verts, new_edges, new_faces

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return
        InVert, InEdge, InFace, InEdInd = self.inputs
        OutVert, OutEdg, OutFace = self.outputs    # OutVert, OutEdg, OutFace, ONVert, ONEdg, ONFace, OOVert, OOEdg, OOFace = self.outputs
        vertices_s = InVert.sv_get()
        edges_s = InEdge.sv_get(default=[[]])
        faces_s = InFace.sv_get(default=[[]])
        result_vertices = []
        result_edges = []
        result_faces = []
     #   r_inner_vertices = []
     #   r_inner_edges = []
     #   r_inner_faces = []
     #   r_split_vertices = []
     #   r_split_edges = []
     #   r_split_faces = []
        bmlist= [bmesh_from_pydata(v, e, f, normal_update=True) for v,e,f in zip(vertices_s,edges_s,faces_s)]
        if InEdInd.is_linked:
            useedges = [np.array(bm.edges[:])[masks] for bm, masks in zip(bmlist, InEdInd.sv_get())]
        else:
            useedges = [bm.edges for bm in bmlist]
        for bm,ind in zip(bmlist,useedges):
            geom = bmesh.ops.subdivide_edges(bm, edges= ind,
                    smooth= self.smooth,
                    smooth_falloff= int(self.falloff_type),
                    fractal= self.fractal, along_normal= self.along_normal,
                    cuts= self.cuts, seed= self.seed,
                    quad_corner_type= int(self.corner_type),
                    use_grid_fill= self.grid_fill,
                    use_single_edge= self.single_edge,
                    use_only_quads= self.only_quads,
                    use_smooth_even= self.smooth_even)
            new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
            result_vertices.append(new_verts)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
      #      if self.show_new:
      #          inner_verts, inner_edges, inner_faces = self.get_result_pydata(geom['geom_inner'])
      #          r_inner_vertices.append(inner_verts)
      #          r_inner_edges.append(inner_edges)
      #          r_inner_faces.append(inner_faces)
      #      if self.show_old:
      #          split_verts, split_edges, split_faces = self.get_result_pydata(geom['geom_split'])
      #          r_split_vertices.append(split_verts)
      #          r_split_edges.append(split_edges)
      #          r_split_faces.append(split_faces)
            bm.free()
        OutVert.sv_set(result_vertices)
        OutEdg.sv_set(result_edges)
        OutFace.sv_set(result_faces)
      #  ONVert.sv_set(r_inner_vertices)
      #  ONEdg.sv_set(r_inner_edges)
      #  ONFace.sv_set(r_inner_faces)
      #  OOVert.sv_set(r_split_vertices)
      #  OOEdg.sv_set(r_split_edges)
      #  OOFace.sv_set(r_split_faces)


def register():
    bpy.utils.register_class(SvSubdivideNode)


def unregister():
    bpy.utils.unregister_class(SvSubdivideNode)
