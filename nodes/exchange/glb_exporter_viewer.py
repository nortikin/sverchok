# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os
import json
import tempfile
import webbrowser
from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty, StringProperty, EnumProperty, 
    FloatProperty, FloatVectorProperty, IntProperty
    )
from mathutils import Vector
import tempfile

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_mesh_utils import mesh_join

# ДОБАВЬ ЭТО ГЛОБАЛЬНО В НАЧАЛЕ ФАЙЛА (после импортов):
import atexit

# Константы
THREE_JS_VERSION = "r128"
_http_server = None

#def stop_http_server():
#    global _http_server
#    if _http_server:
#        print("Останавливаем HTTP сервер...")
#        _http_server.shutdown()
#        _http_server.server_close()
#        _http_server = None

#atexit.register(stop_http_server)

class SvStopServerOperator(bpy.types.Operator):
    """Останавливает HTTP сервер"""
    bl_idname = "node.sv_stop_server"
    bl_label = "Stop Server"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global _http_server
        if _http_server:
            try:
                _http_server.shutdown()
                _http_server.server_close()
                self.report({'INFO'}, "Сервер остановлен")
                _http_server = None
            except Exception as e:
                self.report({'ERROR'}, f"Ошибка: {str(e)}")
        else:
            self.report({'INFO'}, "Сервер не запущен")
        return {'FINISHED'}



