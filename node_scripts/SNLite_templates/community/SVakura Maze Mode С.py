"""
in verts v d=[] n=1
in edges s d=[] n=1
in polys s d=[] n=1
in weights s d=[] n=1
in method s d=0 n=1
in rseed s d=21 n=1
in braid s d=0.0 n=1
in limit s d=30.0 n=1
in axis s d=0 n=1
out link_v v
out link_e s

METHODS:
0: Backtracker, 1: Kruskal, 2: Wilson, 3: BFS, 4: Prim, 5: Multi-Snake
6: Curvature (Angle), 7: Ridge/Valley (Limit sign), 8: Face-to-Face (Dual)
9: Self-Avoiding Directional Growth (axis: 0=X, 1=Y, 2=Z, 3=Line)
"""

import random
import heapq
import math
import mathutils
from collections import deque, defaultdict

# --- Вспомогательные функции ---

def get_adj_weighted(n_v, edges_list, weights_list):
    adj = [[] for _ in range(n_v)]
    has_w = len(weights_list) >= len(edges_list) and len(weights_list) > 0
    for i, e in enumerate(edges_list):
        if len(e) < 2: continue
        u, v = e[0], e[1]
        w = weights_list[i] if has_w else random.random()
        adj[u].append((v, w)); adj[v].append((u, w))
    return adj

def solve_curvature(verts_vec, polys_data, threshold):
    if not polys_data: return []
    limit_rad = math.radians(abs(threshold))
    find_concave = threshold < 0
    face_normals, face_centers = [], []
    for face in polys_data:
        f_verts = [verts_vec[v] for v in face]
        if len(f_verts) < 3:
            face_normals.append(mathutils.Vector((0,0,0)))
            face_centers.append(mathutils.Vector((0,0,0)))
            continue
        face_normals.append(mathutils.geometry.normal(f_verts))
        face_centers.append(sum(f_verts, mathutils.Vector()) / len(face))
    edge_to_faces = defaultdict(list)
    for f_idx, face in enumerate(polys_data):
        for i in range(len(face)):
            u, v = face[i], face[(i+1)%len(face)]
            edge = (u, v) if u < v else (v, u)
            edge_to_faces[edge].append(f_idx)
    res_e = []
    for (u, v), f_idxs in edge_to_faces.items():
        if len(f_idxs) == 2:
            idx1, idx2 = f_idxs
            n1, n2 = face_normals[idx1], face_normals[idx2]
            if n1.length > 0.1 and n2.length > 0.1:
                angle = n1.angle(n2)
                if angle >= limit_rad:
                    c1, c2 = face_centers[idx1], face_centers[idx2]
                    is_concave = (c2 - c1).dot(n1) > 0
                    if find_concave == is_concave: res_e.append([u, v])
        elif len(f_idxs) == 1: res_e.append([u, v])
    return res_e

# --- Исполнение ---

