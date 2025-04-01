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

    resolution: bpy.props.IntProperty(default=10, min=3, max=100,name='resolution for arcs',
        update=updateNode)

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale',
        update=updateNode)

    def sv_init(self, context):
        '''
        self.inputs.new('SvVerticesSocket', 'Tvers')
        self.inputs.new('SvStringsSocket', 'Ttext')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvStringsSocket', 'FDDescr')
        self.inputs.new('SvStringsSocket', 'INFO')
        self.inputs.new('SvVerticesSocket', 'dim1')
        self.inputs.new('SvVerticesSocket', 'dim2')
        self.inputs.new('SvVerticesSocket', 'adim')
        self.inputs.new('SvStringsSocket', 'scal').prop_name = 'scale'
        self.inputs.new('SvStringsSocket', 'leader')
        self.inputs.new('SvVerticesSocket', 'vleader')
        self.inputs.new('SvStringsSocket', 't_scal').prop_name = 'text_scale'
        '''
        self.inputs.new('SvFilePathSocket', 'path').prop_name = 'file_path'
        #self.outputs.new('SvSvgSocket', 'dxf')
        self.outputs.new('SvVerticesSocket', 'verts')
        self.outputs.new('SvStringsSocket', 'edges')
        self.outputs.new('SvStringsSocket', 'pols')
        self.outputs.new('SvCurveSocket', "curves")
        self.outputs.new('SvStringsSocket', "knots")

    def draw_buttons(self, context, layout):
        layout.operator("node.dxf_import", text="Import DXF")
        layout.prop(self, 'implementation', text='')
        layout.prop(self, "scale", expand=False)
        layout.prop(self, "text_scale", expand=False)
        layout.prop(self, "resolution", expand=False)

    def process(self):
        if self.file_path:
            self.DXF_OPEN()

    def DXF_OPEN(self):
        ''' Проблема окружностей в импорте dxf блендера решается этим узлом.
            DXF ИМПОРТ. '''

        resolution = self.resolution
        if not self.file_path:
            fp = self.inputs['path'].sv_get()[0][0]
            self.file_path = fp
        else:
            fp = self.file_path
        dxf = ezdxf.readfile(fp)
        lifehack = 500 # for increase range int values to reduce than to floats. Seems like optimal maybe 50-100
        vers = []
        edges = []
        pols = []
        #a = dxf.query('Arc')[1]
            #arc = sverchok.utils.curve.primitives.SvCircle
            #arc.to_nurbs()
        # similar types grouped, but maybe it is disoriented little
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
        pointered = ['Arc','Circle','Ellipse']
        for typ in pointered:
            for a in dxf.query(typ):
                print('Блок', a.source_block_reference)
                vers_ = []
                center = a.dxf.center
                #radius = a.dxf.radius
                if typ == 'Arc':
                    start  = int(a.dxf.start_angle)
                    end    = int(a.dxf.end_angle)
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
                elif typ == 'Circle':
                    ran = [i/lifehack for i in range(0,lifehack*360,max(1,int((lifehack*360)/resolution)))]
                elif typ == 'Ellipse':
                    start  = a.dxf.start_param
                    end    = a.dxf.end_param
                    ran = [start + ((end-start)*i)/(lifehack*360) for i in range(0,lifehack*360,max(1,int(lifehack*360/resolution)))]
                for i in  a.vertices(ran): # line 43 is 35 in make 24 in import
                    cen = a.dxf.center.xyz
                    vers_.append([j for j in i])
                #vers_.append(a.dxf.)
                vers.append(vers_)
                edges.append([[i,i+1] for i in range(len(vers_)-1)])
                if typ == 'Circle':
                    edges[-1].append([len(vers_)-1,0])
                if typ == 'Ellipse' and (start <= 0.001 or end >= math.pi*4-0.001):
                    edges[-1].append([len(vers_)-1,0])
        for a in dxf.query('Point'):
            vers_.append(a.dxf.location.xyz)
        #print('ACE',vers_)
        vers_ = []
        for a in dxf.query('Line'):
            vers_.append([a.dxf.start.xyz,a.dxf.end.xyz])
            edges.append([[0,1]])
        #print('L',vers_)
        vers.extend(vers_)
        for a in dxf.query('LWPOLYLINE'):
            #arc_points(start, end, bulge, num_points=3)
            #print('Блок', a.source_block_reference)
            edges_ = []
            vers_ = []

            # вариант от DeepSeek
            points = a.get_points()  # Получаем вершины
            #bulges = a.bulge
            vertices = list(a.vertices())
            for i, (x, y, _, _, bulge) in enumerate(points):
                # Добавляем точки сегмента (линия или дуга)
                if bulge != 0:
                    segment_points = arc_points((x,y,0), (vertices[i+1][0],vertices[i+1][1],0), bulge)
                    edges_.extend([[len(vers_)+k-1,len(vers_)+k] for k in range(len(segment_points))])
                else:
                    segment_points = [(x,y,0)]
                    if i != 0:
                        edges_.append([len(vers_)-1,len(vers_)])
                vers_.extend(segment_points)
            # вариант от DeepSeek

            '''
            for i,p in enumerate(a.vertices()): # points in line
                vers_.append([p[0],p[1],0])
                if i != 0:
                    edges_.append([i-1,i])
            '''
            vers.append(vers_)
            edges.append(edges_)
        #print('LWPL',vers_)
        # Splines as NURBS curves
        vers_ = []
        curve_degree = self.curve_degree
        curves_out = []
        knots_out = []

        for a in dxf.query('Spline'):
            #print('Блок', a.source_block_reference)
            control_points = a.control_points
            n_total = len(control_points)
            # Set knot vector
            if a.closed:
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
            if a.closed:
                u_min = curve_knotvector[degree]
                u_max = curve_knotvector[-degree-1]
                new_curve.u_bounds = u_min, u_max
            else:
                u_min = min(curve_knotvector)
                u_max = max(curve_knotvector)
                new_curve.u_bounds = (u_min, u_max)
            curves_out.append(new_curve)
            knots_out.append(curve_knotvector)
        
            
        self.outputs['verts'].sv_set(vers)
        self.outputs['edges'].sv_set(edges)
        if pols:
            self.outputs['pols'].sv_set(pols)
        if curves_out:
            self.outputs['curves'].sv_set(curves_out)
            self.outputs['knots'].sv_set(knots_out)




class DXFImportOperator(bpy.types.Operator):
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
