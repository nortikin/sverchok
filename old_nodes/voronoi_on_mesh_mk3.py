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
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level,\
    ensure_min_nesting
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import mesh_join

from sverchok.data_structure import repeat_last_for_length
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
import random
from collections import defaultdict
import itertools
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.geom import calc_bounds, PlaneEquation, bounding_box_aligned
from sverchok.utils.voronoi3d import calc_bvh_normals, voronoi3d_layer
from sverchok.dependencies import scipy
if scipy is not None:
    from scipy.spatial import Voronoi, SphericalVoronoi, Delaunay

import numpy as np


# see additional info https://github.com/nortikin/sverchok/pull/4948
def voronoi_on_mesh_bmesh(verts, faces, n_orig_sites, sites, spacing=0.0, mode='VOLUME', normal_update = False, precision=1e-8, mask=[]):

    def get_sites_delaunay_params(delaunay, n_orig_sites):
        result = defaultdict(list)
        ridges = []
        sites_pair = dict()
        for simplex in delaunay.simplices:
            ridges += itertools.combinations(tuple( sorted( simplex ) ), 2)

        ridges = list(set( ridges )) # remove duplicates of ridges
        ridges.sort() # for nice view in debugger

        for ridge_idx in range(len(ridges)):
            site1_idx, site2_idx = tuple(ridges[ridge_idx])
            # Remove 4D simplex ridges:
            if n_orig_sites<=site1_idx or n_orig_sites<=site2_idx:
                continue
            # Convert source sites to the 3D
            site1 = delaunay.points[site1_idx]
            site1 = Vector([site1[0], site1[1], site1[2], ])
            site2 = delaunay.points[site2_idx]
            site2 = Vector([site2[0], site2[1], site2[2], ])
            middle = (site1 + site2) * 0.5
            normal =  Vector(site1 - site2).normalized() # normal to site1
            plane1 = PlaneEquation.from_normal_and_point( normal, middle)
            plane2 = PlaneEquation.from_normal_and_point(-normal, middle)
            result[site1_idx].append( (site2_idx, site1, site2, middle,  normal, plane1) )
            result[site2_idx].append( (site1_idx, site2, site1, middle, -normal, plane2) )

        return result

    # some statistics:
    num_bisect = 0 # general count of bisect for full cutting process
    num_unpredicted_erased = 0 # if optimisation can not find a skip bisect case (with using bounding box) then counter incremented

    def cut_cell(start_mesh, sites_delaunay_params, site_idx, spacing, center_of_mass, bbox_aligned):
        nonlocal num_bisect, num_unpredicted_erased
        src_mesh = None
        # Check ridges for sites before bisect. If no ridges then no bisect and no mesh in result
        if site_idx in sites_delaunay_params:
            site_params = sites_delaunay_params[site_idx]

            if len(start_mesh.verts) > 0:
                lst_ridges_to_bisect = []
                #arr_dist_site_middle = np.empty(0)

                out_of_bbox = False

                # Sorting for optiomal bisections and search what can be skipped:
                for i, (site_pair_idx, site_vert, site_pair_vert, middle, plane_no, plane) in enumerate(site_params):
                    # Move bisect plane on size of half of spacing (normal point to the site_idx from site_pair_idx)
                    plane_co = middle + 0.5 * spacing * plane_no
                    # [1]. Test if bbox_aligned outside a site_pair plane?
                    signs_verts_bbox_aligned = PlaneEquation.from_normal_and_point( plane_no, plane_co ).side_of_points(bbox_aligned)
                    # if all vertexes of bbox_aligned out of plane with negation normal then object will be erased anyway.
                    # So one can skeep bisect operation
                    if (signs_verts_bbox_aligned <= 0).all():
                        out_of_bbox = True
                        break
                    # if all vertexes of bbox_aligned is on a positive side of a plane then bisect cannot produce any sections.
                    # So one can skip operation of bisection and stay object unchanged (do not add ringe to bisection list)
                    if (signs_verts_bbox_aligned > 0).all():
                        pass
                    else:
                        # [2]. calc middle planes for optimal bisects sequence (sort later)
                        plane_spacing = PlaneEquation.from_normal_and_point(plane_no, plane_co)
                        sign = plane_spacing.side_of_points(center_of_mass)
                        dist = plane_spacing.distance_to_point(center_of_mass)
                
                        lst_ridges_to_bisect.append( [dist*sign, site_pair_idx, site_vert, site_pair_vert, middle, plane_co, plane_no, plane, ] )
                    
                    # [3]. for test if all (site, middle) dist are less 0.5 spacing?
                    #    if spacing to big and eat all area [all (site-middle).lenght <= spacing/2]
                    # arr_dist_site_middle = np.append(arr_dist_site_middle, np.linalg.norm(site_vert-middle) )

                    # here is the place to extend optimization variants to exclude bisect from process.
                    # To the future: one cannot optimize process of bisection. Only count of bisects can be optimized.
                    pass

                # (3).
                # out_of_bbox may realized before all site pairs observed so arr_dist_site_middle may contain not all dists
                # if out_of_bbox==False and (arr_dist_site_middle<=0.5 * spacing).all():
                #     #out_of_bbox = True # If site has open side then its bisect cannot be skipped. So this rule are disabled.
                #     pass

                if out_of_bbox==False:
                    # (2)
                    lst_ridges_to_bisect.sort()  # less dist gets more points to cut off (with negative dists to. Negative dist is a negative side of bisect plane)

                    src_mesh = start_mesh.copy() # do not need create src_mesh until here.

                    # A main bisection process of site_idx
                    for i in range(len(lst_ridges_to_bisect)):
                        dist_center_of_mass_to_plane, site_pair_idx, site_vert, site_pair_vert, middle, plane_co, plane_no, plane = lst_ridges_to_bisect[i]
                        geom_in = src_mesh.verts[:] + src_mesh.edges[:] + src_mesh.faces[:]
                        res_bisect = bmesh.ops.bisect_plane(
                                src_mesh, geom=geom_in, dist=precision,
                                plane_co = plane_co,
                                plane_no = plane_no,
                                use_snap_center = False,
                                clear_outer = False,
                                clear_inner = True
                            )
                        num_bisect+=1 # for statistics

                        if len(res_bisect['geom_cut'])>0:
                            if mode=='VOLUME': # fill faces after bisect
                                surround = [e for e in res_bisect['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
                                if surround:
                                    fres = bmesh.ops.edgenet_prepare(src_mesh, edges=surround)
                                    if fres['edges']:
                                        #bmesh.ops.edgeloop_fill(src_mesh, edges=fres['edges']) # has glitches
                                        mfilled = bmesh.ops.triangle_fill(src_mesh, use_beauty=True, use_dissolve=True, edges=fres['edges'])
                                    else:
                                        pass
                                else:
                                    pass
                        else:
                            # if no geometry after bisect then break
                            # Geometry get clear in two cases:
                            # 1. Optimisation fail and not realized that this process has no result
                            # 2. Big spacing eat geometry inside mesh
                            if len( res_bisect['geom'] )==0:
                                num_unpredicted_erased+=1 # for statistics
                                break
                            pass
                else:
                    # func come here if out_of_bbox==True
                    pass
            else:
                pass
        else:
            pass


        # if out_of_bbox==True then bisect process jump here
        # if no verts then return noting
        if src_mesh is None or len( src_mesh.verts ) == 0:
            if src_mesh is not None:
                src_mesh.clear() #remember to clear empty geometry
                src_mesh.free()
            return None

        # if src_mesh has vertices then return mesh data
        if mode=='VOLUME' and normal_update==True:
            src_mesh.normal_update()
        pydata = pydata_from_bmesh(src_mesh)
        src_mesh.clear() #remember to clear geometry before return
        src_mesh.free()
        return pydata

    verts_out = []
    edges_out = []
    faces_out = []

    are_sites_plane = True # plane or line
    if len(sites)>=4:
        # select random sites to test are they are tethraeder or 3D?
        # If this thethod get wrong answer then not optimal method will be used.
        list_sites_for_test_plane = random.sample( range(0, len(sites)), 4)
        v0 = Vector(sites[list_sites_for_test_plane[0]])
        v1 = Vector(sites[list_sites_for_test_plane[1]])-v0
        v2 = Vector(sites[list_sites_for_test_plane[2]])-v0
        v3 = Vector(sites[list_sites_for_test_plane[3]])-v0
        cross1_v1_v2 = np.cross(v1, v2)
        cross2_v1_v3 = np.cross(v1, v3)
        cross12 = np.cross(cross1_v1_v2, cross2_v1_v3)

        res_norm = np.linalg.norm(cross12,ord=1)
        if res_norm>0.1:
            are_sites_plane = False
        else:
            are_sites_plane = True

    if are_sites_plane:
        # https://github.com/nortikin/sverchok/pull/4952
        # http://www.qhull.org/html/qdelaun.htm
        # http://www.qhull.org/html/qh-optc.htm
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html
        # Convert sites to 4D
        np_sites = np.array([(s[0], s[1], s[2], 0) for s in sites], dtype=np.float32)
        # Add 3D tetraedre to the 4D with W=1
        np_sites = np.append(np_sites, [[0.0, 0.0, 0.0, 1],
                                        [1.0, 0.0, 0.0, 1],
                                        [0.0, 1.0, 0.0, 1],
                                        [0.0, 0.0, 1.0, 1],
                                        ], axis=0)
    else:
        np_sites = np.array([(s[0], s[1], s[2]) for s in sites], dtype=np.float32)

    delaunay = Delaunay(np.array(np_sites, dtype=np.float32))
    sites_delaunay_params = get_sites_delaunay_params(delaunay, n_orig_sites)

    if isinstance(spacing, list):
        spacing = repeat_last_for_length(spacing, len(sites))
    else:
        spacing = [spacing for i in range(len(sites))]

    # calc center of mass. Using for sort of bisect planes for sites.
    center_of_mass = np.average( verts, axis=0 )
    # using for precalc unneeded bisects
    bbox_aligned, *_ = bounding_box_aligned(verts)

    # Extend mask if it is less len of sites
    if len(mask)==0:
        # if len of mask is 0 then use all sites
        mask = [True] * ( len(sites)-len(mask) )
    else:
        # else extend mask by false and do not use sites that are not in the mask
        mask = mask[:]+[False]*(len(sites)-len(mask) if len(mask)<=len(sites) else 0)

    start_mesh = bmesh_from_pydata(verts, [], faces, normal_update=False)
    used_sites_idx = []
    used_sites_verts = []
    for site_idx in range(len(sites)):
        if(mask[site_idx]):
            cell = cut_cell(start_mesh, sites_delaunay_params, site_idx, spacing[site_idx], center_of_mass, bbox_aligned)
            if cell is not None:
                new_verts, new_edges, new_faces = cell
                if new_verts:
                    verts_out.append(new_verts)
                    edges_out.append(new_edges)
                    faces_out.append(new_faces)
                    used_sites_idx.append( site_idx )
                    used_sites_verts.append( sites[site_idx] )
    start_mesh.clear() # remember to clear empty geometry
    start_mesh.free()
    

    # show statistics:
    # bisects - count of bisects in cut_cell
    # unb - unpredicted erased mesh (bbox_aligned cannot make predicted results)
    # sites - count of sites in process
    # mask - mask of sites that uset to the result. Empty list all sites uset to result.
    # print( f"bisects: {num_bisect: 4d}, unb={num_unpredicted_erased: 4d}, sites={len(sites)}")
    return verts_out, edges_out, faces_out, used_sites_idx, used_sites_verts

def voronoi_on_mesh(verts, faces, sites, thickness,
    spacing = 0.0,
    clip_inner=True, clip_outer=True, do_clip=True,
    clipping=1.0, mode = 'REGIONS', normal_update=False,
    precision = 1e-8,
    mask = []
    ):

    bvh = BVHTree.FromPolygons(verts, faces)
    npoints = len(sites)

    if clipping is None:
        x_min, x_max, y_min, y_max, z_min, z_max = calc_bounds(verts)
        clipping = max(x_max - x_min, y_max - y_min, z_max - z_min) / 2.0

    if mode in {'REGIONS', 'RIDGES'}:
        if clip_inner or clip_outer:
            normals = calc_bvh_normals(bvh, sites)
        k = 0.5*thickness
        sites = np.array(sites)
        all_points = sites.tolist()
        if clip_outer:
            plus_points = sites + k*normals
            all_points.extend(plus_points.tolist())
        if clip_inner:
            minus_points = sites - k*normals
            all_points.extend(minus_points.tolist())

        return voronoi3d_layer(npoints, all_points,
                make_regions = (mode == 'REGIONS'),
                do_clip = do_clip,
                clipping = clipping)

    else: # VOLUME, SURFACE
        all_points = sites[:]
        verts, edges, faces, used_sites_idx, used_sites_verts = voronoi_on_mesh_bmesh(verts, faces, len(sites), all_points,
                spacing = spacing, mode = mode, normal_update = normal_update,
                precision = precision, mask=mask)
        return verts, edges, faces, used_sites_idx, used_sites_verts

class SvVoronoiOnMeshNodeMK3(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Mesh
    Tooltip: Generate Voronoi diagram on the surface of a mesh object
    """
    bl_idname = 'SvVoronoiOnMeshNodeMK3'
    bl_label = 'Voronoi on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'scipy'}

    modes = [
            ('VOLUME', "Split Volume", "Split volume of the mesh into regions of Voronoi diagram", 0),
            ('SURFACE', "Split Surface", "Split the surface of the mesh into regions of Vornoi diagram", 1),
            #('RIDGES', "Ridges near Surface", "Generate ridges of 3D Voronoi diagram near the surface of the mesh", 2),
            #('REGIONS', "Regions near Surface", "Generate regions of 3D Voronoi diagram near the surface of the mesh", 3)
        ]

    spacing : FloatProperty(
        name = "Spacing",
        default = 0.0,
        min = 0.0,
        description="Percent of space to leave between generated fragment meshes",
        update=updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Make sure that all normals of generated meshes point outside",
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['Spacing'].hide_safe = self.mode not in {'VOLUME', 'SURFACE'}
        updateNode(self, context)

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'VOLUME',
        update = update_sockets)
    
    join_modes = [
            ('FLAT', "Flat list", "Output a single flat list of mesh objects (Voronoi diagram ridges / regions) for all input meshes", 0),
            ('SEPARATE', "Separate lists", "Output a separate list of mesh objects (Voronoi diagram ridges / regions) for each input mesh", 1),
            ('JOIN', "Join meshes", "Output one mesh, joined from ridges / edges of Voronoi diagram, for each input mesh", 2)
        ]

    join_mode : EnumProperty(
        name = "Output mode",
        items = join_modes,
        default = 'FLAT',
        update = updateNode)

    def updateMaskMode(self, context):
        if self.mask_mode=='MASK':
            self.inputs["Mask"].label = "Mask of Sites"
        elif self.mask_mode=='INDEXES':
            self.inputs["Mask"].label = "Indexes of Sites"
        updateNode(self, context)

    mask_modes = [
            ('MASK', "Mask of sites", "Boolean value (0/1) to mask of sites", 0),
            ('INDEXES', "Index of sites", "Indexes of sites to mask", 1),
        ]
    mask_mode : EnumProperty(
        name = "Mask mode",
        items = mask_modes,
        default = 'MASK',
        update = updateMaskMode)

    mask_inversion : BoolProperty(
        name = "Inversion",
        default = False,
        description="Invert mask of sites",
        update = updateNode)


    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh bisecting procedure",
            default = 6,
            min = 1,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvVerticesSocket', "Sites")
#         self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', "Mask").label = "Mask of Sites"
        self.inputs.new('SvStringsSocket', 'Spacing').prop_name = 'spacing'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvStringsSocket', "Sites_idx")
        self.outputs.new('SvStringsSocket', "Sites_verts")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Mode:")
        layout.prop(self, "mode", text='')
        split = layout.column().split(factor=0.6)
        split.column().prop(self, "mask_mode", text='')
        split.column().prop(self, "mask_inversion", text='Invert')
        if self.mode == 'VOLUME':
            layout.prop(self, 'normals')
        layout.label(text='Output nesting:')
        layout.prop(self, 'join_mode', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vertices'].sv_get(deepcopy=False)
        faces_in = self.inputs['Faces'].sv_get(deepcopy=False)
        sites_in = self.inputs['Sites'].sv_get(deepcopy=False)

        mask_in = self.inputs['Mask'] #.sv_get(deepcopy=False)
        if mask_in.is_linked==False:
            mask_in = [[[]]]
        else:
            mask_in = mask_in.sv_get(deepcopy=False)
            
        #thickness_in = self.inputs['Thickness'].sv_get()
        spacing_in = self.inputs['Spacing'].sv_get(deepcopy=False)

        verts_in = ensure_nesting_level(verts_in, 4)
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        faces_in = ensure_nesting_level(faces_in, 4)
        #thickness_in = ensure_nesting_level(thickness_in, 2)
        spacing_in = ensure_min_nesting(spacing_in, 2)
        mask_in = ensure_min_nesting(mask_in, 3)

        nested_output = input_level > 3

        precision = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        sites_idx_out = []
        sites_verts_out = []
        for params in zip_long_repeat(verts_in, faces_in, sites_in, spacing_in, mask_in):
            new_verts = []
            new_edges = []
            new_faces = []
            new_sites_idx = []
            new_sites_verts = []
            for verts, faces, sites, spacing, mask in zip_long_repeat(*params):
                # if mask is zero or not connected then do not mask any. Except of inversion,
                if not mask:
                    np_mask = np.ones(len(sites), dtype=bool)
                    if self.mask_inversion==True:
                        np_mask = np.invert(np_mask)
                    mask = np_mask.tolist()
                else:
                    if self.mask_mode=='MASK':
                        if self.mask_inversion==True:
                            mask = list( map( lambda v: False if v==0 else True, mask) )
                            mask = mask[:len(sites)]
                            np_mask = np.zeros(len(sites), dtype=bool)
                            np_mask[0:len(mask)]=mask
                            np_mask = np.invert(np_mask)
                            mask = np_mask.tolist()
                        pass
                    elif self.mask_mode=='INDEXES':
                        mask_len = len(sites)
                        mask_range = []
                        for x in mask:
                            if -mask_len<x<mask_len:
                                mask_range.append(x)
                        np_mask = np.ones(len(sites), dtype=bool)
                        np_mask[mask_range] = False
                        if self.mask_inversion==True:
                            np_mask = np.invert(np_mask)
                        mask = np_mask.tolist()

                verts, edges, faces, used_sites_idx, used_sites_verts = voronoi_on_mesh(verts, faces, sites, thickness=0,
                            spacing = spacing,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.mode,
                            normal_update = self.normals,
                            precision = precision,
                            mask = mask
                            )

                if self.join_mode == 'FLAT':
                    new_verts.extend(verts)
                    new_edges.extend(edges)
                    new_faces.extend(faces)
                    new_sites_idx.extend([[idx] for idx in used_sites_idx])
                    new_sites_verts.extend([[idx] for idx in used_sites_verts])
                elif self.join_mode == 'SEPARATE':
                    new_verts.append(verts)
                    new_edges.append(edges)
                    new_faces.append(faces)
                    new_sites_idx.append(used_sites_idx)
                    new_sites_verts.append(used_sites_verts)
                else: # JOIN
                    verts, edges, faces = mesh_join(verts, edges, faces)
                    new_verts.append(verts)
                    new_edges.append(edges)
                    new_faces.append(faces)
                    new_sites_idx.append(used_sites_idx)
                    new_sites_verts.append(used_sites_verts)

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
                sites_idx_out.append(new_sites_idx)
                sites_verts_out.append(new_sites_verts)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                sites_idx_out.extend(new_sites_idx)
                sites_verts_out.extend(new_sites_verts)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['Sites_idx'].sv_set(sites_idx_out)
        self.outputs['Sites_verts'].sv_set(sites_verts_out)

classes = [SvVoronoiOnMeshNodeMK3]
register, unregister = bpy.utils.register_classes_factory(classes)