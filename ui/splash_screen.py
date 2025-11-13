import bpy
from bpy.types import Operator
import gpu
import os
from gpu_extras.batch import batch_for_shader

# Global variables
textures = []
current_image_index = 0
button_width = 50
button_height = 20
button_margin = 3
close_button_width = 103

# Shaders
if bpy.app.background or if bpy.app.version >= (3, 6, 18):
    image_shader = None
    solid_shader = None
else:
    if bpy.app.version >= (5, 0, 0):
        image_shader = gpu.shader.from_builtin('IMAGE_SCENE_LINEAR_TO_REC709_SRGB')
    else:
        image_shader = gpu.shader.from_builtin('IMAGE')
    solid_shader = gpu.shader.from_builtin('UNIFORM_COLOR')


# Добавьте настройку blending для прозрачности
def enable_alpha_blending():
    """Включает blending для прозрачности"""
    gpu.state.blend_set('ALPHA')

def disable_alpha_blending():
    """Выключает blending"""
    gpu.state.blend_set('NONE')

def load_images_from_script_folder():
    """Load all PNG images from the script folder"""
    global textures

    # Clear existing textures
    textures.clear()

    # Get script folder
    script_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'splash_images')

    # Find all PNG files
    png_files = []
    for file in os.listdir(script_folder):
        if file.lower().endswith('.png'):
            png_files.append(os.path.join(script_folder, file))
    png_files.sort()

    print(f"Found {len(png_files)} PNG files in {script_folder}")

    # Load images and create textures
    for img_file in png_files:
        try:
            img = bpy.data.images.load(img_file)
            # ДОБАВЛЕНО: Исправление цветов для Blender 5.0
            if bpy.app.version >= (5, 0, 0):
                # Для Blender 5.0+ указываем правильное цветовое пространство
                if hasattr(img, 'colorspace_settings'):
                    img.colorspace_settings.name = 'sRGB'
                elif hasattr(img, 'color_space'):
                    # Старый атрибут для обратной совместимости
                    img.color_space = 'sRGB'
            texture = gpu.texture.from_image(img)
            textures.append(texture)
            # Remove image from Blender data to avoid clutter
            bpy.data.images.remove(img)
            print(f"Loaded: {os.path.basename(img_file)}")
        except Exception as e:
            print(f"Error loading {img_file}: {e}")

    return len(textures) > 0

