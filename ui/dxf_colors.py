import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from bpy.types import Panel, Operator, SpaceNodeEditor
import numpy as np

# --- Данные цветов DXF ---
# Здесь должны быть все 256 цветов. Для краткости примера - первые 64.
# Вы можете вставить сюда полный список из 256 цветов, полученный ранее.
DXF_COLORS_255 = [
    # Основные цвета (1-9)
    (1, (255, 0, 0)),        # Red
    (2, (255, 255, 0)),      # Yellow
    (3, (0, 255, 0)),        # Green
    (4, (0, 255, 255)),      # Cyan
    (5, (0, 0, 255)),        # Blue
    (6, (255, 0, 255)),      # Magenta
    (7, (255, 255, 255)),    # White/Black (зависит от фона)
    (8, (128, 128, 128)),    # Dark Gray
    (9, (192, 192, 192)),    # Light Gray
    
    # Красные и оранжевые тона (10-39)
    (10, (255, 0, 0)),
    (11, (255, 127, 127)),
    (12, (204, 0, 0)),
    (13, (204, 102, 102)),
    (14, (153, 0, 0)),
    (15, (153, 76, 76)),
    (16, (127, 0, 0)),
    (17, (127, 63, 63)),
    (18, (76, 0, 0)),
    (19, (76, 38, 38)),
    (20, (255, 63, 0)),
    (21, (255, 159, 127)),
    (22, (204, 51, 0)),
    (23, (204, 127, 102)),
    (24, (153, 38, 0)),
    (25, (153, 95, 76)),
    (26, (127, 31, 0)),
    (27, (127, 79, 63)),
    (28, (76, 19, 0)),
    (29, (76, 47, 38)),
    (30, (255, 127, 0)),
    (31, (255, 191, 127)),
    (32, (204, 102, 0)),
    (33, (204, 153, 102)),
    (34, (153, 76, 0)),
    (35, (153, 114, 76)),
    (36, (127, 63, 0)),
    (37, (127, 95, 63)),
    (38, (76, 38, 0)),
    (39, (76, 57, 38)),
    
    # Желтые и золотистые тона (40-69)
    (40, (255, 191, 0)),
    (41, (255, 223, 127)),
    (42, (204, 153, 0)),
    (43, (204, 178, 102)),
    (44, (153, 114, 0)),
    (45, (153, 133, 76)),
    (46, (127, 95, 0)),
    (47, (127, 111, 63)),
    (48, (76, 57, 0)),
    (49, (76, 66, 38)),
    (50, (255, 255, 0)),
    (51, (255, 255, 127)),
    (52, (204, 204, 0)),
    (53, (204, 204, 102)),
    (54, (153, 153, 0)),
    (55, (153, 153, 76)),
    (56, (127, 127, 0)),
    (57, (127, 127, 63)),
    (58, (76, 76, 0)),
    (59, (76, 76, 38)),
    (60, (191, 255, 0)),
    (61, (223, 255, 127)),
    (62, (153, 204, 0)),
    (63, (178, 204, 102)),
    (64, (114, 153, 0)),
    (65, (133, 153, 76)),
    (66, (95, 127, 0)),
    (67, (111, 127, 63)),
    (68, (57, 76, 0)),
    (69, (66, 76, 38)),
    
    # Зеленые тона (70-99)
    (70, (127, 255, 0)),
    (71, (191, 255, 127)),
    (72, (102, 204, 0)),
    (73, (153, 204, 102)),
    (74, (76, 153, 0)),
    (75, (114, 153, 76)),
    (76, (63, 127, 0)),
    (77, (95, 127, 63)),
    (78, (38, 76, 0)),
    (79, (57, 76, 38)),
    (80, (63, 255, 0)),
    (81, (159, 255, 127)),
    (82, (51, 204, 0)),
    (83, (127, 204, 102)),
    (84, (38, 153, 0)),
    (85, (95, 153, 76)),
    (86, (31, 127, 0)),
    (87, (79, 127, 63)),
    (88, (19, 76, 0)),
    (89, (47, 76, 38)),
    (90, (0, 255, 0)),
    (91, (127, 255, 127)),
    (92, (0, 204, 0)),
    (93, (102, 204, 102)),
    (94, (0, 153, 0)),
    (95, (76, 153, 76)),
    (96, (0, 127, 0)),
    (97, (63, 127, 63)),
    (98, (0, 76, 0)),
    (99, (38, 76, 38)),
    
    # Зелено-голубые тона (100-129)
    (100, (0, 255, 63)),
    (101, (127, 255, 159)),
    (102, (0, 204, 51)),
    (103, (102, 204, 127)),
    (104, (0, 153, 38)),
    (105, (76, 153, 95)),
    (106, (0, 127, 31)),
    (107, (63, 127, 79)),
    (108, (0, 76, 19)),
    (109, (38, 76, 47)),
    (110, (0, 255, 127)),
    (111, (127, 255, 191)),
    (112, (0, 204, 102)),
    (113, (102, 204, 153)),
    (114, (0, 153, 76)),
    (115, (76, 153, 114)),
    (116, (0, 127, 63)),
    (117, (63, 127, 95)),
    (118, (0, 76, 38)),
    (119, (38, 76, 57)),
    (120, (0, 255, 191)),
    (121, (127, 255, 223)),
    (122, (0, 204, 153)),
    (123, (102, 204, 178)),
    (124, (0, 153, 114)),
    (125, (76, 153, 133)),
    (126, (0, 127, 95)),
    (127, (63, 127, 111)),
    (128, (0, 76, 57)),
    (129, (38, 76, 66)),
    
    # Голубые и синие тона (130-169)
    (130, (0, 255, 255)),
    (131, (127, 255, 255)),
    (132, (0, 204, 204)),
    (133, (102, 204, 204)),
    (134, (0, 153, 153)),
    (135, (76, 153, 153)),
    (136, (0, 127, 127)),
    (137, (63, 127, 127)),
    (138, (0, 76, 76)),
    (139, (38, 76, 76)),
    (140, (0, 191, 255)),
    (141, (127, 223, 255)),
    (142, (0, 153, 204)),
    (143, (102, 178, 204)),
    (144, (0, 114, 153)),
    (145, (76, 133, 153)),
    (146, (0, 95, 127)),
    (147, (63, 111, 127)),
    (148, (0, 57, 76)),
    (149, (38, 66, 76)),
    (150, (0, 127, 255)),
    (151, (127, 191, 255)),
    (152, (0, 102, 204)),
    (153, (102, 153, 204)),
    (154, (0, 76, 153)),
    (155, (76, 114, 153)),
    (156, (0, 63, 127)),
    (157, (63, 95, 127)),
    (158, (0, 38, 76)),
    (159, (38, 57, 76)),
    (160, (0, 63, 255)),
    (161, (127, 159, 255)),
    (162, (0, 51, 204)),
    (163, (102, 127, 204)),
    (164, (0, 38, 153)),
    (165, (76, 95, 153)),
    (166, (0, 31, 127)),
    (167, (63, 79, 127)),
    (168, (0, 19, 76)),
    (169, (38, 47, 76)),
    
    # Фиолетовые и пурпурные тона (170-209)
    (170, (0, 0, 255)),
    (171, (127, 127, 255)),
    (172, (0, 0, 204)),
    (173, (102, 102, 204)),
    (174, (0, 0, 153)),
    (175, (76, 76, 153)),
    (176, (0, 0, 127)),
    (177, (63, 63, 127)),
    (178, (0, 0, 76)),
    (179, (38, 38, 76)),
    (180, (63, 0, 255)),
    (181, (159, 127, 255)),
    (182, (51, 0, 204)),
    (183, (127, 102, 204)),
    (184, (38, 0, 153)),
    (185, (95, 76, 153)),
    (186, (31, 0, 127)),
    (187, (79, 63, 127)),
    (188, (19, 0, 76)),
    (189, (47, 38, 76)),
    (190, (127, 0, 255)),
    (191, (191, 127, 255)),
    (192, (102, 0, 204)),
    (193, (153, 102, 204)),
    (194, (76, 0, 153)),
    (195, (114, 76, 153)),
    (196, (63, 0, 127)),
    (197, (95, 63, 127)),
    (198, (38, 0, 76)),
    (199, (57, 38, 76)),
    (200, (191, 0, 255)),
    (201, (223, 127, 255)),
    (202, (153, 0, 204)),
    (203, (178, 102, 204)),
    (204, (114, 0, 153)),
    (205, (133, 76, 153)),
    (206, (95, 0, 127)),
    (207, (111, 63, 127)),
    (208, (57, 0, 76)),
    (209, (66, 38, 76)),
    
    # Розовые и фиолетовые тона (210-249)
    (210, (255, 0, 255)),
    (211, (255, 127, 255)),
    (212, (204, 0, 204)),
    (213, (204, 102, 204)),
    (214, (153, 0, 153)),
    (215, (153, 76, 153)),
    (216, (127, 0, 127)),
    (217, (127, 63, 127)),
    (218, (76, 0, 76)),
    (219, (76, 38, 76)),
    (220, (255, 0, 191)),
    (221, (255, 127, 223)),
    (222, (204, 0, 153)),
    (223, (204, 102, 178)),
    (224, (153, 0, 114)),
    (225, (153, 76, 133)),
    (226, (127, 0, 95)),
    (227, (127, 63, 111)),
    (228, (76, 0, 57)),
    (229, (76, 38, 66)),
    (230, (255, 0, 127)),
    (231, (255, 127, 191)),
    (232, (204, 0, 102)),
    (233, (204, 102, 153)),
    (234, (153, 0, 76)),
    (235, (153, 76, 114)),
    (236, (127, 0, 63)),
    (237, (127, 63, 95)),
    (238, (76, 0, 38)),
    (239, (76, 38, 57)),
    (240, (255, 0, 63)),
    (241, (255, 127, 159)),
    (242, (204, 0, 51)),
    (243, (204, 102, 127)),
    (244, (153, 0, 38)),
    (245, (153, 76, 95)),
    (246, (127, 0, 31)),
    (247, (127, 63, 79)),
    (248, (76, 0, 19)),
    (249, (76, 38, 47)),
    
    # Серые тона (250-255)
    (250, (38, 38, 38)),
    (251, (51, 51, 51)),
    (252, (64, 64, 64)),
    (253, (77, 77, 77)),
    (254, (90, 90, 90)),
    (255, (103, 103, 103))
]
# Нормализуем RGB для gpu (диапазон 0.0 - 1.0) и добавляем альфа-канал (1.0)
DXF_COLORS = [(idx, (r/255.0, g/255.0, b/255.0, 1.0)) for idx, (r, g, b) in DXF_COLORS_255]

