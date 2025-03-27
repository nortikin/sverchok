import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import math
from sverchok.dependencies import ezdxf
if ezdxf != None:
    import ezdxf
from sverchok.core.socket_conversions import vectors_to_matrices as VM
from sverchok.data_structure import get_data_nesting_level, ensure_nesting_level
from sverchok.utils.dxf import LWdict, lineweights, linetypes
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.primitives import SvCircle
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.nodes.generator.basic_3pt_arc import generate_3PT_mode_1 as G3PA # G3PA(pts=None, num_verts=20, make_edges=False)
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
        self.outputs.new('SvVerticesSocket', 'points')
        self.outputs.new('SvCurveSocket', "curves")
        self.outputs.new('SvStringsSocket', "knots")
        self.outputs.new('SvCurveSocket', "dims")

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

        if not self.file_path:
            fp = self.inputs['path'].sv_get()[0][0]
            self.file_path = fp
        else:
            fp = self.file_path
        dxf = ezdxf.readfile(fp) # dxf file itself

        resolution = self.resolution # integers
        lifehack = 500 # for increase range int values to reduce than to floats. Seems like optimal maybe 50-100
        curve_degree = self.curve_degree # for nurbs output
        vers = []
        edges = []
        pols = []
        points_out = []
        curves_out = [] # for nurbs
        knots_out = [] # for nurbs
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

        # first of all, we need to delete lines and arcs data for dimensions, that shipped with dxf file.
        # this is made to purge garbage from dxf
        # maybe to gather first for separate layer...
        for i in dxf.query('Dimension'):
            #for a in dxf.blocks[i.dxf.geometry]:
            #    pass
            del dxf.blocks[i.dxf.geometry]
        def arcing(start,end,center,resolution):
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
            return ran
        # ARCS CIRCLES ELLIPSE
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
                    ran = arcing(start,end,center,resolution)
                    '''
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
                    # similar types grouped, but maybe it is disoriented little
                    '''
                elif typ == 'Circle':
                    #print()
                    #arc = SvCircle(radius=a.dxf.radius, center=[a.dxf.center.xyz])#matrix=VM(a.dxf.center.xyz))
                    #arc.to_nurbs()
                    #curves_out.append(arc)
                    #knots_out.append([])
                    ran = [i/lifehack for i in range(0,lifehack*360,max(1,int((lifehack*360)/resolution)))]
                    
                elif typ == 'Ellipse':
                    start  = a.dxf.start_param
                    end    = a.dxf.end_param
                    ran = [start + ((end-start)*i)/(lifehack*360) for i in range(0,lifehack*360,max(1,int(lifehack*360/resolution)))]
                for i in  a.vertices(ran): # line 43 is 35 in make 24 in import
                    cen = a.dxf.center.xyz
                    vers_.append([j for j in i])
                #vers_.append(a.dxf.)
                edges.append([[i,i+1] for i in range(len(vers_)-1)])
                vers.append(vers_)
                if typ == 'Circle':
                    edges[-1].append([len(vers_)-1,0])
                if typ == 'Ellipse' and (start <= 0.001 or end >= math.pi*4-0.001):
                    edges[-1].append([len(vers_)-1,0])

        # LINES
        vers_ = []
        edges_ = []
        for ind, a in enumerate(dxf.query('Line')):
            vers_.extend([a.dxf.start.xyz,a.dxf.end.xyz])
            edges_.extend([[ind*2,ind*2+1]])
        vers.append(vers_)
        edges.append(edges_)
        #print('L',vers_)

        # LWPOLYLINES
        for a in dxf.query('LWPOLYLINE'):
            #print('Блок', a.source_block_reference)
            points = a.get_points()
            edges_ = []
            vers_ = []
            bul_flag = False
            for i,p in enumerate(points): # points in line
                x, y, start_width, end_width, bulge = p
                if bulge == 0:
                    if i != 0:
                        edges_.append([i-1,i])
                elif not bul_flag:
                    bul_flag = True
                elif bul_flag:
                    prev = vers_[-1]
                    xt,yt = (x+prev[0])/2, (y+prev[1])/2
                    l = sqrt((x-prev[0])**2 + (y-prev[1])**2)
                    h = l/
                    bul_flag = False
                vers_.append([x,y,0])
                    
            if a.closed:
                edges_.append([i,0])
            vers.append(vers_)
            edges.append(edges_)

        '''
        # LWPOLYLINES
        for a in dxf.query('LWPOLYLINE'):
            print('Блок', a.source_block_reference)
            edges_ = []
            vers_ = []
            for i,p in enumerate(a.vertices()): # points in line
                vers_.append([p[0],p[1],0])
                if i != 0:
                    edges_.append([i-1,i])
            if a.closed:
                edges_.append([i,0])
            vers.append(vers_)
            edges.append(edges_)
        #print('LWPL',vers_)
        '''

        # Splines as NURBS curves
        for a in dxf.query('Spline'):
            count = a.dxf.n_fit_points
            vers_ = []
            edges_ = []
            
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

        # POINTS ALWAYS at the end because of non-edges and non-polygons
        for a in dxf.query('Point'):
            vers_.append(a.dxf.location.xyz)
        points_out.append(vers_)
        #print('ACE',vers_)
            
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
