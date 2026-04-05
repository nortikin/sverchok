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

# import bpy
# from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

# from sverchok.node_tree import SverchCustomTreeNode
# from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, ensure_min_nesting
# from sverchok.ui.sv_icons import custom_icon
# from sverchok.utils.sv_bmesh_utils import recalc_normals
# from sverchok.utils.sv_mesh_utils import mesh_join
# from sverchok.utils.voronoi3d import voronoi_on_mesh
# from mathutils import Vector, Matrix
# import numpy as np
# import collections
# import textwrap


import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, ensure_min_nesting
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.voronoi3d import voronoi_on_mesh
import numpy as np
import textwrap

from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from collections import defaultdict, deque
import itertools
import random
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.geom import calc_bounds, PlaneEquation, bounding_box_aligned
from sverchok.data_structure import repeat_last_for_length
from sverchok.utils.voronoi3d import voronoi3d_layer, calc_bvh_normals
from sverchok.dependencies import scipy
from datetime import datetime

if scipy is not None:
    from scipy.spatial import Voronoi, SphericalVoronoi, Delaunay

def separate_loose_mesh(verts_in, poly_edge_in):
        ''' separate a mesh by loose parts.
        input:
          1. list of verts
          2. list of edges/polygons
        output: list of
          1. separated list of verts
          2. separated list of edges/polygons with new indices of separated elements
          3. separated list of edges/polygons (like 2) with old indices
        '''

        verts_out = []
        poly_edge_out = []
        poly_edge_old_indexes_out = []  # faces with old indices 

        # build links
        node_links = {}
        for edge_face in poly_edge_in:
            for i in edge_face:
                if i not in node_links:
                    node_links[i] = set()
                node_links[i].update(edge_face)

        nodes = set(node_links.keys())
        n = nodes.pop()
        node_set_list = [set([n])]
        node_stack = deque()
        node_stack_append = node_stack.append
        node_stack_pop = node_stack.pop
        node_set = node_set_list[-1]
        # find separate sets
        while nodes:
            for node in node_links[n]:
                if node not in node_set:
                    node_stack_append(node)
            if not node_stack:  # new mesh part
                n = nodes.pop()
                node_set_list.append(set([n]))
                node_set = node_set_list[-1]
            else:
                while node_stack and n in node_set:
                    n = node_stack_pop()
                nodes.discard(n)
                node_set.add(n)
        # create new meshes from sets, new_pe is the slow line.
        if len(node_set_list) >= 1:
            for node_set in node_set_list:
                mesh_index = sorted(node_set)
                vert_dict = {j: i for i, j in enumerate(mesh_index)}
                new_vert = [verts_in[i] for i in mesh_index]
                new_pe = [[vert_dict[n] for n in fe]
                            for fe in poly_edge_in
                            if fe[0] in node_set]
                old_pe = [fe for fe in poly_edge_in
                             if fe[0] in node_set]
                verts_out.append(new_vert)
                poly_edge_out.append(new_pe)
                poly_edge_old_indexes_out.append(old_pe)
        elif node_set_list:  # no reprocessing needed
            verts_out.append(verts_in)
            poly_edge_out.append(poly_edge_in)
            poly_edge_old_indexes_out.append(poly_edge_in)

        return verts_out, poly_edge_out, poly_edge_old_indexes_out


