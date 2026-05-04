"""
in Vertices_in v d=[] n=1
in Distance s d=0.1 n=2
in Miter_limit s d=2.0 n=2
in Arc_tol s d=0.1 n=2
enum = Miter Round Square
enum2 = Polygon ClosedLine OpenButt OpenSquare OpenRound
out Vertices_out v
out Edges_out s
# Clipper Offset Pro @il_de_signer
"""

import pyclipper
from mathutils import Vector
import numpy as np

def ui(self, context, layout):
    layout.label(text="Join Type:", icon='MOD_BEVEL')
    row = layout.row(align=True)
    row.prop_enum(self, "custom_enum", "Miter")
    row.prop_enum(self, "custom_enum", "Round")
    row.prop_enum(self, "custom_enum", "Square")
    
    layout.label(text="End Type:", icon='GP_SELECT_POINTS')
    col = layout.column(align=True)
    row2 = col.row(align=True)
    row2.prop_enum(self, "custom_enum_2", "Polygon")
    row2.prop_enum(self, "custom_enum_2", "ClosedLine")
    
    row3 = col.row(align=True)
    row3.prop_enum(self, "custom_enum_2", "OpenButt")
    row3.prop_enum(self, "custom_enum_2", "OpenSquare")
    row3.prop_enum(self, "custom_enum_2", "OpenRound")

    # Инфо-блок
    box = layout.box()
    box.label(text=f"Mode: {self.custom_enum} / {self.custom_enum_2}", icon='TOOL_SETTINGS')

def run():
    if not Vertices_in:
        return [[]], [[]]

    # 1. Масштабирование и параметры
    SCALE = 1000000
    m_limit = float(Miter_limit if Miter_limit is not None else 2.0)
    a_tol = float(Arc_tol if Arc_tol is not None else 0.1)
    
    # Конвертация параметров из Enum
    jt_map = {
        'Miter': pyclipper.JT_MITER,
        'Round': pyclipper.JT_ROUND,
        'Square': pyclipper.JT_SQUARE
    }
    et_map = {
        'Polygon': pyclipper.ET_CLOSEDPOLYGON,
        'ClosedLine': pyclipper.ET_CLOSEDLINE,
        'OpenButt': pyclipper.ET_OPENBUTT,
        'OpenSquare': pyclipper.ET_OPENSQUARE,
        'OpenRound': pyclipper.ET_OPENROUND
    }
    
    join_type = jt_map.get(self.custom_enum, pyclipper.JT_MITER)
    end_type = et_map.get(self.custom_enum_2, pyclipper.ET_CLOSEDPOLYGON)

    # 2. Подготовка пути (только X, Y)
    # Script Lite для n=1 отдает плоский список вершин
    path = [[int(v[0] * SCALE), int(v[1] * SCALE)] for v in Vertices_in]
    
    pco = pyclipper.PyclipperOffset()
    pco.MiterLimit = m_limit
    pco.ArcTolerance = int(a_tol * SCALE)
    pco.AddPath(path, join_type, end_type)
    
    # 3. Выполнение офсета
    d_val = float(Distance if Distance is not None else 0.1)
    solution = pco.Execute(int(d_val * SCALE))
    
    final_v = []
    final_e = []
    v_off = 0
    
    for poly in solution:
        n = len(poly)
        if n < 2: continue
        
        # Добавляем Z=0, чтобы Сверчок не ругался на размерность
        p_verts = [[p[0]/SCALE, p[1]/SCALE, 0.0] for p in poly]
        final_v.extend(p_verts)
        
        # Ребра
        for i in range(n):
            if end_type == pyclipper.ET_CLOSEDPOLYGON or end_type == pyclipper.ET_CLOSEDLINE:
                # Замкнутый контур
                final_e.append([v_off + i, v_off + (i + 1) % n])
            else:
                # Разомкнутый контур (иногда Clipper возвращает их для Open типов)
                if i < n - 1:
                    final_e.append([v_off + i, v_off + i + 1])
        
        v_off += n

    return [final_v], [final_e]

# Выход
Vertices_out, Edges_out = run()
