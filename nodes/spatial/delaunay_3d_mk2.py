# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict
from itertools import combinations

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.geom import PlaneEquation, bounding_box_aligned
from sverchok.dependencies import scipy
from mathutils import Vector

if scipy is not None:
    from scipy.spatial import Delaunay
    from scipy.spatial.transform import Rotation as R

def is_volume_0(verts, idxs, threshold):
    '''Is volume size of 4 verts less threshold (True/False) '''
    if threshold == 0:
        return False
    # a, b, c, d = [verts[i] for i in idxs]
    # a, b, c, d = np.array(a), np.array(b), np.array(c), np.array(d)
    # v1 = b - a
    # v2 = c - a
    # v3 = d - a
    # v1 = v1 / np.linalg.norm(v1)
    # v2 = v2 / np.linalg.norm(v2)
    # v3 = v3 / np.linalg.norm(v3)
    # volume = np.cross(v1, v2).dot(v3) / 6

    vects = verts[ list(idxs) ] # convert set to list #np.array([verts[i] for i in idxs], dtype=np.float64)
    vects = vects-vects[0]
    vects_norm = vects[1:4]/np.linalg.norm(vects[1:4], axis=1, keepdims=True)
    v1_ = vects_norm[0]
    v2_ = vects_norm[1]
    v3_ = vects_norm[2]
    volume_ = np.cross(v1_, v2_).dot(v3_) / 6
    return abs(volume_) < threshold


def is_area_0(verts, idxs, threshold):
    '''Is area size of 3 verts less threshold (True/False) '''
    if threshold == 0:
        return False
    # a, b, c = [verts[i] for i in idxs]
    # a, b, c = np.array(a), np.array(b), np.array(c)
    # v1 = b - a
    # v2 = c - a
    # v1 = v1 / np.linalg.norm(v1)
    # v2 = v2 / np.linalg.norm(v2)
    # area = np.linalg.norm(np.cross(v1, v2)) / 2

    vects = verts[ list(idxs) ] # convert set to list #np.array([verts[i] for i in idxs], dtype=np.float64)
    vects = vects-vects[0]
    vects_norm = vects[1:3]/np.linalg.norm(vects[1:3], axis=1, keepdims=True)
    v1_ = vects_norm[0]
    v2_ = vects_norm[1]
    area_ = np.linalg.norm(np.cross(v1_, v2_)) / 2

    return abs(area_) < threshold

def is_length_0(verts, idxs, threshold):
    '''Is length size of 2 verts less threshold (True/False) '''
    if threshold == 0:
        return False
    a, b = [verts[i] for i in idxs]
    #a, b = np.array(a), np.array(b) # verts is numpy
    v1 = b - a
    len = np.linalg.norm(v1)
    return abs(len) < threshold

