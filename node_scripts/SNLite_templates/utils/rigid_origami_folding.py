"""
in obj_in o
in valleys s d=[] n=1
in valley_angle s d=3.141592 n=2
in mountains s d=[] n=1
in mountain_angle s d=3.141592 n=2
in folding s d=0.0 n=2
in step s d=0.1570796 n=2
in fixed_face s d=0 n=2
out verts v
out edges s
out faces s
"""

import numpy as np
import math
import copy
from collections import deque, defaultdict
        
# === Object wrapper class ===
class ObjectParams:
    
    # constructor
    def __init__(self, obj):
        
        # get vertices, edges and faces
        self.verts = np.array([np.array([v.co[0], v.co[1], v.co[2]]) \
                            for v in obj.data.vertices])
        self.num_verts = len(self.verts)
        self.edges = [tuple(sorted([e.vertices[0], e.vertices[1]])) \
                            for e in obj.data.edges]
        self.faces = obj.data.polygons

# === Crease Lines class ===
class CreaseLines:

    # constructor
    def __init__(self, obj_edges, valley_edges, mountain_edges):
        # select valley/mountain crease lines
        self.edges = [tuple(e) for e in obj_edges \
                                if tuple(e) in valley_edges \
                                or tuple(e) in mountain_edges]
        # create is_valleys list to check valley or mountain
        self.is_valleys = [(tuple(e) in valley_edges) \
                            for e in obj_edges \
                            if tuple(e) in valley_edges \
                            or tuple(e) in mountain_edges]
        self.angles = [0.0] * len(self.edges)

