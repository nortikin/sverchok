"""
in verts_in v d=[] n=0
in faces_in s d=[] n=0
out verts_out v
out faces_out s
out vert_idx s
out face_idx s
"""

def separate():
    if not verts_in or not faces_in:
        return [], [], [], []

    # 1. Нормализация
    mv = verts_in if isinstance(verts_in[0][0], (list, tuple, float, int)) else [verts_in]
    mf = faces_in if isinstance(faces_in[0][0], (int, float, list)) else [faces_in]

    all_v, all_f, all_vi, all_fi = [], [], [], []

    for ve, fe in zip(mv, mf):
        nv = len(ve)
        if nv == 0: continue
        
        # 2. Union-Find
        parent = list(range(nv))
        def find(i):
            root = i
            while parent[root] != root:
                root = parent[root]
            # Сжатие
            while parent[i] != root:
                parent[i], i = root, parent[i]
            return root

        for f in fe:
            if not f: continue
            root_f = find(f[0])
            for v_idx in f[1:]:
                root_v = find(v_idx)
                if root_f != root_v:
                    parent[root_v] = root_f

        # 3. Группировка
        island_map = {} 
        vert_to_island = [0] * nv
        island_counts = [] 
        
        num_islands = 0
        for i in range(nv):
            root = find(i)
            if root not in island_map:
                island_map[root] = num_islands
                island_counts.append(0)
                num_islands += 1
            isl_id = island_map[root]
            vert_to_island[i] = isl_id
            island_counts[isl_id] += 1

        # 4. Пустые списки под каждый остров
        curr_v = [[] for _ in range(num_islands)]
        curr_f = [[] for _ in range(num_islands)]
        
        # Ремаппер
        remapper = [0] * nv
        current_offsets = [0] * num_islands
        
        # Заполнение вершин и ремаппер
        for i, isl_id in enumerate(vert_to_island):
            curr_v[isl_id].append(ve[i])
            remapper[i] = current_offsets[isl_id]
            current_offsets[isl_id] += 1

        # 5. Распределение граней
        for f in fe:
            if not f: continue
            isl_id = vert_to_island[f[0]]
            # Пересчет индексов
            curr_f[isl_id].append([remapper[v] for v in f])

        # Сборка
        for i in range(num_islands):
            all_v.append(curr_v[i])
            all_f.append(curr_f[i])
            all_vi.append([i] * island_counts[i])
            all_fi.append([i] * len(curr_f[i]))

    return all_v, all_f, all_vi, all_fi

verts_out, faces_out, vert_idx, face_idx = separate()