def get_sites_delaunay_params(np_sites, n_orig_sites, threshold=0):
    '''Calculate Delaunay with sites. '''
    # For more info see: https://github.com/nortikin/sverchok/pull/4952
    # http://www.qhull.org/html/qdelaun.htm
    # http://www.qhull.org/html/qh-optc.htm
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html

    delaunay = Delaunay(np_sites)
    dimension_size_1 = -1 # simplex size on start 
    dimension_size_2 = -1 # simplex size of finish
    simplices = []
    dict_source_dsimplex = dict()
    for i, simplex in enumerate(delaunay.simplices):
        dsimplex = tuple(simplex[simplex<n_orig_sites])
        if len(dsimplex)>4:
            # TODO: some time rise. Need attention.
            #print(f"Very strange situation. size of simplex({simplex})=={simplex_size}. Skipped. Need attention")
            continue
        sort_dsimplex = tuple(sorted(dsimplex))
        dict_source_dsimplex[sort_dsimplex] = dsimplex
        simplices.append( sort_dsimplex )

    simplices = np.unique(simplices)
    simplices = np.array(sorted(simplices, key=len, reverse=True)) # https://stackoverflow.com/questions/47271229/sort-a-numpy-array-of-numpy-arrays-by-lengths-of-the-internal-arrays
    dimension_size_1 = len(simplices[0])

    if threshold>0:
        # test simplex size for threshold. Remove simplexes that do not allowed in their dimensions.
        # (plane are disallowed in volumes, line are disallowed in planes).
        arr = []
        vertices = np.array([delaunay.points[i,:3] for i,e in enumerate(delaunay.points)]) # point come with 4d vector coordinates so need extract only first 3 [XYZ]
        
        if len(arr)==0 and len(simplices[0])>=4: # if no elems in arr and first elem in simplices array is more-eq than volume
            for sim in simplices:
                simplex_size = len(sim)
                # simplex is a volumetric. If volume has size(volume)==0 then do not use this simplex
                if simplex_size==4:
                    if is_volume_0(vertices, sim, threshold):
                        continue
                    arr.append(sim)
                elif simplex_size<4:
                    # skip to lower dimenstion. simplices ordered by lower to the end.
                    break

        if len(arr)==0 and len(simplices[0])>=3: # if no elems in arr and first elem in simplices array is more-eq than plane
            for sim in simplices:
                simplex_size = len(sim)
                # simplex is a plane. If plane has size(area)==0 then do not use this simplex
                if simplex_size==3:
                    if is_area_0(vertices, sim, threshold):
                        continue
                    arr.append(sim)
                elif simplex_size<3:
                    # skip to lower dimenstion. simplices ordered by lower to the end.
                    break
                        
        if len(arr)==0 and len(simplices[0])>=2: # if no elems in arr and first elem in simplices array is more-eq than line
            for sim in simplices:
                simplex_size = len(sim)
                # simplex is a line. If line has size(length)==0 then do not use this simplex
                if simplex_size==2:
                    if is_length_0(vertices, sim, threshold):
                        continue
                    arr.append(sim)
                elif simplex_size<2:
                    # skip to lower dimenstion. simplices ordered by lower to the end.
                    break

        # TODO: what todo if len(arr)==0 ?
        pass
    else:
        arr = simplices

    list_restored_orders = []
    for key in arr:
        list_restored_orders.append( dict_source_dsimplex[tuple(key)] )
    return list_restored_orders, dimension_size_1, dimension_size_2

def get_delaunay_simplices(vertices, threshold):
    '''Get simplices for vertices. Verices can be any shape: volume, planes, edges. This function
    automatically get shape with threshold param. If size of volume of one simplex is less threshold then
    that simplixes will be removed. If no volume will exists then planes mode will be selected and recalc rise.
    So this will be for planes to lines.
    '''
    np_sites = np.array([(*v, 0.0 ) for v in vertices], dtype=np.float32)
    for i in range(10): # 2 is max, but for insurance
        # Add 3D tetraedre to the 4D with W=1 (proxy shape). This trick for do not mixing vertices of a source shape and a proxy shape:
        np_sites = np.append(np_sites, [[0.0, 0.0, 0.0, 1.0],
                                        [1.0, 0.0, 0.0, 1.0],
                                        [0.0, 1.0, 0.0, 1.0],
                                        [0.0, 0.0, 1.0, 1.0],
                                        ], axis=0)

        simplices, dim1, dim2 = get_sites_delaunay_params( np_sites, len(vertices), threshold )
        #bbox = bounding_box_aligned(vertices)
        if dim1==dim2: # 4 - volume, 3 - planes, 2 - edges, 1 - dots
            #print(f"Found solution for dim={dim2-1} with {i} attempt")
            break
        else:
            # Get bbox size. TODO: think about oriented BBOX
            oX_size = np.max(np.array(vertices, dtype=np.float16)[:,0]) - np.min(np.array(vertices, dtype=np.float16)[:,0])
            oY_size = np.max(np.array(vertices, dtype=np.float16)[:,1]) - np.min(np.array(vertices, dtype=np.float16)[:,1])
            oZ_size = np.max(np.array(vertices, dtype=np.float16)[:,2]) - np.min(np.array(vertices, dtype=np.float16)[:,2])
            axis = list(np.argsort([oX_size, oY_size, oZ_size]))
            axis.reverse()
            plane_axis_X = axis[0]
            plane_axis_Y = axis[1]
            plane_axis_Z = axis[2]
            if dim2==3: # plane. (faces and edges)
                # Select max plane axises of Bounding Box get it to XY plane
                # convert vertices to plane oXY. get two first elems. Is is plane max area
                np_sites = np.array([(v[plane_axis_X], v[plane_axis_Y], 0, 0) for v in vertices], dtype=np.float32)
                continue
            elif dim2==2: # line (only edges)
                # Select max side axis of Bounding Box get it to oX plane
                np_sites = np.array([(v[plane_axis_X], 0, 0, 0) for v in vertices], dtype=np.float32)
                continue
            elif dim2==1: # dot. no edges
                break
            else:
                # unknown dim2. insurence
                break
    else:
        #print("delaunay_3d_mk2. Solution not found")  # incredibly 
        pass

    #simplices = get_delaunay_simplices_02(vertices, threshold)
    return simplices

