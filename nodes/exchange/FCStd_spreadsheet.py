from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvFCStdSpreadsheetNode', 'SvFCStdSpreadsheetNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy
    from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.logging import info

    class SvFCStdSpreadsheetNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Read FreeCAD file
        Tooltip: Read/write FCStd Spreadsheets from a .FCStd file 
        """
        bl_idname = 'SvFCStdSpreadsheetNode'
        bl_label = 'Read/write FCStd Spreadsheets'
        bl_icon = 'IMPORT'
        solid_catergory = "Outputs"
        

        write_parameter : BoolProperty(name="write_parameter", default=False)
  
        selected_label : StringProperty(default='Spreadsheet')
        selected_sheet : StringProperty(default='',update = updateNode)

        selected_par_label : StringProperty(default='Parameter')
        selected_par : StringProperty(default='',update = updateNode)

        cell_in : FloatProperty( name="cell_in", description='cell_in', default=0.0 )

        def draw_buttons(self, context, layout):

            col = layout.column(align=True)
            if self.inputs['File Path'].is_linked:
                self.wrapper_tracked_ui_draw_op(
                    col, SvShowFcstdSpreadsheetsOp.bl_idname, 
                    icon= 'TRIA_DOWN',
                    text= self.selected_label )


            if self.inputs['File Path'].is_linked:
                self.wrapper_tracked_ui_draw_op(
                    col, SvShowFcstdParNamesOp.bl_idname, 
                    icon= 'TRIA_DOWN',
                    text= self.selected_par_label )

            col.prop(self, 'write_parameter')   


        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")
            self.inputs.new('SvStringsSocket', "cell_in").prop_name = 'cell_in'

            self.outputs.new('SvStringsSocket', "cell_out")   

        def process(self):

            #if not any(socket.is_linked for socket in self.outputs):
                #return

            if not self.inputs['File Path'].is_linked:
                return 

            if self.selected_par != '' :

                files = self.inputs['File Path'].sv_get()[0]

                cell_out=None

                for f in files:
                    cell_out = WriteParameter( 
                        f, 
                        self.selected_sheet, 
                        self.selected_par, 
                        self.inputs['cell_in'].sv_get()[0][0], 
                        self.write_parameter)

                print ('DDDDDDDDDDDDDDDDDIOOOOOOOOOOOOOOOOOOOOOOOOOOO,', cell_out)
                if cell_out != None:
                    
                    self.outputs['cell_out'].sv_set( [ [[cell_out]] ] )

            else:
                self.outputs['cell_out'].sv_set( [ ] )
                return

    class SvShowFcstdSpreadsheetsOp(bpy.types.Operator):
        bl_idname = "node.sv_show_fcstd_spreadsheets"
        bl_label = "Show spreadsheet list"
        bl_options = {'INTERNAL', 'REGISTER'}
        bl_property = "option"

        def LabelReader(self,context):
            labels=[('','','')]

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
            fc_file_list = node.inputs['File Path'].sv_get()[0]

            try:
                for f in fc_file_list:
                    F.open(f) 
                    Fname = bpy.path.display_name_from_filepath(f)
                    F.setActiveDocument(Fname)

                    for obj in F.ActiveDocument.Objects:
                        if obj.Module == 'Spreadsheet':
                            labels.append( (obj.Label, obj.Label, obj.Label) )

            except:
                info('LabelReader Spreadsheet error') 
            finally:
                F.closeDocument(Fname)
            
            return labels
              
        option : EnumProperty(items=LabelReader)
        idtree : StringProperty()
        idname : StringProperty() 

        def execute(self, context):

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
            node.name_filter = self.option
            node.selected_label = self.option
            node.selected_sheet = self.option
            bpy.context.area.tag_redraw()
            return {'FINISHED'}

        def invoke(self, context, event):
            context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
            wm = context.window_manager
            wm.invoke_search_popup(self)
            return {'FINISHED'}
   
    class SvShowFcstdParNamesOp(bpy.types.Operator):
        bl_idname = "node.sv_show_fcstd_par_names"
        bl_label = "Show parameter list"
        bl_options = {'INTERNAL', 'REGISTER'}
        bl_property = "option"

        def LabelReader(self,context):
            labels=[('','','')]

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
            fc_file_list = node.inputs['File Path'].sv_get()[0]

            try:

                for f in fc_file_list:
                    F.open(f) 
                    Fname = bpy.path.display_name_from_filepath(f)
                    F.setActiveDocument(Fname)

                    for obj in F.ActiveDocument.Objects:

                        if obj.Label == node.selected_sheet:
                            props = obj.PropertiesList
                            for label in props:
                                alias = obj.getCellFromAlias(label)
                                if alias:
                                    labels.append( (label, label, label) )
            
            except:
                info('Label reader read cell error')  
            
            finally:
                F.closeDocument(Fname)
            
            return labels

        option : EnumProperty(items=LabelReader)
        idtree : StringProperty()
        idname : StringProperty() 

        def execute(self, context):

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
            node.name_filter = self.option
            node.selected_par_label = self.option
            node.selected_par = self.option
            bpy.context.area.tag_redraw()
            return {'FINISHED'}

        def invoke(self, context, event):
            context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
            wm = context.window_manager
            wm.invoke_search_popup(self)
            return {'FINISHED'}

def WriteParameter(fc_file,spreadsheet,alias,par_write,write):

    #___________________GET FC FILE

    try:
        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)
        
        #___________________SEARCH FOR SKETCHES
        cell_out = None

        for obj in F.ActiveDocument.Objects:

            if obj.Label == spreadsheet:

                if alias in obj.PropertiesList:
                    cell = obj.getCellFromAlias(alias)
                    if write:
                        obj.set(cell,str(par_write))
                        F.ActiveDocument.recompute()
                        F.getDocument(Fname).save()
                    
                    cell_out = obj.get(cell)
                    break
    
    except:
        info('WriteParameter error')

    finally:
        F.closeDocument(Fname)

    return cell_out



def register():
    bpy.utils.register_class(SvFCStdSpreadsheetNode)
    bpy.utils.register_class(SvShowFcstdSpreadsheetsOp)
    bpy.utils.register_class(SvShowFcstdParNamesOp)

def unregister():
    bpy.utils.unregister_class(SvFCStdSpreadsheetNode)
    bpy.utils.register_class(SvShowFcstdSpreadsheetsOp)
    bpy.utils.register_class(SvShowFcstdParNamesOp)