# === Inside Vertex class ===
class InsideVertex:
    # vertex indices inside of the paper
    indices = []
    
    # constructor
    def __init__(self, vertex, v_index, edges, \
                    crease_indices, thetas, rhos, drhos):
        self.vertex = vertex
        self.v_index = v_index
        self.edges = edges
        self.crease_indices = crease_indices
        self.thetas = thetas
        self.rhos = rhos
        self.drhos = drhos
        
    # function to generate inside vertex objects
    @classmethod
    def GenerateInsideVertices(cls, obj, crease_edges, \
                                valley_edges, mountain_edges):
        # create vertex indices
        num_verts = len(obj.verts)
        indices = cls.__GetInsideVertsIndices(obj)
        InsideVertex.indices = indices
        
        # create list of crease edges around each vertices
        crease_indices = [cls.__GetCreaseLinesAroundVertex \
                        (crease_edges, obj.verts, i) for i in indices]
        cr_edges = [[crease_edges[j] for j in crease_indices[i]] \
                    for i in range(len(crease_indices))]
        
        # create theta (between edges) and rho (edge angle) list
        theta_list = [cls.__calc_theta_angles(obj.verts, cr_edges[i], idx) \
                        for i, idx in enumerate(indices)]
        rho_list = [[0.0] * len(crease_indices[i]) \
                        for i in range(len(indices))]
        drho_list = [[np.pi*0.5] * len(crease_indices[i]) \
                        for i in range(len(indices))]
        
        # create list of InsideVertex class
        inside_verts = [InsideVertex(obj.verts[idx], idx, cr_edges[i], \
                        crease_indices[i], theta_list[i], rho_list[i], \
                        drho_list[i]) \
                        for i, idx in enumerate(indices)]
                        
        return inside_verts
    
    # function to get vertex indices inside of the plane
    @classmethod
    def __GetInsideVertsIndices(cls, obj):
        verts_indices = []
        # Regard a vertex as one inside of the plane
        # if the count of each edges (around the vertex)
        # extracted from all faces is '2'
        for v_idx in range(len(obj.verts)):
            connected_edges = defaultdict(int)
            for f in obj.faces:
                for e in f.edge_keys:
                    if e.count(v_idx) > 0:
                        connected_edges[e] += 1
            if list(connected_edges.values()).count(2) == \
                len(connected_edges):
                    verts_indices.append(v_idx)
        
        return verts_indices
            
    # function to get crease lines around the vertex
    @classmethod
    def __GetCreaseLinesAroundVertex(cls, crease_edges, obj_verts, vertexIndex):
        iv_edges = [ce for ce in crease_edges if vertexIndex in ce]
        iv_edges = cls.__SortEdgesCounterclockwise(iv_edges, obj_verts, vertexIndex)
        iv_e_indices = [i for e in iv_edges \
                        for i, x in enumerate(crease_edges) if x == e]
        return iv_e_indices

    # sort edges around the vertex in counterclockwise order
    @classmethod
    def __SortEdgesCounterclockwise(cls, edges, verts, cv_idx):

        thetas = []
        for i, e in enumerate(edges):
            opposite_idx = e[1 if e.index(cv_idx) == 0 else 0]
            vec = np.array([verts[opposite_idx][0] - verts[cv_idx][0], \
                   verts[opposite_idx][1] - verts[cv_idx][1], \
                   verts[opposite_idx][2] - verts[cv_idx][2]])
            if i == 0:
                # to be compared with other edges
                vec0 = vec
                thetas.append(0)
            else:
                # get the angle between vec[current] and vec[0]
                cos_t = np.inner(vec0, vec)/(np.linalg.norm(vec0)*np.linalg.norm(vec))
                sin_t = (vec0[0]*vec[1] - vec0[1]*vec[0])/(np.linalg.norm(vec0)*np.linalg.norm(vec))
                theta = np.arctan2(sin_t, cos_t) if cos_t != 0 else np.arcsin(sin_t)
                thetas.append(theta)
                
        # sort edges with the angles
        sorted_edges = [edges[i] for i in np.argsort(thetas)]
        return sorted_edges

    # function to calc theta angles between crease lines
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
    # current rho angles in process loop
    current_rhos = np.array([])
    
    # function to calculate fold angles of each crease lines
    @classmethod
    def CalcFoldAngle(cls, delta_step, crease_lines, inside_vertices, \
                        dest_valley_angle, dest_mountain_angle):
        # rho angles of crease edges (updated in each steps)
        cls.current_rhos = np.zeros((len(crease_lines.edges)))
        
        # calculate loop count from delta_step
        min_angle = min(abs(dest_valley_angle), abs(dest_mountain_angle))
        loop = math.ceil(min_angle/delta_step)

        for count in range(1, (loop+1)):
            target_v_angle = (dest_valley_angle/loop)*count if count < loop else dest_valley_angle
            target_m_angle = -(dest_mountain_angle/loop)*count if count < loop else -dest_mountain_angle
            
            C = np.zeros((3*len(inside_vertices), len(crease_lines.edges)))
            r = np.zeros(3*len(inside_vertices))
            
            for i, inside_vertex in enumerate(inside_vertices):
                 
                edge_num = len(inside_vertex.edges)
                F = np.identity(3)
                dFdr = [np.identity(3) for j in range(edge_num)]
                
                # create rotation matrices(theta, rho, differential coefficient of rho)
                mat_t = cls.__create_rot_theta_matrices(inside_vertex.thetas)        
                mat_r = cls.__create_rot_rho_matrices(inside_vertex.rhos)
                for j in range(len(inside_vertex.rhos)):
                    inside_vertex.drhos[j] = inside_vertex.rhos[j] + np.pi*0.5
                mat_rd = cls.__create_rot_rho_matrices(inside_vertex.drhos)
                
                # create partial derivative matrices for each rho delta        
                for j in range(edge_num):
                    for k in range(edge_num):
                        # inner product of mat_t and mat_r
                        # (when j == k, use drho(delta rho) to calc dFdr_j)
                        X_k = np.dot((mat_r[k] if j != k else mat_rd[k]), mat_t[k])
                        # erase non related element to delta rho angle
                        if j == k:
                            X_k[0][0] = 0
                            X_k[0][1] = 0
                        dFdr[j] = np.dot(dFdr[j], X_k)
                        
                    F_j = np.dot(mat_r[j], mat_t[j])
                    F = np.dot(F, F_j)

                # create jacobi matrix
                for j, ci in enumerate(inside_vertex.crease_indices):
                    C[3*i+0][ci] = dFdr[j][1][0]
                    C[3*i+1][ci] = dFdr[j][2][1]
                    C[3*i+2][ci] = dFdr[j][0][2]

                # store adjustment to modify delta rho
                r[3*i]= F[1][0]
                r[3*i+1] = F[2][1]
                r[3*i+2] = F[0][2]

            Cp = np.linalg.pinv(C)
            In = np.identity(len(crease_lines.edges))
            dr = np.zeros(len(crease_lines.edges))
            for i in range(len(dr)):
                dr[i] = (target_v_angle \
                        if crease_lines.is_valleys[i] else target_m_angle) \
                        - cls.current_rhos[i]
                        
            # use this adjustment only if step count == 1
            adjustment = -np.dot(Cp, r.T) \
                    if step >= max(abs(dest_valley_angle), abs(dest_mountain_angle)) \
                    else np.zeros(len(crease_lines.edges)).T
            # adjustment = -np.dot(Cp, r.T)
            
            dr_actual = adjustment + np.dot((In - np.dot(Cp, C)), dr.T)
            cls.current_rhos += dr_actual

            # update rho list
            delta_angles = cls.__to_iv_edge_angles(dr_actual, inside_vertices)
            cls.__update_iv_edge_angles(inside_vertices, delta_angles)
            
    # function to create rotation matrix for theta angles
    # (between each edges around center vertex)
    @classmethod
    def __create_rot_theta_matrices(cls, thetas):
        theta_rot_matrices = [np.array([[np.cos(theta), -np.sin(theta),0], \
                                    [np.sin(theta), np.cos(theta), 0], \
                                    [0,0,1]]) \
                                    for theta in thetas]
        return theta_rot_matrices

    # function to create rotation matrix for rho angles
    # (of each edges around center vertex)
    @classmethod
    def __create_rot_rho_matrices(cls, rhos):
        rho_rot_matrices = [np.array([[1,0,0], \
                                [0, np.cos(rho), -np.sin(rho)], \
                                [0, np.sin(rho), np.cos(rho)]]) \
                                for rho in rhos]
        return rho_rot_matrices

    # function to change order from global angles (of edges)
    # to local angles (around each center vertex)
    @classmethod
    def __to_iv_edge_angles(cls, crease_angles, inside_vertices):
        cr_indices = [iv.crease_indices for iv in inside_vertices]
        iv_edge_angles = [[crease_angles[i] for i in indices] \
                        for indices in cr_indices]
        return iv_edge_angles

    # update local (around each center vertex)
    # rho angles adding each delta angles
    @classmethod
    def __update_iv_edge_angles(cls, inside_vertices, delta_angles):
        for i, angles in enumerate(delta_angles):
            for j, angle in enumerate(angles):
                inside_vertices[i].rhos[j] += angle

