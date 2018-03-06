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
import bmesh
from bmesh.ops import subdivide_edges
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvSubdivideLiteNode(bpy.types.Node, SverchCustomTreeNode):
    '''Subdivide Fast'''

    bl_idname = 'SvSubdivideLiteNode'
    bl_label = 'Subdivide lite'
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

    Sel_modes = [
            ("mask", "by mask", "", 0),
            ("index", "by index", "", 1)
        ]

    def update_mode(self, context):
        self.outputs['NewVertices'].hide_safe = not self.show_new
        self.outputs['NewEdges'].hide_safe = not self.show_new
        self.outputs['NewFaces'].hide_safe = not self.show_new
        self.outputs['OldVertices'].hide_safe = not self.show_old
        self.outputs['OldEdges'].hide_safe = not self.show_old
        self.outputs['OldFaces'].hide_safe = not self.show_old
        updateNode(self, context)

    falloff_type = EnumProperty(name="Falloff",
            items=falloff_types,
            default="4",
            update=updateNode)
    corner_type = EnumProperty(name="Corner Cut Type",
            items=corner_types,
            default="0",
            update=updateNode)
    cuts = IntProperty(name="Number of Cuts",
            description="Specifies the number of cuts per edge to make",
            min=1, default=1,
            update=updateNode)
    smooth = FloatProperty(name="Smooth",
            description="Displaces subdivisions to maintain approximate curvature",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    fractal = FloatProperty(name="Fractal",
            description="Displaces the vertices in random directions after the mesh is subdivided",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    along_normal = FloatProperty(name="Along normal",
            description="Causes the vertices to move along the their normals, instead of random directions",
            min=0.0, max=1.0, default=0.0,
            update=updateNode)
    seed = IntProperty(name="Seed",
            description="Random seed",
            default=0,
            update=updateNode)
    grid_fill = BoolProperty(name="Grid fill",
            description="fill in fully-selected faces with a grid",
            default=True,
            update=updateNode)
    single_edge = BoolProperty(name="Single edge",
            description="tessellate the case of one edge selected in a quad or triangle",
            default=False,
            update=updateNode)
    only_quads = BoolProperty(name="Only Quads",
            description="only subdivide quads (for loopcut)",
            default=False,
            update=updateNode)
    smooth_even = BoolProperty(name="Even smooth",
            description="maintain even offset when smoothing",
            default=False,
            update=updateNode)
    show_new = BoolProperty(name="Show New",
            description="Show outputs with new geometry",
            default=False,
            update=update_mode)
    show_old = BoolProperty(name="Show Old",
            description="Show outputs with old geometry",
            default=False,
            update=update_mode)
    show_options = BoolProperty(name="Show Options",
            description="Show options on the node",
            default=False,
            update=updateNode)
    sel_mode = EnumProperty(name="Select Edges",
            items=Sel_modes,
            default="mask",
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "show_options", toggle=True)
        if self.show_options:
            col = layout.column(align=True)
            row = col.row(align=True)
            col.prop(self, "cuts", text="cuts")
            col.prop(self, "smooth", text="smooth")
            col.prop(self, "fractal", text="fractal")
            col.prop(self, "along_normal", text="along_normal")
            col.prop(self, "seed", text="seed")
            row.prop(self, "show_old", toggle=True)
            row.prop(self, "show_new", toggle=True)
            col.prop(self, "sel_mode")
            col.prop(self, "falloff_type")
            col.prop(self, "corner_type")
            col.prop(self, "grid_fill", toggle=True)
            col.prop(self, "single_edge", toggle=True)
            col.prop(self, "only_quads", toggle=True)
            col.prop(self, "smooth_even", toggle=True)

    def sv_init(self, context):
        sin, son = self.inputs.new, self.outputs.new
        sin('VerticesSocket', 'Vertices')
        sin('StringsSocket',  'edg_pol')
        sin('StringsSocket',  'Selection')
        son('VerticesSocket', 'Vertices')
        son('StringsSocket',  'Edges')
        son('StringsSocket',  'Faces')
        son('VerticesSocket', 'NewVertices')
        son('StringsSocket',  'NewEdges')
        son('StringsSocket',  'NewFaces')
        son('VerticesSocket', 'OldVertices')
        son('StringsSocket',  'OldEdges')
        son('StringsSocket',  'OldFaces')
        self.update_mode(context)

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return
        InVert, InEdge, InEdSel = self.inputs
        OutVert, OutEdg, OutFace, ONVert, ONEdg, ONFace, OOVert, OOEdg, OOFace = self.outputs
        vertices_s = InVert.sv_get()
        topo = InEdge.sv_get()
        if len(topo[0][0]) == 2:
            bmlist= [bmesh_from_pydata(v, e, [], normal_update=True) for v,e in zip(vertices_s,topo)]
        else:
            bmlist= [bmesh_from_pydata(v, [], e, normal_update=True) for v,e in zip(vertices_s,topo)]
        rev, ree, ref, riv, rie, rif, rsv, rse, rsf = [],[],[],[],[],[],[],[],[]
        if InEdSel.is_linked:
            if self.sel_mode == "index":
                useedges = [np.array(bm.edges[:])[idxs] for bm, idxs in zip(bmlist, InEdSel.sv_get())]
            elif self.sel_mode == "mask":
                useedges = [np.extract(mask, bm.edges[:]) for bm, mask in zip(bmlist, InEdSel.sv_get())]
        else:
            useedges = [bm.edges for bm in bmlist]
        for bm,ind in zip(bmlist,useedges):
            geom = subdivide_edges(bm, edges=ind,
                    smooth=self.smooth,
                    smooth_falloff=int(self.falloff_type),
                    fractal=self.fractal, along_normal=self.along_normal,
                    cuts=self.cuts, seed=self.seed,
                    quad_corner_type=int(self.corner_type),
                    use_grid_fill=self.grid_fill,
                    use_single_edge=self.single_edge,
                    use_only_quads=self.only_quads,
                    use_smooth_even=self.smooth_even)
            new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
            rev.append(new_verts)
            ree.append(new_edges)
            ref.append(new_faces)
            if self.show_new:
                geo1 = geom['geom_inner']
                riv.append([tuple(v.co) for v in geo1 if isinstance(v, bmesh.types.BMVert)])
                rie.append([[v.index for v in e.verts] for e in geo1 if isinstance(e, bmesh.types.BMEdge)])
                rif.append([[v.index for v in f.verts] for f in geo1 if isinstance(f, bmesh.types.BMFace)])
            if self.show_old:
                geo2 = geom['geom_split']
                rsv.append([tuple(v.co) for v in geo2 if isinstance(v, bmesh.types.BMVert)])
                rse.append([[v.index for v in e.verts] for e in geo2 if isinstance(e, bmesh.types.BMEdge)])
                rsf.append([[v.index for v in f.verts] for f in geo2 if isinstance(f, bmesh.types.BMFace)])
            bm.free()
        OutVert.sv_set(rev)
        OutEdg.sv_set(ree)
        OutFace.sv_set(ref)
        ONVert.sv_set(riv)
        ONEdg.sv_set(rie)
        ONFace.sv_set(rif)
        OOVert.sv_set(rsv)
        OOEdg.sv_set(rse)
        OOFace.sv_set(rsf)


def register():
    bpy.utils.register_class(SvSubdivideLiteNode)


def unregister():
    bpy.utils.unregister_class(SvSubdivideLiteNode)
