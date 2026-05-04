"""
in v1 v d=[] n=0
in f1 s d=[] n=0
in v2 v d=[] n=0
in f2 s d=[] n=0
in mode s d=1 n=2
out v_out v
out f_out s
# manifold boolean @il_de_signer
"""

import numpy as np
try:
    from manifold3d import Manifold, Mesh
except ImportError:
    print("Manifold3D не установлен. Выполните: pip install manifold3d")

def to_manifold(verts, faces):
    """Подготовки Manifold объекта"""
    if not verts or not faces: return None
    
    # Manifold3D треугольники. 
    tris = []
    for f in faces:
        for i in range(1, len(f) - 1):
            tris.append([f[0], f[i], f[i+1]])
            
    v_np = np.array(verts, dtype=np.float32, order='C')
    f_np = np.array(tris, dtype=np.uint32, order='C')
    
    return Manifold(Mesh(vert_properties=v_np, tri_verts=f_np))

def run():
    # 1. Проверка геометрии (v1/f1)
    if not v1 or not f1: return [[]], [[]]
    
    # Извлекаем основной объект
    base_v = v1[0] if isinstance(v1[0][0], (list, tuple, np.ndarray)) else v1
    base_f = f1[0] if isinstance(f1[0][0], (list, tuple, int)) else f1
    m_base = to_manifold(base_v, base_f)
    
    # 2. Проверка (v2/f2)
    if not v2 or not f2:
        # Если вычитать нечего, возвращаем оригинал
        out = m_base.to_mesh()
        return [out.vert_properties.tolist()], [out.tri_verts.tolist()]

    try:
        # Собираем все объекты из v2 в один список Manifold
        tools = []
        for i in range(len(v2)):
            m_tool = to_manifold(v2[i], f2[i])
            if m_tool: tools.append(m_tool)
        
        if not tools:
            out = m_base.to_mesh()
            return [out.vert_properties.tolist()], [out.tri_verts.tolist()]

        # 3. Пакетное объединение всех инструментов (v2) в один меш
        combined_tools = Manifold.batch_boolean(tools, 0) # 0 = Union
        
        # 4. Финальная операция
        op = int(mode)
        if op == 0:    # Union (Объединение A + пачка B)
            res = m_base + combined_tools
        elif op == 1:  # Difference (A - пачка B)
            res = m_base - combined_tools
        elif op == 2:  # Intersection (A ^ пачка B)
            res = m_base ^ combined_tools
        else:
            res = m_base

        # 5. Выгрузка
        out_mesh = res.to_mesh()
        return [out_mesh.vert_properties.tolist()], [out_mesh.tri_verts.tolist()]

    except Exception as e:
        print(f"Batch Manifold Error: {e}")
        return [[]], [[]]

# Выполнение
v_out, f_out = run()