# === Face Rotation class ===
class FaceRotation:
    # class variables
    obj = None
    inside_vertices = None
    crease_lines = None
    fixed_face_index = 0
    
    # constructor
    def __init__(self, face):
        self.face = face
        self.rot_quat = np.identity(4)
    
    # function to get neighbor faces
    def get_neighbors(self, faces):
        neighbors = [f for e_key in self.face.edge_keys \
                        for f in faces \
                        if (f.index != self.face.index) and (e_key in f.edge_keys)]
        hinges = [e_key for e_key in self.face.edge_keys \
                        for f in faces \
                        if (f.index != self.face.index) and (e_key in f.edge_keys)]
        return neighbors, hinges

    # function to rotate all faces
    @classmethod
    def RotateFaces(cls):
        # use deque to process rotating faces
        face_que = deque()
        
        for face in cls.obj.faces:
            if face.index == cls.fixed_face_index:
                face_que.appendleft(FaceRotation(face))
                break

        rotated = [False]*len(cls.obj.faces)
        verts_out = copy.deepcopy(cls.obj.verts)

        while len(face_que) > 0:
            face_rot = face_que.pop()
            
            if not rotated[face_rot.face.index]:
                # rotate face with quaternion
                rotated_indices, rotated_verts = cls.__rotate_face(face_rot)
                for i, v in enumerate(rotated_verts):
                    verts_out[rotated_indices[i]] = v
                rotated[face_rot.face.index] = True
            
            # find neighbor faces
            neighbors, hinges = face_rot.get_neighbors(cls.obj.faces)
            for i, neighbor in enumerate(neighbors):
                if rotated[neighbor.index]:
                    continue
                
                n_rot = FaceRotation(neighbor)
                # load vector, angle and inside vertex related to this rotation        
                vec, rad, iv = cls.__get_edge_vector_angle(neighbor, hinges[i], cls.obj.verts)
                
                # make quaternion to rotate the target face
                shift_quat_left = [[1,0,0,-iv[0]], [0,1,0,-iv[1]], [0,0,1,-iv[2]], \
                                    [0,0,0,1]]
                rotation_quat = cls.__rot_quat(rad, vec)
                shift_quat_right = [[1,0,0,iv[0]], [0,1,0,iv[1]], [0,0,1,iv[2]], \
                                    [0,0,0,1]]
                                    
                # add rotation quaternion
                n_rot.rot_quat = np.dot(shift_quat_left, n_rot.rot_quat)
                n_rot.rot_quat = np.dot(rotation_quat, n_rot.rot_quat)
                n_rot.rot_quat = np.dot(shift_quat_right, n_rot.rot_quat)
                n_rot.rot_quat = np.dot(face_rot.rot_quat, n_rot.rot_quat)
                
                # put new face
                face_que.appendleft(n_rot)
                
        return verts_out.tolist()

    # function to get edge vector, angle and (rotation) center vertex
    @classmethod
    def __get_edge_vector_angle(cls, face, edge, verts):
        
        iv_indices = [iv.v_index for iv in cls.inside_vertices]
        
        if edge[0] in iv_indices or edge[1] in iv_indices:
            # get vertices
            v0_idx = edge[0] if edge[0] in iv_indices else edge[1]
            v1_idx = edge[1] if edge[0] == v0_idx else edge[0]
            
            # create vector (v0 is the center)
            v0, v1 = cls.obj.verts[v0_idx], cls.obj.verts[v1_idx]
            vec = v1 - v0
            
            iv_idx = iv_indices.index(v0_idx)

            # get rotation radian
            crease_idx = cls.crease_lines.edges.index(edge)
            local_idx = cls.inside_vertices[iv_idx].crease_indices.index(crease_idx)
            rad = cls.inside_vertices[iv_idx].rhos[local_idx]
            
            # check rotation orientation comparing with another neighbor edge
            for e in face.edge_keys:
                if e != edge and e in cls.crease_lines.edges:
                    e_cr_idx = cls.crease_lines.edges.index(e)
                    if not e_cr_idx in cls.inside_vertices[iv_idx].crease_indices:
                        continue
                    e_l_idx = cls.inside_vertices[iv_idx].crease_indices.index(e_cr_idx)
                    sign = 1
                    if abs(e_l_idx - local_idx) > 1:
                        sign = -1 if local_idx == 0 else 1
                    else:
                        sign = e_l_idx - local_idx

                    rad *= sign
                    break
        else:
            # center of target polygon
            poly_center = np.array([face.center[0], face.center[1], face.center[2]])
            
            # cross product between 'edge[1] - edge[0]' and 'center - edge[0]'
            va = poly_center - verts[edge[0]]
            vb = verts[edge[1]] - verts[edge[0]]
            n = np.cross(va, vb)
            n = n / np.linalg.norm(n)
            face_n = np.array([face.normal[0], face.normal[1], face.normal[2]])

            rad = 0.0
            if cls.crease_lines.edges.count(edge) > 0:
                rad = cls.crease_lines.angles[cls.crease_lines.edges.index(edge)]
                rad *= -1 if np.dot(n, face_n) > 0 else 1
            return vb, rad, verts[edge[0]]
            
                        
        return vec, rad, v0

    # function to rotate a face
    @classmethod
    def __rotate_face(cls, face_rot):
        v_indices = [v_idx for v_idx in face_rot.face.vertices]
        
        rotated_verts = []
        for v_idx in face_rot.face.vertices:
            # rotate source vertex using quaternion            
            source_q = np.array([cls.obj.verts[v_idx][0], cls.obj.verts[v_idx][1], cls.obj.verts[v_idx][2], 1])
            vq = np.dot(face_rot.rot_quat, source_q.T)
            v_result = np.array([vq[0], vq[1], vq[2]])
            rotated_verts.append(v_result)
            
        return v_indices, rotated_verts
    
    @classmethod
    # function to create rotation quaternion
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

