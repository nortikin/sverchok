'''
in svg FP d=[[]] n=0
out vers v
out edgs s
out pols s
'''

from svgelements import SVG, Path, Circle, Ellipse, Rect, Polygon, Polyline, Line, SimpleLine, Group, Matrix
import math

def parse_svg_to_geometry(svg_file):
    # Инициализация структур данных
    vertices = []  # Список всех вершин
    edges = []     # Список всех рёбер
    polygons = []  # Список всех полигонов
    
    # Загрузка SVG файла
    svg = SVG.parse(svg_file[0][0])
    
    # Функция для добавления вершины и возврата её индекса
    def add_vertex(x, y):
        vertex = [x, -y, 0]  # Инвертируем Y
        vertices.append(vertex)
        return len(vertices) - 1
    
    # Функция для обработки трансформаций
    def apply_transform(point, transform):
        if transform is None:
            return point
        try:
            matrix = Matrix(transform) if not isinstance(transform, Matrix) else transform
            return matrix.point_in_matrix_space(point)
        except:
            return point
    
    # Рекурсивная функция для обработки элементов
    def process_element(element, transform=Matrix()):
        if not hasattr(element, 'values'):
            return
            
        if isinstance(element, Group):
            # Обрабатываем группу с учетом её трансформации
            group_transform = Matrix(element.transform) * transform if hasattr(element, 'transform') and element.transform else transform
            for child in element:
                process_element(child, group_transform)
            return
        
        # Получаем текущую трансформацию
        current_transform = Matrix(element.transform) * transform if hasattr(element, 'transform') and element.transform else transform
        
        # Обработка Path
        if isinstance(element, Path):
            polygon = []
            for segment in element:
                if hasattr(segment, 'start') and segment.start is not None:
                    start = apply_transform((segment.start.x, segment.start.y), current_transform)
                    start_idx = add_vertex(*start)
                    polygon.append(start_idx)
                
                if hasattr(segment, 'end') and segment.end is not None:
                    end = apply_transform((segment.end.x, segment.end.y), current_transform)
                    end_idx = add_vertex(*end)
                    if 'start_idx' in locals():  # Проверяем, определена ли start_idx
                        edges.append([start_idx, end_idx])
                    polygon.append(end_idx)
            
            if hasattr(element, 'closed') and element.closed and len(polygon) > 2:
                polygons.append(polygon)
        
        # Обработка Line и SimpleLine
        elif isinstance(element, (Line, SimpleLine)):
            if all(hasattr(element, attr) for attr in ['x1', 'y1', 'x2', 'y2']):
                start = apply_transform((element.x1, element.y1), current_transform)
                end = apply_transform((element.x2, element.y2), current_transform)
                start_idx = add_vertex(*start)
                end_idx = add_vertex(*end)
                edges.append([start_idx, end_idx])
        
        # Обработка Circle
        elif isinstance(element, Circle):
            if all(hasattr(element, attr) for attr in ['cx', 'cy', 'rx']):
                cx, cy, r = element.cx, element.cy, element.rx
                center = apply_transform((cx, cy), current_transform)
                cx, cy = center
                # Аппроксимируем круг как 32-угольник
                polygon = []
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    x = cx + r * math.cos(angle)
                    y = cy + r * math.sin(angle)
                    polygon.append(add_vertex(x, y))
                polygons.append(polygon)
        
        # Обработка Ellipse
        elif isinstance(element, Ellipse):
            if all(hasattr(element, attr) for attr in ['cx', 'cy', 'rx', 'ry']):
                cx, cy, rx, ry = element.cx, element.cy, element.rx, element.ry
                center = apply_transform((cx, cy), current_transform)
                cx, cy = center
                # Аппроксимируем эллипс как 32-угольник
                polygon = []
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    x = cx + rx * math.cos(angle)
                    y = cy + ry * math.sin(angle)
                    polygon.append(add_vertex(x, y))
                polygons.append(polygon)
        
        # Обработка Rect
        elif isinstance(element, Rect):
            if all(hasattr(element, attr) for attr in ['x', 'y', 'width', 'height']):
                x, y, width, height = element.x, element.y, element.width, element.height
                rx = getattr(element, 'rx', 0) or 0
                ry = getattr(element, 'ry', 0) or 0
                
                # Применяем трансформацию к угловым точкам
                points = [
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height)
                ]
                transformed_points = [apply_transform(p, current_transform) for p in points]
                
                if rx == 0 and ry == 0:
                    # Простой прямоугольник
                    polygon = [add_vertex(*p) for p in transformed_points]
                    polygons.append(polygon)
                else:
                    # Прямоугольник со скруглёнными углами (аппроксимируем)
                    polygon = []
                    # Верхняя сторона
                    p1 = apply_transform((x + rx, y), current_transform)
                    p2 = apply_transform((x + width - rx, y), current_transform)
                    polygon.append(add_vertex(*p1))
                    polygon.append(add_vertex(*p2))
                    # Верхний правый угол
                    for i in range(8):
                        angle = math.pi/2 * (i/8 - 1)
                        px = x + width - rx + rx * math.cos(angle)
                        py = y + ry + ry * math.sin(angle)
                        p = apply_transform((px, py), current_transform)
                        polygon.append(add_vertex(*p))
                    # Правая сторона
                    p3 = apply_transform((x + width, y + height - ry), current_transform)
                    polygon.append(add_vertex(*p3))
                    # Нижний правый угол
                    for i in range(8):
                        angle = math.pi/2 * (i/8)
                        px = x + width - rx + rx * math.cos(angle)
                        py = y + height - ry + ry * math.sin(angle)
                        p = apply_transform((px, py), current_transform)
                        polygon.append(add_vertex(*p))
                    # Нижняя сторона
                    p4 = apply_transform((x + rx, y + height), current_transform)
                    polygon.append(add_vertex(*p4))
                    # Нижний левый угол
                    for i in range(8):
                        angle = math.pi/2 * (i/8 + 1)
                        px = x + rx + rx * math.cos(angle)
                        py = y + height - ry + ry * math.sin(angle)
                        p = apply_transform((px, py), current_transform)
                        polygon.append(add_vertex(*p))
                    # Левая сторона
                    p5 = apply_transform((x, y + ry), current_transform)
                    polygon.append(add_vertex(*p5))
                    # Верхний левый угол
                    for i in range(8):
                        angle = math.pi/2 * (i/8 + 2)
                        px = x + rx + rx * math.cos(angle)
                        py = y + ry + ry * math.sin(angle)
                        p = apply_transform((px, py), current_transform)
                        polygon.append(add_vertex(*p))
                    polygons.append(polygon)
        
        # Обработка Polygon и Polyline
        elif isinstance(element, (Polygon, Polyline)):
            if hasattr(element, 'points'):
                points = [(p.x, p.y) for p in element.points]
                transformed_points = [apply_transform(p, current_transform) for p in points]
                polygon = [add_vertex(*p) for p in transformed_points]
                if len(polygon) > 2:
                    polygons.append(polygon)
                    if isinstance(element, Polygon):  # Замкнутый полигон
                        edges.append([polygon[-1], polygon[0]])
    
    # Обработка всех элементов SVG
    for element in svg.elements():
        process_element(element)
    
    # Форматирование рёбер (каждый сегмент в отдельный список)
    formatted_edges = [[edge] for edge in edges] if edges else []
    
    return {
        'vertices': [vertices] if vertices else [[]],
        'edges': [formatted_edges] if formatted_edges else [[]],
        'polygons': [polygons] if polygons else [[]]
    }

geometry = parse_svg_to_geometry(svg)

print("Vertices:")
#print(geometry['vertices'])
vers = geometry['vertices']
print("\nEdges:")
#print(geometry['edges'])
edgs = geometry['edges']
print("\nPolygons:")
#print(geometry['polygons'])
pols = geometry['polygons']