'''
in vertices    v d=[[]] n=0
in polygons    s d=[[]] n=0
in filepath    FP d=[[]] n=0
in object_name   s d="IFC_Export" n=2
in max_faces     s d=10000 n=2
'''

import bpy

self.make_operator('make')

def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='E X P O R T').cb_name='make'

def make(self, context):
    """
    Главная функция для экспорта геометрии в IFC формат
    Импорты кроме bpy должны быть внутри этой функции
    """
    # Импортируем необходимые модули
    import os
    import uuid
    from datetime import datetime
    
    # Получаем данные из входов ноды - ТЕПЕРЬ СПИСКИ СПИСКОВ
    vertices_list = self.inputs['vertices'].sv_get()  # [[вершины1], [вершины2], ...]
    polygons_list = self.inputs['polygons'].sv_get()  # [[полигоны1], [полигоны2], ...]
    max_faces = max(self.inputs['max_faces'].sv_get()[0][0],10000)
    
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
    object_name_input = self.inputs['object_name'].sv_get()
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
    def create_guid():
        """Создание GUID в формате IFC (32 символа без дефисов)"""
        guid = str(uuid.uuid4()).replace('-', '').upper()
        # ДОБАВЬТЕ проверку:
        if guid == '00000000000000000000000000000000':
            # Генерируем заново если получили нулевой GUID
            guid = str(uuid.uuid4()).replace('-', '').upper()
        print(guid)
        return guid

    def ensure_counter_clockwise(points, indices):
        """Обеспечивает порядок вершин против часовой стрелки"""
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

    # Преобразуйте полигоны в треугольники:
    def triangulate_polygon(indices):
        """Разбивает полигон на треугольники"""
        triangles = []
        if len(indices) < 3:
            return triangles
        
        for i in range(1, len(indices)-1):
            triangles.append([indices[0], indices[i], indices[i+1]])
        
        return triangles

    # Функция для создания геометрических сущностей для одного объекта
    def create_geometry_entities_for_object(verts, polys, start_index, obj_index, max_faces):
        """
        Создание геометрических сущностей IFC для одного объекта
        Возвращает строку с STEP-кодом и индекс для продолжения нумерации
        """
        entities = []
        current_index = start_index
        
        # Запоминаем индексы созданных сущностей для этого объекта
        obj_data = {
            'point_indices': [],
            'face_indices': [],
            'shell_index': None,
            'brep_index': None,
            'shape_rep_index': None,
            'next_index': current_index
        }
        
        # 1. Создаем точки (вершины)
        for i, vert in enumerate(verts):
            # Ограничиваем количество вершин для стабильности
            if i >= max_faces:
                break
                
            # Конвертация из метров в миллиметры (IFC стандарт)
            x_mm = float(vert[0] * 1000.0)
            y_mm = float(vert[1] * 1000.0)
            z_mm = float(vert[2] * 1000.0)
            entities.append(f"#{current_index}=IFCCARTESIANPOINT(({x_mm:.6f},{y_mm:.6f},{z_mm:.6f}));")

            obj_data['point_indices'].append(current_index)
            current_index += 1
        
        # 2. Создаем полигоны и грани
        max_faces = min(max_faces, len(polys))
        
        for i, poly in enumerate(polys[:max_faces]):
            if len(poly) < 3:
                continue
                
            # Проверяем, что все индексы валидны
            valid_indices = [idx for idx in poly if idx < len(obj_data['point_indices'])]
            if len(valid_indices) < 3:
                continue

            

            # Создаем полигон (IFCPOLYLOOP)
            #corrected_indices = ensure_counter_clockwise(verts, valid_indices)
            triangles = triangulate_polygon(valid_indices)
            for tri in triangles:
                # Создайте IFCPOLYLOOP для каждого треугольника
                point_refs = ",".join([f"#{obj_data['point_indices'][idx]}" for idx in tri])
                #point_refs = point_refs + f",#{obj_data['point_indices'][tri[0]]}"  # Замыкаем
                #point_refs = ",".join([f"#{obj_data['point_indices'][idx]}" for idx in valid_indices]) #corrected_indices])
                entities.append(f"#{current_index}=IFCPOLYLOOP(({point_refs}));")
                poly_index = current_index
                current_index += 1
            
                # Создаем внешнюю границу грани (IFCFACEOUTERBOUND)
                entities.append(f"#{current_index}=IFCFACEOUTERBOUND(#{poly_index},.T.);")
                face_bound_index = current_index
                current_index += 1
            
                # Создаем грань (IFCFACE)
                entities.append(f"#{current_index}=IFCFACE((#{face_bound_index}));")
                obj_data['face_indices'].append(current_index)
                current_index += 1
        
        if not obj_data['face_indices'] and len(obj_data['point_indices']) >= 3:
            # Создаем простую грань по умолчанию
            entities.append(f"#{current_index}=IFCPOLYLOOP((#{obj_data['point_indices'][0]},#{obj_data['point_indices'][1]},#{obj_data['point_indices'][2]}));")
            poly_index = current_index
            current_index += 1
            entities.append(f"#{current_index}=IFCFACEOUTERBOUND(#{poly_index},.U.);") # T для правильно ориентированых полигонов F для неправильно
            face_bound_index = current_index
            current_index += 1
            entities.append(f"#{current_index}=IFCFACE((#{face_bound_index}));")
            obj_data['face_indices'].append(current_index)
            current_index += 1
        
        # 3. Создаем геометрические объекты если есть грани
        if obj_data['face_indices']:
            # Замкнутая оболочка
            face_refs = ",".join([f"#{idx}" for idx in obj_data['face_indices']])
            entities.append(f"#{current_index}=IFCCLOSEDSHELL(({face_refs}));")
            obj_data['shell_index'] = current_index
            current_index += 1
            
            # Граничное представление
            entities.append(f"#{current_index}=IFCFACETEDBREP(#{obj_data['shell_index']});")
            obj_data['brep_index'] = current_index
            current_index += 1
            
            # Геометрическое представление
            entities.append(f"#{current_index}=IFCSHAPEREPRESENTATION(#12,'Body','Brep',(#{obj_data['brep_index']}));")
            obj_data['shape_rep_index'] = current_index
            current_index += 1
        
        obj_data['next_index'] = current_index
        return "\n".join(entities) + "\n", obj_data

    # Функция создания полного IFC контента для нескольких объектов
    def generate_ifc_content_multiple(objects_data, base_obj_name,max_faces):
        """Генерация полного содержимого IFC файла для нескольких объектов"""
        timestamp = int(datetime.now().timestamp())
        iso_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        # Генерируем GUID для основных объектов
        project_guid = create_guid()
        site_guid = create_guid()
        building_guid = create_guid()
        storey_guid = create_guid()

        # Собираем все сущности
        all_entities = []
        element_data = []  # Данные об элементах для создания отношений
        current_index = 15  # Начинаем после базовых сущностей
        
        # Создаем геометрию для каждого объекта
        for obj_idx, obj_data in enumerate(objects_data):
            verts = obj_data['vertices']
            polys = obj_data['polygons']
            obj_name = f"{base_obj_name}_{obj_idx + 1}"
            
            # Создаем геометрию для объекта
            geometry_str, obj_geometry_data = create_geometry_entities_for_object(
                verts, polys, current_index, obj_idx,max_faces
            )
            
            all_entities.append(geometry_str)
            
            # Сохраняем данные для создания элемента
            if obj_geometry_data.get('shape_rep_index'):
                element_data.append({
                    'name': obj_name,
                    'guid': create_guid(),
                    'shape_rep_index': obj_geometry_data['shape_rep_index'],
                    'next_index': obj_geometry_data['next_index']
                })
                current_index = obj_geometry_data['next_index']
        
        # Создаем элементы (IfcBuildingElementProxy)
        element_entities = []
        for elem in element_data:
            # Создаем определение формы
            elem_guid = create_guid()
            shape_def_index = current_index
            element_entities.append(f"#{shape_def_index}=IFCPRODUCTDEFINITIONSHAPE($,$,(#{elem['shape_rep_index']}));")
            current_index += 1
            
            # Создаем элемент
            element_entities.append(f"#{current_index}=IFCBUILDINGELEMENTPROXY('{elem_guid}',#5,'{elem['name']}',$,$,#9,#{shape_def_index},$);")
            elem['element_index'] = current_index
            elem['guid'] = elem_guid  # Сохраняем GUID
            current_index += 1
        print(len(element_entities))
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
#1=IFCPERSON($,$,'Sverchok User',$,$,$,$,$);
#2=IFCORGANIZATION($,'Sverchok BIM Export',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION(#2,'1.0','Sverchok IFC Exporter','Sverchok');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,{timestamp},#3,#4);
#6=IFCCARTESIANPOINT((0.,0.,0.));
#7=IFCDIRECTION((0.,0.,1.));
#8=IFCDIRECTION((1.,0.,0.));
#9=IFCAXIS2PLACEMENT3D(#6,#7,#8);
#10=IFCDIRECTION((0.,1.,0.));
#11=IFCAXIS2PLACEMENT2D(#6,#10);
#12=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,$);
#13=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Plan',2,1.E-05,#11,$);
#14=IFCPROJECT('{project_guid}',#5,'{base_obj_name} Project',$,$,$,$,(#12,#13),$);

{allen}

{elen}

#1000=IFCSITE('{site_guid}',#5,'{site_name}',$,$,#9,$,$,$,.ELEMENT.,$,$,$,$);
#1001=IFCBUILDING('{building_guid}',#5,'{building_name}',$,$,#9,$,$,$,$,$);
#1002=IFCBUILDINGSTOREY('{storey_guid}',#5,'{storey_name}',$,$,#9,$,$,$,$,0.);"""
        
        # Добавляем отношения
        element_indices = ",".join([f"#{elem['element_index']}" for elem in element_data])
        rel_guid1 = create_guid()
        rel_guid2 = create_guid()
        rel_guid3 = create_guid()
        rel_guid4 = create_guid()

        relations = f"""
        #2000=IFCRELAGGREGATES('{rel_guid1}',#5,$,$,#14,(#1000));
        #2001=IFCRELAGGREGATES('{rel_guid2}',#5,$,$,#1000,(#1001));
        #2002=IFCRELAGGREGATES('{rel_guid3}',#5,$,$,#1001,(#1002));
        #2003=IFCRELCONTAINEDINSPATIALSTRUCTURE('{rel_guid4}',#5,$,$,({element_indices}),#1002);"""
        
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