#################################

# create tuple list to avoid type mismatch
valley_edges = [e for e in valleys if type(e) is tuple] 
mountain_edges = [e for e in mountains if type(e) is tuple] 
if len(valleys) > 0 and type(valleys[0]) is list:
    valley_edges = [tuple(sorted(e)) for e in valleys]
    mountain_edges = [tuple(sorted(e)) for e in mountains]

# wrap object
obj = ObjectParams(obj_in[0])

# extract crease lines
crease_lines = CreaseLines(obj.edges, \
                valley_edges, mountain_edges)

# extract inside vertices
inside_vertices = InsideVertex.GenerateInsideVertices( \
                    obj, crease_lines.edges, \
                    valley_edges, mountain_edges)

# define loop count to calculate angles
min_angle = min(abs(valley_angle)*folding, abs(mountain_angle)*folding)
loop = int((min_angle/step) + 1)

# calculation loop to determine the final angles
FoldAngleCalculator.CalcFoldAngle(step, crease_lines, inside_vertices, \
                                valley_angle*folding, mountain_angle*folding)
crease_lines.angles = FoldAngleCalculator.current_rhos

# rotate each faces using final angles
FaceRotation.obj = obj
FaceRotation.inside_vertices = inside_vertices
FaceRotation.crease_lines = crease_lines
FaceRotation.fixed_face_index = int(fixed_face)
verts_out = FaceRotation.RotateFaces()

verts = [verts_out]
edges = [obj.edges]
faces = [[list(f.vertices) for f in obj.faces]]