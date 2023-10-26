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
from sverchok.utils.modules.matrix_utils import matrix_apply_np
from sverchok.dependencies import scipy
from mathutils import Vector, Matrix

if scipy is not None:
    from scipy.spatial import Delaunay
    from scipy.spatial.transform import Rotation as R

def is_volume_0(verts, idxs, threshold):
    '''Is volume size of 4 verts less threshold (True/False) '''
    if threshold == 0:
        return False

    a, b, c, d = [Vector(verts[i]) for i in idxs]

    v1 = b-a
    v2 = c-a
    v3 = d-a

    volume_ = abs(v1.cross(v2).dot(v3))/6

    return abs(volume_) < threshold


def is_area_0(verts, idxs, threshold):
    '''Is area size of 3 verts less threshold (True/False) '''
    if threshold == 0:
        return False

    a, b, c = [Vector(verts[i]) for i in idxs]

    v1 = b-a
    v2 = c-a

    area_ = v1.cross(v2).length/2

    return abs(area_) < threshold

def is_length_0(verts, idxs, threshold):
    '''Is length size of 2 verts less threshold (True/False) '''
    if threshold == 0:
        return False

    a, b = [Vector(verts[i]) for i in idxs]
    v1 = b-a
    len_ = v1.length

    return abs(len_) < threshold

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

    # get shape dimension (dim):
    abbox, *_ = bounding_box_aligned(vertices)
    oX_abb_vec = abbox[1]-abbox[0]
    oX_abb_size = abs(np.linalg.norm(oX_abb_vec))
    oY_abb_vec = abbox[3]-abbox[0]
    oY_abb_size = abs(np.linalg.norm(oY_abb_vec))
    oZ_abb_vec = abbox[4]-abbox[0]
    oZ_abb_size = abs(np.linalg.norm(oZ_abb_vec))
    axis_sizes = list(reversed(sorted([oX_abb_size, oY_abb_size, oZ_abb_size]))) # axis's sizes aligned from big to low.
    axis_abb_order = list(np.argsort([oX_abb_size, oY_abb_size, oZ_abb_size]))
    axis_abb_order.reverse()
    plane_axis_X = axis_abb_order[0].tolist()
    plane_axis_Y = axis_abb_order[1].tolist()
    plane_axis_Z = axis_abb_order[2].tolist()

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
    oX_bb_size = np.max(np.array(vertices, dtype=np.float16)[:,0]) - np.min(np.array(vertices, dtype=np.float16)[:,0])
    oY_bb_size = np.max(np.array(vertices, dtype=np.float16)[:,1]) - np.min(np.array(vertices, dtype=np.float16)[:,1])
    oZ_bb_size = np.max(np.array(vertices, dtype=np.float16)[:,2]) - np.min(np.array(vertices, dtype=np.float16)[:,2])
    axis_bb_order = list(np.argsort([oX_bb_size, oY_bb_size, oZ_bb_size]))
    axis_bb_order.reverse()
    plane_axis_bb_X = axis_bb_order[0].tolist()
    plane_axis_bb_Y = axis_bb_order[1].tolist()
    plane_axis_bb_Z = axis_bb_order[2].tolist()

    # to minimise approximation error orient max size of bbox to predifined dimensions
    if dim==3: # volume. (faces and edges)
        np_sites = vertices # no projection
    elif dim==2: # plane. (faces and edges)
        np_sites = vertices
        # calc matrix to rotate oXY:
        align_bbox_axis = [oX_abb_vec, oY_abb_vec, oZ_abb_vec]
        X = np.array(align_bbox_axis[plane_axis_X], dtype=np.float64)
        Y = np.array(align_bbox_axis[plane_axis_Y], dtype=np.float64)
        Z = np.cross(X,Y)
        Y = np.cross(Z,X)
        X = X/np.linalg.norm(X)
        Y = Y/np.linalg.norm(Y)
        Z = Z/np.linalg.norm(Z)

        m = np.matrix(
            [[X[0], Y[0], Z[0], 0.0],
             [X[1], Y[1], Z[1], 0.0],
             [X[2], Y[2], Z[2], 0.0],
             [0, 0, 0, 1]] )
        np_sites = matrix_apply_np(np_sites, np.linalg.inv(m) )
        np_sites = np.delete(np_sites, 2, 1) #remove virtual Z axis
    elif dim==1: # line (only edges)
        # Select max side axis of real Bounding Box get it to oX plane
        np_sites = np.array([(v[plane_axis_bb_X], 0.0) for v in vertices], dtype=np.float32)
        np_sites = np.append(np_sites, [[0.0, 1.0]], axis=0) # to calc delaunay in virtual 2D.
    elif dim==0: # dot. no edges
        np_sites = vertices # no projection

    simplices = [] # no simplices for dot dimension
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
    else:
        simplices = list([[i] for i in range(len(vertices))])

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
        edges_new_3 = self.make_edges([0, 1, 2])     # [ (0, 1), (1, 2), (2, 0), ]
        edges_new_4 = self.make_edges([0, 1, 2, 3])  # [ (0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3) ]
        faces_new_2 = []
        faces_new_3 = self.make_faces([0, 1, 2])     # [ (0, 1, 2) ]
        faces_new_4 = self.make_faces([0, 1, 2, 3])  # [ (0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3) ]
        verts_out = []
        edges_out = []
        faces_out = []
        for params in zip_long_repeat(vertices_s, volume_threshold_s, edge_threshold_s):
            verts_item = []
            edges_item = []
            faces_item = []
            for vertices, volume_threshold, edge_threshold in zip_long_repeat(*params):
                vertices = np.array(vertices, dtype=np.float64)
                simplices = get_delaunay_simplices(vertices, self.volume_threshold)
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

                        if simplex_length==1:
                            continue

                        # if simplex.size>=2 (2,3,4) then create edges
                        if simplex_length==2:
                            if is_length_0(vertices, simplex, self.volume_threshold):
                                continue
                            edges_new.update( [ ( simplex[0], simplex[1] ) ] )
                            continue

                        # if simplex.size>=3 (3,4) then create faces
                        if simplex_length>=3:
                            if simplex_length==3:
                                if is_area_0(vertices, simplex, self.volume_threshold):
                                    continue
                                edges_simplex = [ (simplex[0], simplex[1]),
                                                  (simplex[1], simplex[2]),
                                                  (simplex[2], simplex[0]), ]
                                faces_simplex = [ (simplex[0], simplex[1], simplex[2]) ]
                            else:
                                if is_volume_0(vertices, simplex, self.volume_threshold):
                                    continue
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

                        if simplex_length==1:
                            edges_new.append( [] )
                            faces_new.append( [] )

                            # if some geometry is visible then geometry need verts:
                            verts_simplex = self.get_verts(vertices, simplex)
                            verts_new.append(verts_simplex)                        
                            continue

                        if simplex_length==2:
                            if is_length_0(vertices, simplex, self.volume_threshold):
                                continue
                            edges_new.append( edges_new_2 )
                            faces_new.append( faces_new_2 )

                            # if some geometry is visible then geometry need verts:
                            verts_simplex = self.get_verts(vertices, simplex)
                            verts_new.append(verts_simplex)                        
                            continue

                        # if simplex.size>=2 (2,3,4) then create edges
                        if simplex_length==2:
                            if is_length_0(vertices, simplex, self.volume_threshold):
                                continue
                            edges_new.append( edges_new_2 )
                            faces_new.append( faces_new_2 )

                            # if some geometry is visible then geometry need verts:
                            verts_simplex = self.get_verts(vertices, simplex)
                            verts_new.append(verts_simplex)                        
                            continue

                        # if simplex.size>=3 (3,4) then create faces
                        if simplex_length>=3:
                            if simplex_length==3:
                                if is_area_0(vertices, simplex, self.volume_threshold):
                                    continue
                                edges_simplex = edges_new_3
                                faces_simplex = faces_new_3
                            else:
                                if is_volume_0(vertices, simplex, self.volume_threshold):
                                    continue
                                edges_simplex = edges_new_4
                                faces_simplex = faces_new_4
                            edges_new.append( edges_simplex )
                            faces_new.append( faces_simplex )

                            # if some geometry is visible then geometry need verts:
                            verts_simplex = self.get_verts(vertices, simplex)
                            verts_new.append(verts_simplex)                        

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
                    faces_out.extend(faces_item)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvDelaunay3dMk2Node)


def unregister():
    bpy.utils.unregister_class(SvDelaunay3dMk2Node)
