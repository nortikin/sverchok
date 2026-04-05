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
from sverchok.utils.context_managers import sv_preferences
import subprocess
#from sverchok.settings import dxf_editor



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
    
    scale: bpy.props.FloatProperty(default=1000.0, min=1.0, max=200000.0, name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')
    
    do_block: bpy.props.BoolProperty(default=False, name='do_block')

    block_name: bpy.props.StringProperty(name='block name', default='Sverchok_block', update=updateNode)

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
        col.operator("node.dxf_edit", text="Edit DXF")
        col.prop(self, "scale", expand=False)
        col.prop(self, "text_scale", expand=False)
        col.prop(self, 'do_block', expand=True)
        if self.do_block:
            col.prop(self, 'block_name')

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
        #if self.inputs['path'].is_linked:
        fpath_ = self.inputs['path'].sv_get()
        #print(fpath_)
        if not fpath_[0][0].endswith('.dxf'):
            fpath_[0][0] = fpath_[0][0]+'.dxf'
        if self.inputs['dxf'].is_linked:
            dxf_ = ensure_nesting_level(self.inputs['dxf'].sv_get(),2)
        else:
            return

        #scal_ = self.inputs['scal'].sv_get()[0][0]
        #t_scal_ = self.inputs['t_scal'].sv_get()[0][0]
        #export(vers_,edges_,pols_,Tvers_,Ttext_,fpath_,d1_,d2_,info,dim1_,dim2_,adim1_,scal_,vleader_,leader_,t_scal_,dxf_)
        if self.do_block:
            export(fpath_,dxf_,scal=self.scale,t_scal=self.text_scale,info=info, do_block=self.block_name)
        else:
            export(fpath_,dxf_,scal=self.scale,t_scal=self.text_scale,info=info, do_block=False)



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

class DXFEditOperator(bpy.types.Operator):
    bl_idname = "node.dxf_edit"
    bl_label = "Edit DXF"

    def invoke(self, context, event):
        with sv_preferences() as prefs:
            app_name = prefs.dxf_editor
            
            if not app_name:
                # Показываем диалоговое окно с описанием проблемы
                return context.window_manager.invoke_props_dialog(self, width=500)
        
        # Если app_name есть, сразу выполняем
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        
        # 
        box = layout.box()
        col = box.column(align=True)
        col.label(text="DXF Editor not configured!", icon='ERROR')
        # 
        col = box.column(align=True)
        col.label(text="Propose to download ZCAD (nice and easy GPL3 freepascal CAD)")
        # 
        col.operator("wm.url_open", text="Download ZCAD (linux / windows) (GPL3 license)", icon='FILEBROWSER').url = "https://github.com/zamtmn/zcad"
        # 
        col.operator("node.dxf_select_editor", text="Select your DXF editor executable", icon='URL')
        # /home/ololo/git/zcad/cad/bin/zcad
        col.label(text="💡 Tip: After setting the editor, run this operator again.")

    def execute(self, context):
        node = context.node
        inputs = node.inputs

        file_path = inputs['path'].sv_get()[0][0]

        if not file_path:
            self.report({'ERROR'}, "File path not specified!")
            return {'CANCELLED'}
        if not file_path.endswith('.dxf'):
            file_path = file_path + '.dxf'

        try:
            with sv_preferences() as prefs:

                app_name = prefs.dxf_editor
                if not app_name:
                    self.report({'INFO'}, "Set first a external editor on Sverchok Preferences (User Preferences -> Add-ons)")
                    return {'CANCELLED'}
                #print(app_name,file_path)
                subprocess.Popen([app_name, file_path])
                return {'FINISHED'}
                
                self.report({'INFO'}, f"Opening {file_path}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

class DXFSelectEditorOperator(bpy.types.Operator):
    bl_idname = "node.dxf_select_editor"
    bl_label = "Select DXF Editor"
    bl_description = "Browse and select DXF editor executable"
    
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        
        try:
            with sv_preferences() as prefs:
                prefs.dxf_editor = self.filepath
                self.report({'INFO'}, f"DXF editor set to: {self.filepath}")
                return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save preferences: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(SvDxfExportNode)
    bpy.utils.register_class(DXFExportOperator)
    bpy.utils.register_class(DXFEditOperator)
    bpy.utils.register_class(DXFSelectEditorOperator)

def unregister():
    bpy.utils.unregister_class(DXFSelectEditorOperator)
    bpy.utils.unregister_class(DXFEditOperator)
    bpy.utils.unregister_class(DXFExportOperator)
    bpy.utils.unregister_class(SvDxfExportNode)

if __name__ == "__main__":
    register()