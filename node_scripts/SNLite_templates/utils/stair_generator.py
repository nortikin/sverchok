'''
in stair_width s d=1.5 n=2
in floor_height s d=[3.3] n=1
in distance_between_flights s d=0.15 n=2
in platethick s d=0.15 n=2
in railthick s d=0.05 n=2
enum = CONSTLEN SHRINK
enum2 = RAMP RAILS STEPS
out vertices v
out polygons s
out data s
out thickness s
'''

import bpy

def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)
    layout.prop(self, 'custom_enum_2', expand=True)

def create_staircase(stair_width, floor_height, distance_between_flights):
    """
    Создает 3D модель лестницы с двумя маршами и промежуточными площадками
    
    Parameters:
    stair_width: ширина марша
    floor_height: высота этажа
    distance_between_flights: расстояние между маршами
    
    Returns:
    vertices: список вершин [[x,y,z], ...]
    polygons: список полигонов [[v0,v1,v2,v3], ...]
    """
    
    # Уклон 1:2 означает, что на 1 метр высоты приходится 2 метра длины
    slope_ratio = 2.0
    keep_length = self.custom_enum
    mode = self.custom_enum_2
    rail = 0.9
    
    # Общая ширина конструкции (два марша + зазор)
    total_width = (2 * stair_width) + distance_between_flights
    
    vertices = []
    polygons = []
    base_z = 0
    # Количество этажей (округляем вниз до целого)
    #num_floors = int(building_height // floor_height)
    num_floors = len(floor_height)
    
    # Создаем лестницу для каждого этажа
    for floor in range(num_floors):
        floor_height_ = floor_height[floor]
        # Длина марша по горизонтали
        flight_length = floor_height_ * slope_ratio / 2
        if keep_length == 'CONSTLEN' and base_z == 0:
            monolength = flight_length + stair_width
        elif keep_length != 'CONSTLEN':
            monolength = flight_length + stair_width
        #print(base_z,monolength)
        # Вершины для первого марша (подъем)
        v0 = [0, 0, base_z]  # левая-передняя-низ
        v1 = [stair_width, 0, base_z]  # правая-передняя-низ
        v2 = [stair_width, flight_length, base_z + floor_height_/2]  # правая-задняя-верх
        v3 = [0, flight_length, base_z + floor_height_/2]  # левая-задняя-верх
        
        # Вершины для первой площадки
        v4 = [0, flight_length, base_z + floor_height_/2]
        v5 = [total_width, flight_length, base_z + floor_height_/2]
        v6 = [total_width, monolength, base_z + floor_height_/2]
        v7 = [0, monolength, base_z + floor_height_/2]
        
        # Вершины для второго марша (подъем в обратную сторону)
        v8 = [stair_width + distance_between_flights, 0, base_z + floor_height_]
        v9 = [stair_width + distance_between_flights + stair_width, 0, base_z + floor_height_]
        v10 = [stair_width + distance_between_flights + stair_width, flight_length, base_z + floor_height_/2]
        v11 = [stair_width + distance_between_flights, flight_length, base_z + floor_height_/2]
        
        # Вершины для верхней площадки
        v12 = [0, -stair_width, base_z + floor_height_]
        v13 = [stair_width + distance_between_flights + stair_width, -stair_width, base_z + floor_height_]
        v14 = [stair_width + distance_between_flights + stair_width, 0, base_z + floor_height_]
        v15 = [0, 0, base_z + floor_height_]

        
        # Добавляем вершины текущего этажа
        floor_vertices = [v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15]

        # Смещаем индексы для текущего этажа
        vertex_offset = len(vertices)
        vertices.extend(floor_vertices)

        if mode == 'RAILS' or mode == 'STEPS':
            rvers = [
                    v1,
                    v2,
                    [v2[0],v2[1],v2[2]+rail],
                    [v1[0],v1[1],v1[2]+rail],
                    [v8[0],v8[1],v8[2]+rail],
                    [v11[0],v11[1],v11[2]+rail],
                    v11,
                    v8,
                    ]
            vertices.extend(rvers)
        if mode == 'STEPS':
            svers = []
            #print('svers', v0,v3,v8,v11)
            for i in range(1+int(floor_height_//0.3)):
                svers.extend([
                            [v0[0],  v0[1]+i*0.3,          v0[2]+(i+1)*0.15 ],
                            [v1[0],  v1[1]+i*0.3,          v1[2]+(i+1)*0.15 ],
                            [v1[0],  v1[1]+(i+1)*0.3,      v1[2]+(i+1)*0.15   ],
                            [v0[0],  v0[1]+(i+1)*0.3,      v0[2]+(i+1)*0.15   ],
                            [v11[0], v11[1]-(i+1)*0.3,     v11[2]+(i+1)*0.15 ],
                            [v10[0], v10[1]-(i+1)*0.3,     v10[2]+(i+1)*0.15],
                            [v10[0], v10[1]-i*0.3,         v10[2]+(i+1)*0.15],
                            [v11[0], v11[1]-i*0.3,         v11[2]+(i+1)*0.15 ]
                            ])
            #print('SVERS',svers)
            vertices.extend(svers)
        # Создаем полигоны для текущего этажа
        if mode == 'RAMP':
            r = 4
        elif mode == 'RAILS':
            r = 6
        elif mode == 'STEPS':
            r = 6 + int(len(svers)/4)
        # Каждый полигон - это 4 вершины (прямоугольник)
        thickness = []
        for i in range(r):
            polygon = [vertex_offset + i*4 + j for j in range(4)]
            polygons.append(polygon)
        if mode == 'RAMP':
            thickness.extend([platethick for i in range(4*4)])
        elif mode == 'RAILS':
            thickness.extend([platethick for i in range(4*4)])
            thickness.extend([railthick for i in range(4*2)])
        else:
            thickness.extend([platethick for i in range(4*4)])
            thickness.extend([railthick for i in range(4*2)])
            thickness.extend([platethick for i in range(4*int(len(svers)/4))])
        base_z = base_z + floor_height_
    maxz = max([i[2] for i in vertices])+stair_width
    if mode == 'RAILS':
        maxz -= rail
    data = ['Верхняя отметка '+str(round(maxz,2)),'Ширина лестничной клетки '+str(round(total_width,2)),
        '+ учесть на отделку 20 мм по каждой стене']

    
    return [vertices], [polygons], [data], [thickness]


# Создаем лестницу
vertices, polygons, data, thickness = create_staircase(
    stair_width=stair_width,
    floor_height=floor_height,
    distance_between_flights=distance_between_flights
)