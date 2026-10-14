"""
in vers_in v
in edgs_in s
enum = XY XZ YZ YX ZX ZY
out mats_out m
"""

# Чистая математика: матрицы для вершин по рёбрам (и полигонам), без Blender-библиотек
import bpy

def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)

import math
from mathutils import Matrix

plane_ = self.custom_enum
_EPS = 1e-9

def _add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def _dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _len(a): return math.sqrt(_dot(a, a))

def _normalized(a, fallback=(0.0, 0.0, 1.0)):
    l = _len(a)
    if l < _EPS:
        return fallback
    return (a[0]/l, a[1]/l, a[2]/l)

# ---------- нормали вершин ----------

def normals_from_edges(vertices, edges):
    """Ось Z по рёбрам.
    Концевая точка (1 сосед)  -> Z вдоль ребра К СОСЕДНЕЙ ВЕРШИНЕ.
    Середина линии (2 соседа) -> Z по хорде между соседями (на прямой = вдоль линии).
    Развилка (3+ соседей)     -> среднее направлений рёбер; при компенсации (крест)
                                 перпендикуляр из векторного произведения пары рёбер.
    Вершина без рёбер         -> Z = (0,0,1).
    """
    n = len(vertices)
    neighbors = [[] for _ in range(n)]
    seen = set()
    for e in edges or []:
        a, b = int(e[0]), int(e[1])
        if a == b or not (0 <= a < n) or not (0 <= b < n):
            continue
        key = (a, b) if a < b else (b, a)
        if key in seen:
            continue
        seen.add(key)
        neighbors[a].append(b)
        neighbors[b].append(a)

    normals = []
    for i, nbrs in enumerate(neighbors):
        v = vertices[i]
        if not nbrs:
            normals.append((0.0, 0.0, 1.0))
            continue
        if len(nbrs) == 1:
            z = _sub(vertices[nbrs[0]], v)
        elif len(nbrs) == 2:
            z = _sub(vertices[nbrs[1]], vertices[nbrs[0]])
        else:
            z = (0.0, 0.0, 0.0)
            for j in nbrs:
                z = _add(z, _sub(vertices[j], v))
            if _len(z) < _EPS:  # симметричная развилка: среднее скомпенсировалось
                dirs = [_normalized(_sub(vertices[j], v)) for j in nbrs]
                for p in range(len(dirs)):
                    for q in range(p+1, len(dirs)):
                        c = _cross(dirs[p], dirs[q])
                        if _len(c) > _EPS:
                            z = c
                            break
                    if _len(z) > _EPS:
                        break
        if _len(z) < _EPS:
            z = (0.0, 0.0, 1.0)
        normals.append(_normalized(z))
    return normals

def _polygon_normal(poly):
    # метод Ньюелла: устойчив к невыпуклым контурам
    x = y = z = 0.0
    for i in range(len(poly)):
        p, q = poly[i], poly[(i+1) % len(poly)]
        x += (p[1]-q[1]) * (p[2]+q[2])
        y += (p[2]-q[2]) * (p[0]+q[0])
        z += (p[0]-q[0]) * (p[1]+q[1])
    return (x, y, z)

def normals_from_faces(vertices, faces):
    normals = [(0.0, 0.0, 0.0)] * len(vertices)
    for f in faces:
        fn = _polygon_normal([vertices[i] for i in f])
        for i in f:
            normals[i] = _add(normals[i], fn)
    return [_normalized(n) if _len(n) > _EPS else (0.0, 0.0, 1.0) for n in normals]

# ---------- матрица из track / up ----------

_AXES = {'X': (1.0, 0.0, 0.0), 'Y': (0.0, 1.0, 0.0), 'Z': (0.0, 0.0, 1.0)}
_CYCLIC = {('X', 'Y', 'Z'), ('Y', 'Z', 'X'), ('Z', 'X', 'Y')}

def axis(name):
    sign = -1.0 if name.startswith('-') else 1.0
    return sign, name.lstrip('-')[-1], name.lstrip('-')
def _axis_matrix(normal, track, up, loc):

    sign_t, tl, _ = axis(track)
    sign_u, ul, _ = axis(up)
    if ul == tl:  # up совпал с track — берём третью ось
        ul = ({'X', 'Y', 'Z'} - {tl}).pop()
    t = _mul(normal, sign_t)  # ось track направляем по нормали (со знаком track)
    # проецируем ось up на плоскость, перпендикулярную track
    u = _sub(_mul(_AXES[ul], sign_u), _mul(t, sign_u * _dot(_AXES[ul], t)))
    if _len(u) < _EPS:  # up параллелен нормали — любой перпендикуляр
        for name in ('X', 'Y', 'Z'):
            if name != tl:
                u = _cross(t, _AXES[name])
                if _len(u) > _EPS:
                    break
    u = _normalized(u)

    r = ({'X', 'Y', 'Z'} - {tl, ul}).pop()
    v = _cross(t, u) if (tl, ul, r) in _CYCLIC else _cross(u, t)

    basis = {tl: t, ul: u, r: v}
    bx, by, bz = basis['X'], basis['Y'], basis['Z']
    return Matrix([
        [bx[0], bx[1], bx[2], loc[0]],
        [by[0], by[1], by[2], loc[1]],
        [bz[0], bz[1], bz[2], loc[2]],
        [0.0, 0.0, 0.0, 1.0],
    ])

