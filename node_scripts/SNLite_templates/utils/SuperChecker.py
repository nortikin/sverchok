"""
in verts_in v
in faces_in s
in step_x s d=2 n=1
in step_y s d=2 n=1
in offset s d=1 n=1
in precision s d=3 n=1
enum = XYZ POLAR
out verts v
out faces_out s
"""

# Супер чекер (superchecker) - шахматный выделятор
# выделяет каждый N-ный полигон по двум направлениям
# анализ сетки происходит по кординатам, либо декартовым
# либо полярным, с допуском в виде точности precision
# офсет отступает каждй второй ряд полигонов
# автор @Johanntelemann

import math
import bpy

# Функция для отрисовки кнопок в ряд
def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)

def get_center(face, verts):
    pts = [verts[i] for i in face]
    return [sum(axis) / len(pts) for axis in zip(*pts)]

def to_polar(co):
    x, y, z = co
    angle = math.atan2(y, x)
    radius = math.sqrt(x**2 + y**2)
    # Возвращаем в порядке [угол, z, радиус] для сортировки
    return [angle, z, radius]

if verts_in and faces_in:
    out_faces = []
    
    # Получаем значение из кнопок (0 для XYZ, 1 для POLAR)
    # В Сверчке custom_enum возвращает строку ('XYZ' или 'POLAR')
    mode_str = self.custom_enum 

    for v_mesh, f_mesh in zip(verts_in, faces_in):
        centers = {}
        cur_prec = precision[0] if isinstance(precision, (list, tuple)) else precision

        for i, face in enumerate(f_mesh):
            co = get_center(face, v_mesh)
            # Если выбрано POLAR, конвертируем координаты
            centers[i] = to_polar(co) if mode_str == 'POLAR' else co

        # Остальная логика сортировки
        coords = list(centers.values())
        ranges = [max(c[i] for c in coords) - min(c[i] for c in coords) for i in range(3)]
        sorted_axes = sorted(range(3), key=lambda i: ranges[i], reverse=True)
        ax_y, ax_x = sorted_axes[0], sorted_axes[1]

        rows_dict = {}
        for idx in centers:
            val_y = round(centers[idx][ax_y], int(cur_prec))
            if val_y not in rows_dict: rows_dict[val_y] = []
            rows_dict[val_y].append(idx)

        sorted_y_keys = sorted(rows_dict.keys(), reverse=True)
        to_keep_indices = []

        for r_idx, y_key in enumerate(sorted_y_keys):
            s_y = step_y[0] if isinstance(step_y, (list, tuple)) else step_y
            if r_idx % max(1, s_y) == 0:
                row_items = sorted(rows_dict[y_key], key=lambda i: centers[i][ax_x])
                
                off = offset[0] if isinstance(offset, (list, tuple)) else offset
                s_x = step_x[0] if isinstance(step_x, (list, tuple)) else step_x
                
                # Смещение для шахматного порядка
                current_offset = off if (r_idx // max(1, s_y)) % 2 != 0 else 0
                
                for e_idx, f_idx in enumerate(row_items):
                    if (e_idx + current_offset) % max(1, s_x) == 0:
                        to_keep_indices.append(f_idx)

        out_faces.append([f_mesh[i] for i in to_keep_indices])

    verts = verts_in
    faces_out = out_faces