def draw_callback():
    global current_image_index

    # Получаем контекст
    context = bpy.context
    area = context.area
    if not area:
        return

    # Ищем регион WINDOW
    region = None
    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break

    if not region:
        return

    width = region.width
    height = region.height

    if not textures:
        # Draw "No images" message
        solid_shader.bind()
        solid_shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
        message_vertices = (
            (width/2 - 100, height/2 - 10),
            (width/2 + 100, height/2 - 10),
            (width/2 + 100, height/2 + 10),
            (width/2 - 100, height/2 + 10)
        )
        message_batch = batch_for_shader(solid_shader, 'TRI_FAN', {"pos": message_vertices})
        message_batch.draw(solid_shader)
        return

    # Calculate image dimensions (maintain aspect ratio)
    tex = textures[current_image_index]
    img_width = tex.width
    img_height = tex.height

    # Scale image to fit while maintaining aspect ratio
    scale_factor = min(width * 0.7 / img_width, height * 0.7 / img_height)
    display_width = img_width * scale_factor
    display_height = img_height * scale_factor

    # Image position (centered)
    img_x = (width - display_width) / 2
    img_y = (height - display_height) / 2 + 30  # Slightly raised to make space for buttons

    # Draw image
    vertices = (
        (img_x, img_y),
        (img_x + display_width, img_y),
        (img_x + display_width, img_y + display_height),
        (img_x, img_y + display_height)
    )

    indices = ((0, 1, 2), (0, 2, 3))

    # Включаем blending для прозрачности
    enable_alpha_blending()

    image_shader.bind()
    image_shader.uniform_sampler("image", tex)

    batch = batch_for_shader(image_shader, 'TRIS', {
        "pos": vertices,
        "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1))
    }, indices=indices)
    batch.draw(image_shader)

    # Выключаем blending для остальных элементов (кнопок)
    disable_alpha_blending()

    # Draw buttons
    button_y = 20

    # Button positions
    left_button_x = width / 2 - button_width - button_margin
    right_button_x = width / 2 + button_margin
    close_button_x = width / 2 - close_button_width / 2

    # Left button
    left_button_vertices = (
        (left_button_x, button_y),
        (left_button_x + button_width, button_y),
        (left_button_x + button_width, button_y + button_height),
        (left_button_x, button_y + button_height)
    )

    # Right button
    right_button_vertices = (
        (right_button_x, button_y),
        (right_button_x + button_width, button_y),
        (right_button_x + button_width, button_y + button_height),
        (right_button_x, button_y + button_height)
    )

    # Close button (above navigation buttons)
    close_button_y = button_y + button_height + button_margin
    close_button_vertices = (
        (close_button_x, close_button_y),
        (close_button_x + close_button_width, close_button_y),
        (close_button_x + close_button_width, close_button_y + button_height),
        (close_button_x, close_button_y + button_height)
    )

    # Draw button backgrounds
    solid_shader.bind()

    # Navigation buttons - gray
    solid_shader.uniform_float("color", (0.84, 0.91, 0.83, 0.65))
    left_button_batch = batch_for_shader(solid_shader, 'TRI_FAN', {"pos": left_button_vertices})
    right_button_batch = batch_for_shader(solid_shader, 'TRI_FAN', {"pos": right_button_vertices})
    left_button_batch.draw(solid_shader)
    right_button_batch.draw(solid_shader)

    # Close button - red
    solid_shader.uniform_float("color", (0.84, 0.91, 0.83, 0.65))
    close_button_batch = batch_for_shader(solid_shader, 'TRI_FAN', {"pos": close_button_vertices})
    close_button_batch.draw(solid_shader)

    # Draw button borders
    solid_shader.uniform_float("color", (0.84, 0.91, 0.83, 0.65))
    left_border_batch = batch_for_shader(solid_shader, 'LINE_LOOP', {"pos": left_button_vertices})
    right_border_batch = batch_for_shader(solid_shader, 'LINE_LOOP', {"pos": right_button_vertices})
    close_border_batch = batch_for_shader(solid_shader, 'LINE_LOOP', {"pos": close_button_vertices})

    left_border_batch.draw(solid_shader)
    right_border_batch.draw(solid_shader)
    close_border_batch.draw(solid_shader)

    # Draw button symbols
    solid_shader.uniform_float("color", (0.34, 0.5, 0.76, 1.0))

    # Left arrow
    left_arrow_vertices = (
        (left_button_x + button_width, button_y),
        (left_button_x + button_width, button_y + button_height),
        (left_button_x, button_y + button_height * 0.5)
    )

    # Right arrow
    right_arrow_vertices = (
        (right_button_x, button_y),
        (right_button_x, button_y + button_height),
        (right_button_x + button_width, button_y + button_height * 0.5)
    )

    # Close "X" symbol
    close_x_vertices1 = (
        (close_button_x, close_button_y),
        (close_button_x + close_button_width, close_button_y + button_height)
    )
    close_x_vertices2 = (
        (close_button_x + close_button_width, close_button_y),
        (close_button_x, close_button_y + button_height)
    )

    left_arrow_batch = batch_for_shader(solid_shader, 'TRIS', {"pos": left_arrow_vertices})
    right_arrow_batch = batch_for_shader(solid_shader, 'TRIS', {"pos": right_arrow_vertices})
    close_x_batch1 = batch_for_shader(solid_shader, 'LINES', {"pos": close_x_vertices1})
    close_x_batch2 = batch_for_shader(solid_shader, 'LINES', {"pos": close_x_vertices2})

    left_arrow_batch.draw(solid_shader)
    right_arrow_batch.draw(solid_shader)
    close_x_batch1.draw(solid_shader)
    close_x_batch2.draw(solid_shader)

    # Draw image counter
    counter_y = close_button_y + button_height + 5
    counter_x_start = width / 2 - close_button_width / 2
    counter_y_start = counter_y
    counter_text_bg_vertices = (
        (counter_x_start, counter_y_start),
        (counter_x_start + close_button_width, counter_y_start),
        (counter_x_start + close_button_width, counter_y_start + button_height),
        (counter_x_start, counter_y_start + button_height)
    )

    #solid_shader.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
    counter_border_batch = batch_for_shader(solid_shader, 'LINE_LOOP', {"pos": counter_text_bg_vertices})
    counter_border_batch.draw(solid_shader)

    # Draw counter numbers (simplified - using lines to represent digits)
    # This is a very basic visualization. For real text you'd need blf module.

    current_num = current_image_index
    total_num = len(textures)
    lineage = (
        (counter_x_start + current_num*(close_button_width/total_num), counter_y_start),
        (counter_x_start + (current_num+1)*(close_button_width/total_num), counter_y_start),
        (counter_x_start + (current_num+1)*(close_button_width/total_num), counter_y_start + button_height),
        (counter_x_start + current_num*(close_button_width/total_num), counter_y_start + button_height)
    )
    line_ = batch_for_shader(solid_shader, 'TRI_FAN', {"pos": lineage})
    line_.draw(solid_shader)



