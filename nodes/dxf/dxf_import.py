import bpy
from mathutils import Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator, SvGenericCallbackOldOp
from sverchok.utils.dxf import dxf_read
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.dependencies import geomdl, FreeCAD

# Класс для хранения данных о слоях
class SvDXFLayerCollection(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    enabled: bpy.props.BoolProperty(default=True)

class SVDXF_UL_LayersList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "enabled", text="")
        layout.label(text=item.name, icon='LAYER_ACTIVE')

class SvDxfImportNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfImportNode'
    bl_label = 'DXF Import'
    bl_icon = 'IMPORT'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    file_path: bpy.props.StringProperty(
        name="File Path",
        description="Path to get the DXF file",
        default="",
        subtype='FILE_PATH',
        update=updateNode
    )

    # Свойства для работы со слоями
    dxf_layers: bpy.props.CollectionProperty(type=SvDXFLayerCollection)
    active_layer_index: bpy.props.IntProperty()
    
    # Убрал use_layers_filter и добавим автоматическое применение фильтра
    layers_filter_enabled: bpy.props.BoolProperty(
        name="Layers Filter Enabled",
        description="Enable/disable layers filtering",
        default=False,
        update=updateNode
    )

    implementations = []
    if geomdl is not None:
        implementations.append((SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    implementations.append((SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", 1))
    if FreeCAD is not None:
        implementations.append((SvNurbsMaths.FREECAD, "FreeCAD", "FreeCAD library implementation", 2))

    implementation : bpy.props.EnumProperty(
            name = "Implementation",
            items=implementations,
            update = updateNode)

    scale: bpy.props.FloatProperty(default=1.0,name='scale',
        update=updateNode)

    curve_degree: bpy.props.IntProperty(default=3, min=1, max=4,name='degree for nurbses',
        update=updateNode)

    resolution: bpy.props.IntProperty(default=10, min=3, max=500,name='resolution for arcs',
        update=updateNode)

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale',
        update=updateNode)

    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvFilePathSocket', 'path').prop_name = 'file_path'

        self.outputs.new('SvVerticesSocket', 'vers_e')
        self.outputs.new('SvStringsSocket', 'edgs')
        self.outputs.new('SvVerticesSocket', 'vers_p')
        self.outputs.new('SvStringsSocket', 'pols')
        self.outputs.new('SvVerticesSocket', 'vers_annot')
        self.outputs.new('SvStringsSocket', 'edgs_annot')
        self.outputs.new('SvVerticesSocket', 'vers_text')
        self.outputs.new('SvStringsSocket', "text")
        self.outputs.new('SvCurveSocket', "curves")
        self.outputs.new('SvStringsSocket', "knots")

    def draw_layers_list(self, layout):
        """Отрисовка списка слоёв"""
        if self.dxf_layers:
            # Вместо переключателя - информация о состоянии фильтра
            if self.layers_filter_enabled:
                layout.label(text=f"Layers Filter: ON ({self.get_enabled_layers_count()}/{len(self.dxf_layers)})", icon='CHECKBOX_HLT')
            else:
                layout.label(text="Layers Filter: OFF (all layers)", icon='CHECKBOX_DEHLT')
            
            layout.template_list("SVDXF_UL_LayersList", "", self, "dxf_layers", self, "active_layer_index")
        else:
            layout.label(text='--No layers loaded--')

    def get_enabled_layers_count(self):
        """Получить количество включенных слоёв"""
        return len([layer for layer in self.dxf_layers if layer.enabled])

    def get_dxf_layers(self):
        """Получение списка слоёв из DXF файла"""
        if not self.file_path:
            print("File path not specified")
            return
        
        try:
            import ezdxf
            doc = ezdxf.readfile(self.file_path)
            layers = doc.layers
            
            self.dxf_layers.clear()
            
            # Правильный способ итерации по слоям
            for layer in layers:
                item = self.dxf_layers.add()
                item.name = layer.dxf.name
                item.enabled = True
            
            if not self.dxf_layers:
                print("No layers found in DXF file")
            else:
                print(f"Loaded {len(self.dxf_layers)} layers")
                # Автоматически включаем фильтр при загрузке слоёв
                self.layers_filter_enabled = True
                
        except Exception as e:
            print(f"Error reading DXF file: {str(e)}")

    def update_layers_filter(self):
        """Обновить фильтр слоёв и переимпортировать DXF"""
        if not self.dxf_layers:
            print("No layers loaded to filter")
            return
        
        # Включаем фильтр при обновлении
        self.layers_filter_enabled = True
        print(f"Updated layers filter: {self.get_enabled_layers_count()}/{len(self.dxf_layers)} layers enabled")
        
        # Переимпортируем DXF с новыми настройками фильтра
        if self.file_path:
            self.DXF_OPEN()

    def remove_layer(self):
        """Удаление активного слоя из списка"""
        if 0 <= self.active_layer_index < len(self.dxf_layers):
            self.dxf_layers.remove(self.active_layer_index)
            if self.active_layer_index >= len(self.dxf_layers):
                self.active_layer_index = max(0, len(self.dxf_layers) - 1)

    def clear_layers(self):
        """Очистка всех слоёв"""
        self.dxf_layers.clear()
        self.layers_filter_enabled = False

    def get_enabled_layers(self):
        """Получение списка включенных слоёв"""
        if not self.layers_filter_enabled:
            return None  # None означает использовать все слои
        return [layer.name for layer in self.dxf_layers if layer.enabled]

    def add_viewer_nodes(self):
        """Добавление 5 узлов просмотра для разных типов данных"""
        loc = self.location
        tree = bpy.context.space_data.edit_tree
        links = tree.links

        # 1. Viewer Draw для vers_e и edgs (линии)
        if not self.outputs['vers_e'].is_linked and not self.outputs['edgs'].is_linked:
            vd1 = tree.nodes.new("SvViewerDrawMk4")
            vd1.location = loc + Vector((400, 300))
            links.new(self.outputs['vers_e'], vd1.inputs[0])  # verts
            links.new(self.outputs['edgs'], vd1.inputs[1])    # edges
            vd1.label = "DXF Lines"

        # 2. Viewer Draw для vers_p и pols (полигоны)
        if not self.outputs['vers_p'].is_linked and not self.outputs['pols'].is_linked:
            vd2 = tree.nodes.new("SvViewerDrawMk4")
            vd2.location = loc + Vector((400, 100))
            links.new(self.outputs['vers_p'], vd2.inputs[0])  # verts
            links.new(self.outputs['pols'], vd2.inputs[2])    # polygons
            vd2.label = "DXF Polygons"

        # 3. Viewer Draw для vers_annot и edgs_annot (аннотации)
        if not self.outputs['vers_annot'].is_linked and not self.outputs['edgs_annot'].is_linked:
            vd3 = tree.nodes.new("SvViewerDrawMk4")
            vd3.location = loc + Vector((400, -100))
            links.new(self.outputs['vers_annot'], vd3.inputs[0])  # verts
            links.new(self.outputs['edgs_annot'], vd3.inputs[1])  # edges
            vd3.label = "DXF Annotations"

        # 4. Index Viewer для vers_text и text (текст)
        if not self.outputs['vers_text'].is_linked and not self.outputs['text'].is_linked:
            vi = tree.nodes.new("SvIDXViewer28")
            vi.location = loc + Vector((400, -300))
            vi.draw_bg = True
            links.new(self.outputs['vers_text'], vi.inputs[0])  # vertices
            links.new(self.outputs['text'], vi.inputs[4])       # names/text
            vi.label = "DXF Text"

        # 5. Curve Viewer для curves (кривые)
        if not self.outputs['curves'].is_linked:
            vc = tree.nodes.new("SvCurveViewerDrawNode")
            vc.location = loc + Vector((400, -500))
            links.new(self.outputs['curves'], vc.inputs[0])     # curves
            vc.label = "DXF Curves"

        print("Added 5 viewer nodes for DXF import")

    def draw_buttons(self, context, layout):
        columna = layout.column(align=True)
        callback = 'node.sverchok_generic_callback_old'
        
        # Кнопка добавления узлов просмотра
        row = columna.row(align=True)
        row.label(text='')
        op = row.operator(callback, text="Add Viewers")
        op.fn_name = 'add_viewer_nodes'
        op.tree_name = self.id_data.name
        op.node_name = self.name
        
        # самая главная кнопка
        scale_y = 4.0 if self.prefs_over_sized_buttons else 1
        row = columna.row(align=True)
        row.scale_y = scale_y
        row.operator("node.dxf_import", text="I M P O R T   D X F")

        # Остальные кнопки
        columna.prop(self, 'implementation', text='curve_type')
        row = columna.row(align=True)
        row.prop(self, "scale", expand=False)
        row.prop(self, "resolution", expand=False)

        # Кнопки управления слоями
        row = columna.row(align=True)
        op = row.operator(callback, text="Load Layers")
        op.fn_name = 'get_dxf_layers'
        op.tree_name = self.id_data.name
        op.node_name = self.name


        # Кнопка очистки слоёв
        if self.dxf_layers:
            op = row.operator(callback, text="Clear Layers")
            op.fn_name = 'clear_layers'
            op.tree_name = self.id_data.name
            op.node_name = self.name
        else:
            row.label(text='no data')

        # Кнопка обновления фильтра слоёв
        if self.dxf_layers:

            scale_y = 2.0 if self.prefs_over_sized_buttons else 1
            row = columna.row(align=True)
            row.scale_y = scale_y
            op = row.operator(callback, text="Update Filter")
            op.fn_name = 'update_layers_filter'
            op.tree_name = self.id_data.name
            op.node_name = self.name

        # Список слоёв
        self.draw_layers_list(layout)

    def process(self):
        if self.file_path:
            self.DXF_OPEN()

    def DXF_OPEN(self):
        if not self.file_path:
            if self.inputs['path'].is_linked:
                fp = self.inputs['path'].sv_get()[0][0]
                self.file_path = fp
            else:
                return
        else:
            fp = self.file_path

        resolution = self.resolution
        scale = self.scale
        curve_degree = self.curve_degree
        
        # Получаем список включенных слоёв или None если фильтрация отключена
        enabled_layers = self.get_enabled_layers()

        # Передаем curlayer как список слоёв или None
        curves_out, knots_out, VE, EE, VP, PP, VA, EA, VT, TT = dxf_read(
            self, fp, resolution, scale, curve_degree, enabled_layers
        )

        self.outputs['vers_e'].sv_set(VE)
        self.outputs['edgs'].sv_set(EE)
        self.outputs['vers_p'].sv_set(VP)
        self.outputs['pols'].sv_set(PP)
        self.outputs['vers_annot'].sv_set(VA)
        self.outputs['edgs_annot'].sv_set(EA)
        self.outputs['vers_text'].sv_set(VT)
        self.outputs['text'].sv_set(TT)
        self.outputs['curves'].sv_set(curves_out)
        self.outputs['knots'].sv_set(knots_out)

class DXFImportOperator(bpy.types.Operator, SvGenericNodeLocator):
    bl_idname = "node.dxf_import"
    bl_label = "Import DXF"

    def sv_execute(self, context, node):
        if not node.file_path and node.inputs['path'].is_linked:
            file_path = node.inputs['path'].sv_get()[0][0]
            node.file_path = file_path

        if not node.file_path:
            self.report({'ERROR'}, "File path not specified!")
            return {'CANCELLED'}

        try:
            node.DXF_OPEN()
            self.report({'INFO'}, f"DXF imported from {node.file_path}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(SvDXFLayerCollection)
    bpy.utils.register_class(SVDXF_UL_LayersList)
    bpy.utils.register_class(SvDxfImportNode)
    bpy.utils.register_class(DXFImportOperator)

def unregister():
    bpy.utils.unregister_class(SvDxfImportNode)
    bpy.utils.unregister_class(DXFImportOperator)
    bpy.utils.unregister_class(SVDXF_UL_LayersList)
    bpy.utils.unregister_class(SvDXFLayerCollection)

if __name__ == "__main__":
    register()