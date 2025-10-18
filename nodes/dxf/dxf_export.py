import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.dependencies import ezdxf
if ezdxf != None:
    import ezdxf
    from ezdxf.math import Vec3
    from ezdxf import colors
    from ezdxf import units
    from ezdxf.tools.standards import setup_dimstyle
from mathutils import Vector
from sverchok.data_structure import get_data_nesting_level, ensure_nesting_level
from sverchok.utils.dxf import export



class SvDxfExportNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfExportNode'
    bl_label = 'DXF Export'
    bl_icon = 'EXPORT'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    file_path: bpy.props.StringProperty(
        name="File Path",
        description="Path to save the DXF file",
        default="",
        subtype='FILE_PATH',
        update=updateNode
    )
    
    scale: bpy.props.FloatProperty(default=1.0,name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')

    def sv_init(self, context):
        '''
        self.inputs.new('SvVerticesSocket', 'verts')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvStringsSocket', 'pols')
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
        self.inputs.new('SvSvgSocket', 'dxf')

    def draw_buttons(self, context, layout):
        scale_y = 4.0 if self.prefs_over_sized_buttons else 1
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = scale_y
        row.operator("node.dxf_export", text="Export DXF")
        col.prop(self, "scale", expand=False)
        col.prop(self, "text_scale", expand=False)

    def process(self):
        pass  # Данные будут обрабатываться в операторе

    def DXF_SAVER(self, context):
        ''' ЗАГОТОВКА ДЛЯ БУДУЩИХ ОТДЕЛЬНЫХ УЗЛОВ
            DXF ЭКСПОРТА. УСТРОЙСТВО ПО АНАЛОГИИ
            С SVG УЗЛАМИ '''


        # MAKE DEFINITION BODY HERE #
        
        vers_, edges_, pols_, Tvers_, Ttext_, fpath_ = [],[],[],[],[],[]
        d1_, d2_, info, dim1_, dim2_,adim1_ = [],[],[],[],[],[]
        leader_, vleader_, dxf_ = [],[],[]

        '''
        if self.inputs['verts'].is_linked:
            vers_ = self.inputs['verts'].sv_get()
        #else: return {'FINISHED'}
        if self.inputs['edges'].is_linked:
            edges_ = self.inputs['edges'].sv_get()
        if self.inputs['pols'].is_linked:
            pols_ = self.inputs['pols'].sv_get()
        if self.inputs['Tvers'].is_linked:
            Tvers_ = self.inputs['Tvers'].sv_get()
        if self.inputs['Ttext'].is_linked:
            Ttext_ = self.inputs['Ttext'].sv_get()
        #else: return {'FINISHED'}
        if self.inputs['FaceData'].is_linked:
            d1_ = self.inputs['FaceData'].sv_get()
        if self.inputs['FDDescr'].is_linked:
            d2_ = self.inputs['FDDescr'].sv_get()
        if self.inputs['INFO'].is_linked:
            info = self.inputs['INFO'].sv_get()
        if self.inputs['dim1'].is_linked:
            dim1_ = self.inputs['dim1'].sv_get()
        if self.inputs['dim2'].is_linked:
            dim2_ = self.inputs['dim2'].sv_get()
        if self.inputs['adim'].is_linked:
            adim1_ = self.inputs['adim'].sv_get()
        if self.inputs['leader'].is_linked:
            leader_ = self.inputs['leader'].sv_get()
        if self.inputs['vleader'].is_linked:
            vleader_ = self.inputs['vleader'].sv_get()
            '''
        if self.inputs['path'].is_linked:
            fpath_ = self.inputs['path'].sv_get()
        if self.inputs['dxf'].is_linked:
            dxf_ = ensure_nesting_level(self.inputs['dxf'].sv_get(),2)

        #scal_ = self.inputs['scal'].sv_get()[0][0]
        #t_scal_ = self.inputs['t_scal'].sv_get()[0][0]
        #export(vers_,edges_,pols_,Tvers_,Ttext_,fpath_,d1_,d2_,info,dim1_,dim2_,adim1_,scal_,vleader_,leader_,t_scal_,dxf_)
        export(fpath_,dxf_,scal=self.scale,t_scal=self.text_scale)




class DXFExportOperator(bpy.types.Operator):
    bl_idname = "node.dxf_export"
    bl_label = "Export DXF"

    def execute(self, context):
        node = context.node
        inputs = node.inputs

        file_path = inputs['path'].sv_get()[0][0]

        if not file_path:
            self.report({'ERROR'}, "File path not specified!")
            return {'CANCELLED'}

        try:
            node.DXF_SAVER(context)
            #node.create_dxf(**data)
            self.report({'INFO'}, f"DXF saved to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SvDxfExportNode)
    bpy.utils.register_class(DXFExportOperator)

def unregister():
    bpy.utils.unregister_class(SvDxfExportNode)
    bpy.utils.unregister_class(DXFExportOperator)

if __name__ == "__main__":
    register()