# --- Глобальные переменные для хранения состояния отрисовки ---
class DrawState:
    """Класс для хранения состояния, как в примерах Sverchok."""
    handle = None
    colors = DXF_COLORS  # используем наши цвета
    columns = 16  # количество столбцов в таблице
    square_size = 30  # размер квадратика в пикселях
    padding = 5  # отступ между квадратиками
    start_x = 50  # начальная позиция X отрисовки (может меняться)
    start_y = 50  # начальная позиция Y отрисовки
    hovered_index = -1  # индекс цвета, над которым мышь

draw_state = DrawState()

# --- Шейдеры ---
def get_shaders():
    """Возвращает шейдер для закраски цветом и для текста."""
    if bpy.app.background:
        return None, None
    solid_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return solid_shader, None # Текст будем рисовать через blf

# --- Функции для включения/отключения blending (прозрачности) ---
def enable_alpha_blending():
    gpu.state.blend_set('ALPHA')

def disable_alpha_blending():
    gpu.state.blend_set('NONE')

# --- Основная функция отрисовки (аналог draw_callback из splash_screen.py) ---
def draw_color_table():
    """Рисует таблицу цветов в активном регионе Node Editor."""
    context = bpy.context
    area = context.area
    if not area or area.type != 'NODE_EDITOR':
        return

    region = None
    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break
    if not region:
        return

    # Получаем размеры региона
    width = region.width
    height = region.height

    # Параметры таблицы
    cols = draw_state.columns
    cell_size = draw_state.square_size + draw_state.padding
    rows = (len(draw_state.colors) + cols - 1) // cols

    # Вычисляем центр для размещения таблицы
    table_width = cols * cell_size - draw_state.padding
    table_height = rows * cell_size - draw_state.padding
    start_x = (width - table_width) / 2
    start_y = (height + table_height) / 2 # Начинаем сверху

    solid_shader, _ = get_shaders()
    if not solid_shader:
        return

    enable_alpha_blending()
    gpu.state.line_width_set(1)

    # Создаем вершины для всех квадратов и фоновых прямоугольников
    for i, (color_index, color_rgba) in enumerate(draw_state.colors):
        row = i // cols
        col = i % cols
        x = start_x + col * cell_size
        y = start_y - row * cell_size - draw_state.square_size # Y идет сверху вниз

        # Вершины квадрата
        vertices = (
            (x, y),
            (x + draw_state.square_size, y),
            (x + draw_state.square_size, y + draw_state.square_size),
            (x, y + draw_state.square_size)
        )
        indices = ((0, 1, 2), (0, 2, 3))

        # Рисуем закрашенный квадрат
        batch = batch_for_shader(solid_shader, 'TRIS', {"pos": vertices}, indices=indices)
        solid_shader.bind()
        solid_shader.uniform_float("color", color_rgba)
        batch.draw(solid_shader)

        # Рисуем обводку для наведения мыши
        if i == draw_state.hovered_index:
            # Рисуем белую рамку поверх
            gpu.state.line_width_set(3)
            solid_shader.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
            batch_border = batch_for_shader(solid_shader, 'LINE_LOOP', {"pos": vertices})
            batch_border.draw(solid_shader)
        else:
            # Тонкая темная обводка для всех квадратов
            gpu.state.line_width_set(1)
            solid_shader.uniform_float("color", (0.2, 0.2, 0.2, 1.0))
            batch_border = batch_for_shader(solid_shader, 'LINE_LOOP', {"pos": vertices})
            batch_border.draw(solid_shader)

    disable_alpha_blending()

    # --- Рисуем текст с номером цвета (blf) ---
    font_id = 0
    blf.size(font_id, 11)
    blf.color(font_id, 0.0, 0.0, 0.0, 1.0) # Черный текст

    for i, (color_index, _) in enumerate(draw_state.colors):
        row = i // cols
        col = i % cols
        x = start_x + col * cell_size + 2 # Небольшой отступ слева
        y = start_y - row * cell_size - draw_state.square_size + 5 # Отступ снизу

        # Рисуем текст номера
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, str(color_index))

    # --- Рисуем заголовок ---
    blf.size(font_id, 14)
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0) # Белый
    blf.position(font_id, start_x, start_y + 20, 0)
    blf.draw(font_id, f"DXF Colors ({len(draw_state.colors)}): Click to copy number")