# see additional info https://github.com/nortikin/sverchok/pull/4948
def voronoi_on_mesh_bmesh(verts, faces, n_orig_sites, sites, spacing=0.0, mode='VOLUME', normal_update = False, results_objects_join_mode = 'RESULTS_OBJECTS_JOIN_MODE_KEEP', precision=1e-8, mask=[]):

    def get_bmesh_data(bm, outer_layer_name, mode, ret_verts=True, ret_edges=True, ret_faces=True):
        '''return verts, edges, faces and outer faces property (1-outer, 0-inner face)'''
        verts_res = [v.co[:] for v in bm.verts] if ret_verts==True else None
        edges_res = [[e.verts[0].index, e.verts[1].index] for e in bm.edges] if ret_edges==True else None
        ordered_faces = sorted(bm.faces, key=lambda f: f.index)
        faces_res = [[i.index for i in p.verts] for p in ordered_faces] if ret_faces==True else None

        outer_faces_layer = bm.faces.layers.int.get(outer_layer_name)
        faces_outer_property = [ f[outer_faces_layer] for f in ordered_faces]

        verts_outer_property = []
        edges_outer_property = []

        if mode=='VOLUME':
            for vert in bm.verts:
                faces = vert.link_faces
                is_outer = False
                is_inner = False
                for f in faces:
                    outer_property = f[outer_faces_layer]
                    if outer_property==1:
                        is_outer = True
                    else:
                        is_inner = True
                    pass
                verts_outer_property.append(dict(is_outer=is_outer, is_inner=is_inner, index=vert.index))
                pass

            for edge in bm.edges:
                faces = edge.link_faces
                is_outer = False
                is_inner = False
                for f in faces:
                    outer_property = f[outer_faces_layer]
                    if outer_property==1:
                        is_outer = True
                    else:
                        is_inner = True
                    pass
                edges_outer_property.append(dict(is_outer=is_outer, is_inner=is_inner, index=edge.index))
                pass
        elif mode=='SURFACE':
            # on surface mode no additional faces created.
            outer_edges_layer = bm.edges.layers.int.get(outer_layer_name)

            for vert in bm.verts:
                vert_link_edges = vert.link_edges
                is_outer = False
                is_inner = False
                is_surface_border = False
                for edge in vert_link_edges:
                    outer_property = edge[outer_edges_layer]
                    if outer_property==0: # new edge created
                        is_inner = True
                        is_surface_border = True
                    elif outer_property==1: # old edge external
                        is_outer = True
                        is_surface_border = True
                    else: # 2 value for a while
                        # inside object plane
                        pass
                    pass
                verts_outer_property.append(dict(is_outer=is_outer, is_inner=is_inner, is_surface_border=is_surface_border, index=vert.index))
                pass

            for edge in bm.edges:
                is_outer = False
                is_inner = False
                is_surface_border = False

                outer_property = edge[outer_edges_layer]
                if outer_property==0:  # new edge created
                    is_inner = True
                    is_surface_border = True
                elif outer_property==1: # old edges external
                    is_outer = True
                    is_surface_border = True
                else:
                    # inside object plane
                    pass
                edges_outer_property.append(dict(is_outer=is_outer, is_inner=is_inner, is_surface_border = is_surface_border, index=edge.index))
                pass

            pass
        else:
            raise Exception(f'Unknown mode="{mode}" in voronoi_on_mesh_bmesh->get_bmesh_data')
        return verts_res, edges_res, faces_res, verts_outer_property, edges_outer_property, faces_outer_property


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
    
    def get_face_components(bm):
        visited = set()
        components = []

        for f in bm.faces:
            if f in visited:
                continue

            stack = [f]
            comp = []

            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue

                visited.add(cur)
                comp.append(cur)

                for e in cur.edges:
                    for f2 in e.link_faces:
                        if f2 not in visited:
                            stack.append(f2)
            comp_indexes = list(set([c.index for c in comp]))
            comp_indexes.sort()
            components.append(comp_indexes)

        return components
    
    def keep_only_component(bm, faces_indexes):
        component_faces = [bm.faces[i] for i in faces_indexes]
        keep_faces = set(component_faces)
        keep_edges = set()
        keep_verts = set()

        # Собираем связанные edges и verts
        for f in keep_faces:
            for e in f.edges:
                keep_edges.add(e)
                for v in e.verts:
                    keep_verts.add(v)
                pass
            pass
        pass

        # Всё остальное — на удаление
        del_faces = [f for f in bm.faces if f not in keep_faces]
        #del_edges = [e for e in bm.edges if e not in keep_edges]
        #del_verts = [v for v in bm.verts if v not in keep_verts]

        # Удаляем (порядок важен)
        bmesh.ops.delete(bm, geom=del_faces, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.is_valid and not v.link_faces], context='VERTS')
        return

    def cut_cell(start_mesh, outer_layer_name, voronoi_mode, results_objects_join_mode, sites_delaunay_params, site_idx, spacing, center_of_mass, bbox_aligned):
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
                    outer_layer = src_mesh.faces.layers.int.get(outer_layer_name)

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
                            if voronoi_mode=='VOLUME': # fill faces after bisect
                                surround = [e for e in res_bisect['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
                                if surround:
                                    fres = bmesh.ops.edgenet_prepare(src_mesh, edges=surround)
                                    if fres['edges']:
                                        #bmesh.ops.edgeloop_fill(src_mesh, edges=fres['edges']) # has glitches
                                        #bmesh.ops.holes_fill(src_mesh, edges=fres['edges'])
                                        mfilled = bmesh.ops.triangle_fill(src_mesh, use_beauty=True, use_dissolve=True, edges=fres['edges'], normal=plane_no)
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
        src_mesh.faces.ensure_lookup_table()
        src_mesh.faces.index_update() # sort faces by indexes for 
        src_mesh.edges.ensure_lookup_table()
        src_mesh.edges.index_update() # sort edges by indexes for 
        if voronoi_mode=='VOLUME' and normal_update==True:
            src_mesh.normal_update()
        
        arr_pydata = []
        if results_objects_join_mode == 'RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT':
            arr_faces_indexes = get_face_components(src_mesh)

            if len(arr_faces_indexes)>1:
                for faces_indexes in arr_faces_indexes:
                    src_mesh_copy = src_mesh.copy()
                    src_mesh_copy.verts.ensure_lookup_table()
                    src_mesh_copy.verts.index_update() # sort edges by indexes for 
                    src_mesh_copy.edges.ensure_lookup_table()
                    src_mesh_copy.edges.index_update() # sort edges by indexes for 
                    src_mesh_copy.faces.ensure_lookup_table()
                    src_mesh_copy.faces.index_update() # sort faces by indexes for 
                    keep_only_component(src_mesh_copy, faces_indexes)
                    pydata1 = get_bmesh_data(src_mesh_copy, outer_layer_name, voronoi_mode)
                    if pydata1:
                        arr_pydata.append(pydata1)
                    src_mesh_copy.clear()
                    src_mesh_copy.free()
                    pass
                pass
            else:
                pydata1 = get_bmesh_data(src_mesh, outer_layer_name, voronoi_mode)
                if pydata1:
                    arr_pydata.append(pydata1)
                pass
        else:
            pydata1 = get_bmesh_data(src_mesh, outer_layer_name, voronoi_mode)
            if pydata1:
                arr_pydata.append(pydata1)
            pass

        src_mesh.clear() #remember to clear geometry before return
        src_mesh.free()
        return arr_pydata

    verts_out = []
    edges_out = []
    faces_out = []
    outer_verts_property_out = []
    outer_edges_property_out = []
    outer_faces_property_out = []
    used_sites_idx = []
    used_sites_verts = []


    if len(sites)>=2:
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

        start_mesh = bmesh_from_pydata(verts, [], faces, normal_update=True)
        # fill all faces as outer
        outer_layer_name = "__outer__"
        start_mesh.faces.layers.int.new(outer_layer_name)
        outer_faces_layer = start_mesh.faces.layers.int.get(outer_layer_name)
        for start_mesh_face in start_mesh.faces:
            start_mesh_face[outer_faces_layer] = 1
        start_mesh.edges.layers.int.new(outer_layer_name)
        outer_edges_layer = start_mesh.edges.layers.int.get(outer_layer_name)
        for edge in start_mesh.edges:
            len_linked_faces = len(edge.link_faces)
            if mode=='SURFACE':
                if len_linked_faces==1:
                    edge[outer_edges_layer] = 1 # outer edge of surface (border of surface)
                elif len_linked_faces==2:
                    edge[outer_edges_layer] = 2 # inner edge of surface (inside)
                else:
                    edge[outer_edges_layer] = 3 # non-manifold edge on voronoi SURFACE mode (==0 or >2)
            elif mode=='VOLUME':
                edge[outer_edges_layer] = 1
            else:
                raise Exception(f'Unknown mode="{mode}" in voronoi_on_mesh_bmesh')

        for site_idx in range(len(sites)):
            if(mask[site_idx]):
                cells = cut_cell(start_mesh, outer_layer_name, mode, results_objects_join_mode, sites_delaunay_params, site_idx, spacing[site_idx], center_of_mass, bbox_aligned)
                if cells:
                    for cell in cells:
                        new_verts, new_edges, new_faces, new_verts_outer_property, new_edges_outer_property, new_outer_faces_property = cell
                        if new_verts:
                            verts_out.append(new_verts)
                            edges_out.append(new_edges)
                            faces_out.append(new_faces)
                            outer_verts_property_out.append(new_verts_outer_property)
                            outer_edges_property_out.append(new_edges_outer_property)
                            outer_faces_property_out.append(new_outer_faces_property)
                            used_sites_idx.append( site_idx )
                            used_sites_verts.append( sites[site_idx] )
                            pass
                        pass
                    pass
                pass
            pass
        start_mesh.clear() # remember to clear empty geometry
        start_mesh.free()
    else:
        start_mesh = bmesh_from_pydata(verts, [], faces, normal_update=False)
        new_verts, new_edges, new_faces = pydata_from_bmesh(start_mesh)  # No edges as function params. So one can get edges from bmesh.
        verts_out.append(new_verts)
        edges_out.append(new_edges)
        faces_out.append(new_faces)
        outer_verts_property_out.append([ dict(is_outer=False, is_inner=True, index=e.index) for e in new_verts])
        outer_edges_property_out.append([ dict(is_outer=False, is_inner=True, index=e.index) for e in new_edges])
        outer_edges_property_out.append([ dict(is_outer=False, is_inner=True) for e in new_edges])
        outer_faces_property_out = [[1 for f in new_faces]] # all faces are outer
        start_mesh.clear() # remember to clear empty geometry
        start_mesh.free()
    

    # show statistics:
    # bisects - count of bisects in cut_cell
    # unb - unpredicted erased mesh (bbox_aligned cannot make predicted results)
    # sites - count of sites in process
    # mask - mask of sites that uset to the result. Empty list all sites uset to result.
    # print( f"bisects: {num_bisect: 4d}, unb={num_unpredicted_erased: 4d}, sites={len(sites)}")
    return verts_out, edges_out, faces_out, used_sites_idx, used_sites_verts, outer_verts_property_out, outer_edges_property_out, outer_faces_property_out

def voronoi_on_mesh(verts, faces, sites, thickness,
    spacing = 0.0,
    clip_inner=True, clip_outer=True, do_clip=True,
    clipping=1.0, mode = 'REGIONS', normal_update=False,
    results_objects_join_mode = 'RESULTS_OBJECTS_JOIN_MODE_KEEP',
    precision = 1e-8,
    mask = []
    ):

    all_points = [site for site in sites if site]
    verts, edges, faces, used_sites_idx, used_sites_verts, outer_verts_property_out, outer_edges_property_out, outer_faces_property = voronoi_on_mesh_bmesh(verts, faces, len(sites), all_points,
            spacing = spacing, mode = mode, normal_update = normal_update, results_objects_join_mode = results_objects_join_mode,
            precision = precision, mask=mask)
    return verts, edges, faces, used_sites_idx, used_sites_verts, outer_verts_property_out, outer_edges_property_out, outer_faces_property

class SvVoronoiOnMeshOffUnlinkedSocketsMK5(bpy.types.Operator):
    '''Hide all unlinked sockets'''
    bl_idname = "node.sv_on_voronoi_on_mesh_off_unlinked_sockets_mk5"
    bl_label = "Select object as active"
    description_text: bpy.props.StringProperty(default='Only hide unlinked output sockets.\nTo hide linked socket you have to unlink it first.')

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        #node = context.node
        if node:
            for s in node.outputs:
                if not s.is_linked:
                    s.hide = True
            pass
        return {'FINISHED'}

def draw_properties(layout, node_group, node_name):
    node = bpy.data.node_groups[node_group].nodes[node_name]
    #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
    root_grid = layout.grid_flow(row_major=False, columns=1, align=True)
    root_grid.alignment = 'EXPAND'
    # grid1 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    # grid1.label(text='Viewport Display:')

    grid2 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    grid2.label(text='Output Sockets:')
    row0 = grid2.row(align=True)
    row0.label(text='- socket is visible', icon='CHECKBOX_HLT')
    row0.label(text='- socket is hidden', icon='CHECKBOX_DEHLT')
    grid2.separator()
    row_op = grid2.row(align=True)
    row_op.alignment = "LEFT"
    op = row_op.operator(SvVoronoiOnMeshOffUnlinkedSocketsMK5.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    op.node_group = node_group
    op.node_name  = node_name

    for s in node.outputs:
        row = grid2.row(align=True)
        row.enabled = not s.is_linked
        row.prop(s, 'hide', text=f'{s.label if s.label else s.name}{" (linked)" if s.is_linked else ""}', invert_checkbox=True)

    row_op = grid2.row(align=True)
    row_op.alignment = "LEFT"
    op = row_op.operator(SvVoronoiOnMeshOffUnlinkedSocketsMK5.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    op.node_group = node_group
    op.node_name  = node_name
    pass


class SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5(bpy.types.Operator):
    '''Additional objects properties\nYou can pan dialog window out of node.'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.viewport_display_properties_dialog_voronoi_on_mesh_mk5"
    bl_label = "Voronoi On Mesh node properties"

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    # def is_extended():
    #     return True

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.node_name = context.node.name
        self.node_group = context.annotation_data_owner.name_full
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        draw_properties(self.layout, self.node_group, self.node_name)
        pass

class SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5(bpy.types.Panel):
    '''Additional objects properties'''
    # this combination do not show this panel on the right side panel
    bl_idname="SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5"
    bl_label = "Voronoi On Mesh node properties as Dialog Window."
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    # @classmethod
    # def description(cls, context, properties):
    #     s = "properties.description_text"
    #     return s

    # horizontal size
    bl_ui_units_x = 15

    def draw(self, context):
        if hasattr(context, "node"):
            node_name = context.node.name
            node_group = context.annotation_data_owner.name_full
            draw_properties(self.layout, node_group, node_name)
        pass

class SV_PT_ViewportDisplayInformationVoronoiOnMeshMK5(bpy.types.Panel):
    '''Additional information'''
    # this combination do not show this panel on the right side panel
    bl_idname="SV_PT_ViewportDisplayInformationVoronoiOnMeshMK5"
    bl_label = "Additional information"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    # @classmethod
    # def description(cls, context, properties):
    #     s = "properties.description_text"
    #     return s

    # horizontal size
    bl_ui_units_x = 22

    def draw(self, context):
        if hasattr(context, "node"):
            node_name = context.node.name
            node_group = context.annotation_data_owner.name_full
            #draw_properties(self.layout, node_group, node_name)
            #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
            #root_grid = self.layout.grid_flow(row_major=False, columns=2, align=True)
            root_grid = self.layout.grid_flow(row_major=False, columns=1, align=True)
            root_grid.alignment = 'EXPAND'
            text="'Voronoi Sites Matrices' is Identity Matrix now. If output results join mode is not 'Split (disconnect or sites)' or if it is 'Split (disconnect or sites)' but 'Align results to'!='Voronoi Sites' then 'Voronoi Sites Matrices' has no sense. So results in this socket set with Identity Matrices"
            region_width = context.region.width
            chars = int(region_width / 7)
            for line in textwrap.wrap(text, width=80):
                root_grid.label(text=line)
        pass


class SvVoronoiOnMeshNodeMK5(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Mesh
    Tooltip: Generate Voronoi diagram on the surface of a mesh object
    """
    bl_idname = 'SvVoronoiOnMeshNodeMK5'
    bl_label = 'Voronoi on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'scipy'}

    voronoi_spacing : FloatProperty(
        name = "Spacing",
        default = 0.0,
        #min = 0.0,
        description="Percent of space to leave between generated fragment meshes",
        update=updateNode) # type: ignore

    correct_normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Postprocess:\nMake sure that all normals of generated meshes point outside.\n(Works in volume mode only)",
        update = updateNode) # type: ignore

    def update_sockets(self, context):
        self.inputs['voronoi_spacing'].hide_safe = self.voronoi_mode not in {'VOLUME', 'SURFACE'}
        updateNode(self, context)

    voronoi_modes = [
            ('VOLUME', "Volume", "Split volume of the mesh into regions of Voronoi diagram. If Mesh is not Closed and Manifold then results are weirded", 0),
            ('SURFACE', "Surface", "Split the surface of the mesh into regions of Vornoi diagram. Can be applied to Closed meshes too", 1),
            #('RIDGES', "Ridges near Surface", "Generate ridges of 3D Voronoi diagram near the surface of the mesh", 2),
            #('REGIONS', "Regions near Surface", "Generate regions of 3D Voronoi diagram near the surface of the mesh", 3)
        ]

    voronoi_mode : EnumProperty(
        name = "Voronoi Mode",
        items = voronoi_modes,
        default = 'VOLUME',
        update = update_sockets) # type: ignore
    
    results_objects_join_modes = [
            ('RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT', "Split (disconnect)", "Post processing:\nSeparate (disconnect) the results meshes into individual meshes\nIn process sites can produce more than 1 unconnected objects (volume or surface)", 'SNAP_VERTEX', 0),
            ('RESULTS_OBJECTS_JOIN_MODE_SPLIT_SITES', "Split (sites)", "Post processing:\nSeparate the results meshes into sites meshes.\nCan hold several inner unconnected meshes in one site result", 'SNAP_VERTEX', 1),
            ('RESULTS_OBJECTS_JOIN_MODE_KEEP', "Keep", "Post processing:\nKeep parts of the sources meshes as source meshes.", 'SYNTAX_ON', 2),
            ('RESULTS_OBJECTS_JOIN_MODE_MERGE', "Merge", "Post processing:\nJoin all results meshes into a single mesh", 'STICKY_UVS_LOC', 3)
        ]

    results_objects_join_mode : EnumProperty(
        name = "Output objects join mode postprocess",
        items = results_objects_join_modes,
        default = 'RESULTS_OBJECTS_JOIN_MODE_KEEP',
        update = updateNode) # type: ignore
    
    results_objects_origins_modes = [
            ('ALIGN_SOURCES_OBJECTS_ORIGIN', "Sources origins", "Post processing:\nAlign origins of results objects to parent objects origins.\n'Align Vertices to' works in Split mode only.\nUse only 'Matrices' output socket to get real world position", 'ORIENTATION_VIEW', 0),
            ('ALIGN_INPUT_SITES', "Voronoi Sites", "Post processing:\nAlign origins of results objects to input Voronoi Sites.\n'Align Vertices to' works in Postprocessing 'Split (disconnect)' mode only.\nUse 'Matrices' output socket with 'Sites Matrices' output socket to get real world position", 'STICKY_UVS_DISABLE', 1),
        ]

    results_objects_origins : EnumProperty(
        name = "Origins results objects",
        default = 'ALIGN_SOURCES_OBJECTS_ORIGIN',
        items = results_objects_origins_modes,
        description="Set results objects origins",
        update = updateNode) # type: ignore
    
    source_objects_join_modes = [
            ('SOURCE_OBJECTS_JOIN_MODE_SPLIT', "Split (disconnect)", "Preprocess input objects: Separate the result meshes into individual meshes", 'SNAP_VERTEX', 0),
            ('SOURCE_OBJECTS_JOIN_MODE_KEEP' , "Keep", "Preprocess input objects: Keep as input meshes", 'SYNTAX_ON', 1),
            ('SOURCE_OBJECTS_JOIN_MODE_MERGE', "Merge", "Preprocess input objects: Join all meshes into a single mesh", 'STICKY_UVS_LOC', 2)
        ]

    source_objects_join_mode : EnumProperty(
        name = "Input objects join mode preprocess",
        items = source_objects_join_modes,
        default = 'SOURCE_OBJECTS_JOIN_MODE_KEEP',
        update = updateNode) # type: ignore

    def updateMaskMode(self, context):
        if self.mask_mode=='BOOLEAN':
            self.inputs["voronoi_sites_mask"].label = "Mask of Sites"
        elif self.mask_mode=='INDEXES':
            self.inputs["voronoi_sites_mask"].label = "Indexes of Sites"
        updateNode(self, context)

    mask_modes = [
            ('BOOLEAN', "Booleans", "Boolean values (0/1) as mask of Voronoi Sites per objects [[0,1,0,0,1,1],[1,1,0,0,1],...]. Has no influence if socket is not connected (All sites are used)", 0),
            ('INDEXES', "Indexes", "Indexes as mask of Voronoi Sites per objects [[1,2,0,4],[0,1,4,5,7],..]. Has no influence if socket is not connected (All sites are used)", 1),
        ]
    mask_mode : EnumProperty(
        name = "Mask mode",
        items = mask_modes,
        default = 'BOOLEAN',
        #update = updateMaskMode
        update = updateNode
        ) # type: ignore

    mask_inversion : BoolProperty(
        name = "Invert",
        default = False,
        description="Invert mask of sites. Has no influence if socket is not connected (All sites are used)",
        update = updateNode) # type: ignore


    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh bisecting procedure",
            default = 6,
            min = 1,
            update = updateNode) # type: ignore
    
    def draw_vertices_in_socket(self, socket, context, layout):
        row = layout.row()
        row.alignment = 'LEFT'
        col = row.column()
        if socket.is_linked:  # linked INPUT or OUTPUT
            col.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            col.label(text=f'{socket.label}')
        col = row.column(align=True)
        col.alignment = 'RIGHT'
        col.prop(self, 'source_objects_join_mode', text='')
        pass

    def draw_vertices_out_socket(self, socket, context, layout):
        # grid = layout.grid_flow(row_major=True, columns=2, align=False,)
        # grid.label(text='')
        # col1 = grid.column()
        # col1.alignment = 'RIGHT'
        # if socket.is_linked:  # linked INPUT or OUTPUT
        #     col1.label(text=f"{socket.label}. {socket.objects_number or ''} ")
        # else:
        #     col1.label(text=f'{socket.label} ')
        # col = grid.column()
        # col.alignment='RIGHT'
        # col.label(text=f'Postprocessing:')
        # grid.prop(self, 'results_join_mode', text='')
        # col = grid.column()
        # col.alignment='RIGHT'
        # col.label(text='Align vertices to:')
        # grid.prop(self, 'results_objects_origins', text='')
        
        #grid = layout.grid_flow(row_major=True, columns=1, align=False,)
        row = layout.column().row()
        row.alignment = 'RIGHT'
        row.prop(self, 'results_objects_join_mode', text='')
        if socket.is_linked:  # linked INPUT or OUTPUT
            row.label(text=f"{socket.label}. {socket.objects_number or ''} ")
        else:
            row.label(text=f'{socket.label} ')
        pass

    def draw_sites_matrices_out_socket(self, socket, context, layout):
        col = layout.row(align=True)
        col.alignment='RIGHT'
        if (self.results_objects_join_mode in ['RESULTS_OBJECTS_JOIN_MODE_SPLIT_SITES', 'RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT'] and self.results_objects_origins=='ALIGN_INPUT_SITES')==False:
            col.popover(panel=SV_PT_ViewportDisplayInformationVoronoiOnMeshMK5.bl_idname, icon='INFO', text="",)
        col_prop = col.row()
        col_prop.alignment='RIGHT'
        if self.results_objects_join_mode in ['RESULTS_OBJECTS_JOIN_MODE_SPLIT_SITES', 'RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT'] == False:
            col_prop.enabled=False
        #col_prop.prop(self, 'results_objects_origins', text='')
        if socket.is_linked:  # linked INPUT or OUTPUT
            col.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            col.label(text=f'{socket.label}')
        pass

    def draw_voronoi_sites_mask_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=True, columns=2)
        if not socket.is_linked:
            grid.enabled = False
        col2 = grid.column()
        col2_row1 = col2.row()
        col2_row1.alignment='LEFT'
        if socket.is_linked:
            col2_row1.label(text=f"Mask of sites. {socket.objects_number or ''}:")
        else:
            col2_row1.label(text=f"Mask of sites:")
        col2_row2 = col2.row()
        col2_row2.alignment='LEFT'
        col2_row2.column(align=True).prop(self, "mask_inversion")
        col3 = grid.column()
        col3.prop(self, "mask_mode", expand=True)


    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvVerticesSocket', 'vertices'          ).label     = 'Vertices'
        self.inputs.new('SvStringsSocket' , 'polygons'          ).label     = 'Polygons'
        self.inputs.new('SvMatrixSocket'  , 'matrices'          ).label     = 'Matrices of Meshes'
        self.inputs.new('SvVerticesSocket', 'voronoi_sites'     ).label     = 'Voronoi Sites'
        self.inputs.new('SvStringsSocket' , 'voronoi_sites_mask').label     = "Mask of Voronoi Sites"
        self.inputs.new('SvStringsSocket' , 'voronoi_spacing'   ).prop_name = 'voronoi_spacing'

        self.inputs['vertices']             .custom_draw = 'draw_vertices_in_socket'
        self.inputs['voronoi_sites_mask']   .custom_draw = 'draw_voronoi_sites_mask_in_socket'

        self.outputs.new('SvVerticesSocket', "vertices"             ).label = 'Vertices'
        self.outputs.new('SvVerticesSocket', "verticesOuter"        ).label = 'Outer Vertices'
        self.outputs.new('SvVerticesSocket', "verticesInner"        ).label = 'Inner Vertices'
        self.outputs.new('SvVerticesSocket', "verticesBorder"       ).label = 'Border Vertices'
        self.outputs.new('SvStringsSocket' , "verticesOuterIndexes" ).label = 'Outer Indexes Vertices'
        self.outputs.new('SvStringsSocket' , "verticesInnerIndexes" ).label = 'Inner Indexes Vertices'
        self.outputs.new('SvStringsSocket' , "verticesBorderIndexes").label = 'Border Indexes Vertices'
        self.outputs.new('SvStringsSocket' , "verticesOuterMasks"   ).label = 'Outer Masks Vertices'
        self.outputs.new('SvStringsSocket' , "verticesInnerMasks"   ).label = 'Inner Masks Vertices'
        self.outputs.new('SvStringsSocket' , "verticesBorderMasks"  ).label = 'Border Masks Vertices'
        self.outputs.new('SvStringsSocket' , "edges"                ).label = 'Edges'
        self.outputs.new('SvStringsSocket' , "edgesOuter"           ).label = 'Outer Edges'
        self.outputs.new('SvStringsSocket' , "edgesInner"           ).label = 'Inner Edges'
        self.outputs.new('SvStringsSocket' , "edgesBorder"          ).label = 'Border Edges'
        self.outputs.new('SvStringsSocket' , "edgesOuterIndexes"    ).label = 'Outer Indexes Edges'
        self.outputs.new('SvStringsSocket' , "edgesInnerIndexes"    ).label = 'Inner Indexes Edges'
        self.outputs.new('SvStringsSocket' , "edgesBorderIndexes"   ).label = 'Border Indexes Edges'
        self.outputs.new('SvStringsSocket' , "edgesOuterMasks"      ).label = 'Outer Masks Edges'
        self.outputs.new('SvStringsSocket' , "edgesInnerMasks"      ).label = 'Inner Masks Edges'
        self.outputs.new('SvStringsSocket' , "edgesBorderMasks"     ).label = 'Border Masks Edges'
        self.outputs.new('SvStringsSocket' , "polygons"             ).label = 'Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsOuterInner"   ).label = 'Outer Inner Mask Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsOuter"        ).label = 'Outer Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsInner"        ).label = 'Inner Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsOuterIndexes" ).label = 'Outer Indexes Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsInnerIndexes" ).label = 'Inner Indexes Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsOuterMasks"   ).label = 'Outer Masks Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsInnerMasks"   ).label = 'Inner Masks Polygons'
        self.outputs.new('SvStringsSocket' , "sites_idx"            ).label = 'Used Sites Idx'
        self.outputs.new('SvStringsSocket' , "sites_verts"          ).label = 'Used Sites Verts'
        self.outputs.new('SvMatrixSocket'  , 'matrices'             ).label = 'Matrices'
        self.outputs.new('SvMatrixSocket'  , 'sites_matrices'       ).label = 'Voronoi Sites Matrices'

        self.outputs['vertices']        .custom_draw = 'draw_vertices_out_socket'
        self.outputs['sites_matrices']  .custom_draw = 'draw_sites_matrices_out_socket'

        self.outputs["verticesOuter"]           .hide = True
        self.outputs["verticesInner"]           .hide = True
        self.outputs["verticesBorder"]          .hide = True
        self.outputs["verticesOuterIndexes"]    .hide = True
        self.outputs["verticesInnerIndexes"]    .hide = True
        self.outputs["verticesBorderIndexes"]   .hide = True
        self.outputs["edgesOuter"]              .hide = True
        self.outputs["edgesInner"]              .hide = True
        self.outputs["edgesBorder"]             .hide = True
        self.outputs["edgesOuterIndexes"]       .hide = True
        self.outputs["edgesInnerIndexes"]       .hide = True
        self.outputs["edgesBorderIndexes"]      .hide = True
        self.outputs["polygonsOuterInner"]      .hide = True
        self.outputs["polygonsOuter"]           .hide = True
        self.outputs["polygonsInner"]           .hide = True
        self.outputs["polygonsOuterIndexes"]    .hide = True
        self.outputs["polygonsInnerIndexes"]    .hide = True

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        grid = layout.box().grid_flow(row_major=True, columns=2, align=True)

        row21 = grid.row()
        row22 = grid.row()
        row21.alignment = 'RIGHT'
        row21.label(text="Voronoi Mode:")
        row22.prop(self, 'voronoi_mode', expand=True)

        row31 = grid.row()
        row32 = grid.row()
        if self.voronoi_mode != 'VOLUME':
            row31.enabled = False
            row32.enabled = False
        row31.alignment = 'RIGHT'
        row31.label(text="Correct normals:")
        row32.prop(self, 'correct_normals', text='')

        # row51 = grid.row()
        # row52 = grid.row()
        # row51.alignment = 'RIGHT'
        # row51.label(text='Source join mode:')
        # row52.prop(self, 'source_objects_join_mode', text='', )

        # row41 = grid.row()
        # row42 = grid.row()
        # row41.alignment = 'RIGHT'
        # row41.label(text='Results join mode:')
        # row42.prop(self, 'results_join_mode', text='', )

        row11 = grid.row()
        row12 = grid.row()
        if (self.results_objects_join_mode in ['RESULTS_OBJECTS_JOIN_MODE_SPLIT_SITES', 'RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT']) == False:
            row11.enabled = False
            row12.enabled = False
        row11.alignment = 'RIGHT'
        row11.label(text='Align results to:')
        row12.column(align=True).prop(self, 'results_objects_origins', text='', )

        row01 = grid.row()
        row02 = grid.row(align=True)
        row01.alignment='RIGHT'
        row01.label(text='Settings:')
        row02.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row02.column(align=True).popover(panel=SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5.bl_idname, icon='DOWNARROW_HLT', text="")

        pass

    def draw_buttons_ext(self, context, layout):
        grid = layout.grid_flow(row_major=True, columns=2, align=True)

        row21 = grid.row()
        row22 = grid.row()
        row21.alignment = 'RIGHT'
        row21.label(text="Voronoi Mode:")
        row22.prop(self, 'voronoi_mode', expand=True)

        row31 = grid.row()
        row32 = grid.row()
        if self.voronoi_mode != 'VOLUME':
            row31.enabled = False
            row32.enabled = False
        row31.alignment = 'RIGHT'
        row31.label(text="Correct normals:")
        row32.prop(self, 'correct_normals', text='')

        row51 = grid.row()
        row52 = grid.row()
        row51.alignment = 'RIGHT'
        row51.label(text='Source join mode:')
        row52.prop(self, 'source_objects_join_mode', text='', )

        row41 = grid.row()
        row42 = grid.row()
        row41.alignment = 'RIGHT'
        row41.label(text='Results join mode:')
        row42.prop(self, 'results_objects_join_mode', text='', )

        row11 = grid.row()
        row12 = grid.row()
        if (self.results_objects_join_mode in ['RESULTS_OBJECTS_JOIN_MODE_SPLIT_SITES', 'RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT']) == False:
            row11.enabled = False
            row12.enabled = False
        row11.alignment = 'RIGHT'
        row11.label(text='Align results to:')
        row12.prop(self, 'results_objects_origins', text='', )

        row61 = grid.row()
        row62 = grid.row()
        row61.alignment = 'RIGHT'
        row61.label(text='Accuracy:')
        row62.prop(self, 'accuracy', text='', )
        # TODO: remove input sockets
        pass

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return
        
        if self.inputs["vertices"].is_linked:
            if self.inputs["polygons"].is_linked==False:
                raise Exception(f'socket Polygons are not connected')
            if self.inputs["voronoi_sites"].is_linked==False:
                raise Exception(f'socket "Voronoi Sites" are not connected')

        verts_in    = self.inputs['vertices']      .sv_get(deepcopy=False)
        faces_in    = self.inputs['polygons']      .sv_get(deepcopy=False)
        _Matrices   = self.inputs['matrices'].sv_get(default=[[Matrix()]], deepcopy=False)
        Matrices2   = ensure_nesting_level(_Matrices, 2)
        sites_in    = self.inputs['voronoi_sites'] .sv_get(deepcopy=False)

        mask_in     = self.inputs['voronoi_sites_mask'] #.sv_get(deepcopy=False)
        if mask_in.is_linked==False:
            mask_in = [[]]
        else:
            mask_in = mask_in.sv_get(deepcopy=False)
            
        voronoi_spacing_in  = self.inputs['voronoi_spacing'].sv_get(deepcopy=False)

        verts_in    = ensure_nesting_level(verts_in, 3)
        input_level = get_data_nesting_level(sites_in, search_first_data=True)
        if input_level<=2:
            sites_in = ensure_nesting_level(sites_in, 3)

        faces_in    = ensure_nesting_level(faces_in, 3)
        voronoi_spacing_in  = ensure_min_nesting(voronoi_spacing_in, 2)
        mask_in     = ensure_min_nesting(mask_in, 2)

        precision   = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        matrices_out = []
        sites_matrices_split_mode_out = []
        outer_verts_property_out = []
        outer_edges_property_out = []
        outer_polygons_property_out = []
        sites_idx_out = []
        sites_verts_out = []

        matrix_0 = None
        matrix_0_inverted = None

        verts_in_1 = []
        faces_in_1 = []
        sites_in_1 = []
        voronoi_spacing_in_1 = []
        mask_in_1 = []
        matrices_in_1 = []

        len_verts_in = len(verts_in)
        if len_verts_in>len(faces_in):
            raise Exception(f'list of verts less than faces [{len(verts_in)}<{len(faces_in)}]')
        
        #for I, (verts_I, faces_I, sites_I, voronoi_spacing_I, mask_I) in enumerate(zip_long_repeat(verts_in, faces_in, sites_in, voronoi_spacing_in, mask_in)):
        for I, verts_I in enumerate(verts_in):
            faces_I = faces_in[I if I<=len(faces_in)-1 else -1]
            sites_I = sites_in[I if I<=len(sites_in)-1 else -1]
            voronoi_spacing_I = voronoi_spacing_in[I if I<=len(voronoi_spacing_in)-1 else -1]
            mask_I = mask_in[I if I<=len(mask_in)-1 else -1]

            if len(faces_I)==0:
                raise Exception(f'no faces in Polygons[{I}]')
            if len(sites_I)==0:
                raise Exception(f'no sites in socket "Voronoi Sites" {I} ')
            else:
                empty_sites = [I for I, s in enumerate(sites_I) if len(s)==0]
                if len(empty_sites)>0:
                    raise Exception(f'no sites in socket "Voronoi Sites" {empty_sites}')

            if I<=len(Matrices2[0])-1:
                matrix_I = Matrices2[0][I]
            else:
                matrix_I = Matrices2[0][-1]
            
            if matrix_0 is None:
                matrix_0 = matrix_I
                matrix_0_inverted = matrix_0.inverted()

            # if mask is zero or not connected then do not mask any. Except of inversion,
            if not mask_I:
                np_mask = np.ones(len(sites_I), dtype=bool)
                if self.inputs['voronoi_sites_mask'].is_linked and self.mask_inversion==True:
                    np_mask = np.invert(np_mask)
                mask_I = np_mask.tolist()
            else:
                if self.mask_mode=='BOOLEAN':
                    if self.mask_inversion==True:
                        mask_I = list( map( lambda v: False if v==0 else True, mask_I) )
                        mask_I = mask_I[:len(sites_I)]
                        np_mask = np.zeros(len(sites_I), dtype=bool)
                        np_mask[0:len(mask_I)]=mask_I
                        np_mask = np.invert(np_mask)
                        mask_I = np_mask.tolist()
                    pass
                elif self.mask_mode=='INDEXES':
                    mask_len = len(sites_I)
                    mask_range = []
                    for x in mask_I:
                        if -mask_len<x<mask_len:
                            mask_range.append(x)
                    np_mask = np.zeros(len(sites_I), dtype=bool)
                    np_mask[mask_range] = True
                    if self.mask_inversion==True:
                        np_mask = np.invert(np_mask)
                    mask_I = np_mask.tolist()
                pass

            mtr = matrix_I@matrix_0_inverted

            verts_in_1   .append(verts_I)
            faces_in_1   .append(faces_I)
            matrices_in_1.append(matrix_I)
            sites_in_1   .append(sites_I)
            voronoi_spacing_in_1 .append(voronoi_spacing_I)
            mask_in_1    .append(mask_I)

            pass


        verts_in_2    = []
        faces_in_2    = []
        matrices_in_2 = []
        sites_in_2    = []
        voronoi_spacing_in_2  = []
        mask_in_2     = []

        if self.source_objects_join_mode=='SOURCE_OBJECTS_JOIN_MODE_SPLIT':
            for I, verts_in_1_I in enumerate(verts_in_1):
                objects_I_verts, object_I_faces, _ = separate_loose_mesh(verts_in_1_I, faces_in_1[I])
                if len(objects_I_verts)>1:
                    for IJ, verts_IJ in enumerate(objects_I_verts):
                        verts_in_2              .append(verts_IJ                )
                        faces_in_2              .append(object_I_faces      [IJ])
                        matrices_in_2           .append(matrices_in_1       [I ])
                        sites_in_2              .append(sites_in_1          [I ])
                        voronoi_spacing_in_2    .append(voronoi_spacing_in_1[I ])
                        mask_in_2               .append(mask_in_1           [I ])
                        pass
                else:
                    verts_in_2          .append(verts_in_1_I           )
                    faces_in_2          .append(faces_in_1          [I])
                    matrices_in_2       .append(matrices_in_1       [I])
                    sites_in_2          .append(sites_in_1          [I])
                    voronoi_spacing_in_2.append(voronoi_spacing_in_1[I])
                    mask_in_2           .append(mask_in_1           [I])
                pass
            pass
        elif self.source_objects_join_mode=='SOURCE_OBJECTS_JOIN_MODE_MERGE':
            matrices_in_1_0_inverted = matrices_in_1[0].inverted()
            verts_for_merge = [verts_in_1[0]]
            sites_for_merge = sites_in_1[0][:]
            for I, mat_I in enumerate(matrices_in_1):
                if I>0:
                    mat = matrices_in_1_0_inverted @ mat_I
                    verts_mat = []
                    for v in verts_in_1[I]:
                        v1 = mat @ Vector(v)
                        verts_mat.append( (v1.x, v1.y, v1.z) )
                        pass
                    verts_for_merge.append(verts_mat)

                    sites_mat = []
                    # On merge source meshes do use source sites, not zipped in zip_long_repeat. 
                    # If original sites are less objects then use only these sites
                    if len(sites_in)-1>=I:
                        for s in sites_in[I]:
                            s1 = mat @ Vector(s)
                            sites_mat.append((s1.x, s1.y, s1.z))
                            pass
                        sites_for_merge.extend(sites_mat)
                    #sites_for_merge.extend(sites_in_1[I]) # use sites as local
                    pass
                pass
            merged_verts, _, merged_faces  = mesh_join(verts_for_merge, [], faces_in_1)
            verts_in_2              = [merged_verts]
            faces_in_2              = [merged_faces]
            matrices_in_2.append(matrices_in_1[0])
            sites_in_2              = [sites_for_merge]
            voronoi_spacing_in_2    = [voronoi_spacing_in_1[0]]
            merged_masks = []
            for m in mask_in_1:
                merged_masks = merged_masks+m
            mask_in_2 = [merged_masks]
            pass
        else:
            verts_in_2    = verts_in_1
            faces_in_2    = faces_in_1
            matrices_in_2 = matrices_in_1
            sites_in_2    = sites_in_1
            voronoi_spacing_in_2  = voronoi_spacing_in_1
            mask_in_2     = mask_in_1
            pass
        pass


        for I, (verts_I, faces_I, matrices_I, sites_I, voronoi_spacing_I, mask_I) in enumerate( zip(verts_in_2, faces_in_2, matrices_in_2, sites_in_2, voronoi_spacing_in_2, mask_in_2) ):
            new_verts, new_edges, new_faces, new_used_sites_idx, new_used_sites_verts, outer_verts_property, outer_edges_property, outer_faces_property = voronoi_on_mesh(verts_I, faces_I, sites_I, thickness=0,
                            spacing = voronoi_spacing_I,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.voronoi_mode,
                            results_objects_join_mode = self.results_objects_join_mode,
                            normal_update = self.correct_normals,
                            precision = precision,
                            mask = mask_I
                            )

            # collect sites_idx and used_sites_verts independently of self.results_objects_join_mode
            sites_idx_out.append(new_used_sites_idx)
            sites_verts_out.append(new_used_sites_verts)
            
            if self.results_objects_join_mode in ['RESULTS_OBJECTS_JOIN_MODE_SPLIT_SITES', 'RESULTS_OBJECTS_JOIN_MODE_SPLIT_DISCONNECT']:
                if self.results_objects_origins=='ALIGN_INPUT_SITES':
                    for IJ, obj_verts in enumerate(new_verts):
                        s1 = new_used_sites_verts[IJ]
                        mat_site_translation = Matrix.Translation(s1)
                        mat_site_translation_inverted = mat_site_translation.inverted()
                        obj_verts_site = []
                        for obj_vert in obj_verts:
                            v = mat_site_translation_inverted @ Vector(obj_vert)
                            obj_verts_site.append(v)
                        verts_out.append(obj_verts_site)
                        sites_matrices_split_mode_out.append(mat_site_translation)
                    pass
                elif self.results_objects_origins=='ALIGN_SOURCES_OBJECTS_ORIGIN':
                    verts_out.extend(new_verts)
                    sites_matrices_split_mode_out.extend([Matrix()]*len(new_verts))
                    pass
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                # for s1 in new_used_sites_verts:
                #     mat_site_translation = Matrix.Translation(s1)
                #     mat = matrices_I @ mat_site_translation.inverted()
                #     sites_matrices_split_mode_out.append(mat_site_translation)
                #     matrices_out.append(mat)
                matrices_out.extend([matrices_I]*len(new_verts))
                outer_verts_property_out.extend(outer_verts_property) # dict {is_outer:True/False, is_inner: True/False}
                outer_edges_property_out.extend(outer_edges_property) # dict {is_outer:True/False, is_inner: True/False}
                outer_polygons_property_out.extend(outer_faces_property)
            elif self.results_objects_join_mode in ['RESULTS_OBJECTS_JOIN_MODE_KEEP', 'RESULTS_OBJECTS_JOIN_MODE_MERGE']:
                if self.results_objects_join_mode == 'RESULTS_OBJECTS_JOIN_MODE_KEEP':
                    matrices_out.append(matrices_I)
                    sites_matrices_split_mode_out.append(Matrix())
                verts1, edges1, faces1 = mesh_join(new_verts, new_edges, new_faces)
                verts_out.append(verts1)
                edges_out.append(edges1)
                faces_out.append(faces1)
                outer_verts = [item for sublist in outer_verts_property for item in sublist]
                outer_verts_property_out.append(outer_verts)  # dict {is_outer:True/False, is_inner: True/False}
                outer_edges = [item for sublist in outer_edges_property for item in sublist]
                outer_edges_property_out.append(outer_edges)  # dict {is_outer:True/False, is_inner: True/False}
                outer_faces = [item for sublist in outer_faces_property for item in sublist]
                outer_polygons_property_out.append(outer_faces)
            pass

        if self.results_objects_join_mode == 'RESULTS_OBJECTS_JOIN_MODE_MERGE':
            matrices_in_1_0_inverted = matrices_in_1[0].inverted()
            verts_out_for_merge = [verts_out[0]]
            for I, mat_I in enumerate(matrices_in_2):
                if I>0:
                    mat = matrices_in_1_0_inverted @ mat_I
                    verts_mat = []
                    for v in verts_out[I]:
                        v1 = mat @ Vector(v)
                        verts_mat.append( (v1.x, v1.y, v1.z) )
                        pass
                    verts_out_for_merge.append(verts_mat)
                    pass
                pass
            verts1, edges1, faces1 = mesh_join(verts_out_for_merge, edges_out, faces_out)
            verts_out = [verts1]
            edges_out = [edges1]
            faces_out = [faces1]
            matrices_out.append(matrices_in_2[0])
            sites_matrices_split_mode_out.append(Matrix())
            outer_verts = [item for sublist in outer_verts_property_out for item in sublist]
            outer_verts_property_out = [outer_verts]
            outer_edges = [item for sublist in outer_edges_property_out for item in sublist]
            outer_edges_property_out = [outer_edges]
            outer_faces = [item for sublist in outer_polygons_property_out for item in sublist]
            outer_polygons_property_out = [outer_faces]
            pass

        vertsOuter_out = []
        vertsInner_out = []
        vertsBorder_out = []
        vertsOuterIndexes_out = []
        vertsInnerIndexes_out = []
        vertsBorderIndexes_out = []
        vertsOuterMasks_out = []
        vertsInnerMasks_out = []
        vertsBorderMasks_out = []
        for I, mask in enumerate(outer_verts_property_out):
            verts_out_I = verts_out[I]
            len_verts_out_I = len(verts_out_I)
            vertsOuter_out_I = []
            vertsInner_out_I = []
            vertsBorder_out_I = []
            vertsOuterIndexes_out_I = []
            vertsInnerIndexes_out_I = []
            vertsBorderIndexes_out_I = []
            vertsOuterMasks_out_I  = [False]*len_verts_out_I
            vertsInnerMasks_out_I  = [False]*len_verts_out_I
            vertsBorderMasks_out_I = [False]*len_verts_out_I
            for IJ, (m, v) in enumerate(zip(mask, verts_out_I)):
                m_is_outer = m["is_outer"]
                m_is_inner = m["is_inner"]
                if m_is_outer==True:
                    vertsOuter_out_I       .append(v)
                    vertsOuterIndexes_out_I.append(IJ)
                    vertsOuterMasks_out_I[IJ] = True
                if m_is_inner==True:
                    vertsInner_out_I       .append(v)
                    vertsInnerIndexes_out_I.append(IJ)
                    vertsInnerMasks_out_I[IJ] = True

                if self.voronoi_mode=='VOLUME':
                    if m_is_outer==True and m_is_inner==True:
                        vertsBorder_out_I       .append(v)
                        vertsBorderIndexes_out_I.append(IJ)
                        vertsBorderMasks_out_I[IJ] = True
                    pass
                elif self.voronoi_mode=='SURFACE':
                    m_is_surface_border = m["is_surface_border"]
                    if m_is_surface_border==True:
                        vertsBorder_out_I       .append(v)
                        vertsBorderIndexes_out_I.append(IJ)
                        vertsBorderMasks_out_I[IJ] = True
                    pass
                else:
                    raise Exception(f'Unknown mode="{self.voronoi_mode}" in SvVoronoiOnMeshNodeMK5->process')
                
                if self.voronoi_mode=='SURFACE':
                    pass
                pass
            vertsOuter_out        .append(vertsOuter_out_I)
            vertsInner_out        .append(vertsInner_out_I)
            vertsBorder_out       .append(vertsBorder_out_I)
            vertsOuterIndexes_out .append(vertsOuterIndexes_out_I)
            vertsInnerIndexes_out .append(vertsInnerIndexes_out_I)
            vertsBorderIndexes_out.append(vertsBorderIndexes_out_I)
            vertsOuterMasks_out   .append(vertsOuterMasks_out_I)
            vertsInnerMasks_out   .append(vertsInnerMasks_out_I)
            vertsBorderMasks_out  .append(vertsBorderMasks_out_I)
            pass

        edgesOuter_out = []
        edgesInner_out = []
        edgesBorder_out = []
        edgesOuterIndexes_out = []
        edgesInnerIndexes_out = []
        edgesBorderIndexes_out = []
        edgesOuterMasks_out = []
        edgesInnerMasks_out = []
        edgesBorderMasks_out = []

        for I, mask in enumerate(outer_edges_property_out):
            edges_out_I = edges_out[I]
            len_edges_out_I = len(edges_out_I)
            edgesOuter_out_I = []
            edgesInner_out_I = []
            edgesBorder_out_I = []
            edgesOuterIndexes_out_I = []
            edgesInnerIndexes_out_I = []
            edgesBorderIndexes_out_I = []
            edgesOuterMasks_out_I  = [False]*len_edges_out_I
            edgesInnerMasks_out_I  = [False]*len_edges_out_I
            edgesBorderMasks_out_I = [False]*len_edges_out_I

            for IJ, (m, v) in enumerate(zip(mask, edges_out_I)):
                m_is_outer = m["is_outer"]
                m_is_inner = m["is_inner"]
                if m_is_outer==True:
                    edgesOuter_out_I.append(v)
                    edgesOuterIndexes_out_I.append(IJ)
                    edgesOuterMasks_out_I[IJ] = True
                if m_is_inner==True:
                    edgesInner_out_I.append(v)
                    edgesInnerIndexes_out_I.append(IJ)
                    edgesInnerMasks_out_I[IJ] = True
                if self.voronoi_mode=='VOLUME':
                    if m_is_outer==True and m_is_inner==True:
                        edgesBorder_out_I.append(v)
                        edgesBorderIndexes_out_I.append(IJ)
                        edgesBorderMasks_out_I[IJ] = True
                    pass
                elif self.voronoi_mode=='SURFACE':
                    m_is_surface_border = m["is_surface_border"]
                    if m_is_surface_border==True:
                        edgesBorder_out_I.append(v)
                        edgesBorderIndexes_out_I.append(IJ)
                        edgesBorderMasks_out_I[IJ] = True
                        pass
                    pass
                else:
                    raise Exception(f'Unknown mode="{self.voronoi_mode}" in SvVoronoiOnMeshNodeMK5->process')
                
                if self.voronoi_mode=='SURFACE':
                    pass
                pass
            edgesOuter_out.append(edgesOuter_out_I)
            edgesInner_out.append(edgesInner_out_I)
            edgesBorder_out.append(edgesBorder_out_I)
            edgesOuterIndexes_out.append(edgesOuterIndexes_out_I)
            edgesInnerIndexes_out.append(edgesInnerIndexes_out_I)
            edgesBorderIndexes_out.append(edgesBorderIndexes_out_I)
            edgesOuterMasks_out   .append(edgesOuterMasks_out_I)
            edgesInnerMasks_out   .append(edgesInnerMasks_out_I)
            edgesBorderMasks_out  .append(edgesBorderMasks_out_I)

            pass

        polygonsOuter_out = []
        polygonsInner_out = []
        polygonsOuterIndexes_out = []
        polygonsInnerIndexes_out = []
        polygonsOuterMasks_out = []
        polygonsInnerMasks_out = []

        for I, mask in enumerate(outer_polygons_property_out):
            faces_out_I = faces_out[I]
            len_faces_out_I = len(faces_out_I)
            polygonsOuter_out_I = []
            polygonsInner_out_I = []
            polygonsOuterIndexes_out_I = []
            polygonsInnerIndexes_out_I = []
            polygonsOuterMasks_out_I  = [False]*len_faces_out_I
            polygonsInnerMasks_out_I  = [False]*len_faces_out_I

            for IJ, (m, v) in enumerate(zip(mask, faces_out_I)):
                if m==1:
                    polygonsOuter_out_I.append(v)
                    polygonsOuterIndexes_out_I.append(IJ)
                    polygonsOuterMasks_out_I[IJ] = True
                else:
                    polygonsInner_out_I.append(v)
                    polygonsInnerIndexes_out_I.append(IJ)
                    polygonsInnerMasks_out_I[IJ] = True
                pass
            polygonsOuter_out.append(polygonsOuter_out_I)
            polygonsInner_out.append(polygonsInner_out_I)
            polygonsOuterIndexes_out.append(polygonsOuterIndexes_out_I)
            polygonsInnerIndexes_out.append(polygonsInnerIndexes_out_I)
            polygonsOuterMasks_out   .append(polygonsOuterMasks_out_I)
            polygonsInnerMasks_out   .append(polygonsInnerMasks_out_I)

            pass

        self.outputs['vertices'             ].sv_set(verts_out)
        self.outputs['verticesOuter'        ].sv_set(vertsOuter_out)
        self.outputs['verticesInner'        ].sv_set(vertsInner_out)
        self.outputs['verticesBorder'       ].sv_set(vertsBorder_out)
        self.outputs['verticesOuterIndexes' ].sv_set(vertsOuterIndexes_out)
        self.outputs['verticesInnerIndexes' ].sv_set(vertsInnerIndexes_out)
        self.outputs['verticesBorderIndexes'].sv_set(vertsBorderIndexes_out)
        self.outputs['verticesOuterMasks'   ].sv_set(vertsOuterMasks_out)
        self.outputs['verticesInnerMasks'   ].sv_set(vertsInnerMasks_out)
        self.outputs['verticesBorderMasks'  ].sv_set(vertsBorderMasks_out)
        self.outputs['edges'                ].sv_set(edges_out)
        self.outputs['edgesOuter'           ].sv_set(edgesOuter_out)
        self.outputs['edgesInner'           ].sv_set(edgesInner_out)
        self.outputs['edgesBorder'          ].sv_set(edgesBorder_out)
        self.outputs['edgesOuterIndexes'    ].sv_set(edgesOuterIndexes_out)
        self.outputs['edgesInnerIndexes'    ].sv_set(edgesInnerIndexes_out)
        self.outputs['edgesBorderIndexes'   ].sv_set(edgesBorderIndexes_out)
        self.outputs['edgesOuterMasks'      ].sv_set(edgesOuterMasks_out)
        self.outputs['edgesInnerMasks'      ].sv_set(edgesInnerMasks_out)
        self.outputs['edgesBorderMasks'     ].sv_set(edgesBorderMasks_out)
        self.outputs['polygons'             ].sv_set(faces_out)
        self.outputs['polygonsOuterInner'   ].sv_set(outer_polygons_property_out)
        self.outputs['polygonsOuter'        ].sv_set(polygonsOuter_out)
        self.outputs['polygonsInner'        ].sv_set(polygonsInner_out)
        self.outputs['polygonsOuterIndexes' ].sv_set(polygonsOuterIndexes_out)
        self.outputs['polygonsInnerIndexes' ].sv_set(polygonsInnerIndexes_out)
        self.outputs['polygonsOuterMasks'   ].sv_set(polygonsOuterMasks_out)
        self.outputs['polygonsInnerMasks'   ].sv_set(polygonsInnerMasks_out)
        self.outputs['sites_idx'            ].sv_set(sites_idx_out)
        self.outputs['sites_verts'          ].sv_set(sites_verts_out)
        self.outputs['matrices'             ].sv_set(matrices_out)
        self.outputs['sites_matrices'       ].sv_set(sites_matrices_split_mode_out)

classes = [SvVoronoiOnMeshOffUnlinkedSocketsMK5, SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5, SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5, SV_PT_ViewportDisplayInformationVoronoiOnMeshMK5, SvVoronoiOnMeshNodeMK5]
register, unregister = bpy.utils.register_classes_factory(classes)