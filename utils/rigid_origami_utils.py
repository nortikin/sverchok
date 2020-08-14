# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import math
import copy
from collections import deque, defaultdict
from mathutils import Vector
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
        
# === Object wrapper class ===
class ObjectParams:
    
    # Constructor
    def __init__(self, verts, edges, faces):
        
        # Store the vertices, edges and faces
        self.verts = np.array(verts)
        self.num_verts = len(self.verts)
        self.edges = [tuple(sorted([e[0], e[1]])) for e in edges]
        self.faces = faces
        
        # Create bmesh from the datas
        self.bm = bmesh_from_pydata(verts, self.edges, self.faces)
        self.bm.faces.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.normal_update()
    
    def free(self):
        if self.bm != None:
            self.bm.free()

    # Get the object-edge index from a bmesh edge
    def bm_to_obj_edge_index(self, bm_edge):
        edge = tuple(sorted([bm_edge.verts[0].index, bm_edge.verts[1].index])) 
        return self.edges.index(edge)

    # Get the object face index from a bmesh face
    def bm_to_obj_face_index(self, bm_face):
        v_indices = [v.index for v in bm_face.verts]
        for i, f in enumerate(self.faces):
            if set(f) == set(v_indices):
                return i
        raise ValueError("Created BMesh faces is wrong")
        
# === Crease Lines class ===
class CreaseLines:

    # Constructor
    def __init__(self, obj, fold_edge_indices, fold_edge_angles, folding):
        
        # Collect edges inside of a mesh
        edge_indices = [obj.bm_to_obj_edge_index(obj.bm.edges[i]) \
                        for i, e in enumerate(obj.bm.edges) \
                        if not e.is_boundary]
        self.edges = [tuple(obj.edges[i]) for i in edge_indices]

        # Initialize edge angles with the current angles
        # (round function is needed to calculate pseudo inverse correctly later)
        self.angles = [round(obj.bm.edges[i].calc_face_angle_signed(0.0), 5) \
                        for i, e in enumerate(obj.bm.edges) \
                        if not e.is_boundary]
                        
        final_angles = [round(fold_edge_angles[fold_edge_indices.index(e)], 5) \
                                if (fold_edge_indices.count(e) > 0 \
                                and fold_edge_indices.index(e) < len(fold_edge_angles)) \
                                else self.angles[i] \
                                for i, e in enumerate(edge_indices)]
        diffs = [final - angle \
                    for final, angle in zip(final_angles, self.angles)]

        # Target angles multiplyed with folding ratio
        self.target_angles = [angle + (diff * folding) for angle, diff \
                                in zip(self.angles, diffs)]
        
        # Delta angles to be calculated in this node
        self.delta_angles = [0.0] * len(self.angles)

