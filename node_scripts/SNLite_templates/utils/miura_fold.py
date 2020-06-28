"""
in x_dim s d=3 n=2
in y_dim s d=3 n=2
in theta s d=1.0471973 n=2
in alpha s d=0. n=2
out verts v
out edges s
out faces s
"""

"""
Defining the unit cell vertices from certain angles.
source: http://izumi-math.jp/M_Matumoto/103_matsumoto.pdf

      A---- B ---- C
     /     /      /
    O---- D(I)----E
    
theta : angle between AOD
alpha : angle between DOI (I: point under D)
beta  : angle between AOI
"""

from mathutils import Vector
import math

if x_dim < 1: x_dim = 1
if y_dim < 1: y_dim = 1

# limitation of alpha angle
alpha_abs_max = math.pi*0.5 - 0.03
if abs(alpha) > alpha_abs_max:
    alpha = math.copysign(alpha_abs_max, alpha)

# calculate beta angle with cosine theorem for triangle AOD 
beta = math.acos(math.cos(theta)/math.cos(alpha))

# vertices of the unit cell (left to right, and top to bottom)
v_base = [
            [math.cos(beta), math.sin(beta), 0],
            [math.cos(alpha) + math.cos(beta), math.sin(beta), math.sin(alpha)],
            [2*math.cos(alpha) + math.cos(beta), math.sin(beta), 0],
            [0,0,0],
            [math.cos(alpha), 0, math.sin(alpha)],
            [2*math.cos(alpha), 0, 0],
            [math.cos(beta), -math.sin(beta), 0],
            [math.cos(alpha) + math.cos(beta), -math.sin(beta), math.sin(alpha)],
            [2*math.cos(alpha) + math.cos(beta), -math.sin(beta), 0]
        ]

# arrange vertices
verts = [[]]
v = []
for i in range(y_dim):
    v1 = []
    v2 = []
    v3 = []
    for j in range(x_dim):
        x_offset = 2*math.cos(alpha)*j
        y_offset = -2*math.sin(beta)*i
        if j == 0:
            if i == 0:
                v1.append(Vector((v_base[0][0], v_base[0][1], v_base[0][2])))
            v2.append(Vector((v_base[3][0], y_offset + v_base[3][1], v_base[3][2])))
            v3.append(Vector((v_base[6][0], y_offset + v_base[6][1], v_base[6][2])))
        if i == 0:
            v1.append(Vector((x_offset + v_base[1][0], y_offset + v_base[1][1], v_base[1][2])))
            v1.append(Vector((x_offset + v_base[2][0], y_offset + v_base[2][1], v_base[2][2])))
            
        v2.append(Vector((x_offset + v_base[4][0], y_offset + v_base[4][1], v_base[4][2])))
        v2.append(Vector((x_offset + v_base[5][0], y_offset + v_base[5][1], v_base[5][2])))
            
        v3.append(Vector((x_offset + v_base[7][0], y_offset + v_base[7][1], v_base[7][2])))
        v3.append(Vector((x_offset + v_base[8][0], y_offset + v_base[8][1], v_base[8][2])))

    if i == 0:
        v.extend(v1)
    v.extend(v2)
    v.extend(v3)

verts[0] = v

# connect edges
edges = [[]]
edge_set = set()

y = 3 + 2*(y_dim-1)
x = 3 + 2*(x_dim-1)

index = 0
for i in range(y-1):
    for j in range(x-1):
        index = i * x + j
        edge_set.add(tuple(sorted([index, index+1])))
        edge_set.add(tuple(sorted([index, index+x])))
    # right side
    edge_set.add(tuple(sorted([index + 1, index+x + 1])))
# bottom line
for k in range(x-1):
    index = (y-1) * x + k
    edge_set.add(tuple(sorted([index, index + 1])))
edges[0].extend(list(edge_set))

# create faces
faces = [[]]
face_set = set()
for i in range(y-1):
    for j in range(x-1):
        index = i * x + j
        face_set.add(tuple((index, index+1, index+x+1, index+x)))
faces[0].extend(list(face_set))