def get_delaunay_simplices_02(vertices, threshold):

    # get shape dimension (dim):
    bbox = bounding_box_aligned(vertices)
    oX = bbox[1]-bbox[0]
    oX_size = abs(np.linalg.norm(oX))
    oY = bbox[3]-bbox[0]
    oY_size = abs(np.linalg.norm(oY))
    oZ = bbox[4]-bbox[0]
    oZ_size = abs(np.linalg.norm(oZ))
    axis_sizes = list(reversed(sorted([oX_size, oY_size, oZ_size]))) # axis's sizes aligned from big to low.
    dim = 3 # default dimension as volume
    if axis_sizes[0]<threshold:
        # if first size<threshold then shape is dot:
        dim=0
    elif axis_sizes[1]<threshold:
        # if second size<threshold then shape is line:
        dim=1
    elif axis_sizes[2]<threshold:
        # if third size<threshold then shape is plane:
        dim=2
    
    # get real bbox and calc real max projection for shape:
    oX_size = np.max(np.array(vertices, dtype=np.float16)[:,0]) - np.min(np.array(vertices, dtype=np.float16)[:,0])
    oY_size = np.max(np.array(vertices, dtype=np.float16)[:,1]) - np.min(np.array(vertices, dtype=np.float16)[:,1])
    oZ_size = np.max(np.array(vertices, dtype=np.float16)[:,2]) - np.min(np.array(vertices, dtype=np.float16)[:,2])
    axis = list(np.argsort([oX_size, oY_size, oZ_size]))
    axis.reverse()
    plane_axis_X = axis[0]
    plane_axis_Y = axis[1]
    plane_axis_Z = axis[2]

    # to minimise approximation error orient max size of bbox to predifined dimensions
    if dim==3: # volume. (faces and edges)
        np_sites = vertices # no projection
    elif dim==2: # plane. (faces and edges)
        # Select max plane axises of real Bounding Box get it to XY plane
        # convert vertices to plane oXY. get two first elems. Is is plane max area
        np_sites = np.array([(v[plane_axis_X], v[plane_axis_Y],) for v in vertices], dtype=np.float32)
    elif dim==1: # line (only edges)
        # Select max side axis of real Bounding Box get it to oX plane
        np_sites = np.array([(v[plane_axis_X], 0) for v in vertices], dtype=np.float32)
        np_sites = np.append(np_sites, [[0, 1]], axis=0) # to calc delaunay in 2D. Remove this later
    elif dim==0: # dot. no edges
        np_sites = vertices # no projection

    simplices = [] #np.array([], dtype=np.float64) # no simpleces for dot dimension
    if dim>0:
        delaunay = Delaunay(np_sites)
        simplices = delaunay.simplices
        if dim==1:
            # for lines need remove last vertice
            arr = []
            n_orig_sites = len(vertices)
            for i, simplex in enumerate(delaunay.simplices):
                dsimplex = tuple(simplex[simplex<n_orig_sites])
                arr.append(dsimplex)
            simplices = np.array(arr, dtype=np.int32)

        simplices = np.unique(simplices, axis=0)
        simplices = simplices.tolist()

    return simplices