# === Inside Vertex class ===
class InsideVertex:
    # Vertex indices inside of the paper
    indices = []
    
    # Constructor
    def __init__(self, vertex, v_index, edges, \
                    crease_indices, thetas, rhos, drhos):
        self.vertex = vertex
        self.v_index = v_index
        self.edges = edges
        self.crease_indices = crease_indices
        self.thetas = thetas
        self.init_rhos = [rho for rho in rhos]
        self.rhos = rhos
        self.drhos = drhos
        
    # Function to generate inside vertex objects
    @classmethod
    def generate_inside_vertices(cls, obj, crease_lines):
        
        # Create vertex indices inside of the source paper
        num_verts = len(obj.verts)
        indices = [v.index for v in obj.bm.verts if not v.is_boundary]
        cls.indices = indices
        
        # Create list of crease edges around each vertices
        crease_indices = cls.__get_crease_lines_around_vertex(crease_lines, indices, obj)

        cr_edges = [[crease_lines.edges[j] for j in crease_indices[i]] \
                    for i in range(len(crease_indices))]
        
        # Create theta (between edges) and rho (edge angle) list
        theta_list = [cls.__calc_theta_angles(obj.verts, cr_edges[i], idx) \
                        for i, idx in enumerate(indices)]
        rho_list = [[crease_lines.angles[j] for j in crease_indices[i]] \
                        for i in range(len(indices))]
        drho_list = [[crease_lines.angles[j]+np.pi*0.5 for j in crease_indices[i]] \
                        for i in range(len(indices))]

        # Create list of InsideVertex class
        inside_verts = [InsideVertex(obj.verts[idx], idx, cr_edges[i], \
                        crease_indices[i], theta_list[i], rho_list[i], \
                        drho_list[i]) \
                        for i, idx in enumerate(indices)]

        return inside_verts
    
    # Function to get crease lines around the vertex
    # https://blender.stackexchange.com/questions/92406/circular-order-of-edges-around-vertex
    @classmethod
    def __get_crease_lines_around_vertex(cls, crease_lines, inside_vert_indices, obj):

        # Sort link_edges around each vertices in counter-clockwise order
        bm_edges_ccws = []
        for i in inside_vert_indices:
            bm_vert = obj.bm.verts[i]
            bm_vert.link_edges.index_update()
            
            edges_counterclockwise_order = []
            bm_edge = bm_vert.link_edges[0]
            while bm_edge not in edges_counterclockwise_order:
                edges_counterclockwise_order.append(bm_edge)
                bm_edge = cls.__get_right_side_edge_around_vertex(bm_edge, bm_vert, obj)
            bm_edges_ccws.append(edges_counterclockwise_order)
            
        crease_edge_indices = [[] for i in inside_vert_indices]
        outer_verts_indices = [idx for idx, vert in enumerate(obj.bm.verts) if vert.is_boundary]
        target_indices = [idx for idx in inside_vert_indices]
        
        # Rotate the sorted edge indices to enable the paper foldable
        while len(target_indices) > 0:

            target_list_idx = [inside_vert_indices.index(target_idx) for target_idx in target_indices]
            target_ccws = [ccw for i, ccw in enumerate(bm_edges_ccws) if i in target_list_idx]
            
            # Select outermost indices not yet to be processed
            indices_outermost = [idx for idx, (target_ccw, v_idx) in \
                                        enumerate(zip(target_ccws, target_indices)) \
                                        if any([bme.other_vert(obj.bm.verts[v_idx]).index \
                                        in outer_verts_indices for bme in target_ccw])]
                                        
            # Roll the edge order around each vertices
            for idx, target_ccw in enumerate(target_ccws):
                if idx not in indices_outermost:
                    continue
                
                # Choose a edge connected with a vertex outside, 
                # and next one sould be connected with vertex inside
                bm_vert = obj.bm.verts[target_indices[idx]]
                is_candidate = [bm_edge.other_vert(bm_vert).index in outer_verts_indices and \
                                not target_ccw[(i+1)%len(target_ccw)].other_vert(bm_vert).index in outer_verts_indices \
                                for i, bm_edge in enumerate(target_ccw)]
                
                # Decide rotating amount by the candidate-edge index and roll the edge order
                top_index = is_candidate.index(True) if is_candidate.count(True) > 0 else 0
                rolled_bm_e = np.roll(np.array([bm_e for bm_e in target_ccw]), \
                                    -top_index).tolist()

                # Store the rolled indices to the result list
                list_index = inside_vert_indices.index(target_indices[idx])
                crease_edge_indices[list_index] = [crease_lines.edges.index(obj.edges[obj.bm_to_obj_edge_index(bm_e)]) \
                                            for bm_e in rolled_bm_e \
                                            if crease_lines.edges.count(obj.edges[obj.bm_to_obj_edge_index(bm_e)]) > 0]
                
            # Remove indices processed in this loop
            new_outmost_indices = [target_indices[i] for i in indices_outermost]
            target_indices = [idx for i, idx in enumerate(target_indices) if i not in indices_outermost]
            outer_verts_indices.extend(new_outmost_indices)
        
        return crease_edge_indices
        
    # Return the right edge of param edge regard to param vertex
    @classmethod
    def __get_right_side_edge_around_vertex(cls, bm_edge, bm_vertex, obj):
        for loop in bm_edge.link_loops:
            if loop.vert == bm_vertex:
                break
        return loop.link_loop_prev.edge

    # Function to calculate theta angles between crease lines
    @classmethod
    def __calc_theta_angles(cls, obj_verts, cr_edges, v_index):
        thetas = []
        for j in range(len(cr_edges)):
            a1 = cr_edges[j][1 if cr_edges[j].index(v_index) == 0 else 0]
            b1 = cr_edges[(j+1)%len(cr_edges)][1 if cr_edges[(j+1)%len(cr_edges)].index(v_index) == 0 else 0]
            va = obj_verts[a1] - obj_verts[v_index]
            vb = obj_verts[b1] - obj_verts[v_index]
            thetas.append(np.arccos(np.inner(va, vb)/(np.linalg.norm(va)*np.linalg.norm(vb))))
        return thetas