class SvGltfViewerOperator(bpy.types.Operator, SvGenericNodeLocator):
    """
    Экспортирует GLTF и открывает в веб-просмотрщике
    """
    bl_idname = "node.sv_gltf_viewer"
    bl_label = "Просмотр GLTF"
    bl_options = {'REGISTER', 'UNDO'}

    def sv_execute(self, context, node):
        """Основная функция экспорта и показа"""
        if not (node.inputs['Vertices'].is_linked and node.inputs['Faces'].is_linked):
            self.report({'WARNING'}, "Подключите Vertices и Faces")
            return

        try:
            # Получаем данные из сокетов
            vertices_data = node.inputs['Vertices'].sv_get()
            faces_data = node.inputs['Faces'].sv_get()
            materials_data = node.inputs['Materials'].sv_get() if node.inputs['Materials'].is_linked else []

            # Экспортируем в GLTF
            gltf_path = node.export_to_gltf(vertices_data, faces_data, materials_data)

            # Создаем и открываем HTML просмотрщик с именем как у GLB
            html_path = node.create_html_viewer(gltf_path)

            # Запускаем локальный HTTP сервер для обхода CORS
            import http.server
            import socketserver
            import threading
            import webbrowser
            import os
            import time

            # Останавливаем предыдущий сервер если он есть
            global _http_server
            if _http_server:
                try:
                    stop_http_server()
                    #_http_server.shutdown()
                    #_http_server.server_close()
                    #print("Предыдущий сервер остановлен")
                except:
                    pass
                #_http_server = None

            # Получаем директорию с HTML файлом
            html_dir = os.path.dirname(html_path)

            def run_server():
                global _http_server
                # Меняем рабочую директорию на ту, где лежит HTML
                os.chdir(html_dir)

                # Создаем HTTP сервер с поддержкой CORS
                class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                    def end_headers(self):
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                        super().end_headers()

                    def do_OPTIONS(self):
                        self.send_response(200)
                        self.end_headers()

                # Пробуем разные порты если 8000 занят
                ports_to_try = [8000, 8001, 8002, 8003, 8004]
                port = None

                for test_port in ports_to_try:
                    try:
                        _http_server = socketserver.TCPServer(("", test_port), CORSHTTPRequestHandler)
                        port = test_port
                        print(f"HTTP сервер запущен на http://localhost:{port}")
                        break
                    except OSError as e:
                        if "Address already in use" in str(e):
                            print(f"Порт {test_port} занят, пробуем следующий...")
                            continue
                        else:
                            raise

                if port is None:
                    print("Не удалось найти свободный порт!")
                    return

                try:
                    _http_server.serve_forever()
                except KeyboardInterrupt:
                    pass
                finally:
                    if _http_server:
                        _http_server.server_close()

            # Запускаем сервер в отдельном потоке
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            # Даем серверу время запуститься
            time.sleep(0.5)

            # Открываем в браузере
            html_filename = os.path.basename(html_path)
            webbrowser.open(f'http://localhost:8000/{html_filename}')

            self.report({'INFO'}, f"GLTF экспортирован: {gltf_path}")

        except Exception as e:
            self.report({'ERROR'}, f"Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()

class SvGltfExportOnly(bpy.types.Operator, SvGenericNodeLocator):
    """
    Только экспорт GLTF без открытия
    """
    bl_idname = "node.sv_gltf_export"
    bl_label = "Экспорт GLTF"
    bl_options = {'REGISTER', 'UNDO'}

    def sv_execute(self, context, node):
        if not (node.inputs['Vertices'].is_linked and node.inputs['Faces'].is_linked):
            self.report({'WARNING'}, "Подключите Vertices и Faces")
            return
        
        try:
            vertices_data = node.inputs['Vertices'].sv_get()
            faces_data = node.inputs['Faces'].sv_get()
            materials_data = node.inputs['Materials'].sv_get() if node.inputs['Materials'].is_linked else []
            
            gltf_path = node.export_to_gltf(vertices_data, faces_data, materials_data)
            self.report({'INFO'}, f"GLTF экспортирован: {gltf_path}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка: {str(e)}")

class SvGlbExportNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: GLB Viewer for Sverchok
    Tooltip: Экспорт и просмотр сеток в GLTF/GLB формате через THREE.js
    """
    bl_idname = 'SvGlbExportNode'
    bl_label = 'GLB Viewer Exporter'
    bl_icon = 'SHADING_RENDERED'
    sv_icon = 'SV_GLTF_VIEWER'

    # Свойства узла
    format_items = [
        ('GLB', 'GLB (Binary)', 'Binary GLTF format', 0),
        ('GLTF', 'GLTF (JSON)', 'JSON GLTF format', 1),
        ]
    
    export_format: EnumProperty(
        name="Format",
        description="Формат экспорта",
        items=format_items,
        default='GLB',
        #update=updateNode
        )
    
    file_name: StringProperty(
        name="File Name", 
        default="sverchok_export",
        description="Имя файла без расширения",
        #update=updateNode
        )
    
    auto_open: BoolProperty(
        name="Auto Open",
        description="Автоматически открывать после экспорта",
        default=True,
        #update=updateNode
        )
    
    show_grid: BoolProperty(
        name="Show Grid",
        description="Показывать сетку в просмотрщике",
        default=True,
        #update=updateNode
        )
    
    show_axes: BoolProperty(
        name="Show Axes",
        description="Показывать оси координат",
        default=True,
        #update=updateNode
        )
    
    auto_rotate: BoolProperty(
        name="Auto Rotate",
        description="Автоповорот камеры",
        default=False,
        #update=updateNode
        )
    
    bg_color: FloatVectorProperty(
        name="Background Color",
        description="Цвет фона",
        subtype='COLOR',
        size=3,
        default=(0.4, 0.7, 1.0),
        min=0.0, max=1.0,
        #update=updateNode
        )
    
    mesh_color: FloatVectorProperty(
        name="Mesh Color",
        description="Цвет меша по умолчанию",
        subtype='COLOR',
        size=3,
        default=(0.1, 0.4, 0.15),
        min=0.0, max=1.0,
        #update=updateNode
        )
    
    export_path: StringProperty(
        name="Export Path",
        description="Путь для экспорта файлов",
        default="",
        subtype='DIR_PATH',
        #update=updateNode
        )
    
    export_normals: BoolProperty(
        name="Export Normals",
        description="Экспортировать нормали",
        default=True,
        #update=updateNode
        )
    
    export_uvs: BoolProperty(
        name="Export UVs",
        description="Экспортировать UV координаты",
        default=True,
        #update=updateNode
        )
    
    export_colors: BoolProperty(
        name="Export Colors",
        description="Экспортировать цвета вершин",
        default=False,
        #update=updateNode
        )

    file_path: bpy.props.StringProperty(
        name="File Path",
        description="Path to save the GLB file",
        default="//",
        subtype='FILE_PATH',
        update=updateNode
    )

    def sv_init(self, context):
        """Инициализация узла"""
        self.width = 300
        
        # Входные сокеты
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvFilePathSocket', 'Path').prop_name = 'file_path'
        a = self.inputs.new('SvStringsSocket', 'Materials')
        a.custom_draw = 'draw_materials_socket'
        a.hide_safe = True
        b = self.inputs.new('SvVerticesSocket', 'Normals')
        b.custom_draw = 'draw_optional_socket'
        b.hide_safe = True
        c = self.inputs.new('SvVerticesSocket', 'UVs')
        c.custom_draw = 'draw_optional_socket'
        c.hide_safe = True
        d = self.inputs.new('SvColorSocket', 'Vertex Colors')
        d.custom_draw = 'draw_optional_socket'
        d.hide_safe = True
        
        # Выходные сокеты (для обратной связи)
        self.outputs.new('SvTextSocket', 'Export Path')
        self.outputs.new('SvTextSocket', 'Status')

    def draw_materials_socket(self, socket, context, layout):
        """Кастомное отображение сокета материалов"""
        row = layout.row(align=True)
        if socket.is_linked:
            row.label(text=f"{socket.name}: {socket.objects_number}")
        else:
            row.label(text=f"{socket.name}: Используется цвет из настроек")

    def draw_optional_socket(self, socket, context, layout):
        """Кастомное отображение опциональных сокетов"""
        row = layout.row(align=True)
        if socket.is_linked:
            row.label(text=f"✓ {socket.name}: {socket.objects_number}")
        else:
            row.label(text=f"○ {socket.name}: Не подключен")

    def draw_buttons(self, context, layout):
        """Отрисовка кнопок в узле"""
        # Основные кнопки
        row = layout.row(align=True)
        scale_y = 4.0 if self.prefs_over_sized_buttons else 1.5
        row.scale_y = scale_y
        row.operator("node.sv_gltf_viewer", icon='SHADING_RENDERED', text="View as HTML")
        row.operator("node.sv_gltf_export", icon='EXPORT', text="Export GLB")
        # Кнопка остановки сервера (опционально)
        if _http_server:
            row = layout.row()
            row.alert = True
            row.operator("node.sv_stop_server", icon='CANCEL', text="Stop Server")#.invoke_default = True wm.operator_defaults
        
        # Настройки экспорта
        box = layout.box()
        #box.label(text="Настройки экспорта:")
        #box.prop(self, "export_format", text="Формат")
        box.prop(self, "file_name", text="File name")
        
        #if not self.export_path:
        #    box.alert = True
        #    box.label(text="Укажите путь экспорта!", icon='ERROR')
        #box.prop(self, "export_path", text="Путь")
        
        # Настройки просмотрщика
        #box = layout.box()
        #box.label(text="Настройки просмотрщика:")
        
        col = box.row(align=True)
        col.prop(self, "show_grid")
        col.prop(self, "show_axes")
        col.prop(self, "auto_rotate")
        
        row = box.row(align=True)
        row.prop(self, "bg_color", text="Background")
        row.prop(self, "mesh_color", text="Mesh color")
        
        # Дополнительные настройки
        #box = layout.box()
        #box.label(text="Дополнительно:")
        #box.prop(self, "export_normals")
        #box.prop(self, "export_uvs")
        #box.prop(self, "export_colors")

    def stop_server(self):
        """Останавливает HTTP сервер"""
        global _http_server
        if _http_server:
            try:
                _http_server.shutdown()
                _http_server.server_close()
                print("HTTP сервер остановлен")
                _http_server = None
            except Exception as e:
                print(f"Ошибка при остановке сервера: {e}")

    def get_export_path(self):
        """Получает путь для экспорта"""
        self.export_path = self.inputs['Path'].sv_get()[0][0]
        print(self.export_path)
        if self.export_path and self.export_path.strip():
            # Конвертируем путь Blender в абсолютный путь
            export_dir = Path(bpy.path.abspath(self.export_path.strip()))
        else:
            # Используем временную директорию
            export_dir = Path(tempfile.gettempdir()) / "sverchok_gltf"
        
        # Создаем директорию если не существует
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    def export_to_gltf(self, vertices_data, faces_data, materials_data=None):
        """Экспорт данных в GLTF/GLB формат"""
        print(f"Экспорт начат... Формат: {self.export_format}")
        # Создаем временную сцену
        temp_scene = bpy.data.scenes.new("Temp_GLTF_Export")
        original_scene = bpy.context.window.scene
        bpy.context.window.scene = temp_scene
        
        try:
            # Очищаем временную сцену
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            
            # Обрабатываем каждый меш
            for mesh_idx, (verts, faces_list) in enumerate(zip(vertices_data, faces_data)):
                # Создаем меш из данных
                mesh_name = f"Sverchok_Mesh_{mesh_idx}"
                mesh = bpy.data.meshes.new(mesh_name)
                
                # Конвертируем вершины и грани
                blender_verts = [Vector(v) for v in verts]
                blender_faces = faces_list
                
                # Создаем меш
                mesh.from_pydata(blender_verts, [], blender_faces)
                mesh.update()
                
                # Создаем объект
                obj = bpy.data.objects.new(mesh_name, mesh)
                temp_scene.collection.objects.link(obj)
                
                # Применяем материал если есть
                if materials_data and mesh_idx < len(materials_data):
                    obj_materials = materials_data[mesh_idx]
                    if obj_idx < len(obj_materials):
                        mat_name = obj_materials[obj_idx]
                        if isinstance(mat_name, str) and mat_name in bpy.data.materials:
                            obj.data.materials.append(bpy.data.materials[mat_name])
                        else:
                            # Создаем материал из цвета узла
                            self.create_material_for_object(obj)

            # Экспортируем в GLTF/GLB
            export_dir = self.get_export_path()

            # СОЗДАЕМ ПОДДИРЕКТОРИЮ models
            models_dir = export_dir / "models"
            models_dir.mkdir(parents=True, exist_ok=True)

            file_ext = '.glb' if self.export_format == 'GLB' else '.gltf'

            # Нормализуем имя файла
            safe_filename = "".join(c for c in self.file_name if c.isalnum() or c in ('_', '-')).strip()
            if not safe_filename:
                safe_filename = "sverchok_export"
                
            # СОХРАНЯЕМ В ПОДДИРЕКТОРИЮ
            file_path = models_dir / f"{safe_filename}{file_ext}"
            
            # Конвертируем путь в абсолютный
            absolute_path = bpy.path.abspath(str(file_path))
            print(absolute_path)
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            
            print(f"Exporting to: {absolute_path}")  # Для отладки
            
            # Настройки экспорта
            bpy.ops.export_scene.gltf(
                filepath=absolute_path,
                export_format=self.export_format,
                export_cameras=False,
                export_lights=False,
                export_yup=True,
                export_colors=self.export_colors,
                export_normals=self.export_normals,
                #gltf_trs_w_animation_pointer
                #export_uvs=self.export_uvs,
                export_materials='EXPORT',
                use_selection=False,
                #export_animations=False
            )
            
            print(f"GLTF экспортирован: {absolute_path}")
            print(f"Размер файла: {os.path.getsize(absolute_path)} байт")
            
            return absolute_path
            
        finally:
            # Восстанавливаем оригинальную сцену и очищаем временную
            bpy.context.window.scene = original_scene
            bpy.data.scenes.remove(temp_scene)

    def create_material_for_object(self, obj):
        """Создает материал для объекта из настроек узла"""
        mat_name = f"SvMat_{obj.name}"
        material = bpy.data.materials.new(name=mat_name)
        material.use_nodes = True
        
        # Настраиваем ноды материала
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Очищаем стандартные ноды
        nodes.clear()
        
        # Создаем BSDF нод
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs['Base Color'].default_value = (*self.mesh_color, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 0.5
        
        # Создаем Output нод
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        
        # Соединяем
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        obj.data.materials.append(material)

    def create_html_viewer(self, gltf_path):
        """Создает HTML файл просмотрщика для GLTF с автозагрузкой"""
        export_dir = self.get_export_path()
        #safe_filename = "".join(c for c in self.file_name if c.isalnum() or c in ('_', '-')).strip()
        #if not safe_filename:
        #    safe_filename = "sverchok_export"
        gltf_filename = Path(gltf_path).stem  # Имя без расширения
        html_path = export_dir / f"{gltf_filename}_viewer.html"  # Используем то же имя
        #html_path = export_dir / "gltf_viewer.html" #{safe_filename}
        
        # Получаем абсолютный путь к GLTF файлу
        gltf_abs_path = Path(bpy.path.abspath(gltf_path))
        
        # Для HTML используем относительный путь от HTML файла
        gltf_relative_path = "./models/" + gltf_abs_path.name
        
        # Преобразуем настройки узла в формат для JS
        show_grid_js = 'true' if self.show_grid else 'false'
        show_axes_js = 'true' if self.show_axes else 'false'
        auto_rotate_js = 'true' if self.auto_rotate else 'false'
        bg_color_hex = self.color_to_hex(self.bg_color)
        
        # Создаем HTML с автозагрузкой GLTF
        html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Model Viewer - Sverchok Export</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e6f7ff;
            height: 100vh;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .viewer-section {{
            flex: 3;
            position: relative;
        }}
        
        #three-canvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
        
        .controls-section {{
            flex: 1;
            min-width: 400px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding: 25px;
            overflow-y: auto;
        }}
        
        @media (max-width: 1200px) {{
            .container {{
                flex-direction: column;
            }}
            
            .controls-section {{
                min-width: 100%;
                max-height: 40vh;
            }}
        }}
        
        .panel {{
            background: rgba(255, 255, 255, 0.07);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .panel-title {{
            font-size: 1.4rem;
            margin-bottom: 20px;
            color: #64b5f6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .panel-title i {{
            font-size: 1.2rem;
        }}
        
        button {{
            width: 100%;
            padding: 14px;
            margin-bottom: 12px;
            background: linear-gradient(90deg, #4a6fa5 0%, #64b5f6 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        
        button:hover {{
            background: linear-gradient(90deg, #64b5f6 0%, #90caf9 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(100, 181, 246, 0.3);
        }}
        
        button:active {{
            transform: translateY(1px);
        }}
        
        .slider-container {{
            margin-bottom: 20px;
        }}
        
        .slider-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            color: #bbdefb;
        }}
        
        .slider-value {{
            color: #64b5f6;
            font-weight: bold;
        }}
        
        input[type="range"] {{
            width: 100%;
            height: 6px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            outline: none;
            -webkit-appearance: none;
        }}
        
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #64b5f6;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(100, 181, 246, 0.5);
        }}
        
        .color-picker {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }}
        
        .color-box {{
            width: 40px;
            height: 40px;
            border-radius: 8px;
            cursor: pointer;
            border: 2px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
        }}
        
        .color-box:hover {{
            transform: scale(1.1);
            border-color: #64b5f6;
        }}
        
        .model-info {{
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            font-family: monospace;
            font-size: 0.9rem;
            max-height: 200px;
            overflow-y: auto;
        }}
        
        .info-line {{
            margin-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }}
        
        .info-label {{
            color: #90caf9;
        }}
        
        .info-value {{
            color: #bbdefb;
        }}
        
        .hud {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.5);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
            z-index: 100;
        }}
        
        .hud-item {{
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .hud-item:last-child {{
            margin-bottom: 0;
        }}
        
        .hud-label {{
            color: #90caf9;
            font-size: 0.9rem;
        }}
        
        .hud-value {{
            color: #bbdefb;
            font-weight: bold;
        }}
        
        .instructions {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.6);
            line-height: 1.5;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .material-controls {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }}
        
        .material-btn {{
            padding: 10px;
            background: rgba(100, 181, 246, 0.2);
            border: 1px solid rgba(100, 181, 246, 0.3);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .material-btn:hover {{
            background: rgba(100, 181, 246, 0.4);
            transform: translateY(-2px);
        }}
        
        .material-btn.active {{
            background: rgba(100, 181, 246, 0.6);
            border-color: #64b5f6;
        }}
        
        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            padding: 20px 30px;
            border-radius: 10px;
            border: 1px solid #64b5f6;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .loading-spinner {{
            width: 30px;
            height: 30px;
            border: 3px solid rgba(100, 181, 246, 0.3);
            border-radius: 50%;
            border-top-color: #64b5f6;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            100% {{ transform: rotate(360deg); }}
        }}
        
        .error-message {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(231, 76, 60, 0.9);
            padding: 20px 30px;
            border-radius: 10px;
            border: 1px solid #e74c3c;
            z-index: 1000;
            text-align: center;
            max-width: 500px;
        }}
        
        .error-message button {{
            margin-top: 15px;
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div id="loading" class="loading">
        <div class="loading-spinner"></div>
        <div>Загрузка модели...</div>
    </div>
    
    <div id="errorContainer" class="error-message" style="display: none;">
        <h3><i class="fas fa-exclamation-triangle"></i> Ошибка загрузки</h3>
        <p id="errorText"></p>
        <button id="retryButton"><i class="fas fa-redo"></i> Повторить</button>
        <button id="closeButton"><i class="fas fa-times"></i> Закрыть</button>
    </div>
    
    <div class="container" style="display: none;" id="mainContainer">
        <div class="viewer-section">
            <canvas id="three-canvas"></canvas>
            
            <div class="hud">
                <div class="hud-item">
                    <span class="hud-label"><i class="fas fa-cube"></i> Модель:</span>
                    <span class="hud-value" id="modelName">Загрузка...</span>
                </div>
                <div class="hud-item">
                    <span class="hud-label"><i class="fas fa-cubes"></i> Полигоны:</span>
                    <span class="hud-value" id="polyCount">0</span>
                </div>
                <div class="hud-item">
                    <span class="hud-label"><i class="fas fa-arrows-alt"></i> Размеры:</span>
                    <span class="hud-value" id="modelSize">0 x 0 x 0</span>
                </div>
                <div class="hud-item">
                    <span class="hud-label"><i class="fas fa-download"></i> Статус:</span>
                    <span class="hud-value" id="loadStatus">Загрузка...</span>
                </div>
            </div>
        </div>
        
        <div class="controls-section">
            <div class="panel">
                <div class="panel-title">
                    <i class="fas fa-cube"></i> Управление моделью
                </div>
                
                <button id="resetView">
                    <i class="fas fa-redo"></i> Сбросить вид
                </button>
                
                <button id="screenshot">
                    <i class="fas fa-camera"></i> Сделать скриншот
                </button>
                
                <button id="fullscreen">
                    <i class="fas fa-expand"></i> Полный экран
                </button>
                
                <button id="downloadModel">
                    <i class="fas fa-download"></i> Скачать модель
                </button>
                
                <button id="debugTest">
                    <i class="fas fa-bug"></i> Тест путей
                </button>
            </div>
            
            <div class="panel">
                <div class="panel-title">
                    <i class="fas fa-sliders-h"></i> Настройки отображения
                </div>
                
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Масштаб</span>
                        <span class="slider-value" id="scaleValue">1.0</span>
                    </div>
                    <input type="range" id="scaleSlider" min="0.1" max="5" value="1" step="0.1">
                </div>
                
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Поворот X</span>
                        <span class="slider-value" id="rotationXValue">0°</span>
                    </div>
                    <input type="range" id="rotationXSlider" min="0" max="360" value="0" step="1">
                </div>
                
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Поворот Y</span>
                        <span class="slider-value" id="rotationYValue">0°</span>
                    </div>
                    <input type="range" id="rotationYSlider" min="0" max="360" value="0" step="1">
                </div>
                
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Яркость</span>
                        <span class="slider-value" id="brightnessValue">100%</span>
                    </div>
                    <input type="range" id="brightnessSlider" min="20" max="200" value="100" step="1">
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">
                    <i class="fas fa-palette"></i> Материалы и цвета
                </div>
                
                <div class="material-controls">
                    <div class="material-btn active" data-material="normal">
                        <i class="fas fa-shapes"></i> Нормальный
                    </div>
                    <div class="material-btn" data-material="wireframe">
                        <i class="fas fa-drafting-compass"></i> Каркас
                    </div>
                    <div class="material-btn" data-material="flat">
                        <i class="fas fa-square-full"></i> Плоский
                    </div>
                    <div class="material-btn" data-material="phong">
                        <i class="fas fa-sun"></i> Фонг
                    </div>
                </div>
                
                <div class="color-picker">
                    <div class="color-box" style="background: #ffffff;" data-color="#ffffff"></div>
                    <div class="color-box" style="background: #64b5f6;" data-color="#64b5f6"></div>
                    <div class="color-box" style="background: #81c784;" data-color="#81c784"></div>
                    <div class="color-box" style="background: #ffb74d;" data-color="#ffb74d"></div>
                    <div class="color-box" style="background: #e57373;" data-color="#e57373"></div>
                    <div class="color-box" style="background: #ba68c8;" data-color="#ba68c8"></div>
                    <div class="color-box" style="background: #4db6ac;" data-color="#4db6ac"></div>
                    <div class="color-box" style="background: #ff8a65;" data-color="#ff8a65"></div>
                </div>
                
                <div style="margin-top: 15px;">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="checkbox" id="showGrid" {"checked" if self.show_grid else ""}>
                        <span>Показать сетку</span>
                    </label>
                    
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; margin-top: 10px;">
                        <input type="checkbox" id="showAxes" {"checked" if self.show_axes else ""}>
                        <span>Показать оси</span>
                    </label>
                    
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; margin-top: 10px;">
                        <input type="checkbox" id="autoRotate" {"checked" if self.auto_rotate else ""}>
                        <span>Автоповорот</span>
                    </label>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">
                    <i class="fas fa-info-circle"></i> Информация о модели
                </div>
                
                <div class="model-info" id="modelInfo">
                    <div class="info-line">
                        <span class="info-label">Файл:</span>
                        <span class="info-value" id="infoFile">{gltf_abs_path.name}</span>
                    </div>
                    <div class="info-line">
                        <span class="info-label">Формат:</span>
                        <span class="info-value" id="infoFormat">GLTF/GLB</span>
                    </div>
                    <div class="info-line">
                        <span class="info-label">Вершин:</span>
                        <span class="info-value" id="infoVertices">0</span>
                    </div>
                    <div class="info-line">
                        <span class="info-label">Полигонов:</span>
                        <span class="info-value" id="infoFaces">0</span>
                    </div>
                    <div class="info-line">
                        <span class="info-label">Материалы:</span>
                        <span class="info-value" id="infoMaterials">0</span>
                    </div>
                    <div class="info-line">
                        <span class="info-label">Текстуры:</span>
                        <span class="info-value" id="infoTextures">0</span>
                    </div>
                    <div class="info-line">
                        <span class="info-label">Путь:</span>
                        <span class="info-value" id="infoPath" style="font-size: 0.8rem; word-break: break-all;">models/{gltf_abs_path.name}</span>
                    </div>
                </div>
            </div>
            
            <div class="instructions">
                <p><strong>Управление:</strong></p>
                <p>• ЛКМ + движение - вращение камеры</p>
                <p>• ПКМ + движение - панорамирование</p>
                <p>• Колесо мыши - приближение/отдаление</p>
                <p>• Двойной клик - сброс вида</p>
            </div>
        </div>
    </div>

    <!-- THREE.js и необходимые компоненты -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        // Конфигурация
        const CONFIG = {{
            gltfPath: '{gltf_relative_path}',
            backgroundColor: '{bg_color_hex}',
            showGrid: {show_grid_js},
            showAxes: {show_axes_js},
            autoRotate: {auto_rotate_js}
        }};
        
        console.log('Начинаем загрузку модели:', CONFIG.gltfPath);
        console.log('Цвет фона:', CONFIG.backgroundColor);
        
        // Инициализация сцены
        let scene, camera, renderer, controls;
        let currentModel = null;
        let gridHelper, axesHelper;
        let autoRotate = CONFIG.autoRotate;
        let loadAttempts = 0;
        const MAX_LOAD_ATTEMPTS = 3;
        
        init();
        
        function init() {{
            console.log('Инициализация Three.js сцены...');
            
            // Создаем сцену
            scene = new THREE.Scene();
            scene.background = new THREE.Color(CONFIG.backgroundColor);
            
            // Камера
            camera = new THREE.PerspectiveCamera(75, window.innerWidth * 0.75 / window.innerHeight, 0.1, 1000);
            camera.position.set(5, 5, 5);
            
            // Рендерер
            renderer = new THREE.WebGLRenderer({{ 
                canvas: document.getElementById('three-canvas'),
                antialias: true 
            }});
            renderer.setSize(window.innerWidth * 0.75, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            // Управление камерой
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Освещение
            setupLighting();
            
            // Вспомогательные элементы
            setupHelpers();
            
            // Инициализация UI
            initUI();
            
            // Обработка ресайза окна
            window.addEventListener('resize', onWindowResize);
            
            // Загружаем модель
            loadModel();
            
            // Анимация
            animate();
        }}
        
        function setupLighting() {{
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 15);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
        }}
        
        function setupHelpers() {{
            gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
            gridHelper.visible = CONFIG.showGrid;
            scene.add(gridHelper);
            
            axesHelper = new THREE.AxesHelper(5);
            axesHelper.visible = CONFIG.showAxes;
            scene.add(axesHelper);
        }}
        
        function loadModel() {{
            console.log('Попытка загрузки модели:', CONFIG.gltfPath);
            
            const loader = new THREE.GLTFLoader();
            
            // Пробуем несколько путей для загрузки
            const loadPaths = [
                CONFIG.gltfPath, // Относительный путь
                './' + CONFIG.gltfPath, // Добавляем ./
                window.location.pathname.replace(/[^/]*$/, '') + CONFIG.gltfPath, // Абсолютный путь
                'file://' + window.location.pathname.replace(/[^/]*$/, '') + CONFIG.gltfPath, // file:// протокол
                CONFIG.gltfPath.replace(/\\\\/g, '/') // Заменяем обратные слеши
            ];
            
            console.log('Все пути для загрузки:', loadPaths);
            
            // Функция для проверки существования файла
            function checkFileExists(url, callback) {{
                const xhr = new XMLHttpRequest();
                xhr.open('HEAD', url);
                xhr.onreadystatechange = function() {{
                    if (xhr.readyState === 4) {{
                        callback(xhr.status === 200 || xhr.status === 0);
                    }}
                }};
                xhr.onerror = function() {{
                    callback(false);
                }};
                xhr.send(null);
            }}
            
            // Функция для проверки путей с рекурсией
            function tryLoadWithCheck(pathIndex) {{
                if (pathIndex >= loadPaths.length) {{
                    showError('Все пути недоступны. Файл не найден.');
                    return;
                }}
                
                const currentPath = loadPaths[pathIndex];
                console.log(`Проверка пути ${{pathIndex + 1}}:`, currentPath);
                document.getElementById('loadStatus').textContent = `Проверка пути ${{pathIndex + 1}}...`;
                
                checkFileExists(currentPath, function(exists) {{
                    if (exists) {{
                        console.log(`✅ Путь доступен:`, currentPath);
                        document.getElementById('loadStatus').textContent = 'Файл найден, загружаем...';
                        setTimeout(function() {{ tryLoad(pathIndex); }}, 100);
                    }} else {{
                        console.log(`❌ Путь недоступен:`, currentPath);
                        if (pathIndex < loadPaths.length - 1) {{
                            tryLoadWithCheck(pathIndex + 1);
                        }} else {{
                            showError('Файл не найден ни по одному из путей');
                        }}
                    }}
                }});
            }}
            
            // Функция для загрузки модели
            function tryLoad(index) {{
                const currentPath = loadPaths[index];
                console.log(`Загрузка по пути ${{index + 1}}:`, currentPath);
                
                loader.load(
                    currentPath,
                    function(gltf) {{
                        console.log('✅ Модель успешно загружена!');
                        onModelLoaded(gltf);
                    }},
                    function(xhr) {{
                        // Прогресс загрузки
                        if (xhr.lengthComputable) {{
                            const percent = Math.round((xhr.loaded / xhr.total) * 100);
                            document.querySelector('#loading div:last-child').textContent = 
                                'Загрузка модели... ' + percent + '%';
                            document.getElementById('loadStatus').textContent = 'Загрузка: ' + percent + '%';
                        }} else {{
                            document.getElementById('loadStatus').textContent = 'Загрузка...';
                        }}
                    }},
                    function(error) {{
                        console.error('❌ Ошибка загрузки:', error);
                        
                        let errorMessage = 'Неизвестная ошибка';
                        if (error && error.message) {{
                            errorMessage = error.message;
                        }} else if (error && error.toString) {{
                            errorMessage = error.toString();
                        }}
                        
                        console.log('Код ошибки:', error ? error.code : 'нет кода');
                        console.log('Тип ошибки:', error ? error.type : 'нет типа');
                        
                        if (index < loadPaths.length - 1) {{
                            console.log('🔄 Пробуем следующий путь...');
                            setTimeout(function() {{ tryLoad(index + 1); }}, 500);
                        }} else {{
                            showError(`Ошибка загрузки модели:<br><br>
                                <strong>Причина:</strong> ${{errorMessage}}<br>
                                <strong>Путь:</strong> ${{currentPath}}<br>
                                <strong>Попытка:</strong> ${{index + 1}} из ${{loadPaths.length}}`);
                        }}
                    }}
                );
            }}
            
            // Начинаем проверку путей
            tryLoadWithCheck(0);
        }}
        
        function onModelLoaded(gltf) {{
            if (currentModel) {{
                scene.remove(currentModel);
            }}
            
            currentModel = gltf.scene;
            scene.add(currentModel);
            
            // Обновляем информацию о модели
            updateModelInfo(gltf);
            
            // Центрируем модель
            centerModel();
            
            // Скрываем индикатор загрузки и показываем интерфейс
            document.getElementById('loading').style.display = 'none';
            document.getElementById('mainContainer').style.display = 'flex';
            document.getElementById('loadStatus').textContent = 'Загружено';
            
            console.log('Модель успешно загружена и отображена');
        }}
        
        function updateModelInfo(gltf) {{
            let vertices = 0;
            let faces = 0;
            const materials = new Set();
            const textures = new Set();
            
            gltf.scene.traverse(function(child) {{
                if (child.isMesh) {{
                    if (child.geometry && child.geometry.attributes.position) {{
                        vertices += child.geometry.attributes.position.count;
                    }}
                    if (child.geometry && child.geometry.index) {{
                        faces += child.geometry.index.count / 3;
                    }}
                    
                    if (child.material) {{
                        if (Array.isArray(child.material)) {{
                            child.material.forEach(function(mat) {{
                                materials.add(mat.uuid);
                            }});
                        }} else {{
                            materials.add(child.material.uuid);
                        }}
                        
                        // Сбор текстур
                        for (const key in child.material) {{
                            if (child.material[key] && child.material[key].isTexture) {{
                                textures.add(child.material[key].uuid);
                            }}
                        }}
                    }}
                }}
            }});
            
            document.getElementById('infoVertices').textContent = vertices.toLocaleString();
            document.getElementById('infoFaces').textContent = faces.toLocaleString();
            document.getElementById('infoMaterials').textContent = materials.size;
            document.getElementById('infoTextures').textContent = textures.size;
        }}
        
        function centerModel() {{
            if (!currentModel) return;
            
            const box = new THREE.Box3().setFromObject(currentModel);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            // Центрируем модель
            currentModel.position.x = -center.x;
            currentModel.position.y = -center.y;
            currentModel.position.z = -center.z;
            
            // Обновляем HUD
            document.getElementById('modelName').textContent = 
                currentModel.name || CONFIG.gltfPath.split('/').pop().split('.')[0];
            document.getElementById('polyCount').textContent = countFaces(currentModel);
            document.getElementById('modelSize').textContent = 
                size.x.toFixed(2) + ' x ' + size.y.toFixed(2) + ' x ' + size.z.toFixed(2);
            
            // Настраиваем камеру
            const maxDim = Math.max(size.x, size.y, size.z);
            const cameraDistance = maxDim * 2;
            camera.position.set(cameraDistance, cameraDistance * 0.75, cameraDistance);
            controls.target.copy(center.negate());
            controls.update();
        }}
        
        function countFaces(object) {{
            let count = 0;
            object.traverse(function(child) {{
                if (child.geometry && child.geometry.index) {{
                    count += child.geometry.index.count / 3;
                }}
            }});
            return count;
        }}
        
        function initUI() {{
            // Кнопки
            document.getElementById('resetView').addEventListener('click', resetView);
            document.getElementById('screenshot').addEventListener('click', takeScreenshot);
            document.getElementById('fullscreen').addEventListener('click', toggleFullscreen);
            document.getElementById('downloadModel').addEventListener('click', downloadModel);
            document.getElementById('retryButton').addEventListener('click', retryLoad);
            document.getElementById('closeButton').addEventListener('click', closeError);
            document.getElementById('debugTest').addEventListener('click', testPaths);
            
            // Слайдеры
            initSliders();
            
            // Материалы
            document.querySelectorAll('.material-btn').forEach(function(btn) {{
                btn.addEventListener('click', function() {{
                    document.querySelectorAll('.material-btn').forEach(function(b) {{
                        b.classList.remove('active');
                    }});
                    this.classList.add('active');
                    changeMaterial(this.dataset.material);
                }});
            }});
            
            // Цвета
            document.querySelectorAll('.color-box').forEach(function(box) {{
                box.addEventListener('click', function() {{
                    changeColor(this.dataset.color);
                }});
            }});
            
            // Переключатели
            document.getElementById('showGrid').addEventListener('change', function() {{
                gridHelper.visible = this.checked;
            }});
            
            document.getElementById('showAxes').addEventListener('change', function() {{
                axesHelper.visible = this.checked;
            }});
            
            document.getElementById('autoRotate').addEventListener('change', function() {{
                autoRotate = this.checked;
            }});
        }}
        
        function initSliders() {{
            const sliders = [
                {{ id: 'scaleSlider', valueId: 'scaleValue', format: function(v) {{ return v.toFixed(1); }} }},
                {{ id: 'rotationXSlider', valueId: 'rotationXValue', format: function(v) {{ return v + '°'; }} }},
                {{ id: 'rotationYSlider', valueId: 'rotationYValue', format: function(v) {{ return v + '°'; }} }},
                {{ id: 'brightnessSlider', valueId: 'brightnessValue', format: function(v) {{ return v + '%'; }} }}
            ];
            
            sliders.forEach(function(slider) {{
                const sliderEl = document.getElementById(slider.id);
                const valueEl = document.getElementById(slider.valueId);
                
                if (sliderEl && valueEl) {{
                    valueEl.textContent = slider.format(parseFloat(sliderEl.value));
                    
                    sliderEl.addEventListener('input', function() {{
                        valueEl.textContent = slider.format(parseFloat(this.value));
                        applySliderValues();
                    }});
                }}
            }});
        }}
        
        function applySliderValues() {{
            if (!currentModel) return;
            
            const scale = parseFloat(document.getElementById('scaleSlider').value);
            const rotationX = parseFloat(document.getElementById('rotationXSlider').value) * Math.PI / 180;
            const rotationY = parseFloat(document.getElementById('rotationYSlider').value) * Math.PI / 180;
            const brightness = parseFloat(document.getElementById('brightnessSlider').value) / 100;
            
            currentModel.scale.setScalar(scale);
            currentModel.rotation.x = rotationX;
            currentModel.rotation.y = rotationY;
            
            // Обновление освещения
            scene.traverse(function(child) {{
                if (child.isLight && child.type !== 'AmbientLight') {{
                    child.intensity = brightness * 0.8;
                }}
                if (child.isAmbientLight) {{
                    child.intensity = brightness * 0.6;
                }}
            }});
        }}
        
        function changeMaterial(type) {{
            if (!currentModel) return;
            
            currentModel.traverse(function(child) {{
                if (child.isMesh) {{
                    let newMaterial;
                    
                    switch(type) {{
                        case 'wireframe':
                            newMaterial = new THREE.MeshBasicMaterial({{
                                color: child.material.color || 0x64b5f6,
                                wireframe: true
                            }});
                            break;
                            
                        case 'flat':
                            newMaterial = new THREE.MeshLambertMaterial({{
                                color: child.material.color || 0x64b5f6,
                                flatShading: true
                            }});
                            break;
                            
                        case 'phong':
                            newMaterial = new THREE.MeshPhongMaterial({{
                                color: child.material.color || 0x64b5f6,
                                shininess: 30
                            }});
                            break;
                            
                        default: // normal
                            newMaterial = new THREE.MeshStandardMaterial({{
                                color: child.material.color || 0x64b5f6,
                                metalness: 0.3,
                                roughness: 0.4
                            }});
                    }}
                    
                    child.material = newMaterial;
                }}
            }});
        }}
        
        function changeColor(color) {{
            if (!currentModel) return;
            
            const threeColor = new THREE.Color(color);
            currentModel.traverse(function(child) {{
                if (child.isMesh) {{
                    child.material.color = threeColor;
                    child.material.needsUpdate = true;
                }}
            }});
        }}
        
        function resetView() {{
            controls.reset();
            if (currentModel) {{
                centerModel();
            }}
            
            // Сброс слайдеров
            document.getElementById('scaleSlider').value = 1;
            document.getElementById('rotationXSlider').value = 0;
            document.getElementById('rotationYSlider').value = 0;
            document.getElementById('brightnessSlider').value = 100;
            
            applySliderValues();
            initSliders();
        }}
        
        function takeScreenshot() {{
            renderer.render(scene, camera);
            const dataURL = renderer.domElement.toDataURL('image/png');
            
            const link = document.createElement('a');
            link.href = dataURL;
            link.download = 'screenshot_' + Date.now() + '.png';
            link.click();
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                if (document.exitFullscreen) {{
                    document.exitFullscreen();
                }}
            }}
        }}
        
        function downloadModel() {{
            const link = document.createElement('a');
            link.href = CONFIG.gltfPath;
            link.download = CONFIG.gltfPath.split('/').pop();
            link.click();
        }}
        
        function testPaths() {{
            console.log('=== ТЕСТИРОВАНИЕ ПУТЕЙ ===');
            const testPaths = [
                CONFIG.gltfPath,
                './' + CONFIG.gltfPath,
                window.location.pathname.replace(/[^/]*$/, '') + CONFIG.gltfPath,
                'file://' + window.location.pathname.replace(/[^/]*$/, '') + CONFIG.gltfPath,
                CONFIG.gltfPath.replace(/\\\\/g, '/')
            ];
            
            testPaths.forEach((path, i) => {{
                console.log(`Тест пути ${{i + 1}}:`, path);
                const xhr = new XMLHttpRequest();
                xhr.open('HEAD', path);
                xhr.onreadystatechange = function() {{
                    if (xhr.readyState === 4) {{
                        console.log(`  Статус: ${{xhr.status}} (200 = OK, 0 = локальный файл)`);
                    }}
                }};
                xhr.onerror = function() {{
                    console.log(`  Ошибка при проверке`);
                }};
                xhr.send();
            }});
            alert('Результаты теста в консоли (F12)');
        }}
        
        function showError(message) {{
            console.error('Показать ошибку:', message);
            document.getElementById('errorText').textContent = message;
            document.getElementById('errorContainer').style.display = 'block';
            document.getElementById('loading').style.display = 'none';
            document.getElementById('loadStatus').textContent = 'Ошибка';
        }}
        
        function retryLoad() {{
            document.getElementById('errorContainer').style.display = 'none';
            document.getElementById('loading').style.display = 'flex';
            document.getElementById('loadStatus').textContent = 'Перезагрузка...';
            
            loadAttempts++;
            if (loadAttempts <= MAX_LOAD_ATTEMPTS) {{
                setTimeout(loadModel, 1000);
            }} else {{
                showError('Превышено максимальное количество попыток загрузки.');
            }}
        }}
        
        function closeError() {{
            document.getElementById('errorContainer').style.display = 'none';
            document.getElementById('mainContainer').style.display = 'flex';
        }}
        
        function onWindowResize() {{
            const width = window.innerWidth * 0.75;
            const height = window.innerHeight;
            
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            
            if (autoRotate && currentModel) {{
                currentModel.rotation.y += 0.005;
            }}
            
            controls.update();
            renderer.render(scene, camera);
        }}
        
        // Функция для отладки
        window.debugInfo = function() {{
            console.log('Текущая конфигурация:', CONFIG);
            console.log('Текущая модель:', currentModel);
            console.log('Путь к файлу:', CONFIG.gltfPath);
            console.log('Попытки загрузки:', loadAttempts);
        }};
    </script>
</body>
</html>'''

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML создан: {html_path}")
        print(f"GLTF путь: {gltf_path}")
        print(f"Относительный путь: {gltf_relative_path}")
        
        return str(html_path)

    def _get_checked_attr(self, value):
        """Возвращает строку checked для HTML если значение True"""
        return 'checked' if value else ''

    def color_to_hex(self, color):
        """Конвертирует цвет из RGB в HEX"""
        return f'#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}'

    def process(self):
        """Основной процесс узла"""
        # Проверяем подключенные сокеты
        has_input = self.inputs['Vertices'].is_linked and self.inputs['Faces'].is_linked
        
        # Устанавливаем выходные значения
        if has_input:
            export_dir = str(self.get_export_path())
            self.outputs['Export Path'].sv_set([[export_dir]])
            self.outputs['Status'].sv_set([["Ready"]])
        else:
            self.outputs['Export Path'].sv_set([[""]])
            self.outputs['Status'].sv_set([["Waiting for input"]])


# Регистрация для Sverchok
def register():
    bpy.utils.register_class(SvGltfExportOnly)
    bpy.utils.register_class(SvGltfViewerOperator)
    bpy.utils.register_class(SvStopServerOperator)
    bpy.utils.register_class(SvGlbExportNode)

def unregister():
    bpy.utils.unregister_class(SvGlbExportNode)
    bpy.utils.unregister_class(SvStopServerOperator)
    bpy.utils.unregister_class(SvGltfViewerOperator)
    bpy.utils.unregister_class(SvGltfExportOnly)

if __name__ == '__main__':
    register()