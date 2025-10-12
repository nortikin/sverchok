import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import math
import ezdxf
from sverchok.data_structure import get_data_nesting_level, ensure_nesting_level
from sverchok.utils.dxf import LWdict, lineweights, linetypes, arc_points
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.dependencies import geomdl
from sverchok.dependencies import FreeCAD


def dxf_geometry_loader(self, entity, curve_degree, resolution, lifehack, scale):
    ''' dxf_geometry_loader(entity) ВОЗВРАЩАЕТ вершины, рёбра, полигоны и кривые всей геометрии, что находит у сущности'''
    typ = entity.dxftype().lower()
    #print('!!! type element:',typ)
    vers, edges, pols, VT, TT, curves_out, knots_out = [], [], [], [], [], [], []
    pointered = ['arc','circle','ellipse']
    if typ in pointered:
        vers_ = []
        center = entity.dxf.center*scale
        #radius = a.dxf.radius
        if typ == 'arc':
            start  = int(entity.dxf.start_angle)
            #print('start angle:', start)
            end    = int(entity.dxf.end_angle)
            #print('end angle:', end)
            if start > end:
                start1 = (360-start)
                overall = start1+end
                resolution_arc = max(3,int(resolution*(overall/360))) # redefine resolution for partially angles
                step = max(1,int((start1+end)/resolution_arc))
                ran = [i/lifehack for i in range(lifehack*start,lifehack*360,lifehack*step)]
                ran.extend([i/lifehack for i in range(0,lifehack*end,lifehack*step)])
            else:
                start1 = start
                overall = end-start1
                resolution_arc = max(3,int(resolution*(overall/360))) # redefine resolution for partially angles
                ran = [i/lifehack for i in range(lifehack*start,lifehack*end,max(1,int(lifehack*(end-start)/resolution_arc)))]
        elif typ == 'circle':
            ran = [i/lifehack for i in range(0,lifehack*360,max(1,int((lifehack*360)/resolution)))]
        elif typ == 'ellipse':
            start  = entity.dxf.start_param
            end    = entity.dxf.end_param
            ran = [start + ((end-start)*i)/(lifehack*360) for i in range(0,lifehack*360,max(1,int(lifehack*360/resolution)))]
        for i in entity.vertices(ran): # line 43 is 35 in make 24 in import
            cen = entity.dxf.center.xyz #*scale
            vers_.append([j*scale for j in i])

            vers.append(vers_)
            edges.append([[i,i+1] for i in range(len(vers_)-1)])
        if typ == 'circle':
            edges[-1].append([len(vers_)-1,0])
        if typ == 'ellipse' and (start <= 0.001 or end >= math.pi*4-0.001):
            edges[-1].append([len(vers_)-1,0])

    if typ == 'point':
        mu = 0.2
        ver = [i*scale for i in entity.dxf.location.xyz]
        ver_ = [ ver,
                [-scale*mu+ver[0],-scale*mu+ver[1],ver[2]],
                [-scale*mu+ver[0],scale*mu+ver[1],ver[2]],
                [scale*mu+ver[0],scale*mu+ver[1],ver[2]],
                [scale*mu+ver[0],-scale*mu+ver[1],ver[2]],
                ]
        vers.append(ver_)
        edges.append([[1,3],[2,4]])

    if typ == 'line':
        edges.append([[0,1]])
        vers.append([[i*scale for i in entity.dxf.start.xyz],[i*scale for i in entity.dxf.end.xyz]])
    print(typ)
    if typ in ["3dface", "solid","polymesh", "polyface", "polyline"]:
        print('3Д попалась ========', entity.faces)
    if 'dimension' in typ:
        edges.append([[0,1]])
        if entity.dxf.dimtype == 32:
            mes = round(entity.dxf.defpoint2.distance(entity.dxf.defpoint3),5)
            vers.append([[i*scale for i in entity.dxf.defpoint2.xyz],[i*scale for i in entity.dxf.defpoint3.xyz]])
        else:
            mes = round(entity.dxf.defpoint.distance(entity.dxf.defpoint4),5)
            vers.append([[i*scale for i in entity.dxf.defpoint.xyz],[i*scale for i in entity.dxf.defpoint4.xyz]])
        VT.append([[i*scale for i in entity.dxf.text_midpoint.xyz]])
        TT.append([[mes]])

    if typ == 'lwpolyline':
        edges_ = []
        vers_ = []
        # вариант от DeepSeek
        points = entity.get_points()  # Получаем вершины
        vertices = list(entity.vertices())
        #resolution_arc = max(3,int(resolution*(overall/360)))
        print('Lwpolyline')
        for i, (x, y, _, _, bulge) in enumerate(points):
            # Добавляем точки сегмента (линия или дуга)
            print(bulge, i)
            if bulge !=0 and i<(len(vertices)-1):
                segment_points = arc_points((x*scale,y*scale,0), (vertices[i+1][0]*scale,vertices[i+1][1]*scale,0), bulge, resolution)
                edges_.extend([[len(vers_)+k+1,len(vers_)+k] for k in range(len(segment_points)-1)])
                #print('!!! bulge ',bulge, 'index', i, len(vers_), 'points',len(points), len(vertices))
            else:
                segment_points = [(x*scale,y*scale,0)]
                if i < len(vertices)-1:
                    edges_.append([len(vers_)+1,len(vers_)])
            vers_.extend(segment_points)
        if entity.is_closed:
            edges_.append([len(vers_)-1,0])
        # вариант от DeepSeek
        vers.append(vers_)
        edges.append(edges_)
    #print('LWPL',vers_)

    # Splines as NURBS curves
    vers_ = []
    if typ == 'spline':
        #print('Блок', a.source_block_reference)
        control_points = entity.control_points
        n_total = len(control_points)
        # Set knot vector
        if entity.closed:
            self.debug("N: %s, degree: %s", n_total, curve_degree)
            knots = list(range(n_total + curve_degree + 1))
        else:
            knots = sv_knotvector.generate(curve_degree, n_total)

        curve_weights = [1 for i in control_points]
        self.debug('Auto knots: %s', knots)
        curve_knotvector = knots

        # Nurbs curve
        new_curve = SvNurbsCurve.build(self.implementation, curve_degree, curve_knotvector, control_points, curve_weights, normalize_knots = True)

        curve_knotvector = new_curve.get_knotvector().tolist()
        if entity.closed:
            u_min = curve_knotvector[degree]
            u_max = curve_knotvector[-degree-1]
            new_curve.u_bounds = u_min, u_max
        else:
            u_min = min(curve_knotvector)
            u_max = max(curve_knotvector)
            new_curve.u_bounds = (u_min, u_max)
        curves_out.append(new_curve)
        knots_out.append(curve_knotvector)
    #print('^$#^%^#$%',typ)
    if typ == 'mtext' or typ == 'text':
        #print([(k.dxf.insert, k.text) for k in i.entitydb.query('Mtext')])
        VT.append([[i*scale for i in entity.dxf.insert.xyz]])
        TT.append([[entity.text]])
        #print(VT,TT)
    return vers, edges, pols, curves_out, knots_out, VT, TT


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

    def draw_buttons(self, context, layout):
        layout.operator("node.dxf_import", text="Import DXF")
        layout.prop(self, 'implementation', text='curve_type')
        layout.prop(self, "scale", expand=False)
        #layout.prop(self, "text_scale", expand=False)
        layout.prop(self, "resolution", expand=False)

    def process(self):
        if self.file_path:
            self.DXF_OPEN()

    def DXF_OPEN(self):
        ''' Проблема окружностей в импорте dxf блендера решается этим узлом.
            DXF ИМПОРТ. '''

        if not self.file_path:
            fp = self.inputs['path'].sv_get()[0][0]
            self.file_path = fp
        else:
            fp = self.file_path

        resolution = self.resolution
        scale = self.scale
        dxf = ezdxf.readfile(fp)
        lifehack = 500 # for increase range int values to reduce than to floats. Seems like optimal maybe 50-100
        curves_out = []
        knots_out = []
        curve_degree = self.curve_degree
        VE, EE = [], []
        VP, PP = [], []
        VA, EA = [], []
        VT, TT = [], []

        # all_types = {e.dxftype() for e in doc.modelspace()} # все типы в файле, чтобы не тыкаться 
        # во имя отделения размеров и выносок!
        ANNOTATION_TYPES = [
            "DIMENSION", "LEADER", "MLEADER", "ARC_DIMENSION",
            "TEXT", "MTEXT", "ARC_DIMENSION", "DIAMETER_DIMENSION",
            "RADIAL_DIMENSION", 
        ]
        SERVICE_TYPES = [
            "ATTRIB", "ATTDEF", "HATCH", "DIMENSION_STYLE",
            "VIEWPORT", "IMAGE", "XLINE", "RAY", "TABLE", "TOLERANCE"
        ]
        GEOMETRY_TYPES = [
            "LINE", "CIRCLE", "ARC", "POLYLINE", "LWPOLYLINE", "SPLINE",
            "ELLIPSE", "POINT", "VERTEX", "3DFACE", "SOLID", "3DFACE",
            "POLYMESH", "POLYFACE"
        ]
        #pure_geometry = []
        #annotation_geometry = []
        #servise_geometry = []
        #dimension_handles = {dim.dxf.handle for dim in dxf.query("DIMENSION")}

        for entity in dxf.modelspace():
            if entity.dxftype() in ANNOTATION_TYPES:
                vers, edges, pols, curves, knots, VT_, TT_ = dxf_geometry_loader(self, entity, curve_degree, resolution, lifehack, scale)
                if vers:
                    VA.extend(vers)
                    EA.extend(edges)
                if VT_:
                    VT.extend(VT_)
                    TT.extend(TT_)
            elif entity.dxftype() in GEOMETRY_TYPES:
                vers, edges, pols, curves, knots_out, VT_, TT_ = dxf_geometry_loader(self, entity, curve_degree, resolution, lifehack, scale)
                if edges:
                    VE.extend(vers)
                    EE.extend(edges)
                elif pols:
                    VP.extend(vers)
                    PP.extend(pols)
                if curves:
                    curves_out.extend(curves)
                    knots_out.extend(knots)
            elif entity.dxftype() in SERVICE_TYPES:
                continue

        self.outputs['vers_e'].sv_set(VE)
        self.outputs['edgs'].sv_set(EE)
        if pols:
            self.outputs['vers_p'].sv_set(VP)
            self.outputs['pols'].sv_set(PP)
        if VA:
            self.outputs['vers_annot'].sv_set(VA)
            self.outputs['edgs_annot'].sv_set(EA)
        if VT:
            self.outputs['vers_text'].sv_set(VT)
            self.outputs['text'].sv_set(TT)
        if curves_out:
            self.outputs['curves'].sv_set(curves_out)
            self.outputs['knots'].sv_set(knots_out)
        # типы, которые не надо грузить:
        # DIMENSION	Линейный/угловой/радиальный размер LEADER	Выноска (обычная) MLEADER	Мультивыноска (современный стиль)
        # ARC_DIMENSION	Угловой размер дуги DIAMETER_DIMENSION	Размер диаметра RADIAL_DIMENSION	Радиальный размер
        # также отделить:
        # TEXT	Однострочный текст MTEXT	Многострочный текст ATTRIB	Атрибут блока ATTDEF	Определение атрибута
        # HATCH	Штриховка DIMENSION_STYLE	Стиль размера (не графический объект)
        # и совсем не нужны:
        # VIEWPORT	Видовой экран (в листах) IMAGE	Вставленное изображение XLINE	Бесконечная линия (вспомогательная) 
        # RAY	Луч (вспомогательная линия) TABLE	Таблица TOLERANCE	Допуск (GD&T)
        
        # типы, которые надо грузить:
        # LINE (линия) CIRCLE (окружность) ARC (дуга) POLYLINE (полилиния) LWPOLYLINE (легковесная полилиния) SPLINE (сплайн) 
        # ELLIPSE (эллипс) POINT (точка) 3DFACE (3D-грань) SOLID (залитый многоугольник) REGION (регион) BODY (3D-тело)
        
            

