import bpy
import os
from bpy.props import IntProperty, StringProperty, BoolProperty, PointerProperty
from bpy.types import Operator, Panel

class SV_OT_splash_screen_simple(Operator):
    """Splash Screen для Sverchok"""
    bl_idname = "sv.splash_screen_simple"
    bl_label = "Sverchok - Добро пожаловать!"
    bl_options = {'REGISTER'}

    current_index: IntProperty(default=0)
    _image_files = []
    _loaded_images = []
    _textures = []
    _initialized = False

    def get_image_files(self):
        """Получить список изображений"""
        ui_dir = os.path.dirname(__file__)
        splash_dir = os.path.join(ui_dir, "splash_images")

        if not os.path.exists(splash_dir):
            return []

        image_files = []
        supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tga'}

        try:
            for file in sorted(os.listdir(splash_dir)):
                file_lower = file.lower()
                if any(file_lower.endswith(fmt) for fmt in supported_formats):
                    image_files.append(file)
        except Exception as e:
            print(f"Sverchok Splash Error: {e}")

        return image_files

    def get_image_size(self, image_path):
        """Получить размер изображения"""
        try:
            img = bpy.data.images.load(image_path, check_existing=False)
            width, height = img.size
            bpy.data.images.remove(img)
            return width, height
        except:
            return 800, 600  # Размер по умолчанию

    def load_current_image(self):
        """Загрузить текущее изображение и создать текстуру"""
        if not self._image_files or self.current_index >= len(self._image_files):
            return None

        # Очищаем предыдущие данные
        self.cleanup_images()

        # Загружаем текущее изображение
        current_file = self._image_files[self.current_index]
        ui_dir = os.path.dirname(__file__)
        image_path = os.path.join(ui_dir, "splash_images", current_file)

        try:
            # Загружаем изображение
            img = bpy.data.images.load(image_path, check_existing=True)
            img.name = f"sv_splash_img_{self.current_index}"
            self._loaded_images.append(img)

            # Создаем текстуру
            texture_name = f"sv_splash_tex_{self.current_index}"
            texture = bpy.data.textures.new(name=texture_name, type='IMAGE')
            texture.image = img
            texture.extension = 'CLIP'
            self._textures.append(texture)

            return texture
        except Exception as e:
            print(f"Sverchok Splash: Ошибка загрузки {current_file}: {e}")
            return None

    def invoke(self, context, event):
        if not self._initialized:
            self._image_files = self.get_image_files()
            self._initialized = True

        if not self._image_files:
            self.report({'WARNING'}, "Нет изображений в папке splash_images")
            return {'CANCELLED'}

        self.current_index = 0

        # Получаем размер первого изображения для настройки размера окна
        current_file = self._image_files[self.current_index]
        ui_dir = os.path.dirname(__file__)
        image_path = os.path.join(ui_dir, "splash_images", current_file)
        img_width, img_height = self.get_image_size(image_path)

        # Загружаем изображение
        self.load_current_image()

        # Настраиваем размер окна под изображение (добавляем место для UI)
        width = max(img_width + 100, 1200)  # Максимальная ширина 1200
        height = max(img_height + 200, 900)  # Максимальная высота 900

        return context.window_manager.invoke_popup(self, width=int(width))

    def draw(self, context):
        layout = self.layout

        # Заголовок
        row = layout.row()
        row.label(text="🎉 Добро пожаловать в Sverchok!", icon='NODETREE')

        if not self._image_files:
            box = layout.box()
            box.label(text="📁 Изображения не найдены", icon='ERROR')
            box.label(text="Создайте папку 'splash_images' здесь:")
            ui_dir = os.path.dirname(__file__)
            splash_dir = os.path.join(ui_dir, "splash_images")
            box.label(text=splash_dir)
            box.label(text="И добавьте PNG/JPG изображения")
            return

        # Информация о текущем слайде
        current_file = self._image_files[self.current_index]
        box = layout.box()
        #col = box.column(align=True)
        #col.label(text=f"📊 Слайд {self.current_index + 1} из {len(self._image_files)}")
        #col.label(text=f"📄 {current_file}")

        # Отображение изображения через template_preview
        if self._textures:
            current_texture = self._textures[0]
            try:
                # Создаем box для preview с адаптивным размером
                preview_box = layout.box()

                # Используем template_preview для отображения текстуры
                preview_box.template_preview(
                    current_texture,
                    show_buttons=False,
                    preview_id="splash_preview"
                )

            except Exception as e:
                # Запасной вариант если template_preview не работает
                error_box = layout.box()
                error_box.scale_y = 6.0
                error_box.alignment = 'CENTER'
                error_box.label(text="❌ Ошибка отображения", icon='ERROR')
                print(f"Preview error: {e}")
        else:
            box = layout.box()
            box.scale_y = 6.0
            box.alignment = 'CENTER'
            box.label(text="❌ Не удалось загрузить изображение", icon='ERROR')

        # Навигация
        self.draw_navigation(layout)

        # Кнопки поддержки
        self.draw_support_buttons(layout)

    def draw_navigation(self, layout):
        """Нарисовать панель навигации"""
        row = layout.row()
        row.scale_y = 1.5

        # Кнопка Назад
        if self.current_index > 0:
            op = row.operator("sv.splash_simple_previous", text="◀ Назад", icon='BACK')
        else:
            row.label(text="")

        # Кнопка Закрыть
        #row.operator("sv.splash_simple_close", text="✕ Закрыть", icon='X')

        # Кнопка Далее
        if self.current_index < len(self._image_files) - 1:
            op = row.operator("sv.splash_simple_next", text="Далее ▶", icon='FORWARD')
        else:
            row.label(text="")

    def draw_support_buttons(self, layout):
        """Нарисовать кнопки поддержки"""
        return
        layout.separator()
        layout.label(text="🔗 Ресурсы поддержки:", icon='URL')

        flow = layout.grid_flow(row_major=True, columns=2, even_columns=True)

        urls = [
            ("🐙 GitHub", "https://github.com/nortikin/sverchok"),
            ("📚 Документация", "https://sverchok.readthedocs.io/"),
            ("💬 Форум", "https://blenderartists.org/c/addons/sverchok/"),
            ("❤️ Patreon", "https://www.patreon.com/sverchok")
        ]

        for label, url in urls:
            op = flow.operator("wm.url_open", text=label)
            op.url = url

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        """Очистка при закрытии"""
        self.cleanup_images()

    def cleanup_images(self):
        """Очистить загруженные изображения и текстуры"""
        # Очищаем текстуры
        for texture in self._textures:
            try:
                if texture and texture.name.startswith("sv_splash_tex_"):
                    bpy.data.textures.remove(texture)
            except:
                pass
        self._textures.clear()

        # Очищаем изображения
        for img in self._loaded_images:
            try:
                if img and img.name.startswith("sv_splash_img_"):
                    bpy.data.images.remove(img)
            except:
                pass
        self._loaded_images.clear()