# === Fold Angle Calculator class ===
class FoldAngleCalculator:
    
    # Current rho angles in process loop
    current_rhos = np.array([])
    
    # Function to calculate fold angles of each crease lines
    @classmethod
    def calc_fold_angle(cls, step_count, crease_lines, inside_vertices):
        
        # Initialize current rho angles (updated in each steps)
        cls.current_rhos = np.array([angle for angle in crease_lines.angles])

        diffs = [target - angle for target, angle \
                in zip(crease_lines.target_angles, crease_lines.angles)]
        for loop in range(0, max(0, step_count)):
            target_angles = np.array([angle + (diff/step_count) * (loop + 1) \
                                    if loop < (step_count - 1) else target \
                                    for angle, diff, target in zip(crease_lines.angles, \
                                    diffs, crease_lines.target_angles)])

            C = np.zeros((3*len(inside_vertices), len(crease_lines.edges)))
            r = np.zeros(3*len(inside_vertices))
            
            for i, inside_vertex in enumerate(inside_vertices):
                 
                edge_num = len(inside_vertex.edges)
                F = np.identity(3)
                dFdr = [np.identity(3) for j in range(edge_num)]
                
                # Create rotation matrices(theta, rho, differential coefficient of rho)
                mat_t = cls.__create_rot_theta_matrices(inside_vertex.thetas)        
                mat_r = cls.__create_rot_rho_matrices(inside_vertex.rhos)
                for j in range(len(inside_vertex.rhos)):
                    inside_vertex.drhos[j] = inside_vertex.rhos[j] + np.pi*0.5
                mat_rd = cls.__create_rot_rho_matrices(inside_vertex.drhos)
                
                # Create partial derivative matrices for each rho delta        
                for j in range(edge_num):
                    for k in range(edge_num):
                        # Inner product of mat_t and mat_r
                        # (When j == k, use drho(delta rho) to calc dFdr_j)
                        X_k = np.dot((mat_r[k] if j != k else mat_rd[k]), mat_t[k])
                        # Erase non related element to delta rho angle
                        if j == k:
                            X_k[0][0] = 0
                            X_k[0][1] = 0
                        dFdr[j] = np.dot(dFdr[j], X_k)
                        
                    F_j = np.dot(mat_r[j], mat_t[j])
                    F = np.dot(F, F_j)

                # Create jacobi matrix
                for j, ci in enumerate(inside_vertex.crease_indices):
                    C[3*i+0][ci] = dFdr[j][1][0]
                    C[3*i+1][ci] = dFdr[j][2][1]
                    C[3*i+2][ci] = dFdr[j][0][2]

                # Store adjustment to modify delta rho
                r[3*i]= F[1][0]
                r[3*i+1] = F[2][1]
                r[3*i+2] = F[0][2]

            Cp = np.linalg.pinv(C, rcond=1e-6)
            In = np.identity(len(crease_lines.edges))
            dr = target_angles - cls.current_rhos
            
            # Use this adjustment only if step count == 1 considering error range
            adjustment = -np.dot(Cp, r.T) if step_count == 1 \
                            else np.zeros(len(crease_lines.edges)).T
            
            # Add the calcuated actual delta-rho angles
            dr_actual = adjustment + np.dot((In - np.dot(Cp, C)), dr.T)
            cls.current_rhos += dr_actual

            # Update the rho angles list
            delta_angles = cls.__to_iv_edge_angles(dr_actual, inside_vertices)
            cls.__update_iv_edge_angles(inside_vertices, delta_angles)
            
    # Function to create rotation matrix for theta angles
    # (between each edges around center vertex)
    @classmethod
    def __create_rot_theta_matrices(cls, thetas):
        theta_rot_matrices = [np.array([[np.cos(theta), -np.sin(theta),0], \
                                    [np.sin(theta), np.cos(theta), 0], \
                                    [0,0,1]]) \
                                    for theta in thetas]
        return theta_rot_matrices

    # Function to create rotation matrix for rho angles
    # (of each edges around center vertex)
    @classmethod
    def __create_rot_rho_matrices(cls, rhos):
        rho_rot_matrices = [np.array([[1,0,0], \
                                [0, np.cos(rho), -np.sin(rho)], \
                                [0, np.sin(rho), np.cos(rho)]]) \
                                for rho in rhos]
        return rho_rot_matrices

    # Function to change order from global angles (of edges)
    # to local angles (around each center vertex)
    @classmethod
    def __to_iv_edge_angles(cls, crease_angles, inside_vertices):
        cr_indices = [iv.crease_indices for iv in inside_vertices]
        iv_edge_angles = [[crease_angles[i] for i in indices] \
                        for indices in cr_indices]
        return iv_edge_angles

    # Update local (around each center vertex)
    # rho angles adding each delta angles
    @classmethod
    def __update_iv_edge_angles(cls, inside_vertices, delta_angles):
        for i, angles in enumerate(delta_angles):
            for j, angle in enumerate(angles):
                inside_vertices[i].rhos[j] += angle