link_v, link_e = [], []
if verts and (edges or polys):
    def get_s(val, default):
        try:
            v = val
            while isinstance(v, (list, tuple)): v = v[0]
            return v
        except: return default

    random.seed(int(get_s(rseed, 21)))
    n_v = len(verts); m = int(get_s(method, 0)); limit_val = float(get_s(limit, 30.0))
    verts_vec = [mathutils.Vector(v) for v in verts]
    res_v, res_e = verts, []

    if m == 8: # Face-to-Face Maze (Dual)
        f_centers = []
        for f in polys: f_centers.append(list(sum((verts_vec[v] for v in f), mathutils.Vector())/len(f)))
        res_v = f_centers
        e_to_f = defaultdict(list)
        for f_idx, f in enumerate(polys):
            for i in range(len(f)):
                edge = tuple(sorted((f[i], f[(i+1)%len(f)])))
                e_to_f[edge].append(f_idx)
        f_adj = [[] for _ in range(len(polys))]
        for edge, f_idxs in e_to_f.items():
            if len(f_idxs) == 2:
                u, v = f_idxs; w = random.random()
                f_adj[u].append((v, w)); f_adj[v].append((u, w))
        p = list(range(len(polys)))
        def find(i):
            while p[i] != i: p[i] = p[p[i]]; i = p[i]
            return i
        f_edges = []
        for u, nbs in enumerate(f_adj):
            for v, w in nbs:
                if u < v: f_edges.append((w, u, v))
        f_edges.sort()
        for w, u, v in f_edges:
            ru, rv = find(u), find(v)
            if ru != rv: p[ru] = rv; res_e.append([u, v])
    elif m in {6, 7}: # Curvature & Ridge
        res_e = solve_curvature(verts_vec, polys, limit_val)
    elif m == 9: # Self-Avoiding Directional Growth
        if not edges: res_e = []
        else:
            axis_idx = int(get_s(axis, 0))
            limit_rad = math.radians(limit_val)
            cos_limit = math.cos(limit_rad)
            adj = defaultdict(list)
            for u, v in edges:
                adj[u].append(v); adj[v].append(u)
            
            vstd = [False] * n_v
            res_e = []
            seeds = list(range(n_v))
            random.shuffle(seeds)
            
            targets = [mathutils.Vector((1,0,0)), mathutils.Vector((0,1,0)), mathutils.Vector((0,0,1))]
            main_target = targets[axis_idx] if axis_idx < 3 else None

            for s in seeds:
                if vstd[s]: continue
                vstd[s] = True
                
                # Try growing in two opposite directions
                for mult in [1, -1]:
                    curr = s
                    # Initial direction
                    if main_target:
                        curr_dir = main_target * mult
                    else:
                        # For Linearity (axis 3), pick a random neighbor to start
                        nghs = [n for n in adj[curr] if not vstd[n]]
                        if not nghs: continue
                        nxt = random.choice(nghs)
                        curr_dir = (verts_vec[nxt] - verts_vec[curr]).normalized()
                        # Immediately move to next to establish direction
                        res_e.append([curr, nxt])
                        vstd[nxt] = True
                        curr = nxt

                    while True:
                        best_n = None
                        best_dot = -2.0
                        best_ev = None
                        
                        for n in adj[curr]:
                            if vstd[n]: continue
                            ev = (verts_vec[n] - verts_vec[curr]).normalized()
                            dot = ev.dot(curr_dir)
                            if dot >= cos_limit:
                                if dot > best_dot:
                                    best_dot = dot
                                    best_n = n
                                    best_ev = ev
                        
                        if best_n is not None:
                            res_e.append([curr, best_n])
                            vstd[best_n] = True
                            curr = best_n
                            curr_dir = best_ev # Update direction to follow the curve
                        else:
                            break
    else:
        adj_w = get_adj_weighted(n_v, edges if edges else [], weights)
        adj_s = [[v for v, w in nbs] for nbs in adj_w]
        if m == 0: # Backtracker
            stk, vstd = [random.randint(0, n_v-1)], [False] * n_v
            vstd[stk[0]] = True
            while stk:
                curr = stk[-1]; ngh = [n for n in adj_s[curr] if not vstd[n]]
                if not ngh: stk.pop()
                else:
                    nxt = random.choice(ngh); res_e.append([curr, nxt]); vstd[nxt] = True; stk.append(nxt)
        elif m == 1: # Kruskal
            p = list(range(n_v))
            def find(i):
                while p[i] != i: p[i] = p[p[i]]; i = p[i]
                return i
            shf = list(edges if edges else []); random.shuffle(shf)
            for u, v in shf:
                ru, rv = find(u), find(v)
                if ru != rv: p[ru] = rv; res_e.append([u, v])
        elif m == 2: # Wilson
            unv, vis = set(range(n_v)), {random.randint(0, n_v-1)}
            unv.discard(list(vis)[0])
            while unv:
                curr = random.choice(list(unv)); path = [curr]
                while curr not in vis:
                    if not adj_s[curr]: break
                    curr = random.choice(adj_s[curr])
                    if curr in path: path = path[:path.index(curr)+1]
                    else: path.append(curr)
                for i in range(len(path)-1):
                    u, v = path[i], path[i+1]; res_e.append([u, v]); vis.add(u); unv.discard(u)
        elif m == 3: # BFS
            q, vstd = deque([random.randint(0, n_v-1)]), [False] * n_v
            vstd[q[0]] = True
            while q:
                curr = q.popleft(); ngh = [n for n in adj_s[curr] if not vstd[n]]; random.shuffle(ngh)
                for n in ngh: vstd[n] = True; res_e.append([curr, n]); q.append(n)
        elif m == 4: # Prim
            vstd, front = [False] * n_v, []
            s = random.randint(0, n_v-1); vstd[s] = True
            for n, w in adj_w[s]: heapq.heappush(front, (w, s, n))
            while front:
                w, u, v = heapq.heappop(front)
                if not vstd[v]:
                    vstd[v] = True; res_e.append([u, v])
                    for nxt, nw in adj_w[v]:
                        if not vstd[nxt]: heapq.heappush(front, (nw, v, nxt))
        elif m == 5: # Multi-Snake
            vstd = [False] * n_v; unv = list(range(n_v)); random.shuffle(unv)
            for start in unv:
                if vstd[start]: continue
                path = [start]; vstd[start] = True
                while True:
                    curr = path[-1]; ngh = [n for n in adj_s[curr] if not vstd[n]]
                    if not ngh: break
                    ngh.sort(key=lambda x: len([nn for nn in adj_s[x] if not vstd[nn]]))
                    nxt = ngh[0]; vstd[nxt] = True; res_e.append([curr, nxt]); path.append(nxt)

    # Braid
    br = float(get_s(braid, 0.0))
    if br > 0 and m < 6:
        ld = defaultdict(list)
        for u, v in res_e: ld[u].append(v); ld[v].append(u)
        ends = [i for i in range(len(res_v)) if len(ld[i]) == 1]
        for v in ends:
            if random.random() < br:
                un = [n for n in range(len(res_v)) if n not in ld[v] and n != v]
                if un: t = random.choice(un); res_e.append([v, t]); ld[v].append(t); ld[t].append(v)

    link_v, link_e = [res_v], [res_e]
