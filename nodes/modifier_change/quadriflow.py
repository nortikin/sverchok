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

# Implements the QuadriFlow Node 
# sverchok/nodes/modifier_change/quadriflow.py

import bpy
import bmesh
from bpy.props import IntProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, flatten_data
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

enable_module = False
try:
    import pyQuadriFlow
    from pyQuadriFlow.pyQuadriFlow import pyquadriflow
    enable_module = True
except ModuleNotFoundError:
    enable_module = False

from itertools import chain 
import traceback 
class SvQuadriFlowNode(bpy.types.Node,SverchCustomTreeNode):
    bl_idname = "SvQuadriFlowNode" # Use this for index.md reference 
    bl_label = "Quadriflow"
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = None

    sv_dependencies = ['pyQuadriFlow']

    #maxSubdivision = 6 # creates a self.maxSubdivision attribute 
    flag_preserve_sharp : BoolProperty(
        name = "Preserve Sharp",
        description = "Try to preserve sharp features on the mesh",
        default = False,
        update = updateNode) # type: ignore

    flag_preserve_boundary : BoolProperty(
        name = "Preserve Mesh Boundary",
        description = "Try to preserve mesh boundary on the mesh",
        default = False,
        update = updateNode) # type: ignore

    flag_adaptive_scale : BoolProperty(
        name = "Preserve Adaptive Scale",
        description = "???",
        default = False,
        update = updateNode) # type: ignore

    flag_aggresive_sat : BoolProperty(
        name = "Preserve Aggresive Sat",
        description = "???",
        default = False,
        update = updateNode) # type: ignore

    flag_minimum_cost_flow : BoolProperty(
        name = "Minimum Cost Flow",
        description = "???",
        default = False,
        update = updateNode) # type: ignore
    
    quad_modes = [
        (    "BEAUTY",            "Beauty", "Split the quads in nice triangles, slower method", 1),
        (     "FIXED",             "Fixed", "Split the quads on the 1st and 3rd vertices", 2),
        ( "ALTERNATE",   "Fixed Alternate", "Split the quads on the 2nd and 4th vertices", 3),
        ("SHORT_EDGE", "Shortest Diagonal", "Split the quads based on the distance between the vertices", 4)
    ]

    ngon_modes = [
        (  "BEAUTY", "Beauty", "Arrange the new triangles nicely, slower method", 1),
        ("EAR_CLIP",   "Clip", "Split the ngons using a scanfill algorithm", 2)
    ]

    quad_mode: EnumProperty(
        name='Quads mode',
        description="Quads processing mode",
        items=quad_modes,
        default="BEAUTY",
        update=updateNode) # type: ignore

    ngon_mode: EnumProperty(
        name="Polygons mode",
        description="Polygons processing mode",
        items=ngon_modes,
        default="BEAUTY",
        update=updateNode) # type: ignore
    

    # Mute Node Implementation 
    @property
    def sv_internal_links(self):
        mapping =  [
            (self.inputs['Vertices'],self.outputs['Vertices']),
            (self.inputs['Faces'],self.outputs['Faces'])
        ]        
        return mapping 

    def sv_init(self,context):
        self.width = 200
        self.inputs.new('SvVerticesSocket', "vertices")
        #self.inputs.new('SvVerticesSocket', "Edges")
        self.inputs.new('SvStringsSocket', "faces")
        self.inputs["vertices"].label = "vertices"
        self.inputs["faces"].label = "Faces"

        socket = self.inputs.new('SvStringsSocket', "number_faces")
        socket.use_prop=True
        socket.default_property_type = 'int'
        socket.default_int_property = 1000
        socket.label = "Number of Faces"

        socket = self.inputs.new('SvStringsSocket', "seed")
        socket.use_prop=True
        socket.default_property_type = 'int'
        socket.default_int_property = 0
        socket.label = "Seed"

        self.outputs.new('SvVerticesSocket', "vertices")
        self.outputs.new('SvStringsSocket', "faces")
        self.outputs["vertices"].label = "vertices"
        self.outputs["faces"].label = "Faces"

    def draw_buttons(self, context, layout):
        layout.prop(self, "flag_preserve_sharp")
        layout.prop(self, "flag_preserve_boundary")
        layout.prop(self, "flag_adaptive_scale")
        layout.prop(self, "flag_aggresive_sat")
        layout.prop(self, "flag_minimum_cost_flow")

        col = layout.column()
        col.row().label(text="Triangulate mesh polygons:")
        row = col.row()
        split = row.split(factor=0.4)
        split.column().label(text="Quads mode:")
        split.column().row(align=True).prop(self, "quad_mode", text='')

        row = col.row()
        split = row.split(factor=0.5)
        split.column().label(text="Polygons mode:")
        split.column().row(align=True).prop(self, "ngon_mode", text='')




    def process(self):
        if not enable_module:
            raise Exception("The dependent library is not installed (pyQuadriFlow).")
        
        outputs = self.outputs
        if not any( [o.is_linked for o in outputs]):
            return

        verts_sets = self.inputs['vertices'].sv_get(default=[],deepcopy=False)
        faces_sets = self.inputs['faces'].sv_get(default=[],deepcopy=False)
        _number_faces_sets = self.inputs['number_faces'].sv_get(default=[[4000]],deepcopy=False)
        number_faces_sets = flatten_data(_number_faces_sets)
        _seed_sets = self.inputs['seed'].sv_get(default=[[0]],deepcopy=False)
        seed_sets = flatten_data(_seed_sets)
        
        new_meshes = {
            'vertices':[],            
            'edges':[],
            'faces':[]
        }
        
        if(verts_sets != [] and faces_sets != []):
            for verts_set, faces_set, number_faces_set, seed_set in zip(*match_long_repeat([verts_sets,faces_sets, number_faces_sets, seed_sets])):
                bm_I = bmesh_from_pydata(verts_set, [], faces_set, markup_face_data=True, normal_update=True)
                b_faces = []
                for face in bm_I.faces:
                    b_faces.append(face)
                res = bmesh.ops.triangulate( bm_I, faces=b_faces, quad_method=self.quad_mode, ngon_method=self.ngon_mode )
                new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I, ret_edges=False)
                bm_I.free()

                #new_mesh = {'vertices': new_vertices_I, 'faces': new_faces_I}

                new_mesh = pyquadriflow(number_faces_set,
                                        seed_set,
                                        new_vertices_I,
                                        new_faces_I,
                                        self.flag_preserve_sharp,
                                        self.flag_preserve_boundary, 
                                        self.flag_adaptive_scale, 
                                        self.flag_aggresive_sat, 
                                        self.flag_minimum_cost_flow
                                    )
                
                new_meshes['vertices'].append(new_mesh['vertices'])
                #new_meshes['edges'].append(new_mesh['edges'])
                new_meshes['faces'].append(new_mesh['faces'])

        self.outputs['vertices'].sv_set(new_meshes['vertices'])
        #self.outputs['Edges'].sv_set(new_meshes['edges'])
        self.outputs['faces'].sv_set(new_meshes['faces'])

def register():    
    bpy.utils.register_class(SvQuadriFlowNode)

def unregister():
    bpy.utils.unregister_class(SvQuadriFlowNode)