# === Face Rotation class ===
class FaceRotation:
    
    # Class variables
    obj = None
    inside_vertices = None
    crease_lines = None
    fixed_face_index = 0
    
    # Constructor
    def __init__(self, face):
        self.face = face
        self.rot_quat = np.identity(4)
        self.prev_face_idx = []
        self.rot_angles = []
    
    # Function to get neighbor faces
    def get_neighbors(self, faces):
        neighbors = [f for e in self.face.edges \
                        for f in faces \
                        if (f.index != self.face.index) and (e in f.edges)]
        hinges = [tuple(sorted([e.verts[0].index, e.verts[1].index])) \
                        for e in self.face.edges for f in faces \
                        if (f.index != self.face.index) and (e in f.edges)]
        return neighbors, hinges

    # Function to rotate all faces
    @classmethod
    def rotate_faces(cls):
        # Use deque to process rotating faces
        face_queue = deque()
        
        for face in cls.obj.bm.faces:
            if cls.obj.bm_to_obj_face_index(face) == cls.fixed_face_index:
                face_queue.appendleft(FaceRotation(face))
                break

        rotated = [False]*len(cls.obj.faces)
        verts_out = copy.deepcopy(cls.obj.verts)

        while len(face_queue) > 0:
            face_rot = face_queue.pop()
            
            if not rotated[cls.obj.bm_to_obj_face_index(face_rot.face)]:
                # Rotate face with quaternion
                rotated_indices, rotated_verts = cls.__rotate_face(face_rot)
                for i, v in enumerate(rotated_verts):
                    verts_out[rotated_indices[i]] = v
                rotated[cls.obj.bm_to_obj_face_index(face_rot.face)] = True
            
            # Find neighbor faces
            neighbors, hinges = face_rot.get_neighbors(cls.obj.bm.faces)
            for i, neighbor in enumerate(neighbors):
                if rotated[cls.obj.bm_to_obj_face_index(neighbor)]:
                    continue
                
                # print("face_rot.neighbor.index:", cls.obj.bm_to_obj_face_index(neighbor))
                n_rot = FaceRotation(neighbor)
                # Load vector, angle and inside vertex related to this rotation        
                vec, rad, iv = cls.__get_edge_vector_angle(neighbor, hinges[i], cls.obj.verts)
                
                # Make quaternions to rotate the target face
                shift_quat_left = [[1,0,0,-iv[0]], [0,1,0,-iv[1]], [0,0,1,-iv[2]], \
                                    [0,0,0,1]]
                rotation_quat = cls.__rot_quat(rad, vec)
                shift_quat_right = [[1,0,0,iv[0]], [0,1,0,iv[1]], [0,0,1,iv[2]], \
                                    [0,0,0,1]]
                                    
                # Multiply the rotation quaternions
                n_rot.rot_quat = np.dot(shift_quat_left, n_rot.rot_quat)
                n_rot.rot_quat = np.dot(rotation_quat, n_rot.rot_quat)
                n_rot.rot_quat = np.dot(shift_quat_right, n_rot.rot_quat)
                n_rot.rot_quat = np.dot(face_rot.rot_quat, n_rot.rot_quat)
                for angle in face_rot.rot_angles:
                    n_rot.rot_angles.append(angle)
                for idx in face_rot.prev_face_idx:
                    n_rot.prev_face_idx.append(idx)
                n_rot.rot_angles.append(rad)
                n_rot.prev_face_idx.append(cls.obj.bm_to_obj_face_index(face_rot.face))

                # Store the new face to face queue
                face_queue.appendleft(n_rot)
                
        return verts_out.tolist()

    # Function to get edge vector, angle and (rotation) center vertex
    @classmethod
    def __get_edge_vector_angle(cls, face, edge, verts):
        
        iv_indices = [iv.v_index for iv in cls.inside_vertices]
        
        if edge[0] in iv_indices or edge[1] in iv_indices:
            # Get vertices
            v0_idx = edge[0] if edge[0] in iv_indices else edge[1]
            v1_idx = edge[1] if edge[0] == v0_idx else edge[0]
            
            # Create vector (v0 is the center)
            v0, v1 = cls.obj.verts[v0_idx], cls.obj.verts[v1_idx]
            vec = v1 - v0
            
            iv_idx = iv_indices.index(v0_idx)

            # Get rotation radian
            crease_idx = cls.crease_lines.edges.index(edge)
            local_idx = cls.inside_vertices[iv_idx].crease_indices.index(crease_idx)
            rad = cls.inside_vertices[iv_idx].rhos[local_idx] - \
                    cls.inside_vertices[iv_idx].init_rhos[local_idx]
            
            # Check the rotation orientation comparing with another neighbor edge
            for bm_e in face.edges:
                obj_e = tuple(sorted([bm_e.verts[0].index, bm_e.verts[1].index]))
                if obj_e != edge and obj_e in cls.crease_lines.edges:
                    e_cr_idx = cls.crease_lines.edges.index(obj_e)
                    if e_cr_idx not in cls.inside_vertices[iv_idx].crease_indices:
                        continue
                    e_l_idx = cls.inside_vertices[iv_idx].crease_indices.index(e_cr_idx)
                    sign = 1
                    if abs(e_l_idx - local_idx) > 1:
                        sign = -1 if local_idx == 0 else 1
                    else:
                        sign = e_l_idx - local_idx

                    rad = rad * sign
                    break
        else:
            # Center of the target polygon
            center = face.calc_center_median()
            poly_center = np.array([center[0], center[1], center[2]])
            # Cross product between 'edge[1] - edge[0]' and 'center - edge[0]'
            va = poly_center - verts[edge[0]]
            vb = verts[edge[1]] - verts[edge[0]]
            n = np.cross(va, vb)
            n = n / np.linalg.norm(n)
            face_n = np.array([face.normal[0], face.normal[1], face.normal[2]])

            rad = 0.0
            if cls.crease_lines.edges.count(edge) > 0:
                rad = cls.crease_lines.delta_angles[cls.crease_lines.edges.index(edge)]
                rad *= -1 if np.dot(n, face_n) > 0 else 1
            return vb, rad, verts[edge[0]]
            
                        
        return vec, rad, v0

    # Function to rotate a face
    @classmethod
    def __rotate_face(cls, face_rot):
        v_indices = [v.index for v in face_rot.face.verts]
        
        rotated_verts = []
        for v in face_rot.face.verts:
            # Rotate source vertex using quaternion            
            source_q = np.array([cls.obj.verts[v.index][0], cls.obj.verts[v.index][1], cls.obj.verts[v.index][2], 1])
            vq = np.dot(face_rot.rot_quat, source_q.T)
            v_result = np.array([vq[0], vq[1], vq[2]])
            rotated_verts.append(v_result)
            
        return v_indices, rotated_verts
    
    @classmethod
    # Function to create rotation quaternion
    # to rotate 'rad' radian around 'n' axis
    def __rot_quat(cls, rad, n):
        n = n / np.linalg.norm(n)
        rad = float(rad)
        R = np.array([[np.cos(rad)+n[0]*n[0]*(1-np.cos(rad)), \
                       n[0]*n[1]*(1-np.cos(rad))-n[2]*np.sin(rad), \
                       n[0]*n[2]*(1-np.cos(rad))+n[1]*np.sin(rad), 0], \
                      [n[1]*n[0]*(1-np.cos(rad))+n[2]*np.sin(rad), \
                       np.cos(rad)+n[1]*n[1]*(1-np.cos(rad)), \
                       n[1]*n[2]*(1-np.cos(rad))-n[0]*np.sin(rad), 0], \
                      [n[2]*n[0]*(1-np.cos(rad))-n[1]*np.sin(rad), \
                       n[2]*n[1]*(1-np.cos(rad))+n[0]*np.sin(rad), \
                       np.cos(rad)+n[2]*n[2]*(1-np.cos(rad)), 0], \
                       [0, 0, 0, 1]])
        return R