def check_button_click(mouse_x, mouse_y, context):
    global current_image_index

    if not textures:
        return False

    # Получаем регион через area, а не напрямую из context
    area = context.area
    if not area:
        # Если area недоступен, закрываем сплеш-скрин
        close_splash_screen(context)
        return {'CANCELLED'}

    region = None
    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break

    if not region:
        # Если регион недоступен, закрываем сплеш-скрин
        close_splash_screen(context)
        return {'CANCELLED'}

    width = region.width

    button_y = 20
    close_button_y = button_y + button_height + 10

    # Button positions
    left_button_x = width / 2 - button_width - button_margin
    right_button_x = width / 2 + button_margin
    close_button_x = width / 2 - close_button_width / 2

    # Check left button click
    if (left_button_x <= mouse_x <= left_button_x + button_width and
        button_y <= mouse_y <= button_y + button_height):
        current_image_index = (current_image_index - 1) % len(textures)
        return True

    # Check right button click
    if (right_button_x <= mouse_x <= right_button_x + button_width and
        button_y <= mouse_y <= button_y + button_height):
        current_image_index = (current_image_index + 1) % len(textures)
        return True

    # Check close button click
    if (close_button_x <= mouse_x <= close_button_x + close_button_width and
        close_button_y <= mouse_y <= close_button_y + button_height):
        close_splash_screen(context)
        return {'CANCELLED'}

    return False

def close_splash_screen(context):
    """Универсальная функция для закрытия сплеш-скрина"""
    if operator_instance and operator_instance._handle is not None:
        bpy.types.SpaceNodeEditor.draw_handler_remove(operator_instance._handle, 'WINDOW')
        operator_instance._handle = None
        if context.area:
            context.area.tag_redraw()


class SV_OT_splash_screen_simple(Operator):
    """Splash Screen для Sverchok"""
    bl_idname = "sv.splash_screen_simple"
    bl_label = "Sverchok - Добро пожаловать!"
    bl_description = "Displays help images on Sverchok addon"
    bl_options = {'REGISTER'}

    _handle = None

    def modal(self, context, event):
        # Проверяем, доступен ли регион
        area = context.area
        if not area:
            self.remove_handlers(context)
            return {'CANCELLED'}

        region_available = False
        for r in area.regions:
            if r.type == 'WINDOW':
                region_available = True
                break

        if not region_available:
            self.remove_handlers(context)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            result = check_button_click(event.mouse_region_x, event.mouse_region_y, context)
            if result is True:
                # Проверяем area перед вызовом tag_redraw
                if context.area:
                    context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            elif result == {'CANCELLED'}:
                return {'CANCELLED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.remove_handlers(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global operator_instance
        operator_instance = self

        # Load images from script folder
        if not load_images_from_script_folder():
            self.report({'WARNING'}, "No PNG images found in script folder")
            return {'CANCELLED'}

        self.register_handlers(context)
        context.window_manager.modal_handler_add(self)

        self.report({'INFO'}, f"Loaded {len(textures)} images. Click arrows to navigate, X button or RMB/ESC to close.")
        return {'RUNNING_MODAL'}

    def register_handlers(self, context):
        if self._handle is None:
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(
                draw_callback, (), 'WINDOW', 'POST_PIXEL'
            )
            context.area.tag_redraw()

    def remove_handlers(self, context):
        if self._handle is not None:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None
            # Проверяем, что area доступен перед вызовом tag_redraw
            if context.area:
                context.area.tag_redraw()

# Global reference to operator instance for button callbacks
operator_instance = None

def register():
    if bpy.app.version > (3,6,18):
        bpy.utils.register_class(SV_OT_splash_screen_simple)

def unregister():
    if bpy.app.version > (3,6,18):
        bpy.utils.unregister_class(SV_OT_splash_screen_simple)

# Menu function to easily access the operator
def menu_func(self, context):
    self.layout.operator(SV_OT_splash_screen_simple.bl_idname)

# Register and add to the node editor menu
if __name__ == "__main__":
    register()
    bpy.types.NODE_MT_editor_menus.append(menu_func)
