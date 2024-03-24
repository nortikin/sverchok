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

from itertools import product
import numpy as np
import bpy
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops
from mathutils import Matrix
from datetime import datetime

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, repeat_last_for_length, ensure_nesting_level
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.modules.matrix_utils import matrix_apply_np

from sverchok.data_structure import dataCorrect, updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.math import np_dot

class SvWeightedVectorSumNode(SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """
    Triggers: Center of mass (Mesh)
    Tooltip: Calculate center of mass (barycenter) of mesh per vertices, edges, faces or volume. (Volume is only for closed mesh)
    """
    bl_idname = 'SvWeightedVectorSumNode'
    bl_label = 'Center of mass (Mesh) (Alpha)'
    bl_icon = 'SNAP_FACE_CENTER'
    sv_icon = 'SV_CENTROID'


    def updateSizeSocket(self, context):
        if self.center_mode == 'VERTICES':
            self.outputs['output_sizes'].label = 'Count of verts'
            self.outputs['output_size' ].label = 'Total Verts'
        elif self.center_mode == 'EDGES':
            self.outputs['output_sizes'].label = 'Lengths'
            self.outputs['output_size' ].label = 'Total Length'
        elif self.center_mode == 'FACES':
            self.outputs['output_sizes'].label = 'Areas'
            self.outputs['output_size' ].label = 'Total Area'
        elif self.center_mode == 'VOLUMES':
            self.outputs['output_sizes'].label = 'Volumes'
            self.outputs['output_size' ].label = 'Total Volume'
        
        updateNode(self, context)

    center_modes = [
        ("VERTICES", "Vertices", "Calc center of mass by vertices and ignore edges, faces and volumes", 0),
        (   "EDGES",    "Edges", "Calc center of mass by length of edges and ignore vertices, faces and volumes", 1),
        (   "FACES",    "Faces", "Calc center of mass by surfaces of objects and ignore vertices, edges and volumes", 2),
        ( "VOLUMES",  "Volumes", "Calc center of mass by volume of objects and ignore vertices, edges and faces", 3)
    ]

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

    skip_unmanifold_centers: BoolProperty(
        name='Skip unmanifold centers',
        description='If True then skip unmanifold centers else show Exception\n\nExample:\n   True: if object has only vertices and \'Center mode\'=\'Volumes\', \'Faces\' or \'Edges\' then skip this object without exception',
        default=True,
        update=updateNode) # type: ignore

    skip_test_volume_are_closed: BoolProperty(
        name='Skip test meshes for holes',
        description='If True then skip test meshes for holes. (Only for \'Volumes\' mode)',
        default=True,
        update=updateNode) # type: ignore

    center_mode: EnumProperty(
        name='Center mode',
        description="Calc center mode",
        items=center_modes,
        default="VOLUMES",
        update=updateSizeSocket) # type: ignore

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

    def update_sockets(self, context):
        updateNode(self, context)

    def draw_buttons(self, context, layout):
        col = layout.column()

        row = col.row()
        row.prop(self, 'skip_unmanifold_centers')
        
        row = col.row()
        row.active = False
        row.prop(self, 'skip_test_volume_are_closed')
        if self.center_mode in ['VOLUMES']:
            row.active = True

        row = col.row()
        split = row.split(factor=0.4)
        split.column().label(text="Center mode:")
        split.column().row(align=True).prop(self, "center_mode", text='')

        row = col.row()
        row.active = False
        row.label(text='Triangulation (only Faces or Volumes):')
        if self.center_mode in ['FACES', 'VOLUMES']:
            row.active = True

        row = col.row()
        row.active = False
        split = row.split(factor=0.4)
        split.column().label(text="Quads mode:")
        split.column().row(align=True).prop(self, "quad_mode", text='')
        if self.center_mode in ['FACES', 'VOLUMES']:
            row.active = True

        row = col.row()
        row.active = False
        split = row.split(factor=0.5)
        split.column().label(text="Polygons mode:")
        split.column().row(align=True).prop(self, "ngon_mode", text='')
        if self.center_mode in ['FACES', 'VOLUMES']:
            row.active = True

        pass

    def sv_init(self, context):
        self.width=220
        self.inputs.new('SvVerticesSocket', 'input_vertices')
        self.inputs.new('SvStringsSocket', 'input_edges')
        self.inputs.new('SvStringsSocket', 'input_polygons')
        self.inputs.new('SvStringsSocket', 'input_mass_vert')
        self.inputs.new('SvStringsSocket', 'input_density')

        self.inputs["input_vertices"] .label = 'Vertices'
        self.inputs["input_edges"]    .label = 'Edges'
        self.inputs["input_polygons"] .label = 'Polygons'
        self.inputs["input_mass_vert"].label = 'Mass of vertiсes'
        self.inputs["input_density"]  .label = 'Density'


        self.outputs.new('SvVerticesSocket', 'output_vertices')
        self.outputs.new('SvStringsSocket',  'output_edges')
        self.outputs.new('SvStringsSocket',  'output_polygons')

        self.outputs.new('SvVerticesSocket', 'output_centers_of_mass')
        self.outputs.new('SvVerticesSocket', 'output_total_center')
        self.outputs.new('SvStringsSocket', 'output_sizes')
        self.outputs.new('SvStringsSocket', 'output_size')
        self.outputs.new('SvStringsSocket', 'output_masses')
        self.outputs.new('SvStringsSocket', 'output_mass')
        self.outputs.new('SvStringsSocket', 'output_mask')

        self.outputs['output_vertices'] .label = 'Vertices'
        self.outputs['output_edges'] .label = 'Edges'
        self.outputs['output_polygons'] .label = 'Polygons'
        self.outputs['output_centers_of_mass'].label = 'Centers of mass of objects'
        self.outputs['output_total_center'].label = 'Total center'
        self.outputs['output_sizes'].label = ''
        self.outputs['output_size'] .label = ''
        self.outputs['output_masses'] .label = 'Masses'
        self.outputs['output_mass'] .label = 'Mass'
        self.outputs['output_mask'] .label = 'Mask'

        self.updateSizeSocket(context)
        self.update_sockets(context)

    def process(self):
        outputs = self.outputs
        if not any( [o.is_linked for o in outputs]):
            return
        
        if not (self.inputs['input_vertices'].is_linked):
            return
        if not (any(self.outputs[name].is_linked for name in [
                'output_vertices', 'output_edges', 'output_polygons', 'output_centers_of_mass', 'output_total_center', 'output_sizes', 'output_size', 'output_masses', 'output_mass', 'output_mask',])):
            return

        input_vertices_s    = self.inputs['input_vertices'].sv_get(default=[[]], deepcopy=False)
        input_vertices_s_3  = ensure_nesting_level(input_vertices_s, 3)
        input_edges_s       = self.inputs['input_edges'].sv_get(default=[[]], deepcopy=False)
        input_edges_s_3     = ensure_nesting_level(input_edges_s, 3)
        input_polygons_s    = self.inputs['input_polygons'].sv_get(default=[[]], deepcopy=False)
        input_polygons_s_3  = ensure_nesting_level(input_polygons_s, 3)
        input_mass_vert_s   = self.inputs['input_mass_vert'].sv_get(default=[[1]], deepcopy=False)
        input_mass_vert_s_2 = ensure_nesting_level(input_mass_vert_s, 2)
        input_density_s     = self.inputs['input_density'].sv_get(default=[[1]], deepcopy=False)
        input_density_s_2   = ensure_nesting_level(input_density_s, 2)

        result_vertices = []
        result_edges = []
        result_polygons = []


        center_mass_mesh_list_out = []
        result_masses = []
        result_mask = [] # what object has result

        center_mass_mesh_list = []
        mass_mesh_list = []
        size_mesh_list = []

        mass_center_general = None

        # If density is one level list and objects are many then
        # spead list of density for every mesh. ex.: [[mesh1],[mesh2],[mesh3]], [density:d1,d2,d3] ] => [[mesh1],[mesh2],[mesh3]], [density:[d1],[d2],[d3]] ]
        if len(input_density_s_2)==1 and len(input_vertices_s_3)>1:
            input_density_s_2 = [[d] for d in input_density_s_2[0]]

        # if lists of edges or faces is less vertices then append at the end of edges and faces empty list to extend it later with empty items.
        # verts=[[v1,v2,v3],[v4,v5,v6]]
        # edges=[[[0,1],[1,2]]]=>[[[0,1], [1,2]],[]]
        # faces=[[[0,1,2]]]=>[[[0,1,2]]],[]]
        # this allow skip unmanifold centers
        if len(input_edges_s_3)<len(input_vertices_s_3):
            input_edges_s_3.append([[]]) # like default
        if len(input_polygons_s_3)<len(input_vertices_s_3):
            input_polygons_s_3.append([[]]) # like default

        meshes = match_long_repeat( [input_vertices_s_3, input_edges_s_3[:len(input_vertices_s_3)], input_polygons_s_3[:len(input_vertices_s_3)], input_mass_vert_s_2[:len(input_vertices_s_3)], input_density_s_2[:len(input_vertices_s_3)] ])

        center_mode = self.center_mode
        for vertices_I, edges_I, faces_I, mass_of_vertices_I, density_I in zip(*meshes):
            if len(vertices_I)==0:
                # skip if no vertices at all:
                result_mask.append(False)

            if center_mode=='VERTICES':

                if len(vertices_I)==0:
                    result_mask.append(False)
                else:
                    result_mask.append(True)
                    result_vertices.append(vertices_I)
                    result_edges.append(edges_I)
                    result_polygons.append(faces_I)

                    # shrink or extend mass if list of mass is not equals list of verts:
                    mass_of_vertices_I_shrinked = mass_of_vertices_I[:len(vertices_I)]
                    mass_of_vertices_I_np1 = np.append( mass_of_vertices_I_shrinked, np.full( (len(vertices_I)-len(mass_of_vertices_I_shrinked)), mass_of_vertices_I_shrinked[-1]) )
                    vertices_I_np = np.array(vertices_I)
                    mass_of_vertices_I_np2  = np.array([mass_of_vertices_I_np1])
                    mass_I = mass_of_vertices_I_np2.sum()
                    center_mass_mesh_I = (vertices_I_np * mass_of_vertices_I_np2.T).sum(axis=0) / mass_I

                    center_mass_mesh_list.append( center_mass_mesh_I.tolist() )
                    mass_mesh_list.append(mass_I)
                    size_mesh_list.append(vertices_I_np.shape[0])  # Count of vertices

            elif center_mode=='EDGES':
                    
                old_edges = np.array(edges_I)
                if old_edges.size==0:
                    # skip if no edges at all:
                    result_mask.append(False)
                else:
                    result_mask.append(True)
                    verts_I = np.array(vertices_I)

                    # Do not triangulate mesh for 'EDGE' mode
                    result_vertices.append(vertices_I)
                    result_edges.append(edges_I)
                    result_polygons.append(faces_I)
                    
                    segment_I = verts_I[old_edges]
                    distances_I = np.linalg.norm(segment_I[:,1]-segment_I[:,0], axis=1)
                    length_I = distances_I.sum()
                    segment_center_I = segment_I.sum(axis=1) / 2.0
                    center_mass_mesh_I = (segment_center_I * distances_I[np.newaxis].T).sum(axis=0) / length_I
                    mass_I             = length_I * density_I[0]

                    center_mass_mesh_list.append( center_mass_mesh_I.tolist() )
                    mass_mesh_list.append(mass_I)
                    size_mesh_list.append(length_I)

            elif center_mode=='FACES':
                    
                faces_I_np = np.array(faces_I)
                if faces_I_np.size==0:
                    # skip if no faces at all:
                    result_mask.append(False)
                else:
                    result_mask.append(True)

                    # test if some polygons are not tris:
                    if max(map(len, faces_I_np))>3:
                        # triangulate mesh for 'FACES' mode
                        bm_I = bmesh_from_pydata(vertices_I, edges_I, faces_I, markup_face_data=True, normal_update=True)
                        b_faces = []
                        for face in bm_I.faces:
                            b_faces.append(face)
                        res = bmesh.ops.triangulate(
                            bm_I, faces=b_faces, quad_method=self.quad_mode, ngon_method=self.ngon_mode
                        )
                        new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I)
                        bm_I.free()
                    else:
                        new_vertices_I,new_edges_I,new_faces_I = vertices_I, edges_I, faces_I

                    result_vertices.append(new_vertices_I)
                    result_edges.append(new_edges_I)
                    result_polygons.append(new_faces_I)
                    
                    verts_I_np         = np.array(new_vertices_I)
                    faces_I_np         = np.array(new_faces_I)
                    tris_I_np          = verts_I_np[faces_I_np]
                    areases_I          = np.linalg.norm(np.cross(tris_I_np[:,1]-tris_I_np[:,0], tris_I_np[:,2]-tris_I_np[:,0]) / 2.0, axis=1)
                    area_I             = areases_I.sum()
                    tris_centers_I     = tris_I_np.sum(axis=1) / 3.0
                    center_mass_mesh_I = (tris_centers_I * areases_I[np.newaxis].T).sum(axis=0) / area_I
                    mass_I             = area_I * density_I[0]

                    center_mass_mesh_list.append( center_mass_mesh_I.tolist() )
                    mass_mesh_list.append(mass_I)
                    size_mesh_list.append(area_I)

            elif center_mode=='VOLUMES':
                    
                faces_I_np = np.array(faces_I)
                if faces_I_np.size==0:
                    # skip if no faces at all:
                    result_mask.append(False)
                else:
                    do_calc = False
                    if max(map(len, faces_I_np))==3 and self.skip_test_volume_are_closed==True:
                        new_vertices_I, new_edges_I, new_faces_I = vertices_I, edges_I, faces_I
                        do_calc = True
                    else:
                        # triangulate mesh
                        bm_I = bmesh_from_pydata(vertices_I, edges_I, faces_I, markup_face_data=True, normal_update=True)
                        # test if all edges are contiguous (https://docs.blender.org/api/current/bmesh.types.html#bmesh.types.BMEdge.is_contiguous)
                        # then volume is closed:
                        for edge in bm_I.edges:
                            if edge.is_contiguous==False:
                                do_calc = False
                                break
                        else:
                            do_calc = True
                            # test if some polygons are not tris:
                            if max(map(len, faces_I_np))>3:
                                b_faces = []
                                for face in bm_I.faces:
                                    b_faces.append(face)

                                res = bmesh.ops.triangulate(
                                    bm_I, faces=b_faces, quad_method=self.quad_mode, ngon_method=self.ngon_mode
                                )
                                new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I)
                            else:
                                new_vertices_I, new_edges_I, new_faces_I = vertices_I, edges_I, faces_I
                        bm_I.free()

                    if do_calc==False:
                        result_mask.append(False)
                    else:
                        result_mask.append(True)
                        result_vertices.append(new_vertices_I)
                        result_edges   .append(new_edges_I)
                        result_polygons.append(new_faces_I)
                        
                        verts_I = np.array(new_vertices_I)
                        faces_I = np.array(new_faces_I)
                        tris_I = verts_I[faces_I]
                        # to precise calc move all mesh to median point
                        tris_I_median = np.median(tris_I, axis=(0,1))
                        tris_I_delta = tris_I-tris_I_median
                        signed_volumes_I   = np_dot(tris_I_delta[:,0], np.cross(tris_I_delta[:,1], tris_I_delta[:,2]))
                        volume_I           = signed_volumes_I.sum()
                        tetra_centers_I    = tris_I_delta.sum(axis=1) / 4.0
                        center_mass_mesh_I = (tetra_centers_I * signed_volumes_I[np.newaxis].T).sum(axis=0) / volume_I + tris_I_median
                        mass_I             = volume_I * density_I[0]

                        center_mass_mesh_list.append( center_mass_mesh_I.tolist() )
                        mass_mesh_list.append(mass_I)
                        size_mesh_list.append(volume_I)

        # calc center of mass of all meshes if any mesh has center:
        if center_mass_mesh_list:
            center_mass_mesh_list_np = np.array(center_mass_mesh_list)
            mass_mesh_list_np = np.array([mass_mesh_list])
            mass_center_general_np = (center_mass_mesh_list_np*mass_mesh_list_np.T).sum(axis=0) / mass_mesh_list_np.sum()
            mass_center_general = [[ mass_center_general_np.tolist() ]]
            center_mass_mesh_list_out  = [ [v] for v in center_mass_mesh_list ]
            result_masses = [ [m] for m in mass_mesh_list ]
            result_mass = mass_mesh_list_np.sum()
            result_sizes = [ [s] for s in size_mesh_list ]
            result_size = np.array(size_mesh_list).sum()
        else:
            # if there is no any centers of mass
            mass_center_general = [ [] ]
            center_mass_mesh_list_out  = [ [] ]
            result_masses = [ [] ]
            result_mass = 0
            result_sizes = [ [] ]
            result_size = 0

        self.outputs['output_vertices'].sv_set(result_vertices)
        self.outputs['output_edges'].sv_set(result_edges)
        self.outputs['output_polygons'].sv_set(result_polygons)

        self.outputs['output_centers_of_mass'].sv_set(center_mass_mesh_list_out)
        self.outputs['output_total_center'].sv_set(mass_center_general)
        self.outputs['output_sizes'].sv_set(result_sizes)
        self.outputs['output_size'].sv_set([[result_size]])
        self.outputs['output_masses'].sv_set(result_masses)
        self.outputs['output_mass'].sv_set([[result_mass]])
        self.outputs['output_mask'].sv_set(result_mask)

        unmanifold_centers_indices = [i for i, x in enumerate(result_mask) if not(x)]
        if self.skip_unmanifold_centers==False:
            if unmanifold_centers_indices:
                str_error = f"Unmanifold centers are: [{','.join( map(str,unmanifold_centers_indices))}]"
                raise Exception(str_error)
        pass



def register():
    bpy.utils.register_class(SvWeightedVectorSumNode)


def unregister():
    bpy.utils.unregister_class(SvWeightedVectorSumNode)