class SV_OT_splash_simple_next(Operator):
    bl_idname = "sv.splash_simple_next"
    bl_label = "Далее"
    bl_description = "Следующее изображение"

    def execute(self, context):
        # Закрываем текущее окно и открываем новое со следующим изображением
        bpy.ops.sv.splash_simple_close()

        # Сохраняем индекс для следующего вызова
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PREFERENCES':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            with context.temp_override(window=window, area=area, region=region):
                                try:
                                    if hasattr(context, 'active_operator') and context.active_operator:
                                        op = context.active_operator
                                        if op.bl_idname == 'sv.splash_screen_simple':
                                            next_index = op.current_index + 1
                                            if next_index < len(op._image_files):
                                                # Вызываем новый splash screen с новым индексом
                                                bpy.ops.sv.splash_screen_simple('INVOKE_DEFAULT')
                                                # Обновляем индекс в новом операторе
                                                new_op = getattr(context, 'active_operator', None)
                                                if new_op and new_op.bl_idname == 'sv.splash_screen_simple':
                                                    new_op.current_index = next_index
                                                    new_op.load_current_image()
                                                return {'FINISHED'}
                                except Exception as e:
                                    print(f"Splash next error: {e}")

        # Если не нашли активный оператор, просто вызываем заново
        bpy.ops.sv.splash_screen_simple('INVOKE_DEFAULT')
        return {'FINISHED'}

class SV_OT_splash_simple_previous(Operator):
    bl_idname = "sv.splash_simple_previous"
    bl_label = "Назад"
    bl_description = "Предыдущее изображение"

    def execute(self, context):
        # Закрываем текущее окно и открываем новое с предыдущим изображением
        bpy.ops.sv.splash_simple_close()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PREFERENCES':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            with context.temp_override(window=window, area=area, region=region):
                                try:
                                    if hasattr(context, 'active_operator') and context.active_operator:
                                        op = context.active_operator
                                        if op.bl_idname == 'sv.splash_screen_simple':
                                            prev_index = op.current_index - 1
                                            if prev_index >= 0:
                                                # Вызываем новый splash screen с новым индексом
                                                bpy.ops.sv.splash_screen_simple('INVOKE_DEFAULT')
                                                # Обновляем индекс в новом операторе
                                                new_op = getattr(context, 'active_operator', None)
                                                if new_op and new_op.bl_idname == 'sv.splash_screen_simple':
                                                    new_op.current_index = prev_index
                                                    new_op.load_current_image()
                                                return {'FINISHED'}
                                except Exception as e:
                                    print(f"Splash previous error: {e}")

        # Если не нашли активный оператор, просто вызываем заново
        bpy.ops.sv.splash_screen_simple('INVOKE_DEFAULT')
        return {'FINISHED'}

class SV_OT_splash_simple_close(Operator):
    bl_idname = "sv.splash_simple_close"
    bl_label = "Закрыть"
    bl_description = "Закрыть splash screen"

    def execute(self, context):
        return {'FINISHED'}

class NODE_PT_sverchok_splash_panel(Panel):
    """Панель для Sverchok Splash Screen"""
    bl_label = "Sverchok Splash"
    bl_idname = "NODE_PT_sverchok_splash_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Sverchok"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'SverchokTree'
                if hasattr(context.space_data, 'tree_type') else False)

    def draw(self, context):
        layout = self.layout
        layout.operator("sv.splash_screen_simple",
                       text="Показать Splash Screen",
                       icon='IMAGE_DATA')

def register():
    """Регистрация всех классов"""
    bpy.utils.register_class(SV_OT_splash_screen_simple)
    bpy.utils.register_class(SV_OT_splash_simple_next)
    bpy.utils.register_class(SV_OT_splash_simple_previous)
    bpy.utils.register_class(SV_OT_splash_simple_close)
    bpy.utils.register_class(NODE_PT_sverchok_splash_panel)

    print("Sverchok Splash Screen: успешно зарегистрирован")

def unregister():
    """Отмена регистрации"""
    bpy.utils.unregister_class(NODE_PT_sverchok_splash_panel)
    bpy.utils.unregister_class(SV_OT_splash_simple_close)
    bpy.utils.unregister_class(SV_OT_splash_simple_previous)
    bpy.utils.unregister_class(SV_OT_splash_simple_next)
    bpy.utils.unregister_class(SV_OT_splash_screen_simple)

if __name__ == "__main__":
    register()