class SvDelaunay3dMk2Node(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Delaunay 3D
    Tooltip: Generate 3D Delaunay Triangulation
    """
    bl_idname = 'SvDelaunay3dMk2Node'
    bl_label = 'Delaunay 3D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DELAUNAY'
    sv_dependencies = {'scipy'}

    join : BoolProperty(
        name = "Join",
        default = False,
        description="If checked, then the node will generate one mesh object, composed of all faces of all tetrahedrons (without duplicating vertices and faces). Otherwise, the node will generate a separate mesh object for each tetrahedron",
        update = updateNode)

    volume_threshold : FloatProperty(
        name = "PlanarThreshold",
        min = 0,
        default = 1e-4,
        precision = 4,
        description="This defines the threshold used to filter “too flat” tetrahedrons out. Smaller values of threshold mean more “almost flat” tetrahedrons will be generated. Set this to 0 to skip this filtering step and allow to generate any tetrahedrons",
        update = updateNode)

    edge_threshold : FloatProperty(
        name = "EdgeThreshold",
        min = 0,
        default = 0,
        precision = 4,
        description="This defines the threshold used to filter “too long” tetrahedrons out. Tetrahedrons which have one of their edges longer than value specified here will not be generated. Set this to 0 to skip this filtering step and allow to generate any tetrahedrons",
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "join")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "PlanarThreshold").prop_name = 'volume_threshold'
        self.inputs.new('SvStringsSocket', "EdgeThreshold").prop_name = 'edge_threshold'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def make_edges(self, idxs):
        return [(i, j) for i in idxs for j in idxs if i < j]

    def make_faces(self, idxs):
        return [(i, j, k) for i in idxs for j in idxs for k in idxs if i < j and j < k]

    def get_verts(self, verts, idxs):
        return [verts[i] for i in idxs]

    def is_too_long(self, verts, idxs, threshold):
        if threshold == 0:
            return False
        verts = [np.array(verts[i]) for i in idxs]
        for v1, v2 in combinations(verts, 2):
            d = np.linalg.norm(v1 - v2)
            if d > threshold:
                return True
        return False

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        volume_threshold_s = self.inputs['PlanarThreshold'].sv_get()
        edge_threshold_s = self.inputs['EdgeThreshold'].sv_get()

        input_level = get_data_nesting_level(vertices_s)

        vertices_s = ensure_nesting_level(vertices_s, 4)
        volume_threshold_s = ensure_nesting_level(volume_threshold_s, 2)
        edge_threshold_s = ensure_nesting_level(edge_threshold_s, 2)

        nested_output = input_level > 3

        edges_new_2 = [ (0, 1) ]
        edges_new_3 = [ (0, 1), (1, 2), (2, 0), ]
        edges_new_4 = [ (0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3) ]
        faces_new_2 = []
        faces_new_3 = [ (0, 1, 2) ]
        faces_new_4 = [ (0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3) ]
        verts_out = []
        edges_out = []
        faces_out = []
        for params in zip_long_repeat(vertices_s, volume_threshold_s, edge_threshold_s):
            verts_item = []
            edges_item = []
            faces_item = []
            for vertices, volume_threshold, edge_threshold in zip_long_repeat(*params):
                vertices = np.array(vertices, dtype=np.float64)
                #simplices = get_delaunay_simplices(vertices, self.volume_threshold)
                simplices = get_delaunay_simplices_02(vertices, self.volume_threshold)
                if self.join:

                    verts_new = vertices
                    edges_new = set()
                    faces_new = set()

                    for simplex in simplices:
                        simplex_length = len(simplex)
                        
                        # unknown simplex. skip. Incredible. get_sites_delaunay_params work with size==5 so need test.
                        if simplex_length>4:
                            continue

                        if self.is_too_long(vertices, simplex, edge_threshold):
                             continue

                        # for get_delaunay_simplices_02 no test for threshold dimension.
                        # for get_delaunay_simplices: no need test for threshold now. All elements now is more than threshold.
                        
                        # if simplex.size>=2 (2,3,4) then create edges
                        if simplex_length==2:
                            edges_new.update( [ ( simplex[0], simplex[1] ) ] )
                            continue

                        # if simplex.size>=3 (3,4) then create faces
                        if simplex_length>=3:
                            if simplex_length==3:
                                edges_simplex = [ (simplex[0], simplex[1]),
                                                  (simplex[1], simplex[2]),
                                                  (simplex[2], simplex[0]), ]
                                faces_simplex = [ (simplex[0], simplex[1], simplex[2]) ]
                            else:
                                edges_simplex = [ (simplex[0], simplex[1]),
                                                  (simplex[0], simplex[2]),
                                                  (simplex[0], simplex[3]),
                                                  (simplex[1], simplex[2]),
                                                  (simplex[1], simplex[3]),
                                                  (simplex[2], simplex[3]) ]
                                faces_simplex = [ (simplex[0], simplex[1], simplex[2]),
                                                  (simplex[0], simplex[1], simplex[3]),
                                                  (simplex[0], simplex[2], simplex[3]),
                                                  (simplex[1], simplex[2], simplex[3]) ]
                            #edges_simplex = self.make_edges(list( range(simplex_length) ))
                            #faces_simplex = self.make_faces(list( range(simplex_length) ))
                            edges_new.update( edges_simplex )
                            faces_new.update( faces_simplex )

                    verts_item.append(verts_new)
                    edges_item.append(list(edges_new))
                    faces_item.append(list(faces_new))
                else:
                    verts_new = []
                    edges_new = []
                    faces_new = []
                    for simplex in simplices:
                        simplex_length = len(simplex)

                        # unknown simplex. skip. Incredible. get_sites_delaunay_params work with size==5 so need test.
                        if simplex_length>4:
                            continue

                        if self.is_too_long(vertices, simplex, edge_threshold):
                             continue

                        # if some geometry is visible then geometry need verts:
                        verts_simplex = self.get_verts(vertices, simplex)
                        verts_new.append(verts_simplex)                        

                        # if simplex.size>=2 (2,3,4) then create edges
                        if simplex_length==2:
                            edges_new.append( edges_new_2 )
                            faces_new.append( faces_new_2 )
                            continue

                        # if simplex.size>=3 (3,4) then create faces
                        if simplex_length>=3:
                            if simplex_length==3:
                                edges_simplex = edges_new_3
                                faces_simplex = faces_new_3
                            else:
                                edges_simplex = edges_new_4
                                faces_simplex = faces_new_4
                            #edges_simplex = self.make_edges(list( range(simplex_length) ))
                            #faces_simplex = self.make_faces(list( range(simplex_length) ))
                            edges_new.append( edges_simplex )
                            faces_new.append( faces_simplex )

                    verts_item.extend(verts_new)
                    edges_item.extend(edges_new)
                    faces_item.extend(faces_new)

                if nested_output:
                    verts_out.append(verts_item)
                    edges_out.append(edges_item)
                    faces_out.append(faces_item)
                else:
                    verts_out.extend(verts_item)
                    edges_out.extend(edges_item)
                    #if faces_item:
                    faces_out.extend(faces_item)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvDelaunay3dMk2Node)


def unregister():
    bpy.utils.unregister_class(SvDelaunay3dMk2Node)
