import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from ezdxf.math import Vec3
from mathutils import Vector
import ezdxf
from ezdxf import colors
from ezdxf import units
from ezdxf.tools.standards import setup_dimstyle
from mathutils import Vector
from sverchok.data_structure import get_data_nesting_level, ensure_nesting_level
from sverchok.utils.dxf import LWdict, lineweights, linetypes



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
    
    scale: bpy.props.FloatProperty(default=1.0,name='scale',
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

    def draw_buttons(self, context, layout):
        layout.operator("node.dxf_import", text="Import DXF")
        layout.prop(self, "scale", expand=False)
        layout.prop(self, "text_scale", expand=False)
        layout.prop(self, "resolution", expand=False)

    def process(self):
        if self.file_path:
            self.DXF_OPEN()

    def DXF_OPEN(self):
        ''' ЗАГОТОВКА ДЛЯ БУДУЩИХ ОТДЕЛЬНЫХ УЗЛОВ
            DXF ИМПОРТА. '''

        resolution = self.resolution
        if not self.file_path:
            fp = self.inputs['path'].sv_get()[0][0]
            self.file_path = fp
        else:
            fp = self.file_path
        dxf = ezdxf.readfile(fp)
        lifehack = 50
        vers = []
        edges = []
        pols = []
        #a = dxf.query('Arc')[1]
            #arc = sverchok.utils.curve.primitives.SvCircle
            #arc.to_nurbs()
        pointered = ['Arc','Circle','Ellipse']
        for typ in pointered:
            for a in dxf.query(typ):
                vers_ = []
                center = a.dxf.center
                radius = a.dxf.radius
                start  = int(a.dxf.start_angle)
                end    = int(a.dxf.end_angle)
                if start > end:
                    start1 = (360-start)
                    step = int((start1+end)/resolution)
                    ran = [i for i in range(start,360,step)]
                    ran.extend([i for i in range(0,end,step)])
                else:
                    #ran = [i/lifehack for i in range(start,lifehack*end,int((lifehack*end)/resolution))]
                    ran = [i for i in range(start,end,int((end-start)/resolution))]
                print('!!!!!!',start,end)
                print(ran)
                for i in  a.vertices(ran): # line 43 is 35 in make 24 in import
                    cen = a.dxf.center.xyz
                    vers_.append([j for j in i])
                #vers_.append(a.dxf.)
                vers.append(vers_)
                edges.append([[i,i+1] for i in range(len(vers_)-1)])
                #edges[-1].append([len(vers_)-1,0])
        vers_ = []
        for a in dxf.query('Line'):
            vers_.append([a.dxf.start.xyz,a.dxf.end.xyz])
            edges.append([[0,1]])
        vers.extend(vers_)
            
        self.outputs['verts'].sv_set(vers)
        self.outputs['edges'].sv_set(edges)
        if pols:
            self.outputs['pols'].sv_set(pols)




class DXFImportOperator(bpy.types.Operator):
    bl_idname = "node.dxf_import"
    bl_label = "Import DXF"

    def execute(self, context):
        node = context.node
        inputs = node.inputs

        file_path = inputs['path'].sv_get()[0][0]

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