class DXFImportOperator(bpy.types.Operator):
    ''' DXF Import from file. Gathering lines, polylines, circles, arcs, ellipses '''
    bl_idname = "node.dxf_import"
    bl_label = "Import DXF"

    def execute(self, context):
        node = context.node
        inputs = node.inputs

        file_path = inputs['path'].sv_get()[0][0]
        node.file_path = file_path

        if not file_path:
            self.report({'ERROR'}, "File path not specified!")
            return {'CANCELLED'}

        try:
            node.DXF_OPEN()
            #node.create_dxf(**data)
            self.report({'INFO'}, f"DXF opened as {file_path}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SvDxfImportNode)
    bpy.utils.register_class(DXFImportOperator)

def unregister():
    bpy.utils.unregister_class(SvDxfImportNode)
    bpy.utils.unregister_class(DXFImportOperator)

if __name__ == "__main__":
    register()


'''
• Line
• Point
• 3DFace
• Polyline (3D)
• Vertex (3D)
• Polymesh
• Polyface
• Viewport
---
• Circle
• Arc
• Solid
• Trace
• Text
• Attrib
• Attdef
• Shape
• Insert
• Polyline (2D)
• Vertex (2D)
• LWPolyline
• Hatch
• Image

entry.graphic_properties() - графические свойства, цвет, толщина, слой, тип линий
entry.has_hyperlink()  -->  get_hyperlink()
entry.source_block_reference --> принадлежность к блоку
'''
# filter dimensions
'''
import ezdxf
dxf = ezdxf.readfile('/home/ololo/Documents/BLENDER/SVERCHOK/Blends4.2/dxf/manual.dxf')
for i in dxf.blocks:
    print([dir(k.dxf) for k in i.entitydb.query('Dimension')]) 15 размеров
for i in dxf.blocks: print([k for k in i.query()]) выдаёт первым блоком все элементы чертежа, второй блок пустой, затем солиды и полилини
block: любой блок
    ['__class__', '__contains__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', 
    '__format__', '__ge__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', 
    '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', 
    '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', 
    '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_add_acis_entity', '_add_quadrilateral', 
    '_four_points', '_make_multileader', '_safe_dimstyle', 'add_3dface', 'add_3dsolid', 'add_aligned_dim', 
    'add_angular_dim_2l', 'add_angular_dim_3p', 'add_angular_dim_arc', 'add_angular_dim_cra', 'add_arc', 
    'add_arc_dim_3p', 'add_arc_dim_arc', 'add_arc_dim_cra', 'add_arrow', 'add_arrow_blockref', 'add_attdef', 
    'add_auto_blockref', 'add_blockref', 'add_body', 'add_cad_spline_control_frame', 'add_circle', 
    'add_diameter_dim', 'add_diameter_dim_2p', 'add_ellipse', 'add_entity', 'add_extruded_surface', 
    'add_foreign_entity', 'add_hatch', 'add_helix', 'add_image', 'add_leader', 'add_line', 'add_linear_dim', 
    'add_lofted_surface', 'add_lwpolyline', 'add_mesh', 'add_mline', 'add_mpolygon', 'add_mtext', 
    'add_mtext_dynamic_auto_height_columns', 'add_mtext_dynamic_manual_height_columns', 'add_mtext_static_columns', 
    'add_multi_point_linear_dim', 'add_multileader_block', 'add_multileader_mtext', 'add_open_spline', 
    'add_ordinate_dim', 'add_ordinate_x_dim', 'add_ordinate_y_dim', 'add_point', 'add_polyface', 
    'add_polyline2d', 'add_polyline3d', 'add_polymesh', 'add_radius_dim', 'add_radius_dim_2p', 
    'add_radius_dim_cra', 'add_rational_spline', 'add_ray', 'add_region', 'add_revolved_surface', 'add_shape', 
    'add_solid', 'add_spline', 'add_spline_control_frame', 'add_surface', 'add_swept_surface', 'add_text', 
    'add_trace', 'add_underlay', 'add_wipeout', 'add_xline', 'attdefs', 'base_point', 'block', 'block_record', 
    'block_record_handle', 'can_explode', 'delete_all_entities', 'delete_entity', 'destroy', 'doc', 'dxf', 
    'dxfversion', 'endblk', 'entities_in_redraw_order', 'entity_space', 'entitydb', 'get_attdef', 'get_attdef_text', 
    'get_const_attdefs', 'get_extension_dict', 'get_redraw_order', 'get_sortents_table', 'groupby', 'has_attdef', 
    'has_non_const_attdef', 'is_active_paperspace', 'is_alive', 'is_any_layout', 'is_any_paperspace', 
    'is_block_layout', 'is_modelspace', 'layout_key', 'move_to_layout', 'name', 'new_entity', 'purge', 
    'query', 'rename', 'scale_uniformly', 'set_redraw_order', 'units', 'unlink_entity', 'update_block_flags']
k: размер
    ['ALIGNED', 'ANGULAR', 'ANGULAR_3P', 'ARC', 'DEFAULT_ATTRIBS', 'DIAMETER', 'DXFATTRIBS', 
    'DXFTYPE', 'LINEAR', 'MIN_DXF_VERSION_FOR_EXPORT', 'ORDINATE', 'ORDINATE_TYPE', 'RADIUS', 
    'USER_LOCATION_OVERRIDE', '__annotations__', '__class__', '__delattr__', '__dict__', 
    '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', 
    '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', 
    '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__referenced_blocks__', '__repr__', 
    '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__virtual_entities__', '__weakref__', 
    '_block_content', '_new_compound_entity', '_silent_kill', '_transform_block_content', 'appdata', 
    'append_reactor_handle', 'audit', 'copy', 'copy_data', 'copy_to_layout', 'del_dxf_attrib', 
    'del_source_block_reference', 'del_source_of_copy', 'destroy', 'dim_style_attr_handles_to_names', 
    'dim_style_attr_names_to_handles', 'dim_style_attributes', 'dimtype', 'discard_app_data', 
    'discard_empty_extension_dict', 'discard_extension_dict', 'discard_reactor_handle', 'discard_xdata', 
    'discard_xdata_list', 'doc', 'dxf', 'dxf_attrib_exists', 'dxfattribs', 'dxftype', 'explode', 
    'export_acdb_entity', 'export_base_class', 'export_dxf', 'export_entity', 'export_xdata', 
    'extension_dict', 'from_text', 'get_acad_dstyle', 'get_app_data', 'get_dim_style', 'get_dxf_attrib', 
    'get_extension_dict', 'get_flag_state', 'get_geometry_block', 'get_hyperlink', 'get_layout', 
    'get_measurement', 'get_reactors', 'get_xdata', 'get_xdata_list', 'graphic_properties', 
    'has_app_data', 'has_dxf_attrib', 'has_extension_dict', 'has_hyperlink', 'has_reactors', 
    'has_source_block_reference', 'has_xdata', 'has_xdata_list', 'is_alive', 'is_bound', 'is_copy', 
    'is_dimensional_constraint', 'is_post_transform_required', 'is_supported_dxf_attrib', 
    'is_transparency_by_block', 'is_transparency_by_layer', 'is_virtual', 'link_entity', 'load',
    'load_dxf_attribs', 'load_tags', 'map_resources', 'move_to_layout', 'new', 'new_extension_dict', 
    'notify', 'ocs', 'origin_of_copy', 'override', 'post_bind_hook', 'post_load_hook', 'post_new_hook', 
    'post_transform', 'preprocess_export', 'proxy_graphic', 'reactors', 'register_resources', 
    'remove_dependencies', 'render', 'replace_xdata_list', 'rgb', 'rotate_axis', 'rotate_x', 'rotate_y', 
    'rotate_z', 'scale', 'scale_uniform', 'set_acad_dstyle', 'set_app_data', 'set_dxf_attrib', 
    'set_flag_state', 'set_hyperlink', 'set_owner', 'set_reactors', 'set_source_block_reference', 
    'set_source_of_copy', 'set_xdata', 'set_xdata_list', 'setup_app_data', 'shallow_copy', 
    'source_block_reference', 'source_of_copy', 'transform', 'translate', 'transparency', 
    'unlink_from_layout', 'update_dxf_attribs', 'update_handle', 'uuid', 'virtual_block_content', 
    'virtual_entities', 'xdata']
line:
    ['DEFAULT_ATTRIBS', 'DXFATTRIBS', 'DXFTYPE', 'MIN_DXF_VERSION_FOR_EXPORT', '__annotations__', 
    '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', 
    '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', 
    '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', 
    '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_new_compound_entity', 
    '_silent_kill', 'appdata', 'append_reactor_handle', 'audit', 'copy', 'copy_data', 'copy_to_layout', 
    'del_dxf_attrib', 'del_source_block_reference', 'del_source_of_copy', 'destroy', 'discard_app_data', 
    'discard_empty_extension_dict', 'discard_extension_dict', 'discard_reactor_handle', 'discard_xdata', 
    'discard_xdata_list', 'doc', 'dxf', 'dxf_attrib_exists', 'dxfattribs', 'dxftype', 'export_acdb_entity', 
    'export_base_class', 'export_dxf', 'export_entity', 'export_xdata', 'extension_dict', 'from_text', 
    'get_app_data', 'get_dxf_attrib', 'get_extension_dict', 'get_flag_state', 'get_hyperlink', 
    'get_layout', 'get_reactors', 'get_xdata', 'get_xdata_list', 'graphic_properties', 'has_app_data', 
    'has_dxf_attrib', 'has_extension_dict', 'has_hyperlink', 'has_reactors', 'has_source_block_reference', 
    'has_xdata', 'has_xdata_list', 'is_alive', 'is_bound', 'is_copy', 'is_post_transform_required', 
    'is_supported_dxf_attrib', 'is_transparency_by_block', 'is_transparency_by_layer', 'is_virtual', 
    'link_entity', 'load', 'load_dxf_attribs', 'load_tags', 'map_resources', 'move_to_layout', 'new', 
    'new_extension_dict', 'notify', 'ocs', 'origin_of_copy', 'post_bind_hook', 'post_load_hook', 
    'post_new_hook', 'post_transform', 'preprocess_export', 'proxy_graphic', 'reactors', 
    'register_resources', 'remove_dependencies', 'replace_xdata_list', 'rgb', 'rotate_axis', 
    'rotate_x', 'rotate_y', 'rotate_z', 'scale', 'scale_uniform', 'set_app_data', 'set_dxf_attrib', 
    'set_flag_state', 'set_hyperlink', 'set_owner', 'set_reactors', 'set_source_block_reference', 
    'set_source_of_copy', 'set_xdata', 'set_xdata_list', 'setup_app_data', 'shallow_copy', 
    'source_block_reference', 'source_of_copy', 'transform', 'translate', 'transparency', 
    'unlink_from_layout', 'update_dxf_attribs', 'update_handle', 'uuid', 'xdata']
line.dxf:
    ['__class__', '__deepcopy__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', 
    '__format__', '__ge__', '__getattr__', '__getattribute__', '__getstate__', '__gt__', '__hash__', 
    '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', 
    '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', 
    '__subclasshook__', '__weakref__', '_entity', '_export_dxf_attribute_optional', 
    'all_existing_dxf_attribs', 'color', 'copy', 'discard', 'dxf_default_value', 'dxfattribs', 
    'dxftype', 'end', 'export_dxf_attribs', 'get', 'get_default', 'handle', 'hasattr', 
    'is_supported', 'layer', 'linetype', 'lineweight', 'owner', 'reset_handles', 'rewire', 
    'set', 'start', 'unprotected_set', 'update']
k.dxf: dimention.dxf
    ['__class__', '__deepcopy__', '__delattr__', '__dict__', '__dir__', 
    '__doc__', '__eq__', '__format__', '__ge__', '__getattr__', '__getattribute__', 
    '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', 
    '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', 
    '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 
    '_entity', '_export_dxf_attribute_optional', 'all_existing_dxf_attribs', 
    'attachment_point', 'color', 'copy', 'defpoint', 'defpoint4', 'dimstyle', 'dimtype', 
    'discard', 'dxf_default_value', 'dxfattribs', 'dxftype', 'export_dxf_attribs', 
    'extrusion', 'geometry', 'get', 'get_default', 'handle', 'hasattr', 'is_supported', 
    'layer', 'leader_length', 'line_spacing_style', 'linetype', 'lineweight', 'owner', 
    'reset_handles', 'rewire', 'set', 'text_midpoint', 'text_rotation', 'unprotected_set', 'update']'''