# --- Обработчик событий мыши (модальный оператор, аналог SV_OT_splash_screen_simple) ---
class NODE_OT_dxf_color_table_modal(Operator):
    """Modal operator to handle mouse events for the DXF color table."""
    bl_idname = "node.dxf_color_table_modal"
    bl_label = "DXF Color Table Modal"

    _handle_draw = None
    
    node_name: bpy.props.StringProperty(
        name="Node Name",
        description="Name of the target node",
        default=""
    )

    def modal(self, context, event):
        area = context.area
        if not area or area.type != 'NODE_EDITOR':
            self.cancel(context)
            return {'CANCELLED'}

        # Обновляем состояние при движении мыши (для hover эффекта)
        if event.type == 'MOUSEMOVE':
            self.update_hovered_index(context, event)
            if area:
                area.tag_redraw()
            return {'PASS_THROUGH'}

        # Обработка клика левой кнопкой мыши
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            clicked_index = self.get_color_index_at_mouse(context, event)
            if clicked_index != -1:
                # Копируем номер цвета в буфер обмена
                color_num = str(draw_state.colors[clicked_index][0])
                context.window_manager.clipboard = color_num
                #print('Дырка от контекста',dir(context))
                node_tree = context.space_data.edit_tree
                active_node = node_tree.nodes[self.node_name]
                #active_node = node_tree.nodes.active
                active_node.color_int = int(color_num)
                self.report({'INFO'}, f"Copied DXF Color {color_num}")
                if area:
                    area.tag_redraw()
                return {'RUNNING_MODAL'}
            else:
                # Если кликнули мимо таблицы, можно оставить оператор активным
                return {'PASS_THROUGH'}

        # Выход по ESC (опционально)
        elif event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':
            # Добавляем обработчик рисования
            self._handle_draw = SpaceNodeEditor.draw_handler_add(
                draw_color_table, (), 'WINDOW', 'POST_PIXEL'
            )
            context.window_manager.modal_handler_add(self)
            if context.area:
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Node Editor is not active")
            return {'CANCELLED'}

    def cancel(self, context):
        if self._handle_draw is not None:
            SpaceNodeEditor.draw_handler_remove(self._handle_draw, 'WINDOW')
            self._handle_draw = None
        if context.area:
            context.area.tag_redraw()

    # --- Вспомогательные методы для определения позиции мыши ---
    def get_color_index_at_mouse(self, context, event):
        """Возвращает индекс цвета, на который кликнули, или -1."""
        region = context.region
        if not region:
            return -1

        width = region.width
        height = region.height

        cols = draw_state.columns
        cell_size = draw_state.square_size + draw_state.padding
        rows = (len(draw_state.colors) + cols - 1) // cols

        table_width = cols * cell_size - draw_state.padding
        table_height = rows * cell_size - draw_state.padding
        start_x = (width - table_width) / 2
        start_y = (height + table_height) / 2

        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y

        # Проверяем, попадает ли мышь в область таблицы
        if (mouse_x < start_x or mouse_x > start_x + table_width or
            mouse_y > start_y or mouse_y < start_y - table_height):
            return -1

        # Вычисляем индекс
        col = int((mouse_x - start_x) // cell_size)
        row = int((start_y - mouse_y) // cell_size) # Т.к. Y идет сверху вниз

        # Проверяем границы
        if col < 0 or col >= cols or row < 0 or row >= rows:
            return -1

        index = row * cols + col
        if index < 0 or index >= len(draw_state.colors):
            return -1

        return index

    def update_hovered_index(self, context, event):
        """Обновляет индекс для hover эффекта."""
        new_hover = self.get_color_index_at_mouse(context, event)
        if draw_state.hovered_index != new_hover:
            draw_state.hovered_index = new_hover
            if context.area:
                context.area.tag_redraw()


# layout.operator("node.dxf_color_table_modal", text="Show Color Table", icon='COLOR')

# --- Регистрация классов ---
classes = (
    NODE_OT_dxf_color_table_modal,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # Важно: удаляем обработчик, если он еще активен
    if draw_state.handle:
        SpaceNodeEditor.draw_handler_remove(draw_state.handle, 'WINDOW')
        draw_state.handle = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()