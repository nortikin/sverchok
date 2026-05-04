"""
in v_in v d=[] n=0
in p_in s d=[] n=0
in split_idx s d=[] n=1
in offset s d=0.0 n=2
in use_units s d=0 n=2
out v_out v
out p_out s
# split polygons with offset @il_de_signer
"""

import numpy as np

def run():
    if not v_in or not p_in:
        return [[]], [[]]
        
    vs_arr = np.array(v_in[0])
    ps = p_in[0]
    
    targets = set(split_idx) if split_idx else set()
    off = float(offset)
    mode_units = bool(int(unwrap(use_units, 0))) 
    
    new_v = []
    new_p = []
    v_ptr = 0
    shared_map = {}
    
    _norm = np.linalg.norm

    for face in ps:
        f_len = len(face)
        if f_len < 3: continue
            
        f_coords = vs_arr[face]
        f_center = f_coords.mean(axis=0)
        
        new_face = []
        for i in range(f_len):
            v_orig_idx = face[i]
            
            if v_orig_idx in targets:
                v_pos = f_coords[i].copy()
                
                if off != 0:
                    vec_to_center = f_center - v_pos
                    
                    if mode_units:
                        d = _norm(vec_to_center)
                        if d > 0:
                            v_pos += (vec_to_center / d) * off
                    else:
                        v_pos += vec_to_center * off
                
                new_v.append(v_pos)
                new_face.append(v_ptr)
                v_ptr += 1
            else:
                if v_orig_idx not in shared_map:
                    new_v.append(f_coords[i])
                    shared_map[v_orig_idx] = v_ptr
                    v_ptr += 1
                new_face.append(shared_map[v_orig_idx])
        
        new_p.append(new_face)

    return [np.array(new_v).tolist()], [new_p]

def unwrap(val, default=0):
    while isinstance(val, (list, tuple)):
        if len(val) > 0: val = val[0]
        else: return default
    return val

v_out, p_out = run()
