import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class SV_OT_apply_theme(Operator):
    """Применить тему Sverchok к Блендеру"""
    bl_idname = "sverchok.apply_theme"
    bl_label = "Применить тему Sverchok"
    bl_options = {'REGISTER', 'UNDO'}

    theme_name: StringProperty(
        name="Имя темы",
        description="Имя файла темы (без расширения .xml)",
        default="Sverchok_light_5"
    )

    def execute(self, context):
        # Пути к директориям
        addon_dir = os.path.dirname(__file__)
        themes_source_dir = os.path.join(addon_dir, "themes")
        print(themes_source_dir)

        # Полные пути к файлам
        if bpy.app.version >= (5, 0, 0):
            theme_file = "Sverchok_light_5.xml"
        elif bpy.app.version >= (4, 0, 0):
            theme_file = "Sverchok_light_4.xml"
        elif bpy.app.version >= (3, 0, 0):
            theme_file = "Sverchok_light_3.xml"
        source_theme_path = os.path.join(themes_source_dir, theme_file)
        self.theme_name = theme_file[:-4]
        # Проверяем существует ли тема в datafiles
        if not os.path.exists(source_theme_path):
            self.report({'INFO'}, f"Тема {theme_file} не найдена")

        # Применяем тему
        try:
            # Попытка применить тему через API Sverchok
            bpy.ops.preferences.theme_install(overwrite=True, filepath=source_theme_path, filter_folder=True, filter_glob="*.xml")
            self.report({'INFO'}, f"Тема применена: {self.theme_name}")
        except:
            self.report({'INFO'}, f"Не может быть: {self.theme_name}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        # Можно добастить диалог выбора темы
        return self.execute(context)

# Регистрация класса
classes = [SV_OT_apply_theme]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
