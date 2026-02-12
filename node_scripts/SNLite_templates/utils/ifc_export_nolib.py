'''
in vertices    v d=[[]] n=0
in polygons    s d=[[]] n=0
in filepath    FP d=[[]] n=0
in object_name   s d="IFC_Export" n=2
enum = BREP MESH
in max_faces     s d=10000 n=2
in area_threshold s d=0.00001 n=2
'''

import bpy

self.make_operator('make')


def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='E X P O R T').cb_name='make'
    layout.prop(self, 'custom_enum', expand=True)

def make(self, context):
    """
    Главная функция для экспорта геометрии в IFC формат
    Импорты кроме bpy должны быть внутри этой функции
    """
    # Импортируем необходимые модули
    import os
    import uuid
    from datetime import datetime
    import math
    import numpy as np
    
    # Получаем данные из входов ноды - ТЕПЕРЬ СПИСКИ СПИСКОВ
    vertices_list = self.inputs['vertices'].sv_get()  # [[вершины1], [вершины2], ...]
    polygons_list = self.inputs['polygons'].sv_get()  # [[полигоны1], [полигоны2], ...]
    max_faces = max(self.inputs['max_faces'].sv_get()[0][0],100)
    area_threshold = self.inputs['area_threshold'].sv_get()[0][0]
    geometry_type = self.custom_enum
    
    # Проверяем, что есть данные
    if not vertices_list or not polygons_list:
        print("✗ Нет данных для экспорта")
        return False
    
    # Получаем количество объектов
    num_objects = min(len(vertices_list), len(polygons_list))
    
    if num_objects == 0:
        print("✗ Нет объектов для экспорта")
        return False
    
    # Обрабатываем filepath
    filepath_input = self.inputs['filepath'].sv_get()
    base_filepath = ""
    if filepath_input and filepath_input[0]:
        base_filepath = filepath_input[0][0]
    else:
        base_filepath = os.path.join(os.path.expanduser("~"), "exported_model")
    
    # Обрабатываем имена объектов
    if self.inputs['object_name'].is_linked:        
        object_name_input = self.inputs['object_name'].sv_get()
    else:
        object_name_input = [['Sverchok_object']]
    base_object_name = "IFC_Export"
    
    def clean_ascii_string(text):
        """Удаляет не-ASCII символы из строки"""
        if not text:
            return ""
        # Оставляем только ASCII символы
        cleaned = ''.join(char for char in str(text) if ord(char) < 128)
        # Удаляем кавычки и другие проблемные символы
        cleaned = cleaned.replace('"', '').replace("'", '').replace('\n', ' ').replace('\r', '')
        return cleaned.strip() or "Unknown"

    if object_name_input and object_name_input[0]:
        base_object_name = object_name_input[0][0]
        base_object_name = clean_ascii_string(base_object_name)
    
    # Генерация GUID для IFC объектов
    def create_guid(num=32):
        """Создание GUID в формате IFC (32 символа без дефисов)"""
        if num == 36:
            guid = str(uuid.uuid4()).upper()
        else:
            guid = str(uuid.uuid4()).replace('-', '').upper()
        # ДОБАВЬТЕ проверку:
        if guid == '00000000000000000000000000000000':
            # Генерируем заново если получили нулевой GUID
            guid = str(uuid.uuid4()).replace('-', '').upper()
        print(guid)
        if num == 32:
            return guid
        elif num == 36:
            return guid
        else:
            return guid[:22]

    def ensure_area(points, indices):
        p1 = np.array(points[indices[0]])
        p2 = np.array(points[indices[1]])
        p3 = np.array(points[indices[2]])

        # Вычислить векторное произведение
        v1 = p2 - p1
        v2 = p3 - p1
        cross = np.cross(v1, v2)
        area = np.linalg.norm(cross) / 2
        if area < area_threshold:  # Порог для вырожденности
            return False
        else:
            return True

    def ensure_counter_clockwise(points, indices):
        """Обеспечивает порядок вершин против часовой стрелки"""

        # не работает, хотя все перевели в треугольники, наверное зря
        if len(indices) < 3:
            return indices
        
        # Берем первые три точки
        p0 = points[indices[0]]
        p1 = points[indices[1]]
        p2 = points[indices[2]]
        
        # Вычисляем нормаль
        v1 = [p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]]
        v2 = [p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]]
        
        # Векторное произведение
        normal = [
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        ]
        # Если нормаль направлена вниз (Z отрицательный), разворачиваем порядок
        if normal[2] < 0:
            return list(reversed(indices))
        
        return indices

    def are_points_collinear(points, epsilon=1e-6):
        """Проверяет, коллинеарны ли точки"""
        if len(points) < 3:
            return True
            
        p0, p1, p2 = points[:3]
        
        # Векторы
        v1 = [p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]]
        v2 = [p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]]
        
        # Векторное произведение
        cross = [
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        ]
        
        # Если векторное произведение близко к нулю
        length = (cross[0]**2 + cross[1]**2 + cross[2]**2)**0.5
        return length < epsilon
        #return abs(cross[0]) < epsilon and abs(cross[1]) < epsilon and abs(cross[2]) < epsilon

    def triangulate_polygon_simple(points, indices):
        """Простая триангуляция для выпуклых полигонов"""
        triangles = []
        n = len(indices)
        
        if n < 3:
            return triangles
            
        for i in range(1, n-1):
            area = ensure_area(points, [indices[0], indices[i], indices[i+1]])
            if area:
                triangles.append([indices[0], indices[i], indices[i+1]])

        return triangles

    # Функция для создания геометрических сущностей для одного объекта
    def create_geometry_entities_for_object(verts, polys, start_index, obj_index, max_faces, geometry_type="BREP"):
        """
        Создание геометрических сущностей IFC для одного объекта
        Параметр geometry_type: "BREP" или "MESH"
        """
        entities = []
        current_index = start_index
        
        obj_data = {
            'point_indices': [],
            'face_indices': [],
            'shell_index': None,
            'brep_index': None,
            'shape_rep_index': None,
            'next_index': current_index,
            'mesh_indices': [],
            'geom_set_indices': []
        }
        
        # 1. ОЧИСТКА вершин: удаляем дубликаты и NaN
        unique_verts = []
        unique_indices = {}
        
        for i, vert in enumerate(verts):
            if i >= max_faces:
                break
                
            try:
                x, y, z = float(vert[0]), float(vert[1]), float(vert[2])
                if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
                    continue
                    
                key = (round(x*1000, 3), round(y*1000, 3), round(z*1000, 3))
                
                if key not in unique_indices:
                    unique_indices[key] = len(unique_verts)
                    unique_verts.append((x, y, z))
                    
            except (ValueError, IndexError):
                continue
        
        # 2. Создаем точки 
        to_triangle = []
        for x, y, z in unique_verts:
            x_mm = x * 1000.0
            y_mm = y * 1000.0
            z_mm = z * 1000.0
            entities.append(f"#{current_index}=IFCCARTESIANPOINT(({x_mm:.3f},{y_mm:.3f},{z_mm:.3f}));")
            if geometry_type != "BREP":
                to_triangle.append((round(x_mm,3),round(y_mm,3),round(z_mm,3)))
            obj_data['point_indices'].append(current_index)
            current_index += 1
        
        # 3. Валидация полигонов (без изменений)
        valid_polys = []
        for poly in polys[:max_faces]:
            if len(poly) < 3:
                continue
                
            valid_poly = []
            for idx in poly:
                if idx < len(verts):
                    vert = verts[idx]
                    key = (round(vert[0]*1000, 3), round(vert[1]*1000, 3), round(vert[2]*1000, 3))
                    if key in unique_indices:
                        new_idx = unique_indices[key]
                        if new_idx not in valid_poly:
                            valid_poly.append(new_idx)
            
            if len(valid_poly) >= 3:
                if not are_points_collinear([unique_verts[i] for i in valid_poly[:3]]):
                    valid_poly = ensure_counter_clockwise(verts, valid_poly)
                    valid_polys.append(valid_poly)
        
        # 4. Выбор типа геометрии
        if geometry_type == "BREP":
            entities_part, obj_data = create_brep_geometry(entities, obj_data, unique_verts, valid_polys, current_index)
        else:  # MESH
            entities_part, obj_data = create_triangulated_mesh_geometry(entities, obj_data, unique_verts, valid_polys, to_triangle, current_index)
        
        entities = entities_part
        current_index = obj_data['next_index']
        
        return "\n".join(entities) + "\n", obj_data


    def create_brep_geometry(entities, obj_data, unique_verts, valid_polys, current_index):
        """Создание геометрии в формате FacetedBrep (оболочки из граней)"""
        
        # Создаем треугольники для FacetedBrep
        for poly in valid_polys:
            triangles = triangulate_polygon_simple(unique_verts, poly)
            
            for tri in triangles:
                if len(tri) != 3:
                    continue
                    
                # Проверяем, что все индексы валидны
                if all(idx < len(obj_data['point_indices']) for idx in tri):
                    point_refs = ",".join([f"#{obj_data['point_indices'][idx]}" for idx in tri])
                    entities.append(f"#{current_index}=IFCPOLYLOOP(({point_refs}));")
                    poly_index = current_index
                    current_index += 1
                    
                    entities.append(f"#{current_index}=IFCFACEOUTERBOUND(#{poly_index},.U.);")
                    face_bound_index = current_index
                    current_index += 1
                    
                    entities.append(f"#{current_index}=IFCFACE((#{face_bound_index}));")
                    obj_data['face_indices'].append(current_index)
                    current_index += 1
        
        # Если нет граней, создаем простой тетраэдр
        if not obj_data['face_indices'] and len(obj_data['point_indices']) >= 4:
            tetra_faces = [
                [0, 1, 2],
                [0, 2, 3],
                [0, 3, 1],
                [1, 3, 2]
            ]
            
            for face in tetra_faces:
                if all(idx < len(obj_data['point_indices']) for idx in face):
                    point_refs = ",".join([f"#{obj_data['point_indices'][idx]}" for idx in face])
                    entities.append(f"#{current_index}=IFCPOLYLOOP(({point_refs}));")
                    poly_index = current_index
                    current_index += 1
                    
                    entities.append(f"#{current_index}=IFCFACEOUTERBOUND(#{poly_index},.U.);")
                    face_bound_index = current_index
                    current_index += 1
                    
                    entities.append(f"#{current_index}=IFCFACE((#{face_bound_index}));")
                    obj_data['face_indices'].append(current_index)
                    current_index += 1
        
        # Создаем геометрические объекты для BREP
        if obj_data['face_indices']:
            if len(obj_data['face_indices']) >= 4:
                face_refs = ",".join([f"#{idx}" for idx in obj_data['face_indices']])
                entities.append(f"#{current_index}=IFCCLOSEDSHELL(({face_refs}));")
                obj_data['shell_index'] = current_index
                current_index += 1
                
                entities.append(f"#{current_index}=IFCFACETEDBREP(#{obj_data['shell_index']});")
                obj_data['brep_index'] = current_index
                current_index += 1
                
                entities.append(f"#{current_index}=IFCSHAPEREPRESENTATION(#12,'Body','Brep',(#{obj_data['brep_index']}));")
                obj_data['shape_rep_index'] = current_index
                current_index += 1
        
        obj_data['next_index'] = current_index
        return entities, obj_data

    def create_triangulated_mesh_geometry(entities, obj_data, unique_verts, valid_polys, to_triangle, current_index):
        """Создание геометрии в формате TriangulatedFaceSet (IFC4)"""
        
        # Собираем все треугольники
        all_triangles = []
        
        for poly in valid_polys:
            triangles = triangulate_polygon_simple(unique_verts, poly)
            for tri in triangles:
                if len(tri) == 3 and all(idx < len(obj_data['point_indices']) for idx in tri):
                    all_triangles.append(tri)
        
        # Если нет треугольников, создаем простой тетраэдр
        if not all_triangles and len(obj_data['point_indices']) >= 4:
            tetra_faces = [
                [0, 1, 2],
                [0, 2, 3],
                [0, 3, 1],
                [1, 3, 2]
            ]
            for face in tetra_faces:
                if all(idx < len(obj_data['point_indices']) for idx in face):
                    all_triangles.append(face)
        
        # Создаем IfcTriangulatedFaceSet
        if all_triangles:
            # Получаем все уникальные индексы точек, используемые в треугольниках
            used_indices = set()
            for tri in all_triangles:
                used_indices.update(tri)
            sorted_indices = sorted(used_indices)
            
            # Создаем карту переиндексации (старый индекс -> новый индекс в координатном списке)
            remap = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted_indices)}
            
            # 1. Создаем IfcCartesianPointList3D с координатами в правильном формате
            coord_refs = []
            for idx in sorted_indices:
                coord_refs.append(f"#{obj_data['point_indices'][idx]}")
            
            #entities.append(f"#{current_index}=IFCCARTESIANPOINTLIST3D(({','.join(coord_refs)}));")
            entities.append(f"#{current_index}=IFCCARTESIANPOINTLIST3D({tuple(to_triangle)});")
            point_list_idx = current_index
            current_index += 1
            
            # 2. Создаем список индексов треугольников в формате ((i1,i2,i3),...)
            tri_indices_list = []
            for tri in all_triangles:
                # Переиндексируем точки
                t1, t2, t3 = remap[tri[0]], remap[tri[1]], remap[tri[2]]
                tri_indices_list.append(f"({t1},{t2},{t3})")
            
            tri_indices_str = ",".join(tri_indices_list)
            
            # 3. Создаем IfcTriangulatedFaceSet
            # ВАЖНО: Для IFC4 TriangulatedFaceSet не требует IfcFace, это прямой GeometricRepresentationItem tri_indices_str
            entities.append(f"#{current_index}=IFCTRIANGULATEDFACESET(#{point_list_idx},$,$,({tri_indices_str}),$,$);")
            mesh_idx = current_index
            obj_data['mesh_indices'].append(mesh_idx)
            current_index += 1
            
            # 4. Создаем IfcShapeRepresentation с правильным типом 'Tessellation'
            entities.append(f"#{current_index}=IFCSHAPEREPRESENTATION(#12,'Body','Tessellation',(#{mesh_idx}));")
            obj_data['shape_rep_index'] = current_index
            current_index += 1
        
        obj_data['next_index'] = current_index
        return entities, obj_data


    # Функция создания полного IFC контента для нескольких объектов
    def generate_ifc_content_multiple(objects_data, base_obj_name,max_faces):
        """Генерация полного содержимого IFC файла для нескольких объектов"""
        timestamp = int(datetime.now().timestamp())
        iso_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        # Генерируем GUID для основных объектов
        project_guid = create_guid(num=22)
        site_guid = create_guid(num=22)
        building_guid = create_guid(num=22)
        storey_guid = create_guid(num=22)

        # Собираем все сущности
        all_entities = []
        element_data = []  # Данные об элементах для создания отношений
        current_index = 16  # Начинаем после базовых сущностей
        
        # Создаем геометрию для каждого объекта
        for obj_idx, obj_data in enumerate(objects_data):
            verts = obj_data['vertices']
            polys = obj_data['polygons']
            obj_name = f"{base_obj_name}_{obj_idx + 1}"
            
            # Создаем геометрию для объекта
            geometry_str, obj_geometry_data = create_geometry_entities_for_object(
                verts, polys, current_index, obj_idx,max_faces, geometry_type
            )
            
            all_entities.append(geometry_str)
            
            # Сохраняем данные для создания элемента
            if obj_geometry_data.get('shape_rep_index'):
                element_data.append({
                    'name': obj_name,
                    'guid': create_guid(num=22),
                    'shape_rep_index': obj_geometry_data['shape_rep_index'],
                    'next_index': obj_geometry_data['next_index']
                })
                current_index = obj_geometry_data['next_index']
        
        # Создаем элементы (IfcBuildingElementProxy)
        element_entities = []
        index_IFCBUILDINGSTOREY = current_index+2+len(element_data)*2
        for elem in element_data:
            # Создаем определение формы
            elem_guid = create_guid(num=22)
            additional_guid = create_guid(num=36)
            shape_def_index = current_index
            element_entities.append(f"#{shape_def_index}=IFCPRODUCTDEFINITIONSHAPE($,$,(#{elem['shape_rep_index']}));")
            current_index += 1
            # Создаем элемент
            element_entities.append(f"#{current_index}=IFCBUILDINGELEMENTPROXY('{elem_guid}',#5,'{elem['name']}',$,$,$,#{shape_def_index},'{additional_guid}',$);")
            elem['element_index'] = current_index
            elem['guid'] = elem_guid  # Сохраняем GUID
            current_index += 1
        #print(len(element_entities))
        # Формируем полный IFC файл
        filename = f"{base_obj_name}.ifc"
        site_name = clean_ascii_string(f"Site_{base_obj_name}")
        building_name = clean_ascii_string(f"Building_{base_obj_name}")
        storey_name = "Level_0"
        allen = "\n".join(all_entities)
        elen = "\n".join(element_entities)
        
        ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('{filename}','{iso_date}',(''),(''),'Sverchok IFC Export','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPERSON($,'Sverchok User',$,$,$,$,$,$);
#2=IFCORGANIZATION($,'Sverchok BIM Export',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION(#2,'1.0','Sverchok IFC Exporter','Sverchok');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,$,$,{timestamp});
#6=IFCCARTESIANPOINT((0.,0.,0.));
#7=IFCDIRECTION((0.,0.,1.));
#8=IFCDIRECTION((1.,0.,0.));
#9=IFCAXIS2PLACEMENT3D(#6,#7,#8);
#10=IFCDIRECTION((0.,1.));
#11=IFCAXIS2PLACEMENT2D(#6,#10);
#12=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,$);
#13=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Plan',2,1.E-05,#11,$);
#14=IFCPROJECT('{project_guid}',#5,'{base_obj_name} Project',$,$,$,$,(#12,#13),$);


{allen}

{elen}

#{current_index+0}=IFCSITE('{site_guid}',#5,'{site_name}',$,$,$,$,$,.ELEMENT.,$,$,$,$,$);
#{current_index+1}=IFCBUILDING('{building_guid}',#5,'{building_name}',$,$,$,$,$,.ELEMENT.,$,$,$);
#{current_index+2}=IFCBUILDINGSTOREY('{storey_guid}',#5,'{storey_name}',$,$,$,$,$,.ELEMENT.,0.);"""
        # Добавляем отношения
        element_indices = ",".join([f"#{elem['element_index']}" for elem in element_data])
        rel_guid1 = create_guid(num=22)
        rel_guid2 = create_guid(num=22)
        rel_guid3 = create_guid(num=22)
        rel_guid4 = create_guid(num=22)

        relations = f"""
        #{current_index+3}=IFCRELAGGREGATES('{rel_guid1}',#5,$,$,#14,(#{current_index+0}));
        #{current_index+4}=IFCRELAGGREGATES('{rel_guid2}',#5,$,$,#{current_index+0},(#{current_index+1}));
        #{current_index+5}=IFCRELAGGREGATES('{rel_guid3}',#5,$,$,#{current_index+1},(#{current_index+2}));
        #{current_index+6}=IFCRELCONTAINEDINSPATIALSTRUCTURE('{rel_guid4}',#5,$,$,({element_indices}),#{current_index+2});"""
        
        ifc_content += relations + "\nENDSEC;\nEND-ISO-10303-21;"
        
        return ifc_content
    
    # Основной процесс
    try:
        # Подготавливаем данные объектов
        objects_data = []
        for i in range(num_objects):
            # Проверяем, что у нас есть соответствующие данные
            if i < len(vertices_list) and i < len(polygons_list):
                objects_data.append({
                    'vertices': vertices_list[i],
                    'polygons': polygons_list[i]
                })
            else:
                print(f"⚠ Предупреждение: нет данных для объекта {i}")

        
        # Определяем путь для файла
        if not base_filepath.lower().endswith('.ifc'):
            final_filepath = base_filepath + '.ifc'
        else:
            final_filepath = base_filepath
        
        # Создаем директорию
        os.makedirs(os.path.dirname(os.path.abspath(final_filepath)), exist_ok=True)
        # Генерируем содержимое IFC
        ifc_content = generate_ifc_content_multiple(objects_data, base_object_name,max_faces)
        
        # Сохраняем файл
        with open(final_filepath, 'w', encoding='utf-8') as f:
            f.write(ifc_content)
        
        # Выводим информацию
        print(f"✓ IFC файл успешно создан:")
        print(f"  Путь: {final_filepath}")
        print(f"  Количество объектов: {num_objects}")
        print(f"  Базовое имя: {base_object_name}")
        
        # Дополнительная информация по объектам
        for i, obj_data in enumerate(objects_data):
            print(f"  Объект {i+1}: {len(obj_data['vertices'])} вершин, {len(obj_data['polygons'])} полигонов")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при создании IFC файла:")
        print(f"  Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