# ---------- главная функция ----------

def vertex_matrix(vertices, edges, faces, track, up):
    """Матрица [4x4, строки = оси + позиция] на каждую вершину.
    Есть полигоны  -> Z по нормали полигонов (как раньше, но чистой математикой).
    Только рёбра   -> Z по рёбрам (концевые точки: по ребру к соседней вершине).
    """
    if faces:
        normal = normals_from_faces(vertices, faces)
    else:
        normal = normals_from_edges(vertices, edges)
    return [_axis_matrix(n, track, up, loc) for loc, n in zip(vertices, normal)]

def main():
    if vers_in and edgs_in:
        match plane_:
            case "XY": 
                ax, ay = "X","Y"
            case "YX": 
                ax, ay = "Y","X"
            case "XZ": 
                ax, ay = "X","Z"
            case "ZX": 
                ax, ay = "Z","X"
            case "YZ": 
                ax, ay = "Y","Z"
            case "ZY": 
                ax, ay = "Z","Y"
        #print(vers_in[0], edgs_in[0], [], ax, ay)
        return vertex_matrix(vers_in[0], edgs_in[0], [], ax, ay)
    else: return []
mats_out = main()

## tests
"""
def det3(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
          - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
          + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))

def check(m, name):
    bx, by, bz = m[0][:3], m[1][:3], m[2][:3]
    ok = (abs(_dot(bx, by)) < _EPS and abs(_dot(bx, bz)) < _EPS
          and abs(_dot(by, bz)) < _EPS
          and abs(_len(bx)-1) < 1e-6 and abs(_len(by)-1) < 1e-6
          and abs(_len(bz)-1) < 1e-6 and abs(det3(m) - 1) < 1e-6)
    print(f"{name}: Z=({bz[0]:+.3f},{bz[1]:+.3f},{bz[2]:+.3f}) "
          f"det={det3(m):+.3f} {'OK' if ok else 'FAIL'}")
    return ok

results = []

# 1. Прямая линия: Z везде вдоль +X
v = [(0,0,0),(1,0,0),(2,0,0)]
ns = normals_from_edges(v, [[0,1],[1,2]])
print("нормали прямой:", [tuple(round(c,3) for c in n) for n in ns])
results.append(all(_dot(n,(1,0,0)) > 0.999 for n in ns))

# 2. Концевая точка: Z к соседней вершине
results.append(_dot(normals_from_edges(v, [[0,1]])[0], (1,0,0)) > 0.999)

# 3. Замкнутый квадрат: хорды-диагонали, всё ортонормировано
sq = [(0,0,0),(1,0,0),(1,1,0),(0,1,0)]
sq_edges = [[0,1],[1,2],[2,3],[3,0]]
mats = vertex_matrix(sq, sq_edges, [], 'Z', 'Y')
results.append(all(check(m, f"квадрат v{i}") for i, m in enumerate(mats)))

# 4. Крест-развилка: Z перпендикулярно плоскости креста
star = [(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]
st_edges = [[0,1],[0,2],[0,3],[0,4]]
n = normals_from_edges(star, st_edges)[0]
print("нормаль центра креста:", tuple(round(c,3) for c in n))
results.append(abs(_dot(n,(0,0,1))) > 0.999)

# 5. Полигоны: треугольник, Z наружу (+Z)
tri = [(0,0,0),(1,0,0),(0,1,0)]
m = vertex_matrix(tri, [], [[0,1,2]], 'Z', 'Y')[0]
results.append(check(m, "треугольник v0"))

# 6. track='X', up='Z': матричная X-ось должна смотреть по нормали
m = vertex_matrix(tri, [], [[0,1,2]], 'X', 'Z')[0]
bx = m[0][:3]
results.append(_dot(bx, (0,0,1)) > 0.999)

# 7. Отрицательные оси: track='-Z' -> Z-ось против нормали
m = vertex_matrix(tri, [], [[0,1,2]], '-Z', '-Y')[0]
results.append(_dot(m[2][:3], (0,0,-1)) > 0.999)

# 8. Пустые рёбра, одинокая вершина
results.append(normals_from_edges([(5,5,5)], [])[0] == (0.0,0.0,1.0))

print("\nИТОГ:", "ВСЕ ТЕСТЫ ПРОШЛИ" if all(results) else f"ПРОВАЛ: {results}")
"""